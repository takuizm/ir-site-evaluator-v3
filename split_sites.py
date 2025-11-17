#!/usr/bin/env python
"""サイトリストをバッチファイルに分割

407社を50社ずつのバッチに分割します。
"""
import pandas as pd
from pathlib import Path

def split_sites(input_file: str, batch_size: int = 50, output_dir: str = "input"):
    """サイトリストをバッチファイルに分割

    Args:
        input_file: 入力CSVファイル（例: input/sample_sites.csv）
        batch_size: 1バッチあたりのサイト数（デフォルト: 50）
        output_dir: 出力ディレクトリ（デフォルト: input）
    """
    print(f"📂 Reading: {input_file}")

    # エンコーディングを自動検出
    encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso-2022-jp']
    df = None

    for encoding in encodings:
        try:
            df = pd.read_csv(input_file, encoding=encoding)
            print(f"✓ Detected encoding: {encoding}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if df is None:
        raise ValueError(f"Could not decode {input_file} with any of the supported encodings: {encodings}")
    total_sites = len(df)
    print(f"✅ Total sites: {total_sites}")

    # 出力ディレクトリの作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # バッチごとに分割
    batch_num = 1
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batch_file = output_path / f"batch_{batch_num:02d}.csv"
        batch_df.to_csv(batch_file, index=False, encoding='utf-8')

        print(f"  Batch {batch_num:02d}: {len(batch_df):3d} sites → {batch_file}")
        batch_num += 1

    print(f"\n🎉 Created {batch_num - 1} batch files in {output_dir}/")
    print(f"   Total sites split: {total_sites}")

    # サマリー
    print(f"\n📊 Batch Summary:")
    print(f"   Batch size: {batch_size} sites")
    print(f"   Full batches: {total_sites // batch_size}")
    print(f"   Last batch: {total_sites % batch_size} sites" if total_sites % batch_size > 0 else "")

    return batch_num - 1

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="サイトリストをバッチファイルに分割")
    parser.add_argument(
        "--input",
        default="input/sample_sites.csv",
        help="入力CSVファイル（デフォルト: input/sample_sites.csv）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="1バッチあたりのサイト数（デフォルト: 50）"
    )
    parser.add_argument(
        "--output-dir",
        default="input",
        help="出力ディレクトリ（デフォルト: input）"
    )

    args = parser.parse_args()

    split_sites(args.input, args.batch_size, args.output_dir)
