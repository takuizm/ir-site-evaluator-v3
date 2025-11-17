# IRサイト評価ツール

企業のIRサイトを自動評価するツール。249項目の評価基準に基づき、スクリプト検証とLLM検証を組み合わせたハイブリッドシステムで評価を実施します。

## 特徴

- **249項目の自動評価**: 2025年版評価基準に完全対応
- **ハイブリッド検証**: Script検証（145項目）+ LLM検証（104項目）
- **高精度**: 明確なPASS/FAIL判定、詳細な検証レポート
- **低コスト**: 約$0.02/サイト（gpt-4o-mini使用時）
- **効率的**: 約2.4分/サイト

## セットアップ

### 必要環境

- Python 3.10以上
- OpenAI API キー または Anthropic API キー

### インストール

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd ir-site-evaluator-v3

# 2. Python仮想環境を作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. Playwrightブラウザをインストール
playwright install chromium

# 5. 環境変数を設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 環境変数設定

`.env`ファイルに以下を設定：

```bash
# OpenAI APIを使用する場合
OPENAI_API_KEY=your_openai_api_key_here

# Claude APIを使用する場合
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 使用方法

### 基本的な実行

```bash
python -m src.main --config config.yaml
```

### 設定ファイル

`config.yaml`で以下を設定可能：

- **api.provider**: 使用するLLM（`openai` または `claude`）
- **api.openai.model**: OpenAIモデル（デフォルト: `gpt-4o-mini`）
- **api.claude.model**: Claudeモデル（デフォルト: `claude-3-5-sonnet-20241022`）
- **scraping.headless**: ヘッドレスモード（デフォルト: `true`）
- **input.sites_list**: 評価対象サイトリスト（デフォルト: `input/sample_sites.csv`）
- **output.summary_csv**: 結果出力先（デフォルト: `output/results_summary.csv`）

### 評価対象サイトの設定

`input/sample_sites.csv`を編集して評価対象サイトを設定：

```csv
site_id,company_name,url
1,企業名,https://example.com/ir/
```

## 出力結果

実行すると以下のファイルが生成されます：

### results_summary.csv

各評価項目の詳細結果（全チェック結果）

```csv
site_id,company_name,url,item_id,item_name,category,subcategory,result,confidence,details,checked_at
1,トヨタ自動車,https://...,1,メニュー構造により...,ウェブサイトの使いやすさ,メニューとナビゲーション,PASS,0.9,...,2025-11-07 17:37:08
```

### results_detailed.csv

カテゴリ別の集計結果

```csv
site_id,company_name,category,total_items,pass_count,fail_count,unknown_count,error_count,avg_confidence,pass_rate
1,トヨタ自動車,ウェブサイトの使いやすさ,76,57,19,0,0,0.87,0.75
```

### execution.log

実行ログ（詳細なデバッグ情報）

## プロジェクト構成

```
ir-site-evaluator-v3/
├── README.md                    # このファイル
├── SETUP.md                     # 詳細セットアップガイド
├── LICENSE                      # ライセンス
├── config.yaml                  # メイン設定ファイル
├── requirements.txt             # Python依存関係
├── .env.example                 # 環境変数テンプレート
├── input/
│   ├── validation_items.csv     # 249項目評価基準
│   └── sample_sites.csv         # サンプルサイトリスト
├── output/                      # 実行結果
├── src/                         # ソースコード
│   ├── main.py                  # メインスクリプト
│   ├── models.py                # データモデル
│   ├── config.py                # 設定管理
│   ├── validators/              # 検証エンジン
│   │   ├── script_validator.py  # スクリプト検証（145項目）
│   │   └── llm_validator.py     # LLM検証（104項目）
│   └── utils/                   # ユーティリティ
│       ├── scraper.py           # Webスクレイピング
│       ├── llm_client.py        # LLM APIクライアント
│       ├── logger.py            # ロガー
│       └── reporter.py          # レポート生成
├── tests/                       # テストコード
└── docs/                        # 技術ドキュメント
    ├── architecture.md          # システムアーキテクチャ
    ├── criteria_2025.md         # 評価基準詳細（249項目）
    ├── data_structures.md       # データ構造定義
    ├── requirements.md          # 要件定義書
    └── technical_stack.md       # 技術スタック詳細
```

## 評価基準

### 249項目の構成

| カテゴリ | 項目数 |
|---------|--------|
| ウェブサイトの使いやすさ | 76項目 |
| 企業・経営情報の充実度 | 58項目 |
| 情報開示の積極性・先進性 | 45項目 |
| 財務・決算情報の充実度 | 70項目 |
| **合計** | **249項目** |

詳細は [docs/criteria.md](docs/criteria.md) を参照してください。

## トラブルシューティング

### Playwright関連のエラー

```bash
playwright install chromium
```

### API接続エラー

`.env`ファイルのAPIキーが正しく設定されているか確認してください。

### メモリ不足

`config.yaml`の並列処理設定を調整：

```yaml
processing:
  enable_parallel: false
  max_parallel_sites: 1
```

## ライセンス

Copyright © 2025 プロトソル合同会社 (Brotosol LLC)
All rights reserved.

本ソフトウェアおよび関連ドキュメントファイル（以下「本ソフトウェア」）の著作権は、プロトソル合同会社が保有します。

## サポート

問題が発生した場合は、プロトソル合同会社の開発チームにお問い合わせください。
https://brotosol.co.jp/
