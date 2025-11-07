"""Webスクレイピング

Playwrightを使用したWebページ取得機能を提供する。
"""
from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright
from typing import Optional
import asyncio
from pathlib import Path


class Scraper:
    """Playwrightラッパー

    Webページの取得、DOM操作、スクリーンショット取得などを提供する。
    """

    def __init__(self, config, logger):
        """初期化

        Args:
            config: ScrapingConfig インスタンス
            logger: ロガーインスタンス
        """
        self.config = config
        self.logger = logger
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def initialize(self):
        """ブラウザを初期化する"""
        self.logger.info("Initializing browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless,
            args=['--disable-blink-features=AutomationControlled']  # ボット検出回避
        )
        self.context = await self.browser.new_context(
            user_agent=self.config.user_agent,
            viewport={'width': 1920, 'height': 1080},
            locale='ja-JP',
            timezone_id='Asia/Tokyo',
            extra_http_headers={
                'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        )
        self.logger.info("Browser initialized successfully")

    async def get_page(self, url: str, retries: int = 3) -> Page:
        """ページを取得する

        Args:
            url: 取得するURL
            retries: リトライ回数

        Returns:
            Pageインスタンス

        Raises:
            Exception: ページ取得に失敗した場合
        """
        if not self.context:
            await self.initialize()

        page = await self.context.new_page()

        # JavaScript Injection（ボット検出回避）
        await page.add_init_script("""
            // navigator.webdriverを削除
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Chrome automation拡張を隠す
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // languagesを設定
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ja-JP', 'ja', 'en-US', 'en']
            });
        """)

        for attempt in range(retries):
            try:
                self.logger.debug(f"Loading page: {url} (attempt {attempt + 1}/{retries})")

                response = await page.goto(
                    url,
                    wait_until=self.config.wait_until,
                    timeout=self.config.timeout * 1000
                )

                # HTTPステータスコードをチェック
                if response:
                    status = response.status
                    if status == 403:
                        raise Exception(f"Access forbidden (403): {url} - Bot detection triggered")
                    elif status == 404:
                        raise Exception(f"Page not found (404): {url}")
                    elif status >= 400:
                        raise Exception(f"HTTP error {status}: {url}")

                # 追加待機
                await page.wait_for_timeout(int(self.config.delay_after_load * 1000))

                self.logger.debug(f"Page loaded successfully: {url}")
                return page

            except Exception as e:
                self.logger.warning(
                    f"Failed to load page (attempt {attempt + 1}/{retries}): {url} - {e}"
                )
                if attempt == retries - 1:
                    # 最後の試行でも失敗した場合
                    if self.config.screenshot_on_error:
                        screenshot_path = f"output/error_screenshots/{Path(url).name}_{attempt}.png"
                        await self.save_screenshot(page, screenshot_path)
                    raise Exception(f"Failed to load page after {retries} attempts: {url}") from e

                # リトライ前に待機
                await asyncio.sleep(2 ** attempt)  # 指数バックオフ

    async def save_screenshot(self, page: Page, filepath: str):
        """スクリーンショットを保存する

        Args:
            page: Pageインスタンス
            filepath: 保存先パス
        """
        try:
            screenshot_path = Path(filepath)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.debug(f"Screenshot saved: {filepath}")
        except Exception as e:
            self.logger.warning(f"Failed to save screenshot: {filepath} - {e}")

    async def extract_html(self, page: Page) -> str:
        """HTMLコンテンツを抽出する

        Args:
            page: Pageインスタンス

        Returns:
            HTML文字列
        """
        return await page.content()

    async def evaluate_script(self, page: Page, script: str):
        """JavaScriptを実行する

        Args:
            page: Pageインスタンス
            script: 実行するJavaScriptコード

        Returns:
            実行結果
        """
        return await page.evaluate(script)

    async def close_page(self, page: Page):
        """ページを閉じる

        Args:
            page: Pageインスタンス
        """
        try:
            await page.close()
        except Exception as e:
            self.logger.warning(f"Failed to close page: {e}")

    async def close(self):
        """ブラウザを閉じる"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.warning(f"Failed to close browser: {e}")

    async def __aenter__(self):
        """非同期コンテキストマネージャー (enter)"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー (exit)"""
        await self.close()
