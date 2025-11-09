from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Tuple, List

CRITERIA_COLUMNS = [
    'ID',
    '2025追加削除',
    'レポート抽出用',
    'CategoryNo.',
    'カテゴリ',
    'SubCategoryNo.',
    'サブカテゴリ',
    '項目グループ',
    '項目名',
]


def load_criteria_metadata(path: Path) -> Tuple[Dict[int, Dict[str, str]], List[str]]:
    metadata: Dict[int, Dict[str, str]] = {}
    if not path.exists():
        return metadata, []

    with path.open(encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                item_id = int(row.get('ID') or row.get('id') or 0)
            except ValueError:
                continue
            if not item_id:
                continue
            meta = {}
            for col in CRITERIA_COLUMNS:
                value = row.get(col, '')
                if isinstance(value, str):
                    value = value.replace('\r', ' ').replace('\n', ' ').strip()
                meta[col] = value
            metadata[item_id] = meta

    return metadata, CRITERIA_COLUMNS
