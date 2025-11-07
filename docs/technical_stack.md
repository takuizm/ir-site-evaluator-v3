# IRサイト評価ツール - 技術スタック詳細

**バージョン**: 1.0
**作成日**: 2025-10-25

---

## 目次

1. [技術選定の原則](#技術選定の原則)
2. [コア技術スタック](#コア技術スタック)
3. [ライブラリ詳細](#ライブラリ詳細)
4. [代替案との比較](#代替案との比較)
5. [開発環境](#開発環境)
6. [デプロイメント](#デプロイメント)

---

## 技術選定の原則

### 選定基準

1. **信頼性**: 枯れた技術、活発なメンテナンス
2. **パフォーマンス**: 大規模処理に耐えうる性能
3. **拡張性**: 将来の機能追加に対応可能
4. **コスト**: ライセンス・運用コストが妥当
5. **学習コスト**: チーム内での習得が容易

---

## コア技術スタック

### 全体構成

```
┌─────────────────────────────────────────────────┐
│              Application Layer                  │
│                                                 │
│  Python 3.10+                                   │
│  ├─ Async/Await (asyncio)                      │
│  └─ Type Hints (typing)                        │
└─────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐           ┌──────────▼─────────┐
│ Web Automation │           │   AI/LLM Layer     │
│                │           │                    │
│ Playwright     │           │ Anthropic Claude   │
│  1.40.0        │           │  (API)             │
│                │           │                    │
│                │           │ OpenAI GPT         │
│                │           │  (API)             │
└────────────────┘           └────────────────────┘
        │                               │
        │                               │
┌───────▼────────┐           ┌──────────▼─────────┐
│ HTML Processing│           │  Data Processing   │
│                │           │                    │
│ BeautifulSoup4 │           │  pandas 2.1.0      │
│  4.12.0        │           │  openpyxl 3.1.0    │
│                │           │                    │
│ lxml 5.0.0     │           │                    │
└────────────────┘           └────────────────────┘
```

---

## ライブラリ詳細

### 1. Web自動化: Playwright

**バージョン**: 1.40.0

#### 選定理由

✅ **モダンなAPI**: async/await対応、直感的なAPI
✅ **ブラウザエンジン**: Chromium/Firefox/WebKit対応
✅ **ヘッドレス対応**: サーバー環境での実行可能
✅ **待機機能**: 自動待機、ネットワークアイドル検出
✅ **スクリーンショット**: デバッグ・検証に有用

#### 主要機能

```python
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # ページ読み込み（自動待機）
        await page.goto('https://example.com', wait_until='networkidle')

        # DOM操作
        menu_count = await page.locator('nav > ul > li').count()

        # JavaScript実行
        font_size = await page.evaluate('''
            () => getComputedStyle(document.body).fontSize
        ''')

        # スクリーンショット
        await page.screenshot(path='screenshot.png')

        await browser.close()
```

#### 代替案との比較

| 項目 | Playwright | Selenium | Puppeteer |
|-----|-----------|----------|-----------|
| **パフォーマンス** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **API設計** | モダン | 古い | モダン |
| **ブラウザ対応** | 3種類 | 多数 | Chrome のみ |
| **待機機能** | 優秀 | 手動 | 良好 |
| **コミュニティ** | 成長中 | 大規模 | 大規模 |
| **Python対応** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

**結論**: Playwrightを採用
- モダンなAPI、優れた待機機能、Python async/await対応

---

### 2. LLM API: Anthropic Claude & OpenAI GPT

#### 2.1 Claude API (Anthropic)

**バージョン**: anthropic 0.39.0
**使用モデル**: Claude 3.5 Sonnet / Claude 3 Haiku

##### 選定理由

✅ **日本語能力**: 日本語の理解・生成が優秀
✅ **長文対応**: 200K トークン（約60万文字）
✅ **コスト効率**: Haiku は $0.25/M input tokens
✅ **安全性**: 有害コンテンツ生成の抑制

##### 使用例

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_API_KEY")

message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "以下のHTMLから社長経歴の有無を判定してください。\n\n{html_content}"
        }
    ]
)

print(message.content[0].text)
```

##### 料金

| モデル | Input | Output | 用途 |
|--------|-------|--------|------|
| **Claude 3.5 Sonnet** | $3.00/M tokens | $15.00/M tokens | 高精度検証 |
| **Claude 3 Haiku** | $0.25/M tokens | $1.25/M tokens | 大量処理 |

#### 2.2 OpenAI GPT API

**バージョン**: openai 1.54.0
**使用モデル**: GPT-4o / GPT-4o-mini

##### 選定理由

✅ **実績**: 豊富な実装事例
✅ **精度**: 高い精度
✅ **エコシステム**: 豊富なツール・ライブラリ

##### 使用例

```python
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "あなたはWebサイト検証の専門家です。"},
        {"role": "user", "content": f"以下のHTMLから社長経歴の有無を判定してください。\n\n{html_content}"}
    ]
)

print(response.choices[0].message.content)
```

##### 料金

| モデル | Input | Output | 用途 |
|--------|-------|--------|------|
| **GPT-4o** | $2.50/M tokens | $10.00/M tokens | 高精度検証 |
| **GPT-4o-mini** | $0.150/M tokens | $0.600/M tokens | コスト重視 |

#### LLM選択戦略

**プロトタイプ**: Claude 3.5 Sonnet（精度優先）
**本番**: Claude 3 Haiku または GPT-4o-mini（コスト重視）

---

### 3. HTML解析: BeautifulSoup4 + lxml

**バージョン**: BeautifulSoup4 4.12.0, lxml 5.0.0

#### 選定理由

✅ **高速**: lxml パーサーは C実装で高速
✅ **柔軟**: 壊れたHTMLも処理可能
✅ **シンプル**: Pythonic なAPI
✅ **軽量**: トークン削減のための前処理に最適

#### 使用例

```python
from bs4 import BeautifulSoup, Comment

def clean_html(html: str) -> str:
    """HTML前処理（トークン削減）"""
    soup = BeautifulSoup(html, 'lxml')

    # 不要タグ削除
    for tag in soup(['script', 'style', 'noscript', 'svg']):
        tag.decompose()

    # コメント削除
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # テキスト抽出
    text = soup.get_text(separator='\n', strip=True)

    return text
```

#### 代替案との比較

| 項目 | BeautifulSoup4 | lxml単体 | html.parser |
|-----|---------------|----------|-------------|
| **速度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **柔軟性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **API** | Pythonic | XML的 | 標準 |
| **依存関係** | lxml必要 | なし | なし |

**結論**: BeautifulSoup4 + lxml を採用
- 高速かつ柔軟、壊れたHTMLも処理可能

---

### 4. データ処理: pandas + openpyxl

**バージョン**: pandas 2.1.0, openpyxl 3.1.0

#### 選定理由

✅ **標準的**: データ処理のデファクトスタンダード
✅ **豊富な機能**: 集計、フィルタリング、ピボット
✅ **Excel出力**: openpyxl で Excel 形式対応
✅ **パフォーマンス**: NumPy ベースで高速

#### 使用例

```python
import pandas as pd

# 結果をDataFrameに変換
df = pd.DataFrame([
    {
        'site_id': 1,
        'company_name': 'トヨタ自動車',
        'item_id': 1,
        'item_name': 'メニュー項目数は適切',
        'result': 'PASS',
        'confidence': 1.0,
        'details': 'グローバルメニュー8項目',
        'checked_at': '2025-10-25 14:30:00'
    },
    # ...
])

# CSV出力
df.to_csv('output/results_summary.csv', index=False, encoding='utf-8-sig')

# Excel出力
with pd.ExcelWriter('output/results_detailed.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='All Results', index=False)

    # カテゴリ別シート
    for category in df['category'].unique():
        category_df = df[df['category'] == category]
        category_df.to_excel(writer, sheet_name=category, index=False)
```

---

### 5. 設定管理: PyYAML + python-dotenv

**バージョン**: PyYAML 6.0, python-dotenv 1.0.0

#### 選定理由

✅ **可読性**: YAML は人間が読みやすい
✅ **階層構造**: ネストした設定を表現可能
✅ **環境変数**: .env ファイルで秘密情報を管理

#### 使用例

```python
import yaml
from dotenv import load_dotenv
import os

# .env読み込み
load_dotenv()

# config.yaml読み込み
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 環境変数から API Key 取得
api_key = os.getenv(config['api']['claude']['api_key_env'])
```

---

### 6. ログ管理: loguru

**バージョン**: loguru 0.7.2

#### 選定理由

✅ **シンプル**: 標準logging より簡単
✅ **カラー出力**: コンソール出力が見やすい
✅ **自動ローテーション**: ログファイルの自動管理
✅ **構造化ログ**: JSON形式での出力可能

#### 使用例

```python
from loguru import logger

# ログ設定
logger.add(
    "output/execution.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# ログ出力
logger.info("Starting evaluation for site: {}", site_name)
logger.warning("Retry {}/{}: {}", attempt, max_retries, error)
logger.error("Failed to process site: {}", site_id)
```

---

### 7. プログレスバー: tqdm

**バージョン**: tqdm 4.66.0

#### 選定理由

✅ **視覚的**: 進捗状況が一目瞭然
✅ **シンプル**: イテレータをラップするだけ
✅ **柔軟**: カスタマイズ可能

#### 使用例

```python
from tqdm import tqdm

# サイトループ
for site in tqdm(sites, desc="Processing sites", unit="site"):
    process_site(site)

# 検証項目ループ
for item in tqdm(items, desc=f"Validating {site.name}", unit="item"):
    validate_item(site, item)
```

出力例:
```
Processing sites:  20%|████      | 2/10 [00:30<02:00, 15.0s/site]
Validating トヨタ自動車:  50%|█████     | 25/50 [00:15<00:15,  1.6item/s]
```

---

### 8. HTTP リクエスト: requests

**バージョン**: requests 2.31.0

#### 選定理由

✅ **標準的**: HTTP通信のデファクトスタンダード
✅ **シンプル**: 直感的なAPI
✅ **機能豊富**: セッション管理、リトライ、タイムアウト

#### 使用例

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# リトライ設定
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

# TLS バージョン確認
response = session.get('https://example.com')
print(response.headers.get('Strict-Transport-Security'))
```

---

## 代替案との比較

### Web自動化ツール

| ツール | メリット | デメリット | 採用理由 |
|--------|---------|-----------|---------|
| **Playwright** ✅ | モダンAPI、高速、async対応 | 新しい | API設計が優秀 |
| Selenium | 実績豊富、多ブラウザ対応 | API古い、遅い | - |
| Puppeteer | 高速 | Chrome のみ | ブラウザ対応少ない |
| Scrapy | 高速クローリング | 学習コスト高 | オーバースペック |

### LLM API

| API | メリット | デメリット | 採用理由 |
|-----|---------|-----------|---------|
| **Claude** ✅ | 日本語強い、長文対応 | 新しい | 日本語評価に最適 |
| **OpenAI GPT** ✅ | 実績豊富、高精度 | コスト高め | 代替選択肢として |
| Gemini | 無料枠大きい | 品質が不安定 | - |
| Local LLM | コスト0 | 精度低い、遅い | - |

### HTML解析

| ツール | メリット | デメリット | 採用理由 |
|--------|---------|-----------|---------|
| **BeautifulSoup4** ✅ | 柔軟、Pythonic | lxml より遅い | バランスが良い |
| lxml | 高速 | API が難しい | - |
| html.parser | 標準 | 機能少ない | - |
| html5lib | HTML5準拠 | 遅い | - |

---

## 開発環境

### Python バージョン

- **必須**: Python 3.10以上
- **推奨**: Python 3.11
- **理由**: 型ヒント強化、パフォーマンス改善

### OS対応

- ✅ macOS (開発環境)
- ✅ Windows (WSL2推奨)
- ✅ Linux (本番環境想定)

### IDE推奨設定

#### VS Code

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.analysis.typeCheckingMode": "basic"
}
```

#### 推奨拡張機能

- Python (Microsoft)
- Pylance
- Black Formatter
- YAML

---

## デプロイメント

### ローカル実行（現在）

```bash
# セットアップ
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 実行
python src/main.py
```

### サーバー実行（将来）

```bash
# Docker化（将来の拡張）
docker build -t ir-site-evaluator .
docker run -v $(pwd)/output:/app/output ir-site-evaluator

# cron実行
0 2 * * * cd /path/to/project && python src/main.py >> /var/log/ir-evaluator.log 2>&1
```

---

## 依存関係の管理

### requirements.txt

すべての依存関係を固定バージョンで管理:

```txt
playwright==1.40.0
anthropic==0.39.0
openai==1.54.0
pandas==2.1.0
openpyxl==3.1.0
pyyaml==6.0
python-dotenv==1.0.0
tqdm==4.66.0
requests==2.31.0
loguru==0.7.2
beautifulsoup4==4.12.0
lxml==5.0.0
```

### バージョン更新戦略

- **セマンティックバージョニング**: メジャーアップデートは慎重に
- **定期更新**: 四半期ごとに依存関係を確認
- **セキュリティパッチ**: 即座に適用

---

## パフォーマンス指標

### 目標値

| 指標 | 目標値 | 測定方法 |
|-----|-------|---------|
| **1サイトあたり処理時間** | 30秒以内 | タイムスタンプ計測 |
| **LLM呼び出し成功率** | 95%以上 | 成功/失敗カウント |
| **メモリ使用量** | 2GB以内 | psutil測定 |
| **コスト（LLM）** | $0.05/サイト以下 | API usage tracking |

---

## セキュリティ

### 脆弱性スキャン

```bash
# 依存関係の脆弱性チェック
pip install safety
safety check

# コード品質チェック
pip install bandit
bandit -r src/
```

### API Keyローテーション

- 3ヶ月ごとにAPI Keyを更新
- `.env`ファイルを`.gitignore`に追加

---

## まとめ

このプロジェクトは以下の技術スタックで構成されます：

| レイヤー | 技術 | 理由 |
|---------|------|------|
| **Web自動化** | Playwright 1.40.0 | モダンAPI、高速、async対応 |
| **LLM** | Claude 3.5 Sonnet / GPT-4o-mini | 日本語能力、コスト効率 |
| **HTML解析** | BeautifulSoup4 + lxml | 柔軟性と速度のバランス |
| **データ処理** | pandas + openpyxl | 標準的、Excel出力対応 |
| **設定管理** | PyYAML + python-dotenv | 可読性、環境変数管理 |
| **ログ** | loguru | シンプル、カラー出力 |

これらの選択により、**信頼性**、**パフォーマンス**、**拡張性**を兼ね備えたシステムを実現します。

---

**作成者**: Claude Code
**最終更新**: 2025-10-25
