"""Playwright Page/Locator を模したシンプルなモック"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup, Tag


class MockElement:
    def __init__(self, node: Tag):
        self.node = node

    async def inner_text(self) -> str:
        return self.node.get_text(" ", strip=True)


class MockLocator:
    def __init__(self, nodes: List[Tag]):
        self.nodes = nodes

    async def count(self) -> int:
        return len(self.nodes)

    async def all(self) -> List[MockElement]:
        return [MockElement(node) for node in self.nodes]

    def nth(self, index: int) -> MockElement:
        return MockElement(self.nodes[index])

    async def all_text_contents(self) -> List[str]:
        return [node.get_text(" ", strip=True) for node in self.nodes]


class MockPage:
    HAS_TEXT_PATTERN = re.compile(r'^(?P<selector>[^:]+):has-text\("(?P<text>[^"]+)"\)$')

    def __init__(self, html: str, url: str = "https://example.com/ir"):
        self.html = html
        self.url = url
        try:
            self.soup = BeautifulSoup(html, "lxml")
        except Exception:
            self.soup = BeautifulSoup(html, "html.parser")

    def _select(self, selector: str) -> List[Tag]:
        selector = selector.strip()
        if not selector:
            return []

        match = self.HAS_TEXT_PATTERN.match(selector)
        if match:
            base_selector = match.group("selector")
            text = match.group("text")
            base_nodes = self.soup.select(base_selector)
            return [node for node in base_nodes if text in node.get_text()]

        try:
            return self.soup.select(selector)
        except Exception:
            return []

    def locator(self, selector: str) -> MockLocator:
        nodes: List[Tag] = []
        for part in selector.split(','):
            part = part.strip()
            if not part:
                continue
            nodes.extend(self._select(part))
        return MockLocator(nodes)

    async def inner_text(self, selector: str) -> str:
        nodes = self._select(selector)
        if not nodes:
            return ""
        return nodes[0].get_text(" ", strip=True)

    async def content(self) -> str:
        return self.html

    async def evaluate(self, script: str, arg: Optional[object] = None):
        if "window.innerHeight" in script and "getBoundingClientRect" in script:
            viewport = 600
            count = 0
            for link in self.soup.select('a[href$=".pdf"]'):
                top = self._extract_top(link)
                if 0 <= top <= viewport:
                    count += 1
            return count

        if "document.querySelectorAll('a[href$=\".pdf\"]')" in script:
            pdf_links = self.soup.select('a[href$=".pdf"]')
            indicated = 0
            for link in pdf_links:
                text = link.get_text()
                has_icon = link.select_one('img[src*="pdf"], i[class*="pdf"], svg')
                has_text = 'PDF' in text or 'pdf' in text
                has_class = 'pdf' in (link.get('class') or [])
                if has_icon or has_text or has_class:
                    indicated += 1
            return {'total': len(pdf_links), 'indicated': indicated}

        if "document.querySelectorAll('a[target=\"_blank\"]')" in script:
            links = self.soup.select('a[target="_blank"]')
            indicated = 0
            for link in links:
                text = (link.get_text() or "")
                title = link.get('title') or ""
                has_icon = bool(link.select_one('svg, i, img'))
                has_text = any(keyword in text for keyword in ['別ウィンドウ', '新しいウィンドウ', '外部サイト']) or '別ウィンドウ' in title
                if has_icon or has_text:
                    indicated += 1
            return indicated

        if "const elements = document.querySelectorAll('*');" in script and 'style.overflow' in script:
            count = 0
            for node in self.soup.find_all(True):
                if node.name in ('html', 'body'):
                    continue
                style = (node.get('style') or '').lower()
                if any(kw in style for kw in ['overflow:', 'overflowx:', 'overflowy:']):
                    if any(val in style for val in ['scroll', 'auto']):
                        count += 1
                        continue
                classes = ' '.join(node.get('class') or []).lower()
                if 'scroll' in classes:
                    count += 1
            return count

        if "return lhValue / fsValue;" in script:
            font_size = self._get_typography_value('font-size')
            line_height = self._get_typography_value('line-height', font_size)
            return line_height / font_size if font_size else 1.0

        if "window.getComputedStyle(mainElement).fontSize" in script:
            size = self._get_typography_value('font-size')
            return f"{size}px"

        if 'document.querySelectorAll(\'input[type="search"], input[name*="search"]\')' in script:
            inputs = self.soup.select('input[type="search"], input[name*="search"]')
            for node in inputs:
                styles = self._parse_style_attr(node)
                display = styles.get('display', 'block')
                visibility = styles.get('visibility', 'visible')
                width = styles.get('width', '200px')
                if display != 'none' and visibility != 'hidden' and not width.startswith('0'):
                    return True
            return False

        raise NotImplementedError("MockPage.evaluate is not implemented for this script.")

    # --- helpers ---

    def _first_typography_node(self) -> Tag:
        for selector in ['main', 'article', '.main-content']:
            nodes = self._select(selector)
            if nodes:
                return nodes[0]
        return self.soup.body or self.soup

    @staticmethod
    def _parse_style_attr(node: Optional[Tag]) -> Dict[str, str]:
        style = (node.get('style') if node else '') or ''
        result: Dict[str, str] = {}
        for part in style.split(';'):
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            result[key.strip().lower()] = value.strip().lower()
        return result

    def _get_typography_value(self, prop: str, font_size: Optional[float] = None) -> float:
        node = self._first_typography_node()
        styles = self._parse_style_attr(node)
        if prop not in styles:
            styles = self._parse_style_attr(self.soup.body)
        value = styles.get(prop)
        if not value:
            if prop == 'font-size':
                return 16.0
            if prop == 'line-height':
                return (font_size or 16.0) * 1.4
        if value.endswith('px'):
            return float(value.replace('px', ''))
        try:
            numeric = float(value)
            if prop == 'line-height' and font_size:
                return numeric * font_size
            return numeric
        except ValueError:
            if prop == 'font-size':
                return 16.0
            return (font_size or 16.0) * 1.4

    @staticmethod
    def _extract_top(node: Tag) -> float:
        data_top = node.get('data-top')
        if data_top:
            try:
                return float(data_top)
            except ValueError:
                pass
        style = (node.get('style') or '').lower()
        match = re.search(r'margin-top:\s*([0-9.]+)px', style)
        if match:
            return float(match.group(1))
        return 800.0
