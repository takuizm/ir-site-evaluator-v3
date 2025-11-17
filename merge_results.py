#!/usr/bin/env python
"""バッチ実行結果を統合

全バッチの結果CSVを1つのファイルに統合します。
"""
import pandas as pd
import glob
from pathlib import Path
from datetime import datetime

def merge_results(
    pattern: str = "output/batch_*_results.csv",
    detailed_pattern: str = "output/batch_*_detailed.csv",
    output_dir: str = "output"
):
    """バッチ実行結果を統合

    Args:
        pattern: サマリーCSVのファイルパターン（注: 実際は全チェック結果CSV）
        detailed_pattern: 詳細CSVのファイルパターン（注: 実際はサイト別サマリーCSV）
        output_dir: 出力ディレクトリ
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 全チェック結果の統合（batch_*_results.csv）
    print("📊 Merging all validation results...")
    result_files = sorted(glob.glob(pattern))

    if not result_files:
        print(f"❌ No result files found matching: {pattern}")
        return

    all_results = []
    for batch_file in result_files:
        df = pd.read_csv(batch_file, low_memory=False)
        all_results.append(df)
        print(f"  ✓ {batch_file}: {len(df)} validation checks")

    results_df = pd.concat(all_results, ignore_index=True)
    results_output = output_path / f"final_all_results_{timestamp}.csv"
    results_df.to_csv(results_output, index=False, encoding='utf-8-sig')

    print(f"\n✅ All validation results merged: {results_output}")
    print(f"   Total validation checks: {len(results_df):,}")
    print(f"   Unique sites: {results_df['site_id'].nunique()}")

    # サイト別サマリーの統合（batch_*_detailed.csv）
    print("\n📋 Merging site summaries...")
    detailed_files = sorted(glob.glob(detailed_pattern))

    if not detailed_files:
        print(f"⚠️  No detailed files found matching: {detailed_pattern}")
        detailed_df = None
    else:
        all_details = []
        for batch_file in detailed_files:
            df = pd.read_csv(batch_file)
            all_details.append(df)
            print(f"  ✓ {batch_file}: {len(df)} sites")

        detailed_df = pd.concat(all_details, ignore_index=True)
        detailed_output = output_path / f"final_site_summary_{timestamp}.csv"
        detailed_df.to_csv(detailed_output, index=False, encoding='utf-8-sig')

        print(f"\n✅ Site summaries merged: {detailed_output}")
        print(f"   Total rows (site × category): {len(detailed_df)}")
        print(f"   Unique sites: {detailed_df['site_id'].nunique()}")

    # 統計情報
    print("\n" + "=" * 60)
    print("📈 Statistics")
    print("=" * 60)

    # サイト別サマリーから統計（batch_*_detailed.csv）
    if detailed_df is not None and 'pass_count' in detailed_df.columns:
        total_pass = detailed_df['pass_count'].sum()
        total_fail = detailed_df['fail_count'].sum()
        total_unknown = detailed_df.get('unknown_count', pd.Series([0])).sum()
        total_error = detailed_df.get('error_count', pd.Series([0])).sum()
        total_not_supported = detailed_df.get('not_supported_count', pd.Series([0])).sum()
        total_checks = detailed_df['total_items'].sum()

        print(f"Total Sites: {detailed_df['site_id'].nunique()}")
        print(f"Total Checks: {total_checks:,}")
        print(f"\nResults by count:")
        print(f"  PASS:           {total_pass:6,} ({total_pass/total_checks*100:5.2f}%)")
        print(f"  FAIL:           {total_fail:6,} ({total_fail/total_checks*100:5.2f}%)")
        print(f"  UNKNOWN:        {total_unknown:6,} ({total_unknown/total_checks*100:5.2f}%)")
        print(f"  ERROR:          {total_error:6,} ({total_error/total_checks*100:5.2f}%)")
        print(f"  NOT_SUPPORTED:  {total_not_supported:6,} ({total_not_supported/total_checks*100:5.2f}%)")

    # 詳細結果別カウント（batch_*_results.csvから）
    if 'result' in results_df.columns:
        print(f"\n📊 Detailed Result Distribution:")
        result_counts = results_df['result'].value_counts()
        total = len(results_df)
        for result, count in result_counts.items():
            percentage = count / total * 100
            print(f"  {result:15s}: {count:6,} ({percentage:5.2f}%)")

    print("\n🎉 Merge completed!")
    print(f"\n📁 Output files:")
    print(f"  All Results: {results_output}")
    if detailed_files:
        print(f"  Site Summary: {detailed_output}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="バッチ実行結果を統合")
    parser.add_argument(
        "--pattern",
        default="output/batch_*_results.csv",
        help="サマリーCSVのファイルパターン（デフォルト: output/batch_*_results.csv）"
    )
    parser.add_argument(
        "--detailed-pattern",
        default="output/batch_*_detailed.csv",
        help="詳細CSVのファイルパターン（デフォルト: output/batch_*_detailed.csv）"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="出力ディレクトリ（デフォルト: output）"
    )

    args = parser.parse_args()

    merge_results(args.pattern, args.detailed_pattern, args.output_dir)
