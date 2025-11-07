# IRサイト評価ツール - データ構造定義

**バージョン**: 1.0
**作成日**: 2025-10-25

---

## 目次

1. [入力データ構造](#入力データ構造)
2. [中間データ構造](#中間データ構造)
3. [出力データ構造](#出力データ構造)
4. [Pythonデータクラス定義](#pythonデータクラス定義)
5. [データ検証ルール](#データ検証ルール)

---

## 入力データ構造

### 1. sites_list.csv

**概要**: 評価対象サイトのリスト

**スキーマ**:

| カラム名 | 型 | 必須 | 説明 | 例 |
|---------|-----|------|------|-----|
| `site_id` | int | ✅ | サイト一意ID | 1 |
| `company_name` | string | ✅ | 企業名 | トヨタ自動車 |
| `url` | string | ✅ | URL（トップページ） | https://global.toyota/jp/ |
| `industry` | string | ❌ | 業種 | 製造業（自動車） |
| `note` | string | ❌ | 備考 | 世界的企業・充実したIR |

**サンプル**:

```csv
site_id,company_name,url,industry,note
1,トヨタ自動車,https://global.toyota/jp/,製造業（自動車）,世界的企業・充実したIR
2,ソニーグループ,https://www.sony.com/ja/,電機・エレクトロニクス,グローバル企業・英語IR充実
3,三菱UFJフィナンシャル・グループ,https://www.mufg.jp/,金融（銀行）,メガバンク・IR情報豊富
```

**バリデーションルール**:

- `site_id`: 1以上の整数、重複なし
- `url`: 有効なHTTP/HTTPS URL
- `company_name`: 1文字以上100文字以内

---

### 2. validation_items.csv

**概要**: 評価項目の定義

**スキーマ**:

| カラム名 | 型 | 必須 | 説明 | 例 |
|---------|-----|------|------|-----|
| `item_id` | int | ✅ | 項目一意ID | 1 |
| `category` | string | ✅ | カテゴリ | サイトの使いやすさ |
| `subcategory` | string | ✅ | サブカテゴリ | メニューとナビゲーション |
| `item_name` | string | ✅ | 項目名 | メニュー項目数は適切 |
| `automation_type` | string | ✅ | 自動化分類 | A, B, C, D |
| `check_type` | string | ✅ | 検証タイプ | script, llm |
| `priority` | string | ✅ | 優先度 | high, medium, low |
| `difficulty` | int | ✅ | 難易度 | 1, 2, 3 |
| `instruction` | string | ✅ | 検証手順 | nav要素内のメニュー項目数をカウント |
| `target_page` | string | ✅ | 対象ページ | グローバルメニュー |
| `original_no` | int | ✅ | 元の項目番号 | 40 |

**サンプル**:

```csv
item_id,category,subcategory,item_name,automation_type,check_type,priority,difficulty,instruction,target_page,original_no
1,サイトの使いやすさ,メニューとナビゲーション,メニュー項目数は適切な数,A,script,high,1,nav要素内のメニュー項目数をカウント,グローバルメニュー,40
2,サイトの使いやすさ,メニューとナビゲーション,グローバルメニューに「株主」を含む,A,script,high,1,グローバルメニュー内のテキストに「株主」が含まれるか,グローバルメニュー,70
```

**バリデーションルール**:

- `item_id`: 1以上の整数、重複なし
- `automation_type`: A, B, C, D のいずれか
- `check_type`: script または llm
- `priority`: high, medium, low のいずれか
- `difficulty`: 1, 2, 3 のいずれか

---

### 3. config.yaml

**概要**: システム設定

**構造**:

```yaml
# API設定
api:
  provider: "claude"  # claude or openai
  claude:
    model: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
    max_tokens: 4096
  openai:
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"
    max_tokens: 4096
  max_retries: 3
  timeout: 60
  rate_limit_delay: 0.5

# スクレイピング設定
scraping:
  headless: true
  wait_until: "networkidle"
  delay_after_load: 2.0
  timeout: 30
  user_agent: "Mozilla/5.0 (compatible; IRSiteEvaluator/1.0)"
  max_parallel: 3
  screenshot_on_error: true

# 処理設定
processing:
  checkpoint_interval: 5
  batch_semantic_checks: true
  skip_errors: true
  max_retries_per_site: 2

# ログ設定
logging:
  level: "INFO"
  file: "output/execution.log"
  console: true
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 出力設定
output:
  summary_csv: "output/results_summary.csv"
  detailed_csv: "output/results_detailed.csv"
  error_log: "output/error_log.txt"
  checkpoint_dir: "checkpoint"

# 入力設定
input:
  sites_list: "input/sample_sites.csv"
  validation_items: "input/validation_items.csv"

# パフォーマンス設定
performance:
  enable_caching: true
  cache_dir: ".cache"
  max_cache_size_mb: 500
```

---

## 中間データ構造

### 1. Site（サイト情報）

**役割**: 評価対象サイトの表現

```python
@dataclass
class Site:
    """サイト情報"""
    site_id: int
    company_name: str
    url: str
    industry: Optional[str] = None
    note: Optional[str] = None

    def __post_init__(self):
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {self.url}")
```

---

### 2. ValidationItem（検証項目）

**役割**: 検証項目の定義

```python
@dataclass
class ValidationItem:
    """検証項目"""
    item_id: int
    category: str
    subcategory: str
    item_name: str
    automation_type: Literal['A', 'B', 'C', 'D']
    check_type: Literal['script', 'llm']
    priority: Literal['high', 'medium', 'low']
    difficulty: Literal[1, 2, 3]
    instruction: str
    target_page: str
    original_no: int

    def is_script_validation(self) -> bool:
        return self.check_type == 'script'

    def is_llm_validation(self) -> bool:
        return self.check_type == 'llm'
```

---

### 3. ValidationResult（検証結果）

**役割**: 1つの検証結果を表現

```python
@dataclass
class ValidationResult:
    """検証結果"""
    site_id: int
    company_name: str
    url: str
    item_id: int
    item_name: str
    category: str
    subcategory: str
    result: Literal['PASS', 'FAIL', 'UNKNOWN', 'ERROR']
    confidence: float  # 0.0-1.0
    details: str
    checked_at: datetime
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            'site_id': self.site_id,
            'company_name': self.company_name,
            'url': self.url,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'category': self.category,
            'subcategory': self.subcategory,
            'result': self.result,
            'confidence': self.confidence,
            'details': self.details,
            'checked_at': self.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': self.error_message or '',
            'screenshot_path': self.screenshot_path or ''
        }

    def is_success(self) -> bool:
        return self.result == 'PASS'

    def is_failure(self) -> bool:
        return self.result == 'FAIL'

    def is_error(self) -> bool:
        return self.result == 'ERROR'
```

---

### 4. LLMResponse（LLM応答）

**役割**: LLM APIからの応答を解析

```python
@dataclass
class LLMResponse:
    """LLM応答"""
    raw_response: str
    found: bool
    confidence: float
    details: str
    reasoning: Optional[str] = None

    @classmethod
    def from_json(cls, response_text: str) -> 'LLMResponse':
        """JSON文字列からパース"""
        try:
            data = json.loads(response_text)
            return cls(
                raw_response=response_text,
                found=data.get('found', False),
                confidence=data.get('confidence', 0.0),
                details=data.get('details', ''),
                reasoning=data.get('reasoning')
            )
        except json.JSONDecodeError:
            # フォールバック処理
            return cls(
                raw_response=response_text,
                found=False,
                confidence=0.0,
                details='Failed to parse LLM response',
                reasoning=None
            )
```

---

### 5. Checkpoint（チェックポイント）

**役割**: 処理の中断・再開のための中間保存

```python
@dataclass
class Checkpoint:
    """チェックポイント"""
    timestamp: datetime
    completed_sites: List[int]
    total_sites: int
    results: List[ValidationResult]
    current_site_id: int

    def to_json(self) -> str:
        """JSON形式にシリアライズ"""
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'completed_sites': self.completed_sites,
            'total_sites': self.total_sites,
            'results': [r.to_dict() for r in self.results],
            'current_site_id': self.current_site_id
        }, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Checkpoint':
        """JSONからデシリアライズ"""
        data = json.loads(json_str)
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            completed_sites=data['completed_sites'],
            total_sites=data['total_sites'],
            results=[ValidationResult(**r) for r in data['results']],
            current_site_id=data['current_site_id']
        )

    def save(self, filepath: str):
        """ファイルに保存"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> 'Checkpoint':
        """ファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
```

---

## 出力データ構造

### 1. results_summary.csv

**概要**: 全検証結果のサマリー（フラット形式）

**スキーマ**:

| カラム名 | 型 | 説明 | 例 |
|---------|-----|------|-----|
| `site_id` | int | サイトID | 1 |
| `company_name` | string | 企業名 | トヨタ自動車 |
| `url` | string | URL | https://global.toyota/jp/ |
| `item_id` | int | 項目ID | 1 |
| `item_name` | string | 項目名 | メニュー項目数は適切 |
| `category` | string | カテゴリ | サイトの使いやすさ |
| `subcategory` | string | サブカテゴリ | メニューとナビゲーション |
| `result` | string | 結果 | PASS, FAIL, UNKNOWN, ERROR |
| `confidence` | float | 信頼度（0.0-1.0） | 1.0 |
| `details` | string | 詳細 | グローバルメニュー8項目 |
| `checked_at` | datetime | チェック日時 | 2025-10-25 14:30:00 |
| `error_message` | string | エラーメッセージ | (空白) |
| `screenshot_path` | string | スクリーンショットパス | (空白) |

**サンプル**:

```csv
site_id,company_name,url,item_id,item_name,category,subcategory,result,confidence,details,checked_at,error_message,screenshot_path
1,トヨタ自動車,https://global.toyota/jp/,1,メニュー項目数は適切,サイトの使いやすさ,メニューとナビゲーション,PASS,1.0,グローバルメニュー8項目,2025-10-25 14:30:00,,
1,トヨタ自動車,https://global.toyota/jp/,2,グローバルメニューに「株主」を含む,サイトの使いやすさ,メニューとナビゲーション,PASS,1.0,「投資家情報」メニュー検出,2025-10-25 14:30:05,,
```

**行数**: 500行（10サイト × 50項目）

---

### 2. results_detailed.csv

**概要**: カテゴリ別集計やサイト別スコア

**スキーマ（カテゴリ別集計）**:

| カラム名 | 型 | 説明 | 例 |
|---------|-----|------|-----|
| `site_id` | int | サイトID | 1 |
| `company_name` | string | 企業名 | トヨタ自動車 |
| `category` | string | カテゴリ | サイトの使いやすさ |
| `total_items` | int | 総項目数 | 30 |
| `pass_count` | int | PASS数 | 25 |
| `fail_count` | int | FAIL数 | 3 |
| `unknown_count` | int | UNKNOWN数 | 1 |
| `error_count` | int | ERROR数 | 1 |
| `pass_rate` | float | PASS率 | 0.833 |
| `avg_confidence` | float | 平均信頼度 | 0.95 |

**サンプル**:

```csv
site_id,company_name,category,total_items,pass_count,fail_count,unknown_count,error_count,pass_rate,avg_confidence
1,トヨタ自動車,サイトの使いやすさ,30,25,3,1,1,0.833,0.95
1,トヨタ自動車,財務・業績情報,15,12,2,1,0,0.800,0.90
```

---

### 3. error_log.txt

**概要**: エラー詳細ログ

**フォーマット**:

```
[ERROR] 2025-10-25 14:35:00 | Site: トヨタ自動車 (ID: 1) | Item: パンくずリスト (ID: 3)
Message: Timeout while loading page
URL: https://global.toyota/jp/ir/
Retry: 1/3
Stacktrace:
  TimeoutError: Timeout 30000ms exceeded.
  ...

[ERROR] 2025-10-25 14:40:00 | Site: ソニーグループ (ID: 2) | Item: 社長経歴掲載 (ID: 45)
Message: LLM API rate limit exceeded
Retry: 2/3
Stacktrace:
  RateLimitError: Rate limit exceeded. Please retry after 60 seconds.
  ...
```

---

### 4. execution.log

**概要**: 実行全体のログ

**フォーマット**:

```
2025-10-25 14:30:00 - INFO - ===== IRサイト評価ツール 開始 =====
2025-10-25 14:30:00 - INFO - 設定読み込み完了: config.yaml
2025-10-25 14:30:00 - INFO - 対象サイト数: 10
2025-10-25 14:30:00 - INFO - 検証項目数: 50
2025-10-25 14:30:00 - INFO - 総検証数: 500
2025-10-25 14:30:05 - INFO - [1/10] Processing: トヨタ自動車 (https://global.toyota/jp/)
2025-10-25 14:30:10 - INFO -   [1/50] Checking: メニュー項目数は適切 → PASS (1.0)
2025-10-25 14:30:15 - INFO -   [2/50] Checking: グローバルメニューに「株主」を含む → PASS (1.0)
...
2025-10-25 14:32:00 - INFO - Checkpoint saved: checkpoint/progress_5.json
...
2025-10-25 14:45:00 - INFO - ===== IRサイト評価ツール 完了 =====
2025-10-25 14:45:00 - INFO - 実行時間: 15分00秒
2025-10-25 14:45:00 - INFO - 総検証数: 500
2025-10-25 14:45:00 - INFO - PASS: 420 (84.0%)
2025-10-25 14:45:00 - INFO - FAIL: 70 (14.0%)
2025-10-25 14:45:00 - INFO - UNKNOWN: 5 (1.0%)
2025-10-25 14:45:00 - INFO - ERROR: 5 (1.0%)
2025-10-25 14:45:00 - INFO - LLM API呼び出し回数: 230
2025-10-25 14:45:00 - INFO - 推定コスト: $1.20
```

---

## Pythonデータクラス定義

### 完全なデータモデル定義

**ファイル**: `src/models.py`

```python
"""データモデル定義"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal
import json


@dataclass
class Site:
    """サイト情報"""
    site_id: int
    company_name: str
    url: str
    industry: Optional[str] = None
    note: Optional[str] = None


@dataclass
class ValidationItem:
    """検証項目"""
    item_id: int
    category: str
    subcategory: str
    item_name: str
    automation_type: Literal['A', 'B', 'C', 'D']
    check_type: Literal['script', 'llm']
    priority: Literal['high', 'medium', 'low']
    difficulty: Literal[1, 2, 3]
    instruction: str
    target_page: str
    original_no: int

    def is_script_validation(self) -> bool:
        return self.check_type == 'script'

    def is_llm_validation(self) -> bool:
        return self.check_type == 'llm'


@dataclass
class ValidationResult:
    """検証結果"""
    site_id: int
    company_name: str
    url: str
    item_id: int
    item_name: str
    category: str
    subcategory: str
    result: Literal['PASS', 'FAIL', 'UNKNOWN', 'ERROR']
    confidence: float
    details: str
    checked_at: datetime
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'site_id': self.site_id,
            'company_name': self.company_name,
            'url': self.url,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'category': self.category,
            'subcategory': self.subcategory,
            'result': self.result,
            'confidence': self.confidence,
            'details': self.details,
            'checked_at': self.checked_at.strftime('%Y-%m-%d %H:%M:%S'),
            'error_message': self.error_message or '',
            'screenshot_path': self.screenshot_path or ''
        }


@dataclass
class LLMResponse:
    """LLM応答"""
    raw_response: str
    found: bool
    confidence: float
    details: str
    reasoning: Optional[str] = None


@dataclass
class Checkpoint:
    """チェックポイント"""
    timestamp: datetime
    completed_sites: List[int]
    total_sites: int
    results: List[ValidationResult]
    current_site_id: int

    def to_json(self) -> str:
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'completed_sites': self.completed_sites,
            'total_sites': self.total_sites,
            'results': [r.to_dict() for r in self.results],
            'current_site_id': self.current_site_id
        }, ensure_ascii=False, indent=2)
```

---

## データ検証ルール

### 入力データ検証

```python
def validate_sites_csv(df: pd.DataFrame) -> List[str]:
    """sites_list.csv のバリデーション"""
    errors = []

    # 必須カラム確認
    required_cols = ['site_id', 'company_name', 'url']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    # site_id の重複確認
    if df['site_id'].duplicated().any():
        errors.append("Duplicate site_id found")

    # URL の妥当性確認
    invalid_urls = df[~df['url'].str.match(r'https?://.*')]
    if not invalid_urls.empty:
        errors.append(f"Invalid URLs: {invalid_urls['url'].tolist()}")

    return errors


def validate_validation_items_csv(df: pd.DataFrame) -> List[str]:
    """validation_items.csv のバリデーション"""
    errors = []

    # automation_type の妥当性
    invalid_types = df[~df['automation_type'].isin(['A', 'B', 'C', 'D'])]
    if not invalid_types.empty:
        errors.append(f"Invalid automation_type: {invalid_types['automation_type'].tolist()}")

    # check_type の妥当性
    invalid_checks = df[~df['check_type'].isin(['script', 'llm'])]
    if not invalid_checks.empty:
        errors.append(f"Invalid check_type: {invalid_checks['check_type'].tolist()}")

    return errors
```

---

## まとめ

このドキュメントでは、IRサイト評価ツールで使用される全データ構造を定義しました：

✅ **入力データ**: CSV形式（sites_list, validation_items）、YAML形式（config）
✅ **中間データ**: Pythonデータクラス（Site, ValidationItem, ValidationResult等）
✅ **出力データ**: CSV形式（results_summary, results_detailed）、ログファイル
✅ **データ検証**: 入力データのバリデーションルール

これらの構造により、データの一貫性と型安全性を保証します。

---

**作成者**: Claude Code
**最終更新**: 2025-10-25
