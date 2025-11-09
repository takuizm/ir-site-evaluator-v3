"""レポート生成

検証結果をCSV/Excel形式で出力する。
"""
import pandas as pd
from pathlib import Path
from typing import List
from datetime import datetime
from src.models import ValidationResult


class Reporter:
    """レポート生成クラス

    ValidationResultのリストからCSV/Excelレポートを生成する。
    """

    def __init__(self, config, logger, item_lookup=None, criteria_metadata=None, criteria_columns=None):
        """初期化

        Args:
            config: OutputConfig インスタンス
            logger: ロガーインスタンス
        """
        self.config = config
        self.logger = logger
        self.item_lookup = item_lookup or {}
        self.criteria_metadata = criteria_metadata or {}
        self.criteria_columns = criteria_columns or []

    def generate_summary_csv(self, results: List[ValidationResult]):
        """サマリーCSVを生成する

        Args:
            results: ValidationResultのリスト
        """
        if not results:
            self.logger.warning("No results to generate summary CSV")
            return

        # 出力ディレクトリを作成
        output_path = Path(self.config.summary_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # ValidationResultを辞書のリストに変換
        data = []
        for result in results:
            row = result.to_dict()
            criteria_id = self.item_lookup.get(row['item_id'])
            meta = self.criteria_metadata.get(criteria_id)
            if meta:
                for col in self.criteria_columns:
                    row[col] = meta.get(col, '')
            data.append(row)

        # DataFrameに変換
        df = pd.DataFrame(data)

        if self.item_lookup:
            df.insert(
                4,
                'criteria_no',
                df['item_id'].map(self.item_lookup).fillna('').astype(str)
            )

        # CSVに出力
        df.to_csv(
            self.config.summary_csv,
            index=False,
            encoding='utf-8-sig'  # Excelで日本語を正しく表示するため
        )

        self.logger.info(f"Summary CSV generated: {self.config.summary_csv} ({len(results)} results)")

    def generate_detailed_csv(self, results: List[ValidationResult]):
        """詳細CSVを生成する（カテゴリ別集計）

        Args:
            results: ValidationResultのリスト
        """
        if not results:
            self.logger.warning("No results to generate detailed CSV")
            return

        # 出力ディレクトリを作成
        output_path = Path(self.config.detailed_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # ValidationResultを辞書のリストに変換
        data = []
        for result in results:
            row = result.to_dict()
            criteria_id = self.item_lookup.get(row['item_id'])
            meta = self.criteria_metadata.get(criteria_id)
            if meta:
                for col in self.criteria_columns:
                    row[col] = meta.get(col, '')
            data.append(row)
        df = pd.DataFrame(data)

        # confidence列が欠けている場合は0.0で補完
        if 'confidence' not in df.columns:
            df['confidence'] = 0.0

        # カテゴリ別集計（Named Aggregation で列名を固定）
        aggregated = df.groupby(['site_id', 'company_name', 'category']).agg(
            total_items=('item_id', 'count'),
            pass_count=('result', lambda x: (x == 'PASS').sum()),
            fail_count=('result', lambda x: (x == 'FAIL').sum()),
            unknown_count=('result', lambda x: (x == 'UNKNOWN').sum()),
            error_count=('result', lambda x: (x == 'ERROR').sum()),
            not_supported_count=('result', lambda x: (x == 'NOT_SUPPORTED').sum()),
            avg_confidence=('confidence', 'mean')
        ).reset_index()

        # PASS率を計算
        aggregated['pass_rate'] = aggregated['pass_count'] / aggregated['total_items']

        # CSVに出力
        aggregated.to_csv(
            self.config.detailed_csv,
            index=False,
            encoding='utf-8-sig'
        )

        self.logger.info(f"Detailed CSV generated: {self.config.detailed_csv}")

    def generate_statistics(self, results: List[ValidationResult]) -> dict:
        """統計情報を生成する

        Args:
            results: ValidationResultのリスト

        Returns:
            統計情報の辞書
        """
        if not results:
            return {}

        total = len(results)
        pass_count = sum(1 for r in results if r.result == 'PASS')
        fail_count = sum(1 for r in results if r.result == 'FAIL')
        unknown_count = sum(1 for r in results if r.result == 'UNKNOWN')
        error_count = sum(1 for r in results if r.result == 'ERROR')
        not_supported_count = sum(1 for r in results if r.result == 'NOT_SUPPORTED')

        avg_confidence = sum(r.confidence for r in results) / total if total > 0 else 0.0

        # サイト数とアイテム数
        unique_sites = len(set(r.site_id for r in results))
        unique_items = len(set(r.item_id for r in results))

        return {
            'total_checks': total,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'unknown_count': unknown_count,
            'error_count': error_count,
            'pass_rate': pass_count / total if total > 0 else 0.0,
            'fail_rate': fail_count / total if total > 0 else 0.0,
            'avg_confidence': avg_confidence,
            'unique_sites': unique_sites,
            'unique_items': unique_items,
            'not_supported_count': not_supported_count,
        }

    def print_statistics(self, results: List[ValidationResult]):
        """統計情報をログ出力する

        Args:
            results: ValidationResultのリスト
        """
        stats = self.generate_statistics(results)

        if not stats:
            self.logger.warning("No statistics to print")
            return

        self.logger.info("=" * 60)
        self.logger.info("Validation Results Statistics")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Checks: {stats['total_checks']:,}")
        self.logger.info(f"Unique Sites: {stats['unique_sites']}")
        self.logger.info(f"Unique Items: {stats['unique_items']}")
        self.logger.info("-" * 60)
        self.logger.info(f"PASS:    {stats['pass_count']:4,} ({stats['pass_rate']*100:5.1f}%)")
        self.logger.info(f"FAIL:    {stats['fail_count']:4,} ({stats['fail_rate']*100:5.1f}%)")
        self.logger.info(f"UNKNOWN: {stats['unknown_count']:4,} ({stats['unknown_count']/stats['total_checks']*100:5.1f}%)")
        self.logger.info(f"ERROR:   {stats['error_count']:4,} ({stats['error_count']/stats['total_checks']*100:5.1f}%)")
        self.logger.info(f"NOT SUPPORTED: {stats['not_supported_count']:4,} ({stats['not_supported_count']/stats['total_checks']*100:5.1f}%)")
        self.logger.info("-" * 60)
        self.logger.info(f"Average Confidence: {stats['avg_confidence']:.2f}")
        self.logger.info("=" * 60)
