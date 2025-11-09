"""NOT_SUPPORTED 観点の理由管理

共通の理由テキストを返して ValidationResult.details を統一する。
"""
from __future__ import annotations

from typing import Optional

from src.models import ValidationItem

# 観点固有の理由（item_id ベース）
ITEM_REASON_MAP = {
    # サイト内検索やフィルタ系（英語サイト含む）
    44: 'サイト内検索やフィルタ操作の自動再現が必要なため、現行パイプラインでは測定できません。',
    47: 'カテゴリ絞り込みは動的検索UIの操作が必要で、現行パイプラインでは未サポートです。',
    51: '検索結果のファイル種別フィルタは対話操作が必須のため、自動測定に対応していません。',
    52: '検索結果のチューニング有無は動的挙動の比較が必要で、現行パイプラインでは測定できません。',
    234: 'ニュース検索はフリーワード入力と結果取得が必要で、対話操作を自動化していないため測定不可です。',
    235: 'ニュース内容別ソートはフィルタUIの操作が前提で、現行パイプラインでは測定できません。',
    # Web Vitals / パフォーマンス計測
    53: 'Action Duration を評価するには実ブラウザでのパフォーマンス計測が必要なため、現行パイプラインでは測定できません。',
    54: 'Action Duration 1秒基準は実測環境が必要なため、現行パイプラインでは測定できません。',
    55: 'Largest Contentful Paint (LCP) は Web Vitals 計測が必要なため未サポートです。',
    56: '稼働率は監視ログや外部モニタリングが必要なため、本ツールでは測定できません。',
    57: 'Cumulative Layout Shift (CLS) は連続描画の追跡が必要で、静的取得では算出できません。',
    58: 'Time To First Byte (TTFB) はネットワーク計測が必要なため、現行パイプラインでは測定できません。',
    59: 'Speed Index は動画キャプチャ解析が必要で、現行パイプラインでは測定できません。',
    # セキュリティ / ログ計測系
    62: 'TLS バージョンの確認にはネットワーク層の検証が必要で、ブラウザDOMだけでは判定できません。',
    63: 'TLS1.0/1.1 無効化はサーバ設定の検証が必要なため、現行パイプラインでは測定できません。',
    64: '統合報告書のプロテクト有無はPDFメタ情報の解析が必要で、現行パイプラインでは測定できません。',
    65: '正常URL率は全ページのクロール＆監視ログが必要なため、本ツールでは測定できません。',
    66: '404エラー率の算出には全リソース監視が必要で、現行パイプラインでは測定できません。',
    67: '重複/正規化エラー率は全ページクロールが前提のため、現行パイプラインでは測定できません。',
    68: '混在コンテンツ比率の測定には全リソース解析が必要で、現行パイプラインでは測定できません。',
}

# キーワードルール（item_idが変わっても検知できるように）
KEYWORD_RULES = [
    {
        'keywords': ['action duration', 'アクションデュレーション'],
        'reason': 'Action Duration（表示速度）は実ブラウザでの計測が必要なため、現行パイプラインでは測定できません。'
    },
    {
        'keywords': ['largest contentful paint', 'lcp'],
        'reason': 'Largest Contentful Paint (LCP) は Web Vitals 計測が必要なため未サポートです。'
    },
    {
        'keywords': ['cumulative layout shift', 'cls'],
        'reason': 'Cumulative Layout Shift (CLS) は連続描画の追跡が必要で、静的取得では算出できません。'
    },
    {
        'keywords': ['time to first byte', 'ttfb'],
        'reason': 'Time To First Byte (TTFB) はネットワーク計測が必要なため、現行パイプラインでは測定できません。'
    },
    {
        'keywords': ['speed index'],
        'reason': 'Speed Index は動画キャプチャ解析が必要で、現行パイプラインでは測定できません。'
    },
    {
        'keywords': ['稼働率', 'uptime'],
        'reason': '稼働率/アップタイムは監視ログとの連携が必須なため、本ツールでは測定できません。'
    }
]


def get_not_supported_reason(item: ValidationItem) -> Optional[str]:
    """観点が NOT_SUPPORTED かどうかを判定し、理由を返す。"""
    if item.item_id in ITEM_REASON_MAP:
        return ITEM_REASON_MAP[item.item_id]

    text = f"{item.item_name} {item.instruction or ''}".lower()
    for rule in KEYWORD_RULES:
        if any(keyword.lower() in text for keyword in rule['keywords']):
            return rule['reason']

    return None
