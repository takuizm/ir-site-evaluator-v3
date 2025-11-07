"""target_pageとSiteMapカテゴリのマッピング

validation_items.csvのtarget_page列の値を、
SiteMapのカテゴリにマッピングする。
"""

from typing import Optional
from .site_mapper import SiteMap
from ..models import ValidationItem


# target_page → SiteMapカテゴリのマッピング辞書
TARGET_PAGE_TO_CATEGORY = {
    # IRトップページ
    'IRトップ': 'ir_top',
    'IRトップとコーポレートトップ': 'ir_top',
    'グローバルメニュー': 'ir_top',
    'フッター': 'ir_top',
    'Cookieポップアップ': 'ir_top',
    'サイトについて': 'ir_top',
    'IR配下ページ': 'ir_top',
    '全体': 'ir_top',

    # 財務・業績情報
    'IR＞財務、業績ハイライト': 'financial',
    'IR＞財務': 'financial',
    '業績ハイライト': 'financial',

    # IR資料室
    'IR資料室': 'library',
    'IR資料室（ライブラリ）': 'library',
    'IRライブラリ': 'library',
    'IR資料室・IRライブラリ': 'library',  # 追加: 複合表記
    'IR資料室・IRライブラリ、統合報告書PDFを開く': 'library',  # 追加: 詳細指示付き
    '業績ハイライト、IR資料室・IRライブラリにある場合も': 'library',  # 追加: 複数候補

    # 決算・説明会資料
    '決算短信': 'library',  # 追加: 決算短信ページ
    '株主総会': 'library',  # 追加: 株主総会ページ

    # ガバナンス
    'ガバナンス配下': 'governance',
    'ガバナンス': 'governance',
    'コーポレートガバナンス': 'governance',

    # 役員情報
    '役員、役員一覧': 'officers',
    '役員一覧': 'officers',
    '役員': 'officers',
    '経営陣': 'officers',

    # ESG・サステナビリティ
    'サステナビリティ＞マテリアリティ': 'esg',
    'サステナビリティ': 'esg',
    'ESG': 'esg',
    'CSR': 'esg',

    # 個人投資家向け
    '個人投資家向けページ': 'individual',
    '個人株主': 'individual',

    # トップメッセージ（IRトップまたは専用ページ）
    'トップメッセージ': 'officers',  # 役員ページにあることが多い

    # IRニュース
    'IRニュース': 'news',
    'ニュースリリース': 'news',

    # 株式情報
    '株式情報': 'stock',
    '株価': 'stock',
    '株主還元': 'stock',

    # IRカレンダー
    'IRカレンダー': 'calendar',
    'イベント': 'calendar',

    # 英語ページ（18項目の検証に必須）
    '英語トップ': 'english_top',  # 追加
    '英語ページ': 'english_top',  # 追加
    '英語ページ、IRトップ': 'english_top',  # 追加
    '英語ページ、コーポレートトップ': 'english_top',  # 追加
    '英語ページ、トップメッセージ': 'english_top',  # 追加
    '英語ページ、グローバルメニュー': 'english_top',  # 追加
}


def get_target_url(item: ValidationItem, site_map: SiteMap) -> str:
    """検証項目に必要なページURLを取得

    Args:
        item: 検証項目
        site_map: サイトマップ

    Returns:
        対象ページのURL（該当なしの場合はIRトップ）
    """
    # target_pageが空の場合はIRトップ
    if not item.target_page or item.target_page.strip() == '':
        return site_map.ir_top_url

    # マッピング辞書から検索（完全一致）
    target_page_normalized = item.target_page.strip()
    category = TARGET_PAGE_TO_CATEGORY.get(target_page_normalized)

    if category:
        # カテゴリに対応するURLを取得
        return site_map.get_best_url(category)

    # 完全一致がない場合、部分一致でフォールバック（柔軟性向上）
    target_page_lower = target_page_normalized.lower()

    # 英語ページの部分一致（最優先）
    if '英語' in target_page_normalized or 'english' in target_page_lower:
        category = 'english_top'
    # IR資料室・ライブラリの部分一致
    elif 'ライブラリ' in target_page_normalized or '資料室' in target_page_normalized or 'library' in target_page_lower:
        category = 'library'
    # 決算短信・株主総会の部分一致
    elif '決算短信' in target_page_normalized or '株主総会' in target_page_normalized:
        category = 'library'
    # 業績ハイライトの部分一致
    elif '業績' in target_page_normalized or 'ハイライト' in target_page_normalized or 'financial' in target_page_lower:
        category = 'financial'
    # ガバナンスの部分一致
    elif 'ガバナンス' in target_page_normalized or 'governance' in target_page_lower:
        category = 'governance'
    # 役員の部分一致
    elif '役員' in target_page_normalized or '経営陣' in target_page_normalized or 'officers' in target_page_lower:
        category = 'officers'
    # 個人投資家向けの部分一致
    elif '個人投資家' in target_page_normalized or '個人株主' in target_page_normalized:
        category = 'individual'
    # 株式情報の部分一致
    elif '株式' in target_page_normalized or '株価' in target_page_normalized or 'stock' in target_page_lower:
        category = 'stock'
    # カレンダーの部分一致
    elif 'カレンダー' in target_page_normalized or 'calendar' in target_page_lower:
        category = 'calendar'
    else:
        # どれにも該当しない場合はIRトップ
        return site_map.ir_top_url

    return site_map.get_best_url(category)


def get_category_from_target_page(target_page: str) -> Optional[str]:
    """target_pageからカテゴリ名を取得（デバッグ用）

    Args:
        target_page: target_page列の値

    Returns:
        カテゴリ名（該当なしの場合None）
    """
    if not target_page:
        return None

    return TARGET_PAGE_TO_CATEGORY.get(target_page.strip())
