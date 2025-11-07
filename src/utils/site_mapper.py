"""IRサイト構造マッピングモジュール

IRトップページから主要なサブページURLを自動検出し、
各検証項目に適したページURLを提供する。
"""

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Set
from playwright.async_api import Page
from loguru import logger


@dataclass
class SiteMap:
    """IRサイトの構造マップ"""
    ir_top_url: str
    discovered_urls: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self):
        """カテゴリの初期化"""
        if not self.discovered_urls:
            self.discovered_urls = {
                'ir_top': [self.ir_top_url],
                'financial': [],      # 財務・業績ハイライト
                'library': [],        # IR資料室・ライブラリ
                'governance': [],     # ガバナンス・コーポレートガバナンス
                'officers': [],       # 役員情報・役員一覧
                'esg': [],           # ESG・サステナビリティ
                'individual': [],    # 個人投資家向け
                'news': [],          # IRニュース
                'stock': [],         # 株式情報
                'calendar': [],      # IRカレンダー
                'english_top': [],   # 英語ページ（18項目の検証に必須）
            }

    def get_best_url(self, category: str) -> str:
        """カテゴリの最適URLを取得（なければIRトップ）"""
        if category in self.discovered_urls and self.discovered_urls[category]:
            return self.discovered_urls[category][0]
        return self.ir_top_url


class SiteMapper:
    """IRサイトの構造を自動マッピング"""

    # カテゴリ別キーワード定義
    CATEGORY_KEYWORDS = {
        'financial': [
            '財務', '業績', 'ハイライト', 'financial', 'highlights',
            'performance', '決算', 'results', '財務情報'
        ],
        'library': [
            '資料室', 'ライブラリ', 'library', '資料', 'documents',
            'IR資料', 'IRライブラリ',
            # 追加: 企業ごとの表記ゆれに対応
            '情報', 'materials', 'publications', 'disclosure',
            '開示資料', '説明会資料'
        ],
        'governance': [
            'ガバナンス', 'governance', 'コーポレートガバナンス',
            'corporate governance', '統治'
        ],
        'officers': [
            '役員', '経営陣', 'officers', 'management', '取締役',
            '監査役', 'board', 'directors', '役員一覧'
        ],
        'esg': [
            'ESG', 'サステナビリティ', 'sustainability', 'CSR',
            'サステナビリティ', '環境', '社会', 'マテリアリティ'
        ],
        'individual': [
            '個人投資家', 'individual', 'investors', '株主',
            'shareholders', '個人株主'
        ],
        'news': [
            'ニュース', 'news', 'プレスリリース', 'press release',
            'お知らせ', 'IRニュース'
        ],
        'stock': [
            '株式', '株価', 'stock', 'share', '株主還元',
            'dividend', '配当'
        ],
        'calendar': [
            'カレンダー', 'calendar', 'スケジュール', 'schedule',
            'イベント', 'events'
        ],
        'english_top': [
            # 英語ページ検出用（18項目の検証に必須）
            'english', 'en/', '/en', 'global', 'グローバル',
            'investors', 'ir/en', 'english/', '/en/',
            'investor relations', '/global', 'global/', 'en.html'
        ],
    }

    def __init__(self):
        """初期化"""
        pass

    async def map_site(self, page: Page, ir_top_url: str, max_links: int = 200) -> SiteMap:
        """IRサイトの構造をマッピング

        Args:
            page: Playwrightページオブジェクト（既に開いている）
            ir_top_url: IRトップページURL
            max_links: 収集する最大リンク数

        Returns:
            SiteMap: サイト構造マップ
        """
        site_map = SiteMap(ir_top_url=ir_top_url)

        try:
            logger.info(f"Mapping site structure: {ir_top_url}")

            # リンク要素を取得
            link_elements = await page.locator('a').all()
            logger.debug(f"Found {len(link_elements)} link elements")

            # リンクを収集
            processed_count = 0
            for link_elem in link_elements[:max_links]:
                if processed_count >= max_links:
                    break

                try:
                    href = await link_elem.get_attribute('href')
                    text = await link_elem.inner_text()

                    if not href or not text:
                        continue

                    # 絶対URLに変換
                    absolute_url = urljoin(ir_top_url, href)

                    # 同一ドメインのみ対象
                    if not self._is_same_domain(ir_top_url, absolute_url):
                        continue

                    # アンカーリンク、PDF、外部リンクを除外
                    if self._should_skip_url(absolute_url):
                        continue

                    # テキストからカテゴリを判定
                    category = self._categorize_link(text, absolute_url)
                    if category and category != 'ir_top':
                        if absolute_url not in site_map.discovered_urls[category]:
                            site_map.discovered_urls[category].append(absolute_url)
                            logger.debug(f"Categorized: {category} -> {text} ({absolute_url})")

                    processed_count += 1

                except Exception as e:
                    logger.debug(f"Failed to process link: {e}")
                    continue

            # 検出結果をログ出力
            self._log_discovered_urls(site_map)

            return site_map

        except Exception as e:
            logger.error(f"Site mapping failed: {e}")
            # エラー時もIRトップのみのマップを返す
            return site_map

    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        """同一ドメインかチェック"""
        base_domain = urlparse(base_url).netloc
        target_domain = urlparse(target_url).netloc
        return base_domain == target_domain

    def _should_skip_url(self, url: str) -> bool:
        """スキップすべきURLかチェック"""
        # アンカーリンク
        if '#' in url and url.split('#')[0] == '':
            return True

        # PDF、ZIP等のファイル
        file_extensions = ['.pdf', '.zip', '.xls', '.xlsx', '.csv', '.ppt', '.pptx']
        if any(url.lower().endswith(ext) for ext in file_extensions):
            return True

        # 外部サイトへのリンク（mailto, tel, javascript等）
        if url.startswith(('mailto:', 'tel:', 'javascript:')):
            return True

        return False

    def _categorize_link(self, text: str, url: str) -> Optional[str]:
        """リンクテキストとURLからカテゴリを判定

        Args:
            text: リンクテキスト
            url: リンクURL

        Returns:
            カテゴリ名（該当なしの場合None）
        """
        # テキストとURLを小文字化して検索
        text_lower = text.lower().strip()
        url_lower = url.lower()
        combined = f"{text_lower} {url_lower}"

        # 各カテゴリのキーワードでマッチング
        category_scores = {}

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # テキストに完全一致
                if keyword.lower() in text_lower:
                    score += 10
                # URLに含まれる
                elif keyword.lower() in url_lower:
                    score += 5

            if score > 0:
                category_scores[category] = score

        # 最もスコアの高いカテゴリを返す
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            return best_category[0]

        return None

    def _log_discovered_urls(self, site_map: SiteMap):
        """検出されたURLをログ出力"""
        logger.info("Site mapping completed:")
        for category, urls in site_map.discovered_urls.items():
            if urls and category != 'ir_top':
                logger.info(f"  {category}: {len(urls)} URLs")
                for url in urls[:3]:  # 最初の3つのみ表示
                    logger.debug(f"    - {url}")
