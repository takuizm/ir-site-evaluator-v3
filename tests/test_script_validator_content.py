"""コンテンツ/アクセシビリティ系 ScriptValidator テスト"""
from __future__ import annotations

from tests.mock_page import MockPage
from tests.script_validator_utils import (
    load_fixture,
    make_item,
    make_site,
    make_validator,
    run_async,
)


async def _ambiguous_link_case():
    validator = make_validator()
    site = make_site()
    item = make_item(17, "曖昧リンクテスト")

    clean_page = MockPage(load_fixture("navigation_pass.html"))
    ambiguous_page = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_link_text_not_ambiguous(site, clean_page, item)
    ng = await validator.check_link_text_not_ambiguous(site, ambiguous_page, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _cookie_policy_case():
    validator = make_validator()
    site = make_site()
    item = make_item(23, "Cookieポリシーテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_cookie_policy(site, page_with, item)
    ng = await validator.check_cookie_policy(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _cookie_consent_case():
    validator = make_validator()
    site = make_site()
    item = make_item(24, "Cookie同意テスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_cookie_consent(site, page_with, item)
    ng = await validator.check_cookie_consent(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _pdf_icon_case():
    validator = make_validator()
    site = make_site()
    item = make_item(27, "PDFアイコンテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_pdf_icon(site, page_with, item)
    ng = await validator.check_pdf_icon(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _pdf_new_window_case():
    validator = make_validator()
    site = make_site()
    item = make_item(26, "PDF別ウィンドウテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_pdf_new_window(site, page_with, item)
    ng = await validator.check_pdf_new_window(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _external_link_icon_case():
    validator = make_validator()
    site = make_site()
    item = make_item(18, "外部リンクアイコンテスト")

    page_pass = MockPage(load_fixture("layout_external_link_pass.html"))
    page_fail = MockPage(load_fixture("layout_external_link_fail.html"))

    ok = await validator.check_external_link_icon(site, page_pass, item)
    ng = await validator.check_external_link_icon(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _financial_metric_case(item_id: int, keyword_case: str):
    validator = make_validator()
    site = make_site()
    item = make_item(item_id, keyword_case)

    page_pass = MockPage(load_fixture("layout_financial_metrics_pass.html"))
    page_fail = MockPage(load_fixture("layout_financial_metrics_fail.html"))

    check_map = {
        28: validator.check_roe_data,
        29: validator.check_equity_ratio,
        30: validator.check_pbr_data,
        31: validator.check_financial_statements,
        32: validator.check_securities_report,
    }
    func = check_map[item_id]

    ok = await func(site, page_pass, item)
    ng = await func(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _latest_document_case():
    validator = make_validator()
    site = make_site()
    item = make_item(10, "最新資料テスト")

    page_pass = MockPage(load_fixture("layout_fv_pdf_pass.html"))
    page_fail = MockPage(load_fixture("layout_fv_pdf_fail.html"))

    ok = await validator.check_latest_document_download(site, page_pass, item)
    ng = await validator.check_latest_document_download(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _search_input_case():
    validator = make_validator()
    site = make_site()
    item = make_item(45, "サイト内検索テスト")

    page_pass = MockPage(load_fixture("layout_search_visible.html"))
    page_fail = MockPage(load_fixture("layout_search_hidden.html"))

    ok = await validator.check_search_input_visible(site, page_pass, item)
    ng = await validator.check_search_input_visible(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _recommended_browser_case():
    validator = make_validator()
    site = make_site()
    item = make_item(61, "推奨ブラウザテスト")

    page_pass = MockPage(load_fixture("layout_recommended_browsers_pass.html"))
    page_fail = MockPage(load_fixture("layout_recommended_browsers_fail.html"))

    ok = await validator.check_recommended_browsers(site, page_pass, item)
    ng = await validator.check_recommended_browsers(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


def test_roe_data_detection():
    run_async(_financial_metric_case(28, "ROEテスト"))


def test_equity_ratio_detection():
    run_async(_financial_metric_case(29, "自己資本比率テスト"))


def test_pbr_data_detection():
    run_async(_financial_metric_case(30, "PBRテスト"))


def test_financial_statements_link():
    run_async(_financial_metric_case(31, "決算短信テスト"))


def test_securities_report_link():
    run_async(_financial_metric_case(32, "有価証券報告書テスト"))


def test_latest_document_link():
    run_async(_latest_document_case())


def test_search_input_visible():
    run_async(_search_input_case())


def test_recommended_browsers():
    run_async(_recommended_browser_case())


async def _scroll_area_case():
    validator = make_validator()
    site = make_site()
    item = make_item(5, "スクロールエリアテスト")

    page_pass = MockPage(load_fixture("layout_scroll_pass.html"))
    page_fail = MockPage(load_fixture("layout_scroll_fail.html"))

    ok = await validator.check_no_scroll_areas(site, page_pass, item)
    ng = await validator.check_no_scroll_areas(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _font_size_small_case():
    validator = make_validator()
    site = make_site()
    item = make_item(11, "フォントサイズ最小テスト")

    page_pass = MockPage(load_fixture("layout_typography_pass.html"))
    page_fail = MockPage(load_fixture("layout_typography_fail.html"))

    ok = await validator.check_font_size_not_too_small(site, page_pass, item)
    ng = await validator.check_font_size_not_too_small(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _font_size_large_case():
    validator = make_validator()
    site = make_site()
    item = make_item(12, "フォントサイズ確保テスト")

    page_pass = MockPage(load_fixture("layout_typography_pass.html"))
    page_fail = MockPage(load_fixture("layout_typography_fail.html"))

    ok = await validator.check_font_size_large_enough(site, page_pass, item)
    ng = await validator.check_font_size_large_enough(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _line_height_case():
    validator = make_validator()
    site = make_site()
    item = make_item(13, "行間テスト")

    page_pass = MockPage(load_fixture("layout_typography_pass.html"))
    page_fail = MockPage(load_fixture("layout_typography_fail.html"))

    ok = await validator.check_line_height(site, page_pass, item)
    ng = await validator.check_line_height(site, page_fail, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


def test_ambiguous_link_detection():
    run_async(_ambiguous_link_case())


def test_cookie_policy_link():
    run_async(_cookie_policy_case())


def test_cookie_consent_banner():
    run_async(_cookie_consent_case())


def test_pdf_icon_indicator():
    run_async(_pdf_icon_case())


def test_pdf_new_window_requirement():
    run_async(_pdf_new_window_case())


def test_scroll_area_detection():
    run_async(_scroll_area_case())


def test_external_link_icon():
    run_async(_external_link_icon_case())

def test_font_size_not_too_small():
    run_async(_font_size_small_case())


def test_font_size_large_enough():
    run_async(_font_size_large_case())


def test_line_height_requirement():
    run_async(_line_height_case())
