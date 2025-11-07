"""LLM検証エンジン

LLMを使用したセマンティック判定を行う。
"""
from src.models import Site, ValidationItem, ValidationResult, LLMResponse
from datetime import datetime
from playwright.async_api import Page
from bs4 import BeautifulSoup
import re


class LLMValidator:
    """LLM検証エンジン

    23項目のLLMベース検証を実行する。
    """

    def __init__(self, llm_client, logger):
        """初期化

        Args:
            llm_client: LLMClientインスタンス
            logger: ロガーインスタンス
        """
        self.llm_client = llm_client
        self.logger = logger

    async def validate(self, site: Site, page: Page, item: ValidationItem, checked_url: str) -> ValidationResult:
        """LLM検証を実行する

        Args:
            site: サイト情報
            page: Playwrightページインスタンス
            item: 検証項目
            checked_url: 実際に調査したページのURL

        Returns:
            ValidationResult
        """
        try:
            # 1. HTML抽出
            html_content = await page.content()

            # 2. HTML前処理（トークン削減）
            cleaned_html = self.preprocess_html(html_content)

            # DEBUG: HTMLの長さとサンプルをログ
            self.logger.debug(f"Cleaned HTML length: {len(cleaned_html)}")
            self.logger.debug(f"Cleaned HTML sample (first 300 chars): {cleaned_html[:300]}")

            # 3. プロンプト構築
            prompt = self.build_prompt(item)

            # 4. LLM呼び出し
            self.logger.debug(f"Calling LLM for item {item.item_id}: {item.item_name}")
            llm_response_text = self.llm_client.call(prompt, cleaned_html)

            # 5. 応答パース
            llm_response = LLMResponse.from_json(llm_response_text)

            # 6. ValidationResult作成
            return ValidationResult(
                site_id=site.site_id,
                company_name=site.company_name,
                url=site.url,
                item_id=item.item_id,
                item_name=item.item_name,
                category=item.category,
                subcategory=item.subcategory,
                result='PASS' if llm_response.found else 'FAIL',
                confidence=llm_response.confidence,
                details=llm_response.details,
                checked_at=datetime.now(),
                checked_url=checked_url
            )

        except Exception as e:
            self.logger.error(f"LLM validation error for item {item.item_id}: {e}")
            return self._create_error_result(site, item, str(e), checked_url)

    def preprocess_html(self, html: str, max_chars: int = 15000) -> str:
        """HTML前処理（トークン削減）

        Args:
            html: 元のHTML
            max_chars: 最大文字数

        Returns:
            クリーニングされたテキスト
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # 不要タグ削除
            for tag in soup(['script', 'style', 'noscript', 'svg', 'iframe']):
                tag.decompose()

            # コメント削除
            from bs4 import Comment
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            # テキスト抽出
            text = soup.get_text(separator='\n', strip=True)

            # 連続する空白を削除
            text = re.sub(r'\n+', '\n', text)
            text = re.sub(r' +', ' ', text)

            # 文字数制限
            return text[:max_chars]

        except Exception as e:
            self.logger.warning(f"HTML preprocessing failed: {e}")
            return html[:max_chars]

    def build_prompt(self, item: ValidationItem) -> str:
        """プロンプト構築

        Args:
            item: 検証項目

        Returns:
            プロンプト文字列
        """
        return f"""あなたは企業IRサイト評価の専門家です。
投資家向け情報（IR）ページの品質を評価しています。

## 評価項目
「{item.item_name}」

## 判定基準
{item.instruction}

## 重要な判定ポイント
- このページは企業の投資家向け情報（IR）ページです
- 財務情報、業績データ、経営方針などのIR関連コンテンツを探してください
- 明確な証拠がある場合のみPASS（found: true）と判定してください
- 曖昧な場合や不確実な場合はFAIL（found: false）と判定してください

## 判定例

### PASS例:
テキスト内に「IRニュース一覧」というセクションがあり、複数のニュース項目と日付が記載されている
→ {{ "found": true, "confidence": 0.9, "details": "IRニュース一覧セクションが存在し、複数の適時開示情報が掲載されている" }}

### FAIL例:
テキスト内に「ニュース」はあるが、IRやプレスリリースと区別できない
→ {{ "found": false, "confidence": 0.7, "details": "一般的なニュースは確認できたが、IR専用のニュース一覧は確認できない" }}

## 出力形式
以下のJSON形式のみを返してください（JSON以外の説明は一切不要）:

{{
  "found": true/false,
  "confidence": 0.0-1.0,
  "details": "判定の根拠を具体的に説明（100文字以内）"
}}

判定を開始してください。"""

    async def validate_with_html(self, site: Site, html_content: str, item: ValidationItem, checked_url: str) -> ValidationResult:
        """HTML文字列を直接受け取って検証を実行する（並列実行対応）

        Args:
            site: サイト情報
            html_content: HTML文字列（事前取得済み）
            item: 検証項目
            checked_url: 実際に調査したページのURL

        Returns:
            ValidationResult
        """
        try:
            # 1. HTML前処理（トークン削減）
            cleaned_html = self.preprocess_html(html_content)

            # DEBUG: HTMLの長さとサンプルをログ
            self.logger.debug(f"Cleaned HTML length: {len(cleaned_html)}")
            self.logger.debug(f"Cleaned HTML sample (first 300 chars): {cleaned_html[:300]}")

            # 2. プロンプト構築
            prompt = self.build_prompt(item)

            # 3. LLM呼び出し
            self.logger.debug(f"Calling LLM for item {item.item_id}: {item.item_name}")
            llm_response_text = self.llm_client.call(prompt, cleaned_html)

            # 4. 応答パース
            llm_response = LLMResponse.from_json(llm_response_text)

            # 5. ValidationResult作成
            return ValidationResult(
                site_id=site.site_id,
                company_name=site.company_name,
                url=site.url,
                item_id=item.item_id,
                item_name=item.item_name,
                category=item.category,
                subcategory=item.subcategory,
                result='PASS' if llm_response.found else 'FAIL',
                confidence=llm_response.confidence,
                details=llm_response.details,
                checked_at=datetime.now(),
                checked_url=checked_url
            )

        except Exception as e:
            self.logger.error(f"LLM validation error for item {item.item_id}: {e}")
            return self._create_error_result(site, item, str(e), checked_url)

    def _create_error_result(self, site: Site, item: ValidationItem, error_msg: str, checked_url: str = None) -> ValidationResult:
        """エラー結果を作成"""
        return ValidationResult(
            site_id=site.site_id,
            company_name=site.company_name,
            url=site.url,
            item_id=item.item_id,
            item_name=item.item_name,
            category=item.category,
            subcategory=item.subcategory,
            result='ERROR',
            confidence=0.0,
            details=error_msg,
            checked_at=datetime.now(),
            checked_url=checked_url,
            error_message=error_msg
        )
