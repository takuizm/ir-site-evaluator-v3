"""VISUAL 観点用ヘルパー

ScriptValidator から呼び出して、CSS 指標やスクリーンショット/カルーセル情報を取得・評価する。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from src.utils.structure_extractor import capture_visual_context

DEFAULT_SCREENSHOT_DIR = Path('output/visual')


@dataclass
class VisualCheckResult:
    selector: str
    metrics: Dict[str, Any]
    screenshot_path: Optional[str] = None


@dataclass
class CarouselAnalysis:
    selector: str
    slide_count: int
    has_pause_control: bool
    autoplay: bool


class VisualAnalyzer:
    def __init__(self, screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR):
        self.screenshot_dir = screenshot_dir

    async def capture(self, page: Page, selectors: Optional[List[str]] = None) -> Dict[str, Any]:
        return await capture_visual_context(page, selectors, self.screenshot_dir)

    @staticmethod
    def evaluate_carousels(carousels: List[Dict[str, Any]]) -> List[CarouselAnalysis]:
        analyses: List[CarouselAnalysis] = []
        for carousel in carousels:
            analyses.append(
                CarouselAnalysis(
                    selector=carousel.get('selector', ''),
                    slide_count=int(carousel.get('slideCount') or carousel.get('slide_count') or 0),
                    has_pause_control=bool(carousel.get('hasPauseControl')),
                    autoplay=bool(carousel.get('autoplay')),
                )
            )
        return analyses

    @staticmethod
    def find_style(styles: List[Dict[str, Any]], selector: str) -> Optional[Dict[str, Any]]:
        for entry in styles:
            if entry.get('selector') == selector:
                return entry
        return None


async def get_visual_snapshot(
    page: Page,
    selectors: Optional[List[str]] = None,
    screenshot_dir: Path = DEFAULT_SCREENSHOT_DIR,
) -> Dict[str, Any]:
    analyzer = VisualAnalyzer(screenshot_dir)
    return await analyzer.capture(page, selectors)
