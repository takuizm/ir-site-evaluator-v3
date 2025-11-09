"""ナビゲーション関連 ScriptValidator テスト"""
from __future__ import annotations

from tests.mock_page import MockPage
from tests.script_validator_utils import (
    load_fixture,
    make_item,
    make_site,
    make_validator,
    run_async,
)


async def _menu_count_case():
    validator = make_validator()
    site = make_site()
    item = make_item(1, "メニュー構成テスト")

    pass_page = MockPage(load_fixture("navigation_pass.html"))
    fail_page = MockPage(load_fixture("navigation_fail.html"))

    pass_result = await validator.check_menu_count(site, pass_page, item)
    fail_result = await validator.check_menu_count(site, fail_page, item)

    assert pass_result.result == "PASS"
    assert fail_result.result == "FAIL"


async def _menu_keyword_case():
    validator = make_validator()
    site = make_site()
    item = make_item(2, "キーワードテスト")

    pass_page = MockPage(load_fixture("navigation_pass.html"))
    fail_page = MockPage(load_fixture("navigation_fail.html"))

    pass_result = await validator.check_menu_investor_keyword(site, pass_page, item)
    fail_result = await validator.check_menu_investor_keyword(site, fail_page, item)

    assert pass_result.result == "PASS"
    assert fail_result.result == "FAIL"


async def _breadcrumb_case():
    validator = make_validator()
    site = make_site()
    item = make_item(3, "パンくずテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_breadcrumb(site, page_with, item)
    ng = await validator.check_breadcrumb(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _back_to_top_case():
    validator = make_validator()
    site = make_site()
    item = make_item(4, "ページトップテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_back_to_top_link(site, page_with, item)
    ng = await validator.check_back_to_top_link(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _footer_nav_case():
    validator = make_validator()
    site = make_site()
    item = make_item(6, "フッターナビテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_footer_navigation(site, page_with, item)
    ng = await validator.check_footer_navigation(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


async def _sitemap_case():
    validator = make_validator()
    site = make_site()
    item = make_item(7, "サイトマップテスト")

    page_with = MockPage(load_fixture("navigation_pass.html"))
    page_without = MockPage(load_fixture("navigation_fail.html"))

    ok = await validator.check_sitemap(site, page_with, item)
    ng = await validator.check_sitemap(site, page_without, item)

    assert ok.result == "PASS"
    assert ng.result == "FAIL"


def test_menu_count_pass_and_fail():
    run_async(_menu_count_case())


def test_menu_keyword_detection():
    run_async(_menu_keyword_case())


def test_breadcrumb_detection():
    run_async(_breadcrumb_case())


def test_back_to_top_button():
    run_async(_back_to_top_case())


def test_footer_navigation():
    run_async(_footer_nav_case())


def test_sitemap_link():
    run_async(_sitemap_case())
