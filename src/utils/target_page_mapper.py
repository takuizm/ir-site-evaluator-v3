"""target_pageとSiteMapカテゴリのマッピング

validation_items.csvのtarget_page列の値を、
SiteMapのカテゴリにマッピングする。
"""

from typing import List, Optional
import re

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


def _resolve_category(target_page_normalized: str) -> Optional[str]:
    if not target_page_normalized:
        return None

    category = TARGET_PAGE_TO_CATEGORY.get(target_page_normalized)
    if category:
        return category

    lower = target_page_normalized.lower()

    if '英語' in target_page_normalized or 'english' in lower:
        return 'english_top'
    if any(keyword in target_page_normalized for keyword in ['ライブラリ', '資料室']) or 'library' in lower:
        return 'library'
    if any(keyword in target_page_normalized for keyword in ['決算短信', '株主総会']):
        return 'library'
    if any(keyword in target_page_normalized for keyword in ['業績', 'ハイライト']) or 'financial' in lower:
        return 'financial'
    if 'ガバナンス' in target_page_normalized or 'governance' in lower:
        return 'governance'
    if any(keyword in target_page_normalized for keyword in ['役員', '経営陣']) or 'officers' in lower:
        return 'officers'
    if any(keyword in target_page_normalized for keyword in ['個人投資家', '個人株主']):
        return 'individual'
    if any(keyword in target_page_normalized for keyword in ['株式', '株価']) or 'stock' in lower:
        return 'stock'
    if 'カレンダー' in target_page_normalized or 'calendar' in lower:
        return 'calendar'
    return None


def _split_target_page(target_page: str) -> List[str]:
    if not target_page:
        return []
    raw_parts = re.split(r'[、,\/]|\s+と\s+|\s+＆\s+|\s+and\s+', target_page)
    return [part.strip() for part in raw_parts if part and part.strip()]


def get_target_urls(item: ValidationItem, site_map: SiteMap) -> List[str]:
    """target_pageに紐づくURL候補を複数返す"""
    if not item.target_page or item.target_page.strip() == '':
        return [site_map.ir_top_url]

    parts = _split_target_page(item.target_page)
    if not parts:
        parts = [item.target_page.strip()]

    urls = []
    seen_categories = set()
    for part in parts:
        category = _resolve_category(part)
        if category:
            if category in seen_categories:
                continue
            seen_categories.add(category)
            urls.append(site_map.get_best_url(category))
        else:
            urls.append(site_map.ir_top_url)

    return urls or [site_map.ir_top_url]


def get_target_url(item: ValidationItem, site_map: SiteMap) -> str:
    """後方互換用: 最初のURLを返す"""
    return get_target_urls(item, site_map)[0]


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
