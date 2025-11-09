"""LLM検証エンジン

LLMを使用したセマンティック判定を行う。
"""
from src.models import Site, ValidationItem, ValidationResult, LLMResponse
from src.utils.structure_extractor import summarize_structure, extract_structure
from src.utils.not_supported import get_not_supported_reason
from datetime import datetime
from playwright.async_api import Page
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
import re

STRUCTURE_KEYWORDS = [
    'メニュー', 'ナビ', 'breadcrumb', 'パンくず', 'マウス', 'マウスオーバー',
    '色', 'カラー', 'フォント', 'レイアウト', 'ボタン', '図', 'グラフ',
    'チャート', '画像', '動画', 'pdf', 'ダウンロード'
]

# カテゴリ / サブカテゴリ単位のテンプレート（docs/llm_prompt_templates.md と連動）
CATEGORY_HINTS: Dict[Tuple[str, str], List[str]] = {
    ('ウェブサイトの使いやすさ', 'メニューとナビゲーション'): [
        'メニュー見出しやリンク文言を引用し、観点で求められる状態（例: 現在位置の強調、同一デザイン、横移動可否）が確認できる場合のみ PASS としてください。',
    ],
    ('ウェブサイトの使いやすさ', 'デザインとアクセシビリティ'): [
        '色・フォント・レイアウトに関する具体的な記述を証拠として示し、要件を満たさない場合は FAIL としてください。',
    ],
    ('企業・経営情報の充実度', '事業内容と経営戦略'): [
        '中期経営計画や定量目標、ビジョンなど経営戦略に関する具体的な文章を引用し、条件を満たす場合のみ PASS としてください。',
    ],
    ('企業・経営情報の充実度', 'ESGへの取り組み'): [
        'サステナビリティ/ESGセクションから施策や KPI の記述を抜粋し、観点要件と一致する場合のみ PASS としてください。',
    ],
    ('情報公開の透明性', 'IR資料'): [
        'IR資料のタイトル・発行年・フォーマットを列挙し、観点が求める資料（例: 統合報告書、決算短信）が揃っている場合のみ PASS としてください。',
    ],
}

CATEGORY_ONLY_HINTS: Dict[str, List[str]] = {
    'ウェブサイトの使いやすさ': [
        'UI/UX の根拠を具体的な要素名やテキストで説明し、証拠が不十分な場合は FAIL としてください。'
    ],
    '企業・経営情報の充実度': [
        '経営・ESG 情報は公式な記述や定量的根拠がない限り PASS にしないでください。'
    ],
}

ITEM_HINTS: Dict[int, List[str]] = {
    190: ['ESG KPI や進捗状況を示す数値表現が本文にある場合のみ PASS としてください。'],
    221: ['IR担当の電話番号・部署名など具体的な連絡先が本文にあるか確認し、連絡先が曖昧なら FAIL としてください。'],
    24: ['IRニュース一覧で適時開示・プレスリリースの区別方法（タグ/アイコン/ラベル）を説明し、根拠が確認できない場合は FAIL にしてください。'],
    32: ['リンクテキストと周辺文を引用し、「詳しくはこちら」など目的不明な表現が多い場合は FAIL としてください。'],
    41: ['外部サイト（株価、信託銀行など）へ遷移するリンクの注意書きや説明が本文にあるか確認し、無い場合は FAIL としてください。'],
    44: ['IRサイトの検索導線が常設されているか、英語サイトも含めて入力欄が見えるか記述ください。'],
    45: ['検索フォームの入力欄がヘッダー等に常時表示されているか判断し、開閉が必要なら FAIL としてください。'],
    85: ['キャッシュフロー推移のグラフ/図表が公開されているか、5期分以上かどうか本文から判断してください。'],
    93: ['四半期別の決算概況を文章で説明している箇所を要約し、見つからない場合は FAIL としてください。'],
    116: ['決算説明会の質疑応答（Q&A）内容が資料やPDFで提供されているか確認し、案内が無ければ FAIL としてください。'],
}

MAX_HINTS = 5


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
        self.max_context_chars = 30000

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
            reason = get_not_supported_reason(item)
            if reason:
                return ValidationResult(
                    site_id=site.site_id,
                    company_name=site.company_name,
                    url=site.url,
                    item_id=item.item_id,
                    item_name=item.item_name,
                    category=item.category,
                    subcategory=item.subcategory,
                    result='NOT_SUPPORTED',
                    confidence=0.0,
                    details=reason,
                    checked_at=datetime.now(),
                    checked_url=checked_url,
                )

            html_content = await page.content()
            structure = extract_structure(html_content)
            payload = {
                'url': checked_url,
                'html': html_content,
                'structure': structure
            }
            return await self.validate_with_pages(site, item, [payload])

        except Exception as e:
            self.logger.error(f"LLM validation error for item {item.item_id}: {e}")
            return self._create_error_result(site, item, str(e), checked_url)

    def preprocess_html(self, html: str, max_chars: int = 30000) -> str:
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

            # 重複行の除去（完全一致のみ）
            lines = text.split('\n')
            seen_lines = set()
            unique_lines = []
            for line in lines:
                if line and line not in seen_lines:
                    unique_lines.append(line)
                    seen_lines.add(line)
            text = '\n'.join(unique_lines)

            # 文字数制限（スマート切り詰め: 前半70% + 後半30%）
            if len(text) > max_chars:
                front_chars = int(max_chars * 0.7)
                back_chars = max_chars - front_chars
                text = text[:front_chars] + '\n...(中間省略)...\n' + text[-back_chars:]

            return text

        except Exception as e:
            self.logger.warning(f"HTML preprocessing failed: {e}")
            return html[:max_chars]

    def build_prompt(self, item: ValidationItem) -> str:
        """プロンプト構築"""
        target_page = item.target_page or '（対象ページ指定なし）'
        hints = self._build_prompt_hints(item)
        hints_text = '\n'.join(f"- {hint}" for hint in hints) if hints else "- 特別な追加要件はありません。"

        return f"""あなたは企業IRサイト評価の専門家です。投資家向け情報（IR）ページの品質を評価します。

## 評価項目
「{item.item_name}」

## 判定基準
{item.instruction}

## 調査対象ページ
{target_page}

## 追加要件
{hints_text}

## 判定ルール

### PASS条件（found: true）
- 本文テキストまたは構造情報（メニュー、リンク、見出し等）に、判定基準を満たす**明確な証拠**がある
- 証拠は具体的な文言、セクション名、リンクテキスト、または構造要素として確認できる
- 推測や解釈ではなく、**実際に記載されている内容**に基づいて判断する

### FAIL条件（found: false）
- 本文や構造情報に証拠が見つからない、または不十分
- 判定基準の一部のみを満たす（全体要件を満たさない）
- 関連情報はあるが、判定基準が求める具体性に欠ける

### 信頼度スコア（confidence）の設定基準
- **0.9-1.0**: 判定基準を満たす証拠が複数箇所に明確に記載されている
- **0.7-0.9**: 証拠は1箇所だが明確、または複数箇所だが解釈の余地がある
- **0.5-0.7**: 証拠が間接的、または部分的にのみ基準を満たす
- **0.3-0.5**: 関連情報はあるが証拠として不十分（通常FAIL）
- **0.0-0.3**: 証拠がほぼ存在しない（明確なFAIL）

## 重要な注意事項
1. **架空の情報は絶対に作らない**：本文や構造情報に記載されていない内容を推測で補完しない
2. **構造情報の活用**：メニュー、ナビゲーション、見出し、リンク等の構造要素も重要な証拠として使用する
3. **具体的な証拠の記載**：details には以下を120文字以内で記載
   - PASS時：証拠となる具体的な文言やセクション名（例：「決算短信」「統合報告書」等のリンクあり）
   - FAIL時：何が不足しているか（例：「IR資料リンクなし」「該当セクション未確認」）
4. **厳密な判定**：曖昧な場合は証拠不足としてFAILにする

## 出力形式
JSON形式のみを返してください。他の文字列は一切含めないでください。

{{
  "found": true/false,
  "confidence": 0.0-1.0,
  "details": "証拠または理由を120文字以内で記載"
}}

判定を開始してください。"""

    def _build_prompt_hints(self, item: ValidationItem) -> List[str]:
        text_lower = f"{item.item_name} {item.instruction}".lower()
        hints: List[str] = []
        seen = set()

        def add_hint(value: str):
            if not value:
                return
            if value in seen or len(hints) >= MAX_HINTS:
                return
            hints.append(value)
            seen.add(value)

        category_key = (item.category or '', item.subcategory or '')
        for hint in CATEGORY_HINTS.get(category_key, []):
            add_hint(hint)

        for hint in CATEGORY_ONLY_HINTS.get(item.category or '', []):
            add_hint(hint)

        for hint in ITEM_HINTS.get(item.item_id, []):
            add_hint(hint)

        keyword_hints = [
            (['グラフ', 'graph', 'chart', '推移'],
             'グラフ/チャートの存在と内容を確認し、指標名（例: 売上高・経常利益・純利益）が記載されているか判断してください。'),
            (['faq', 'よくある質問'],
             'FAQ や Q&A 形式の見出しがあるか確認し、代表的な質問が掲載されている場合のみ PASS としてください。'),
            (['ニュース', 'news', 'リリース'],
             'IRニュースやプレスリリースの一覧が明確に区別されているかを確認し、一般ニュースだけの場合は FAIL としてください。'),
            (['ガバナンス', 'governance'],
             'コーポレートガバナンスに関する具体的な記述（取締役会構成、コーポレートガバナンス報告書等）がある場合のみ PASS としてください。'),
            (['株価', 'stock'],
             '株価情報に関連指標（時価総額、最低購入代金など）が併記されているかを確認してください。'),
        ]

        for keywords, hint in keyword_hints:
            if any(keyword in text_lower for keyword in keywords):
                add_hint(hint)

        return hints

    async def validate_with_html(self, site: Site, html_content: str, item: ValidationItem, checked_url: str) -> ValidationResult:
        """HTML文字列を直接受け取って検証を実行する（後方互換用）"""
        payload = {
            'url': checked_url,
            'html': html_content,
            'structure': extract_structure(html_content)
        }
        return await self.validate_with_pages(site, item, [payload])

    async def validate_with_pages(self, site: Site, item: ValidationItem, payloads: list[dict]) -> ValidationResult:
        try:
            context = self._build_context_from_payloads(item, payloads)
            prompt = self.build_prompt(item)

            self.logger.debug(f"Calling LLM for item {item.item_id}: {item.item_name} (pages={len(payloads)})")
            llm_response_text = self.llm_client.call(prompt, context)

            llm_response = LLMResponse.from_json(llm_response_text)
            checked_urls = ','.join(payload.get('url', '') for payload in payloads[:3])

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
                checked_url=checked_urls
            )

        except Exception as e:
            self.logger.error(f"LLM validation error for item {item.item_id}: {e}")
            checked_url = payloads[0].get('url') if payloads else None
            return self._create_error_result(site, item, str(e), checked_url)

    def _build_context_from_payloads(self, item: ValidationItem, payloads: list[dict]) -> str:
        if not payloads:
            return ""

        per_page_limit = max(3000, self.max_context_chars // len(payloads))
        include_structure = self._needs_structure(item)
        sections = []

        for payload in payloads:
            html_text = payload.get('html') or ''
            cleaned_html = self.preprocess_html(html_text, max_chars=per_page_limit)
            block_parts = [f"### Page URL: {payload.get('url', 'N/A')}"]
            block_parts.append(cleaned_html if cleaned_html else "(テキストを抽出できませんでした)")

            if include_structure:
                summary = summarize_structure(payload.get('structure'))
                if summary:
                    block_parts.append("[Structure]\n" + summary)

            sections.append('\n'.join(part for part in block_parts if part).strip())

        return '\n\n'.join(sections)

    def _needs_structure(self, item: ValidationItem) -> bool:
        text = f"{item.item_name} {item.instruction}" if item.instruction else item.item_name
        lower = text.lower()
        for keyword in STRUCTURE_KEYWORDS:
            if keyword in text or keyword in lower:
                return True
        return False

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
