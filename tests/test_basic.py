"""基本動作テスト

実装が正しく動作するかの基本テスト
"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """すべてのモジュールがインポート可能かテスト"""
    print("Testing imports...")

    try:
        from src.models import Site, ValidationItem, ValidationResult, LLMResponse
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Models import failed: {e}")
        return False

    try:
        from src.config import Config
        print("✓ Config imported successfully")
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        return False

    try:
        from src.utils.logger import setup_logger
        print("✓ Logger imported successfully")
    except Exception as e:
        print(f"✗ Logger import failed: {e}")
        return False

    try:
        from src.utils.scraper import Scraper
        print("✓ Scraper imported successfully")
    except Exception as e:
        print(f"✗ Scraper import failed: {e}")
        return False

    try:
        from src.utils.llm_client import LLMClient
        print("✓ LLM Client imported successfully")
    except Exception as e:
        print(f"✗ LLM Client import failed: {e}")
        return False

    try:
        from src.utils.reporter import Reporter
        print("✓ Reporter imported successfully")
    except Exception as e:
        print(f"✗ Reporter import failed: {e}")
        return False

    try:
        from src.validators.script_validator import ScriptValidator
        print("✓ Script Validator imported successfully")
    except Exception as e:
        print(f"✗ Script Validator import failed: {e}")
        return False

    try:
        from src.validators.llm_validator import LLMValidator
        print("✓ LLM Validator imported successfully")
    except Exception as e:
        print(f"✗ LLM Validator import failed: {e}")
        return False

    try:
        from src.main import IRSiteEvaluator
        print("✓ Main module imported successfully")
    except Exception as e:
        print(f"✗ Main module import failed: {e}")
        return False

    return True


def test_config_loading():
    """設定ファイルの読み込みテスト"""
    print("\nTesting config loading...")

    try:
        from src.config import Config

        config_path = project_root / "config.yaml"
        if not config_path.exists():
            print(f"✗ Config file not found: {config_path}")
            return False

        config = Config.load(str(config_path))
        print("✓ Config loaded successfully")

        # 設定値の確認
        print(f"  - API Provider: {config.api.provider}")
        print(f"  - Headless mode: {config.scraping.headless}")
        print(f"  - Max parallel: {config.scraping.max_parallel}")

        # バリデーション
        errors = config.validate()
        if errors:
            print(f"✗ Config validation failed: {errors}")
            return False

        print("✓ Config validation passed")
        return True

    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_models():
    """データモデルの基本動作テスト"""
    print("\nTesting data models...")

    try:
        from src.models import Site, ValidationItem, ValidationResult, LLMResponse
        from datetime import datetime

        # Site モデル
        site = Site(
            site_id=1,
            company_name="テスト株式会社",
            url="https://example.com",
            industry="製造業"
        )
        print("✓ Site model created")

        # ValidationItem モデル
        item = ValidationItem(
            item_id=1,
            category="カテゴリ",
            subcategory="サブカテゴリ",
            item_name="テスト項目",
            automation_type="A",
            check_type="script",
            priority=1,
            difficulty=1,
            instruction="テスト指示",
            target_page="TOP",
            original_no="1-1"
        )
        print("✓ ValidationItem model created")

        # ValidationResult モデル
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
        print("✓ ValidationResult model created")

        # to_dict テスト
        result_dict = result.to_dict()
        assert 'site_id' in result_dict
        assert 'result' in result_dict
        print("✓ ValidationResult.to_dict() works")

        # LLMResponse モデル
        llm_response = LLMResponse(
            raw_response='{"found": true, "confidence": 0.9, "details": "test"}',
            found=True,
            confidence=0.9,
            details="test"
        )
        print("✓ LLMResponse model created")

        # from_json テスト
        json_str = '{"found": true, "confidence": 0.8, "details": "テスト詳細"}'
        parsed = LLMResponse.from_json(json_str)
        assert parsed.found == True
        assert parsed.confidence == 0.8
        print("✓ LLMResponse.from_json() works")

        return True

    except Exception as e:
        print(f"✗ Data models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_input_files():
    """入力ファイルの存在確認"""
    print("\nTesting input files...")

    try:
        import pandas as pd

        # sites_list.csv
        sites_csv = project_root / "input" / "sample_sites.csv"
        if not sites_csv.exists():
            print(f"✗ Sites CSV not found: {sites_csv}")
            return False

        sites_df = pd.read_csv(sites_csv)
        print(f"✓ Sites CSV loaded: {len(sites_df)} sites")

        required_columns = ['site_id', 'company_name', 'url']
        for col in required_columns:
            if col not in sites_df.columns:
                print(f"✗ Missing column in sites CSV: {col}")
                return False
        print("✓ Sites CSV has required columns")

        # validation_items.csv
        items_csv = project_root / "input" / "validation_items.csv"
        if not items_csv.exists():
            print(f"✗ Validation items CSV not found: {items_csv}")
            return False

        items_df = pd.read_csv(items_csv)
        print(f"✓ Validation items CSV loaded: {len(items_df)} items")

        required_columns = [
            'item_id', 'category', 'subcategory', 'item_name',
            'automation_type', 'check_type', 'priority', 'difficulty',
            'instruction', 'target_page', 'original_no'
        ]
        for col in required_columns:
            if col not in items_df.columns:
                print(f"✗ Missing column in items CSV: {col}")
                return False
        print("✓ Validation items CSV has required columns")

        return True

    except Exception as e:
        print(f"✗ Input files test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("=" * 60)
    print("IR Site Evaluator - Basic Tests")
    print("=" * 60)

    results = []

    # テスト実行
    results.append(("Import Test", test_imports()))
    results.append(("Config Loading Test", test_config_loading()))
    results.append(("Data Models Test", test_data_models()))
    results.append(("Input Files Test", test_input_files()))

    # 結果サマリー
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:6} - {name}")

    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    return all(result for _, result in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
