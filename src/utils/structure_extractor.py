"""HTML構造＋ビジュアル解析ユーティリティ

LLM向けメタデータおよび VISUAL 観点向けの CSS / スクリーンショット情報を抽出する。
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterable

from bs4 import BeautifulSoup
from playwright.async_api import Page

MAX_MENU_ITEMS = 10
MAX_MEDIA_ITEMS = 10
MAX_HEADING_ITEMS = 10
MAX_FAQ_ITEMS = 6
MAX_LINK_ITEMS = 12
MAX_LIST_ITEMS = 5
MAX_NEWS_ITEMS = 8
MAX_SEARCH_ITEMS = 5

DEFAULT_VISUAL_SELECTORS = [
    'body',
    'header',
    'main',
    'footer',
    '.hero',
    '.fv',
    '.main-visual',
    '.carousel',
    '[data-carousel]',
    '.swiper',
    '.slick-slider',
]
VISUAL_SCREENSHOT_DIR = Path('output/visual')


def _clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _extract_menu(container, depth: int = 0, limit: int = MAX_MENU_ITEMS) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    if depth > 2:
        return items
    li_elements = container.find_all("li", recursive=False)
    for li in li_elements:
        link = li.find("a", href=True)
        if link:
            items.append({
                "text": _clean_text(link.get_text())[:80],
                "href": link.get("href", ""),
                "depth": depth
            })
            if len(items) >= limit:
                break
        sub = li.find("ul")
        if sub and len(items) < limit:
            items.extend(_extract_menu(sub, depth + 1, limit - len(items)))
    return items


def _collect_navs(soup: BeautifulSoup) -> List[Dict[str, object]]:
    navs: List[Dict[str, object]] = []
    for nav in soup.find_all("nav"):
        label = nav.get("aria-label") or nav.get("role") or "nav"
        ul = nav.find("ul")
        if not ul:
            continue
        entries = _extract_menu(ul)
        if entries:
            navs.append({"label": label[:40], "items": entries})
        if len(navs) >= 3:
            break
    return navs


def _collect_breadcrumbs(soup: BeautifulSoup) -> List[str]:
    selectors = [
        ('nav', {"aria-label": "breadcrumb"}),
        ('.breadcrumb', {}),
        ('ol.breadcrumb', {}),
        ('ul.breadcrumb', {}),
    ]
    crumbs: List[str] = []
    for selector, attrs in selectors:
        if selector.startswith('.'):
            elements = soup.select(selector)
        else:
            elements = soup.find_all(selector, attrs=attrs)
        for el in elements:
            texts = [_clean_text(item.get_text()) for item in el.find_all('li')]
            text = " > ".join(filter(None, texts))
            if text:
                crumbs.append(text[:120])
        if crumbs:
            break
    return crumbs[:2]


def _collect_media_links(soup: BeautifulSoup) -> Dict[str, List[str]]:
    pdf_links = []
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        if any(href.endswith(ext) for ext in ['.pdf', '.xls', '.xlsx', '.ppt', '.pptx']):
            pdf_links.append(f"{_clean_text(link.get_text())[:60]} -> {link['href']}")
    video_sources = [video.get('src', '') for video in soup.find_all('video') if video.get('src')]
    if not video_sources:
        video_sources = [source.get('src', '') for source in soup.find_all('source') if source.get('type', '').startswith('video')]
    image_alts = [img.get('alt') for img in soup.find_all('img') if img.get('alt')]
    return {
        'pdf_links': pdf_links[:MAX_MEDIA_ITEMS],
        'video_sources': [src for src in video_sources[:MAX_MEDIA_ITEMS] if src],
        'image_alts': [alt[:80] for alt in image_alts[:MAX_MEDIA_ITEMS]]
    }


def _collect_headings(soup: BeautifulSoup) -> List[str]:
    headings = []
    for level in ['h1', 'h2', 'h3']:
        for node in soup.find_all(level):
            text = _clean_text(node.get_text())
            if text:
                headings.append(f"{level.upper()}: {text[:100]}")
            if len(headings) >= MAX_HEADING_ITEMS:
                return headings
    return headings


def _collect_faqs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    faq_sections = soup.select('.faq, .qa, .qna, section:has(h2:contains("FAQ"))')
    faqs: List[Dict[str, str]] = []
    for section in faq_sections:
        questions = section.find_all(['dt', 'p', 'div'], limit=MAX_FAQ_ITEMS * 2)
        for node in questions:
            text = _clean_text(node.get_text())
            if not text:
                continue
            if text.startswith('Q') or 'Q:' in text or '？' in text:
                faqs.append({'question': text[:120]})
                if len(faqs) >= MAX_FAQ_ITEMS:
                    return faqs
        if len(faqs) >= MAX_FAQ_ITEMS:
            break
    return faqs


def _collect_link_summaries(soup: BeautifulSoup) -> List[Dict[str, str]]:
    links: List[Dict[str, str]] = []
    for link in soup.find_all('a', href=True):
        text = _clean_text(link.get_text())
        href = link['href']
        if not text or len(text) < 3:
            continue
        if href.startswith('#'):
            continue
        entry = {'text': text[:80], 'href': href[:200]}
        if entry not in links:
            links.append(entry)
        if len(links) >= MAX_LINK_ITEMS:
            break
    return links


def _collect_list_summaries(soup: BeautifulSoup) -> List[str]:
    lists: List[str] = []
    for ul in soup.find_all(['ul', 'ol']):
        items = [_clean_text(li.get_text()) for li in ul.find_all('li', limit=3)]
        items = [item for item in items if item]
        if len(items) >= 2:
            lists.append(', '.join(items)[:120])
        if len(lists) >= MAX_LIST_ITEMS:
            break
    return lists

NEWS_SELECTORS = [
    'section.news',
    'section[class*="news"]',
    'section:has(h2:contains("ニュース"))',
    'section:has(h2:contains("IR NEWS"))',
    '.ir-news',
    '#ir-news',
    '.news-list',
    '.irNews',
]
DATE_PATTERN = re.compile(r'(20\\d{2}[./年]\\s?\\d{1,2}[./月]\\s?\\d{1,2}日?|\\d{4}-\\d{1,2}-\\d{1,2}|\\d{1,2}\\s?[A-Za-z]{3}\\s?20\\d{2})')


def _collect_news_entries(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    seen = set()
    containers: List[Any] = []
    for selector in NEWS_SELECTORS:
        containers.extend(soup.select(selector))
        if len(containers) >= 3:
            break

    for container in containers:
        for item in container.select('li, article, div'):
            text = _clean_text(item.get_text())
            if not text or len(text) < 5:
                continue
            if text in seen:
                continue
            seen.add(text)
            date = ''
            match = DATE_PATTERN.search(text)
            if match:
                date = match.group(0)
            labels = []
            for badge in item.select('span, em, strong'):
                badge_text = _clean_text(badge.get_text())
                if badge_text and len(badge_text) <= 12:
                    labels.append(badge_text)
            link = item.find('a', href=True)
            href = link['href'] if link else ''
            entries.append({
                'text': text[:160],
                'date': date,
                'labels': labels[:3],
                'href': href[:200]
            })
            if len(entries) >= MAX_NEWS_ITEMS:
                return entries
    return entries


def _collect_search_inputs(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    forms = soup.find_all('form')
    for form in forms:
        inputs = form.find_all('input', {'type': ['search', 'text']})
        for inp in inputs:
            name = inp.get('name', '')
            classes = ' '.join(inp.get('class') or [])
            placeholder = inp.get('placeholder', '')
            if 'search' not in (name + classes + placeholder).lower():
                continue
            entry = {
                'placeholder': placeholder[:80],
                'name': name,
                'class': classes,
                'visible': 'display:none' not in (inp.get('style') or '').lower()
            }
            entries.append(entry)
            if len(entries) >= MAX_SEARCH_ITEMS:
                return entries
    # fallback: standalone input[type=search]
    for inp in soup.find_all('input', {'type': 'search'}):
        entry = {
            'placeholder': (inp.get('placeholder') or '')[:80],
            'name': inp.get('name', ''),
            'class': ' '.join(inp.get('class') or []),
            'visible': 'display:none' not in (inp.get('style') or '').lower()
        }
        if entry not in entries:
            entries.append(entry)
        if len(entries) >= MAX_SEARCH_ITEMS:
            break
    return entries


def extract_structure(html: str) -> Dict[str, object]:
    """HTML文字列から構造メタデータを抽出"""
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception:
        soup = BeautifulSoup(html, 'html.parser')

    data = {
        'menus': _collect_navs(soup),
        'breadcrumbs': _collect_breadcrumbs(soup),
        'media': _collect_media_links(soup),
        'headings': _collect_headings(soup),
        'faqs': _collect_faqs(soup),
        'links': _collect_link_summaries(soup),
        'lists': _collect_list_summaries(soup),
        'news': _collect_news_entries(soup),
        'search_inputs': _collect_search_inputs(soup),
    }
    return data


async def extract_structure_from_page(
    page: Page,
    include_visual: bool = False,
    visual_selectors: Optional[Iterable[str]] = None,
    screenshot_dir: Path = VISUAL_SCREENSHOT_DIR,
) -> Dict[str, object]:
    """Playwrightページから構造データ（必要に応じてビジュアル情報込み）を抽出"""
    html = await page.content()
    structure = extract_structure(html)
    if include_visual:
        structure['visual'] = await capture_visual_context(
            page,
            selectors=list(visual_selectors) if visual_selectors else None,
            screenshot_dir=screenshot_dir,
        )
    return structure


def summarize_structure(structure: Optional[Dict[str, object]], max_lines: int = 12) -> str:
    if not structure:
        return ""
    lines: List[str] = []

    for nav in structure.get('menus', [])[:2]:
        items = nav.get('items', [])
        snippet = ', '.join(item.get('text', '') for item in items[:5])
        lines.append(f"Menu({nav.get('label', 'nav')}): {snippet}")

    crumbs = structure.get('breadcrumbs') or []
    for crumb in crumbs:
        lines.append(f"Breadcrumb: {crumb}")

    media = structure.get('media') or {}
    pdfs = media.get('pdf_links') or []
    if pdfs:
        lines.append(f"PDFs: {len(pdfs)} (例: {pdfs[0][:80]})")
    videos = media.get('video_sources') or []
    if videos:
        lines.append(f"Videos: {len(videos)} (例: {videos[0][:80]})")

    headings = structure.get('headings') or []
    for heading in headings[:3]:
        lines.append(f"{heading}")

    faqs = structure.get('faqs') or []
    for faq in faqs[:2]:
        lines.append(f"FAQ: {faq.get('question', '')}")

    lists_summary = structure.get('lists') or []
    for lst in lists_summary[:2]:
        lines.append(f"List: {lst}")

    link_entries = structure.get('links') or []
    if link_entries:
        first_link = link_entries[0]
        lines.append(f"Links: {len(link_entries)} (例: {first_link.get('text', '')})")

    text = '\n'.join(lines)
    return text[:1000]


# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------

def _sanitize_selector(selector: str) -> str:
    sanitized = re.sub(r'[^a-zA-Z0-9_-]+', '_', selector.strip()) or 'element'
    return sanitized[:50]


def _parse_color_to_rgb(value: str) -> Optional[tuple]:
    if not value:
        return None
    value = value.strip()
    hex_match = re.fullmatch(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})', value)
    if hex_match:
        hex_value = hex_match.group(1)
        if len(hex_value) == 3:
            hex_value = ''.join(ch * 2 for ch in hex_value)
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        return (r, g, b)
    rgb_match = re.fullmatch(
        r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*(\d*\.?\d+))?\s*\)',
        value
    )
    if rgb_match:
        r, g, b = map(int, rgb_match.groups()[:3])
        return (r, g, b)
    return None


def _relative_luminance(rgb: tuple) -> float:
    def normalize(channel: int) -> float:
        c = channel / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * normalize(r) + 0.7152 * normalize(g) + 0.0722 * normalize(b)


def _contrast_ratio(color_a: Optional[str], color_b: Optional[str]) -> Optional[float]:
    rgb_a = _parse_color_to_rgb(color_a or '')
    rgb_b = _parse_color_to_rgb(color_b or '')
    if not rgb_a or not rgb_b:
        return None
    lum_a = _relative_luminance(rgb_a)
    lum_b = _relative_luminance(rgb_b)
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return round((lighter + 0.05) / (darker + 0.05), 2)


async def _capture_element_screenshot(locator, selector: str, screenshot_dir: Path) -> Optional[str]:
    try:
        count = await locator.count()
        if count == 0:
            return None
        target = locator.first
        # skip invisible elements
        box = await target.bounding_box()
        if not box or box['width'] < 4 or box['height'] < 4:
            return None
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        filename = _sanitize_selector(selector)
        path = screenshot_dir / f"{filename}.png"
        await target.screenshot(path=str(path))
        return str(path)
    except Exception:
        return None


async def capture_visual_context(
    page: Page,
    selectors: Optional[List[str]] = None,
    screenshot_dir: Path = VISUAL_SCREENSHOT_DIR,
) -> Dict[str, Any]:
    """CSSプロパティ、カルーセル情報、要素スクリーンショットを取得"""
    selector_list = selectors or DEFAULT_VISUAL_SELECTORS
    selector_list = list(dict.fromkeys(selector_list))  # unique order保持

    computed_styles = await page.evaluate(
        """
        (selectors) => {
            return selectors.map((selector) => {
                const element = document.querySelector(selector);
                if (!element) {
                    return { selector, found: false };
                }
                const styles = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return {
                    selector,
                    found: true,
                    styles: {
                        color: styles.color,
                        backgroundColor: styles.backgroundColor,
                        fontSize: styles.fontSize,
                        fontWeight: styles.fontWeight,
                        lineHeight: styles.lineHeight,
                        display: styles.display,
                        opacity: styles.opacity,
                    },
                    rect: {
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left,
                    }
                };
            });
        }
        """,
        selector_list,
    )

    style_results: List[Dict[str, Any]] = []
    screenshot_entries: List[Dict[str, Any]] = []

    for style in computed_styles:
        if not style.get('found'):
            style_results.append(style)
            continue

        color = style['styles'].get('color')
        background = style['styles'].get('backgroundColor')
        contrast = _contrast_ratio(color, background)
        style['styles']['contrastRatio'] = contrast
        style_results.append(style)

        locator = page.locator(style['selector'])
        screenshot_path = await _capture_element_screenshot(locator, style['selector'], screenshot_dir)
        if screenshot_path:
            screenshot_entries.append({
                'selector': style['selector'],
                'path': screenshot_path,
                'width': style.get('rect', {}).get('width'),
                'height': style.get('rect', {}).get('height'),
            })

    carousel_info = await page.evaluate(
        """
        () => {
            const selectors = [
                '.carousel',
                '[data-carousel]',
                '.swiper',
                '.splide',
                '.slick-slider',
                '.slider',
            ];
            const seen = new Set();
            const carousels = [];
            selectors.forEach((selector) => {
                document.querySelectorAll(selector).forEach((element) => {
                    if (seen.has(element)) return;
                    seen.add(element);
                    const slides = element.querySelectorAll(
                        '.slide, .swiper-slide, .splide__slide, .slick-slide, li'
                    );
                    const pauseButton = element.querySelector(
                        'button[aria-label*="停止"], button[class*="pause"], [data-action="pause"]'
                    );
                    const autoplayAttr = element.getAttribute('data-autoplay') || '';
                    carousels.push({
                        selector: element.id ? `#${element.id}` : (element.className ? '.' + element.className.trim().replace(/\\s+/g, '.') : 'carousel'),
                        slideCount: slides.length,
                        hasPauseControl: !!pauseButton,
                        autoplay: /auto|swiper|slick|true/.test(autoplayAttr),
                    });
                });
            });
            return carousels.slice(0, 5);
        }
        """
    )

    return {
        'styles': style_results,
        'screenshots': screenshot_entries,
        'carousels': carousel_info,
    }
