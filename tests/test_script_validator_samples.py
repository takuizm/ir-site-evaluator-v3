"""ScriptValidator 回帰テスト一括ランナー"""
from __future__ import annotations

from typing import Callable, List, Tuple
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests import test_script_validator_navigation as nav_tests
from tests import test_script_validator_content as content_tests


def run_test(name: str, func: Callable[[], None]) -> Tuple[str, bool]:
    try:
        func()
        print(f"PASS   - {name}")
        return name, True
    except AssertionError as exc:
        print(f"FAIL   - {name}: {exc}")
        return name, False
    except Exception as exc:
        print(f"ERROR  - {name}: {exc}")
        return name, False


def main():
    print("=" * 60)
    print("Script Validator Regression Suite")
    print("=" * 60)

    tests: List[Tuple[str, Callable[[], None]]] = [
        ("Menu Count", nav_tests.test_menu_count_pass_and_fail),
        ("Menu Keyword", nav_tests.test_menu_keyword_detection),
        ("Breadcrumb", nav_tests.test_breadcrumb_detection),
        ("Back To Top", nav_tests.test_back_to_top_button),
        ("Footer Navigation", nav_tests.test_footer_navigation),
        ("Sitemap Link", nav_tests.test_sitemap_link),
        ("Ambiguous Link", content_tests.test_ambiguous_link_detection),
        ("Cookie Policy", content_tests.test_cookie_policy_link),
        ("Cookie Consent", content_tests.test_cookie_consent_banner),
        ("PDF Icon", content_tests.test_pdf_icon_indicator),
        ("PDF New Window", content_tests.test_pdf_new_window_requirement),
        ("Scroll Area", content_tests.test_scroll_area_detection),
        ("External Link Icon", content_tests.test_external_link_icon),
        ("Font Size >12px", content_tests.test_font_size_not_too_small),
        ("Font Size >=16px", content_tests.test_font_size_large_enough),
        ("Line Height >=1.5", content_tests.test_line_height_requirement),
        ("ROE Data", content_tests.test_roe_data_detection),
        ("Equity Ratio", content_tests.test_equity_ratio_detection),
        ("PBR Data", content_tests.test_pbr_data_detection),
        ("Financial Statements Link", content_tests.test_financial_statements_link),
        ("Securities Report Link", content_tests.test_securities_report_link),
        ("First View PDF Link", content_tests.test_latest_document_link),
        ("Search Input Visible", content_tests.test_search_input_visible),
        ("Recommended Browsers", content_tests.test_recommended_browsers),
    ]

    results = [run_test(name, func) for name, func in tests]
    passed = sum(1 for _, ok in results if ok)
    print("-" * 60)
    print(f"Total: {passed}/{len(tests)} scenarios passed")
    print("=" * 60)
    return passed == len(tests)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
