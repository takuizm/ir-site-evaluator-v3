"""データモデル定義

IRサイト評価ツールで使用する全データモデルを定義。
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Literal
import json


@dataclass
class Site:
    """サイト情報

    評価対象のWebサイトを表現するデータクラス。
    """
    site_id: int
    company_name: str
    url: str
    industry: Optional[str] = None
    note: Optional[str] = None

    def __post_init__(self):
        """初期化後のバリデーション"""
        if not self.url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {self.url}")
        if self.site_id <= 0:
            raise ValueError(f"Invalid site_id: {self.site_id}")


@dataclass
class ValidationItem:
    """検証項目

    1つの評価項目を表現するデータクラス。
    """
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

    def __post_init__(self):
        """初期化後のバリデーション"""
        if self.item_id <= 0:
            raise ValueError(f"Invalid item_id: {self.item_id}")
        if self.automation_type not in ['A', 'B', 'C', 'D']:
            raise ValueError(f"Invalid automation_type: {self.automation_type}")
        if self.check_type not in ['script', 'llm']:
            raise ValueError(f"Invalid check_type: {self.check_type}")

    def is_script_validation(self) -> bool:
        """スクリプト検証かどうか"""
        return self.check_type == 'script'

    def is_llm_validation(self) -> bool:
        """LLM検証かどうか"""
        return self.check_type == 'llm'


@dataclass
class ValidationResult:
    """検証結果

    1つの検証項目の実行結果を表現するデータクラス。
    """
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
    checked_url: Optional[str] = None  # 実際に調査したサブページURL
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None

    def __post_init__(self):
        """初期化後のバリデーション"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Invalid confidence: {self.confidence}")
        if self.result not in ['PASS', 'FAIL', 'UNKNOWN', 'ERROR']:
            raise ValueError(f"Invalid result: {self.result}")

    def to_dict(self) -> dict:
        """辞書形式に変換

        CSV出力などで使用。
        """
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
            'checked_url': self.checked_url or '',
            'error_message': self.error_message or '',
            'screenshot_path': self.screenshot_path or ''
        }

    def is_success(self) -> bool:
        """検証成功かどうか"""
        return self.result == 'PASS'

    def is_failure(self) -> bool:
        """検証失敗かどうか"""
        return self.result == 'FAIL'

    def is_error(self) -> bool:
        """エラーかどうか"""
        return self.result == 'ERROR'

    def is_unknown(self) -> bool:
        """判定不能かどうか"""
        return self.result == 'UNKNOWN'


@dataclass
class LLMResponse:
    """LLM応答

    LLM APIからの応答を解析した結果を表現するデータクラス。
    """
    raw_response: str
    found: bool
    confidence: float
    details: str
    reasoning: Optional[str] = None

    @classmethod
    def from_json(cls, response_text: str) -> 'LLMResponse':
        """JSON文字列からパース

        Args:
            response_text: LLMからのJSON応答

        Returns:
            LLMResponseインスタンス
        """
        try:
            data = json.loads(response_text)
            return cls(
                raw_response=response_text,
                found=data.get('found', False),
                confidence=float(data.get('confidence', 0.0)),
                details=data.get('details', ''),
                reasoning=data.get('reasoning')
            )
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # JSONパース失敗時のフォールバック
            return cls(
                raw_response=response_text,
                found=False,
                confidence=0.0,
                details=f'Failed to parse LLM response: {str(e)}',
                reasoning=None
            )

    @classmethod
    def from_text(cls, response_text: str, found: bool = False) -> 'LLMResponse':
        """プレーンテキストから作成

        JSONパースに失敗した場合などに使用。

        Args:
            response_text: LLMからのテキスト応答
            found: 発見されたかどうか

        Returns:
            LLMResponseインスタンス
        """
        return cls(
            raw_response=response_text,
            found=found,
            confidence=0.5 if found else 0.0,
            details=response_text[:500],  # 最大500文字
            reasoning=None
        )


@dataclass
class Checkpoint:
    """チェックポイント

    処理の中断・再開のための中間保存データ。
    """
    timestamp: datetime
    completed_sites: List[int]
    total_sites: int
    results: List[dict]  # ValidationResultの辞書表現
    current_site_id: int

    def to_json(self) -> str:
        """JSON形式にシリアライズ

        Returns:
            JSON文字列
        """
        return json.dumps({
            'timestamp': self.timestamp.isoformat(),
            'completed_sites': self.completed_sites,
            'total_sites': self.total_sites,
            'results': self.results,
            'current_site_id': self.current_site_id
        }, ensure_ascii=False, indent=2)

    def save(self, filepath: str):
        """ファイルに保存

        Args:
            filepath: 保存先ファイルパス
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> 'Checkpoint':
        """ファイルから読み込み

        Args:
            filepath: 読み込み元ファイルパス

        Returns:
            Checkpointインスタンス
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            completed_sites=data['completed_sites'],
            total_sites=data['total_sites'],
            results=data['results'],
            current_site_id=data['current_site_id']
        )


# データバリデーション関数

def validate_sites_list(sites: List[Site]) -> List[str]:
    """サイトリストのバリデーション

    Args:
        sites: サイトのリスト

    Returns:
        エラーメッセージのリスト（空ならバリデーション成功）
    """
    errors = []

    # site_id の重複確認
    site_ids = [site.site_id for site in sites]
    if len(site_ids) != len(set(site_ids)):
        errors.append("Duplicate site_id found")

    # URLの妥当性は__post_init__でチェック済み

    return errors


def validate_validation_items(items: List[ValidationItem]) -> List[str]:
    """検証項目リストのバリデーション

    Args:
        items: 検証項目のリスト

    Returns:
        エラーメッセージのリスト（空ならバリデーション成功）
    """
    errors = []

    # item_id の重複確認
    item_ids = [item.item_id for item in items]
    if len(item_ids) != len(set(item_ids)):
        errors.append("Duplicate item_id found")

    # automation_type と check_type の整合性確認
    for item in items:
        if item.automation_type == 'A' and item.check_type != 'script':
            errors.append(f"Item {item.item_id}: automation_type 'A' should have check_type 'script'")
        elif item.automation_type == 'B' and item.check_type != 'llm':
            errors.append(f"Item {item.item_id}: automation_type 'B' should have check_type 'llm'")

    return errors
