# バッチ実行ガイド

407社のIRサイト評価を、50社ずつのバッチに分割して実行する方法を説明します。

## 📋 概要

- **総サイト数**: 407社
- **バッチサイズ**: 50社/バッチ
- **総バッチ数**: 9バッチ（8バッチ × 50社 + 1バッチ × 7社）
- **実行時間**: 約2.4分/サイト → 約2時間/バッチ
- **総実行時間**: 約18-20時間（分散実行推奨）

## 🚀 実行手順

### ステップ1: サイトリストをバッチに分割

```bash
python split_sites.py
```

**出力**:
```
input/batch_01.csv (50社)
input/batch_02.csv (50社)
...
input/batch_09.csv (7社)
```

**オプション**:
```bash
# バッチサイズを変更（例: 30社ずつ）
python split_sites.py --batch-size 30

# 異なる入力ファイルを使用
python split_sites.py --input input/other_sites.csv
```

---

### ステップ2: バッチを実行

#### オプションA: 全バッチを自動実行（推奨しない）

```bash
./run_all_batches.sh
```

⚠️ **注意**: 約18-20時間かかるため、分散実行を推奨します。

#### オプションB: 1バッチずつ手動実行（推奨）

```bash
# バッチ1を実行（約2時間）
python -m src.main --config <(cat <<EOF
api:
  provider: "openai"
  openai:
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"
    max_tokens: 4096
  max_retries: 3
  timeout: 60
  rate_limit_delay: 0.5

scraping:
  headless: true
  wait_until: "domcontentloaded"
  delay_after_load: 5.0
  timeout: 60
  max_parallel: 1
  screenshot_on_error: true

processing:
  checkpoint_interval: 1
  batch_semantic_checks: true
  skip_errors: true
  max_retries_per_site: 2
  enable_parallel: false

logging:
  level: "INFO"
  file: "output/batch_01_execution.log"
  console: true

output:
  summary_csv: "output/batch_01_results.csv"
  detailed_csv: "output/batch_01_detailed.csv"
  error_log: "output/batch_01_error_log.txt"
  checkpoint_dir: "checkpoint/batch_01"

input:
  sites_list: "input/batch_01.csv"
  validation_items: "input/validation_items.csv"

performance:
  enable_caching: true
  cache_dir: ".cache"
  max_cache_size_mb: 500
EOF
)
```

**より簡単な方法**: 設定ファイルを作成して使用

```bash
# batch_01用の設定ファイルを作成（config_batch_01.yamlとして保存）
# 上記のYAML内容をファイルに保存

# 実行
python -m src.main --config config_batch_01.yaml
```

**各バッチ用の設定ファイルテンプレート**:
```bash
# バッチ2-9用は input/sites_list と output ファイル名のみ変更
cp config_batch_01.yaml config_batch_02.yaml
# sites_list, summary_csv, detailed_csv, error_log, checkpoint_dir を編集
```

---

### ステップ3: エラーが発生した場合

チェックポイント機能により、途中から再開できます：

```bash
# 同じコマンドを再実行するだけ
python -m src.main --config config_batch_03.yaml
```

処理済みサイトはスキップされ、未処理サイトから再開されます。

---

### ステップ4: 全バッチ完了後、結果を統合

```bash
python merge_results.py
```

**出力**:
```
output/final_results_summary_YYYYMMDD_HHMMSS.csv  # サマリー結果
output/final_results_detailed_YYYYMMDD_HHMMSS.csv # 詳細結果
```

---

## 📊 実行スケジュール例

### パターン1: 業務時間内で実行

```
月曜 09:00-13:00 → バッチ1,2 (4時間)
月曜 14:00-18:00 → バッチ3,4 (4時間)
火曜 09:00-13:00 → バッチ5,6 (4時間)
火曜 14:00-18:00 → バッチ7,8 (4時間)
水曜 09:00-10:00 → バッチ9 (1時間)
```

**合計: 3日間**

### パターン2: 夜間バッチ実行

```
月曜夜 20:00-翌6:00 → バッチ1-5 (10時間)
火曜夜 20:00-翌6:00 → バッチ6-9 (10時間)
```

**合計: 2日間（夜間のみ）**

---

## 🔍 モニタリング

### 進捗確認

```bash
# ログファイルをリアルタイム監視
tail -f output/batch_01_execution.log

# 完了したサイト数を確認
wc -l output/batch_01_results.csv
```

### チェックポイント確認

```bash
# チェックポイントディレクトリの確認
ls checkpoint/batch_01/

# 処理済みサイトの確認
cat checkpoint/batch_01/completed_sites.txt
```

---

## ⚠️ トラブルシューティング

### エラー: API Rate Limit超過

```bash
# config.yamlで rate_limit_delay を増やす
rate_limit_delay: 1.0  # 0.5 → 1.0秒に変更
```

### エラー: メモリ不足

```bash
# キャッシュをクリア
rm -rf .cache/*
```

### エラー: ネットワークタイムアウト

```bash
# config.yamlでタイムアウトを増やす
timeout: 120  # 60 → 120秒に変更
```

---

## 📁 ファイル構造

```
ir-site-evaluator-v3/
├── input/
│   ├── sample_sites.csv          # 元の407社リスト
│   ├── batch_01.csv              # バッチ1 (50社)
│   ├── batch_02.csv              # バッチ2 (50社)
│   └── ...
├── output/
│   ├── batch_01_results.csv      # バッチ1のサマリー結果
│   ├── batch_01_detailed.csv     # バッチ1の詳細結果
│   ├── batch_01_execution.log    # バッチ1の実行ログ
│   └── ...
├── split_sites.py                # 分割スクリプト
├── run_all_batches.sh            # 一括実行スクリプト
└── merge_results.py              # 結果統合スクリプト
```

---

## 💰 コスト見積もり

### LLM API コスト

- **モデル**: gpt-4o-mini
- **LLM項目数**: 104項目/サイト
- **総LLM呼び出し**: 104 × 407 = 42,328回
- **推定コスト**: 約$8-10

### 実行時間コスト

- **1サイト**: 約2.4分
- **407サイト**: 約18-20時間
- **分散実行**: 2-3日間（1日8-10時間）

---

## ✅ チェックリスト

実行前:
- [ ] 環境変数 `OPENAI_API_KEY` が設定されている
- [ ] `split_sites.py` でバッチファイルが作成されている
- [ ] `output/` ディレクトリに十分な空き容量がある

実行中:
- [ ] ログファイルで進捗を定期的に確認
- [ ] エラーが発生したら速やかに対処
- [ ] チェックポイントファイルが正常に作成されている

実行後:
- [ ] 全バッチの結果ファイルが作成されている
- [ ] `merge_results.py` で結果を統合
- [ ] 統計情報を確認（PASS/FAIL率など）
