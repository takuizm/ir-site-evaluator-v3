# IRサイト評価ツール - セットアップガイド

## 前提条件

- Python 3.10以上
- pip（Pythonパッケージマネージャー）
- Git

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd ir-site-evaluator-v3
```

### 2. Python仮想環境の作成（推奨）

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

主な依存パッケージ:
- `playwright`: ブラウザ自動化
- `anthropic`: Claude API クライアント
- `openai`: OpenAI API クライアント
- `pandas`: データ処理
- `beautifulsoup4`: HTML解析
- `loguru`: ロギング

### 4. Playwright ブラウザのインストール

```bash
playwright install chromium
```

### 5. 環境変数の設定

`.env`ファイルを作成してAPIキーを設定:

```bash
cp .env.example .env
```

`.env`ファイルを編集:

```bash
# OpenAI APIを使用する場合
OPENAI_API_KEY=your_actual_openai_api_key_here

# Claude APIを使用する場合
ANTHROPIC_API_KEY=your_actual_anthropic_api_key_here
```

**注意**: どちらか一方のAPIキーがあれば動作します。`config.yaml`の`api.provider`で使用するプロバイダーを指定できます。

### 6. 設定の確認

`config.yaml`ファイルで各種設定を確認・調整:

```yaml
api:
  provider: "openai"  # または "claude"
  openai:
    model: "gpt-4o-mini"

scraping:
  headless: true  # ブラウザを非表示で実行

processing:
  enable_parallel: false  # 並列処理の有効/無効
  max_parallel_sites: 1   # 同時処理サイト数
```

### 7. 入力データの確認

以下のファイルが存在することを確認:

- `input/sample_sites.csv`: 評価対象のサイトリスト
- `input/validation_items.csv`: 検証項目リスト（249項目）

### 8. 動作確認

基本的な動作確認:

```bash
python -m src.main --config config.yaml
```

## 実行方法

### 基本的な実行

```bash
python -m src.main --config config.yaml
```

### 実行結果

以下のファイルが自動生成されます:

- `output/results_summary.csv`: 全検証結果の詳細
- `output/results_detailed.csv`: カテゴリ別集計結果
- `output/execution.log`: 実行ログ
- `checkpoint/checkpoint_N.csv`: チェックポイントファイル

## トラブルシューティング

### エラー: "No module named 'xxx'"

依存パッケージがインストールされていません:

```bash
pip install -r requirements.txt
```

### エラー: "API Key not found"

`.env`ファイルにAPIキーが設定されていません:

1. `.env`ファイルを作成
2. 適切なAPIキーを設定
3. `.env`ファイルがプロジェクトルートにあることを確認

### エラー: "playwright._impl._api_types.Error: Executable doesn't exist"

Playwrightブラウザがインストールされていません:

```bash
playwright install chromium
```

### 評価が途中で止まる

- ネットワーク接続を確認
- `config.yaml`の`scraping.timeout`を増やす
- チェックポイントファイルから再開可能

### LLM APIのレート制限エラー

- `config.yaml`の`api.rate_limit_delay`を増やす（例: 1.0秒）
- `api.max_retries`を調整

## API コスト見積もり

### OpenAI gpt-4o-mini使用時

**1サイトあたり（249項目中132項目がLLM評価）:**
- コスト: 約$0.09
- 実行時間: 約7.5分

**10サイトの場合:**
- コスト: 約$0.90
- 実行時間: 約75分

### Claude 3.5 Sonnet使用時

**1サイトあたり:**
- コスト: 約$0.15
- 実行時間: 約7.5分

実行後、コストサマリーがログに表示されます。

## 推奨事項

### 初回実行時

1. まず1-2サイトで試す:
   - `input/sample_sites.csv`を編集して少数のサイトのみにする

2. ログを確認:
   - `output/execution.log`で詳細な実行ログを確認

3. 結果を確認:
   - `output/results_summary.csv`をExcelで開いて結果を確認
   - PASS/FAIL/ERROR/UNKNOWNの分布を確認

### 本番運用時

- `scraping.headless: true`を維持（パフォーマンス向上）
- 並列処理は通常無効のまま使用を推奨
- チェックポイント機能により中断しても再開可能
- 定期的にログファイルを確認

## 次のステップ

1. 基本動作確認が成功したら、実際のIRサイトで実行
2. 結果を確認して評価精度を検証
3. 必要に応じて設定を調整

## サポート

問題が発生した場合は、以下を確認してください:

1. `output/execution.log`の最新のログ
2. エラーメッセージの全文
3. 使用しているPythonバージョン（`python3 --version`）
4. 環境（OS、メモリ、ネットワーク状況）

お問い合わせ: プロトソル合同会社
https://brotosol.co.jp/

---

Copyright © 2025 プロトソル合同会社 (Brotosol LLC)
All rights reserved.
