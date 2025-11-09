"""基本動作テスト

実装が正しく動作するかの基本テスト
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """すべての主要モジュールがインポートできることを確認"""
    print("Testing imports...")

    from src.models import Site, ValidationItem, ValidationResult, LLMResponse  # noqa: F401
    from src.config import Config  # noqa: F401
    from src.utils.logger import setup_logger  # noqa: F401
    from src.utils.scraper import Scraper  # noqa: F401
    from src.utils.llm_client import LLMClient  # noqa: F401
    from src.utils.reporter import Reporter  # noqa: F401
    from src.validators.script_validator import ScriptValidator  # noqa: F401
    from src.validators.llm_validator import LLMValidator  # noqa: F401
    from src.main import IRSiteEvaluator  # noqa: F401

    print("✓ All modules imported successfully")


def test_config_loading():
    """config.yaml が読み込めてバリデーションを通ることを確認"""
    print("\nTesting config loading...")

    from src.config import Config

    config_path = project_root / "config.yaml"
    assert config_path.exists(), f"Config file not found: {config_path}"

    config = Config.load(str(config_path))
    print("✓ Config loaded successfully")

    errors = config.validate()
    assert not errors, f"Config validation failed: {errors}"

    print("✓ Config validation passed")


def test_data_models():
    """主要データモデルの基本的な挙動を確認"""
    print("\nTesting data models...")

    from datetime import datetime
    from src.models import Site, ValidationItem, ValidationResult, LLMResponse

    site = Site(
        site_id=1,
        company_name="テスト株式会社",
        url="https://example.com",
        industry="製造業"
    )
    assert site.url == "https://example.com"

    item = ValidationItem(
        item_id=1,
        category="カテゴリ",
        subcategory="サブカテゴリ",
        item_name="テスト項目",
        automation_type="A",
        check_type="script",
        priority="high",
        difficulty=1,
        instruction="テスト指示",
        target_page="TOP",
        original_no=1
    )
    assert item.is_script_validation()

    result = ValidationResult(
        site_id=1,
        company_name="テスト株式会社",
        url="https://example.com",
        item_id=1,
        item_name="テスト項目",
        category="カテゴリ",
        subcategory="サブカテゴリ",
        result="PASS",
        confidence=1.0,
        details="テスト詳細",
        checked_at=datetime.now()
    )
    result_dict = result.to_dict()
    assert result_dict['result'] == 'PASS'

    json_str = '{"found": true, "confidence": 0.8, "details": "テスト詳細"}'
    parsed = LLMResponse.from_json(json_str)
    assert parsed.found is True
    assert parsed.confidence == 0.8

    print("✓ Data models behave as expected")


def test_not_supported_reason():
    """NOT_SUPPORTED理由の共通化が機能しているかを確認"""
    print("\nTesting NOT_SUPPORTED reason registry...")

    from src.models import ValidationItem
    from src.utils.not_supported import get_not_supported_reason

    perf_item = ValidationItem(
        item_id=53,
        category="ウェブサイトの使いやすさ",
        subcategory="パフォーマンスと推奨環境",
        item_name="IRトップページ：Action Duration（表示速度）は2.0秒以下",
        automation_type="D",
        check_type="llm",
        priority="high",
        difficulty=3,
        instruction="Action Durationを測定する。",
        target_page="IRトップ",
        original_no=530
    )
    reason = get_not_supported_reason(perf_item)
    assert reason is not None
    assert "Action Duration" in reason

    supported_item = ValidationItem(
        item_id=1,
        category="カテゴリ",
        subcategory="サブカテゴリ",
        item_name="通常観点",
        automation_type="A",
        check_type="script",
        priority="low",
        difficulty=1,
        instruction="DOMで確認できる項目",
        target_page="TOP",
        original_no=10
    )
    assert get_not_supported_reason(supported_item) is None

    print("✓ NOT_SUPPORTED reasons are consistent")


def test_input_files():
    """入力CSVが存在し、必要なカラムを保持しているかを確認"""
    print("\nTesting input files...")

    import pandas as pd

    sites_csv = project_root / "input" / "sample_sites.csv"
    assert sites_csv.exists(), f"Sites CSV not found: {sites_csv}"
    sites_df = pd.read_csv(sites_csv)
    required_columns = ['site_id', 'company_name', 'url']
    for col in required_columns:
        assert col in sites_df.columns, f"Missing column in sites CSV: {col}"

    items_csv = project_root / "input" / "validation_items.csv"
    assert items_csv.exists(), f"Validation items CSV not found: {items_csv}"
    items_df = pd.read_csv(items_csv)
    required_item_columns = [
        'item_id', 'category', 'subcategory', 'item_name',
        'automation_type', 'check_type', 'priority', 'difficulty',
        'instruction', 'target_page', 'original_no'
    ]
    for col in required_item_columns:
        assert col in items_df.columns, f"Missing column in items CSV: {col}"

    print("✓ Input CSVs are present with required schema")


def run_test(name, func):
    try:
        func()
        print(f"PASS   - {name}")
        return True
    except AssertionError as e:
        print(f"FAIL   - {name}: {e}")
        return False
    except Exception as e:
        print(f"ERROR  - {name}: {e}")
        return False


def main():
    """メインテスト実行"""
    print("=" * 60)
    print("IR Site Evaluator - Basic Tests")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Config Loading Test", test_config_loading),
        ("Data Models Test", test_data_models),
        ("NOT_SUPPORTED Reason Test", test_not_supported_reason),
        ("Input Files Test", test_input_files),
    ]

    results = [(name, run_test(name, func)) for name, func in tests]

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
