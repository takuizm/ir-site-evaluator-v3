"""ScriptValidator テスト向け共通ユーティリティ"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from src.models import Site, ValidationItem
from src.validators.script_validator import ScriptValidator

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    path = FIXTURE_DIR / name
    return path.read_text(encoding="utf-8")


def make_site(url: str = "https://example.com/ir") -> Site:
    return Site(
        site_id=1,
        company_name="テスト株式会社",
        url=url,
    )


def make_item(item_id: int, name: str) -> ValidationItem:
    return ValidationItem(
        item_id=item_id,
        category="ウェブサイトの使いやすさ",
        subcategory="テスト",
        item_name=name,
        automation_type="A",
        check_type="script",
        priority="high",
        difficulty=1,
        instruction="テスト観点",
        target_page="IRトップ",
        original_no=item_id * 10,
    )


def make_validator() -> ScriptValidator:
    logger = logging.getLogger("script-validator-test")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.ERROR)
    return ScriptValidator(scraper=None, logger=logger)


def run_async(coro):
    return asyncio.run(coro)
