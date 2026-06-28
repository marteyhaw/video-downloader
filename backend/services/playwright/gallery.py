"""Gallery and widget stepping logic for Playwright scans.

Discovers embed URLs hidden behind paginated or lazy-loaded gallery
interfaces by clicking through next buttons, load-more controls,
thumbnails, and pagination links using generic semantic selectors.
"""

import logging

from playwright.sync_api import Locator, Page

from backend.config import settings
from backend.services.embeds.page_embeds import PageEmbeds
from backend.services.embeds.registry import get_embed_providers
from backend.services.playwright.gallery_selectors import (
    _GALLERY_LOAD_MORE_SELECTORS,
    _GALLERY_NEXT_SELECTORS,
    _GALLERY_PAGINATION_SELECTORS,
    _GALLERY_THUMB_SELECTORS,
    _WIDGET_ROOT_SELECTORS,
)
from backend.services.scanning.progress import ScanProgressCallback, noop_progress

logger = logging.getLogger(__name__)

# --- Embed discovery helpers ---


def _discover_page_embeds(page: Page) -> PageEmbeds:
    """Run all registered embed providers against the live page."""
    embeds = PageEmbeds()
    for provider in get_embed_providers():
        try:
            for url in provider.discover_from_page(page):
                embeds.add(provider.name, url)
        except Exception as exc:
            logger.debug("Embed provider %r discover_from_page failed: %s", provider.name, exc)
    return embeds


def _merge_urls(into: PageEmbeds, found: PageEmbeds) -> None:
    into.merge(found)


def merge_page_embeds(into: PageEmbeds, page: Page) -> None:
    """Union newly discovered embed URLs into an accumulating PageEmbeds."""
    _merge_urls(into, _discover_page_embeds(page))


def _merge_widget_embeds(into: PageEmbeds, widget: Locator, page: Page) -> None:
    """Merge page-wide discovery plus widget-scoped HTML fragment."""
    merge_page_embeds(into, page)
    try:
        html = widget.evaluate("el => el.innerHTML")
        base = page.url
        for provider in get_embed_providers():
            try:
                for url in provider.discover_from_html(html or "", base):
                    into.add(provider.name, url)
            except Exception as exc:
                logger.debug("Embed provider %r discover_from_html failed: %s", provider.name, exc)
    except Exception as exc:
        logger.debug("Widget HTML evaluation failed: %s", exc)


# --- Page hydration ---


def hydrate_page_widgets(page: Page) -> None:
    """Scroll widget containers and the page so lazy galleries render."""
    selectors = ", ".join(_WIDGET_ROOT_SELECTORS)
    try:
        page.evaluate(
            """(sel) => {
                document.querySelectorAll(sel).forEach((el) => {
                    el.scrollIntoView({ block: 'center', behavior: 'instant' });
                });
            }""",
            selectors,
        )
        page.wait_for_timeout(500)
    except Exception as exc:
        logger.debug("Widget scroll-into-view failed: %s", exc)
    try:
        page.evaluate(
            """() => {
                const h = document.body.scrollHeight || 0;
                const stops = [0, h * 0.33, h * 0.66, h];
                for (const y of stops) {
                    window.scrollTo(0, y);
                }
            }"""
        )
        page.wait_for_timeout(800)
    except Exception as exc:
        logger.debug("Page scroll pass failed: %s", exc)


# --- Click helpers ---


def _try_click_first(page: Page, selectors: tuple[str, ...], *, timeout_ms: int) -> bool:
    """Click the first visible match from a list of selectors."""
    for selector in selectors:
        try:
            loc = page.locator(selector)
            if loc.count() > 0:
                loc.first.click(timeout=timeout_ms)
                return True
        except Exception as exc:
            logger.debug("Click on %r failed: %s", selector, exc)
    return False


def _try_click_in_widget(
    widget: Locator,
    selectors: tuple[str, ...],
    *,
    timeout_ms: int,
) -> bool:
    """Click the first visible match scoped to a single widget."""
    for selector in selectors:
        try:
            loc = widget.locator(selector)
            count = loc.count()
            for i in range(count):
                item = loc.nth(i)
                try:
                    if item.is_visible():
                        item.click(timeout=timeout_ms)
                        return True
                except Exception as exc:
                    logger.debug("Widget item click on %r failed: %s", selector, exc)
        except Exception as exc:
            logger.debug("Widget locator %r failed: %s", selector, exc)
    return False


def _try_click_nth_in_widget(
    widget: Locator,
    selectors: tuple[str, ...],
    index: int,
    *,
    timeout_ms: int,
) -> bool:
    """Click the nth item matching selectors within a widget."""
    for selector in selectors:
        try:
            loc = widget.locator(selector)
            if loc.count() > index:
                item = loc.nth(index)
                if item.is_visible():
                    item.click(timeout=timeout_ms)
                    return True
        except Exception as exc:
            logger.debug("Nth-item click on %r failed: %s", selector, exc)
    return False


# --- Widget stepping ---


def widget_gallery_step_budget(
    widget_count: int,
    global_max: int,
    per_widget: int,
) -> int:
    """Total click budget when processing up to widget_count widgets."""
    if widget_count <= 0 or global_max <= 0 or per_widget <= 0:
        return 0
    return min(global_max, widget_count * per_widget)


def _widget_roots(page: Page) -> list[Locator]:
    """Find gallery/carousel/slider widget root elements on the page."""
    all_roots: list[Locator] = []
    cap = max(0, settings.playwright_gallery_max_widgets)
    if cap == 0:
        return []
    for selector in _WIDGET_ROOT_SELECTORS:
        roots = page.locator(selector)
        count = roots.count()
        for i in range(count):
            if len(all_roots) >= cap:
                return all_roots
            all_roots.append(roots.nth(i))
    return all_roots


def _scroll_widget_internals(widget: Locator, page: Page) -> None:
    """Scroll overflow containers inside a widget (playlist sidebars, lists)."""
    try:
        widget.evaluate(
            """(root) => {
                const scrollables = [];
                const walk = (el) => {
                    if (!el || el === document.body) return;
                    const style = window.getComputedStyle(el);
                    const oy = style.overflowY;
                    if (
                        (oy === 'auto' || oy === 'scroll') &&
                        el.scrollHeight > el.clientHeight + 20
                    ) {
                        scrollables.push(el);
                    }
                    for (const child of el.children) walk(child);
                };
                walk(root);
                for (const el of scrollables) {
                    const steps = 3;
                    for (let i = 1; i <= steps; i++) {
                        el.scrollTop = (el.scrollHeight * i) / steps;
                    }
                }
            }"""
        )
        page.wait_for_timeout(200)
    except Exception as exc:
        logger.debug("Widget internal-scroll failed: %s", exc)


def _after_gallery_click(
    into: PageEmbeds,
    page: Page,
    widget: Locator | None,
    *,
    wait_ms: int,
) -> None:
    if wait_ms > 0:
        try:
            page.wait_for_timeout(wait_ms)
        except Exception as exc:
            logger.debug("Post-click wait failed: %s", exc)
    if widget is not None:
        _merge_widget_embeds(into, widget, page)
    else:
        merge_page_embeds(into, page)


def _step_single_widget(
    widget: Locator,
    page: Page,
    *,
    into: PageEmbeds,
    steps_budget: int,
    wait_ms: int,
    click_ms: int,
) -> int:
    """Interact with one gallery widget; return number of clicks performed."""
    if steps_budget <= 0:
        return 0
    clicks = 0
    consecutive_misses = 0
    load_more_used = False
    card_index = 0

    while clicks < steps_budget and consecutive_misses < 2:
        acted = False

        if not load_more_used:
            if _try_click_in_widget(widget, _GALLERY_LOAD_MORE_SELECTORS, timeout_ms=click_ms):
                load_more_used = True
                acted = True

        if not acted:
            acted = _try_click_in_widget(widget, _GALLERY_PAGINATION_SELECTORS, timeout_ms=click_ms)

        if not acted:
            acted = _try_click_in_widget(widget, _GALLERY_NEXT_SELECTORS, timeout_ms=click_ms)

        if not acted:
            acted = _try_click_nth_in_widget(widget, _GALLERY_THUMB_SELECTORS, card_index, timeout_ms=click_ms)
            if acted:
                card_index += 1

        if not acted:
            consecutive_misses += 1
            break

        consecutive_misses = 0
        clicks += 1
        _after_gallery_click(into, page, widget, wait_ms=wait_ms)

    return clicks


def _step_gallery_generic(
    page: Page,
    *,
    into: PageEmbeds,
    progress: ScanProgressCallback | None = None,
) -> None:
    """Page-wide gallery stepping when no scoped widget containers are found."""
    report = progress or noop_progress
    max_steps = max(0, settings.playwright_gallery_max_steps)
    if max_steps == 0:
        return
    click_ms = settings.playwright_click_timeout_ms
    wait_ms = max(0, settings.playwright_gallery_step_wait_ms)
    report("playwright_gallery", f"Stepping gallery (up to {max_steps} interactions)…")

    for step in range(max_steps):
        clicked = _try_click_first(page, _GALLERY_NEXT_SELECTORS, timeout_ms=click_ms)
        if not clicked and step < max_steps // 2:
            thumb_index = step % 6
            for selector in _GALLERY_THUMB_SELECTORS:
                try:
                    thumbs = page.locator(selector)
                    if thumbs.count() > thumb_index:
                        thumbs.nth(thumb_index).click(timeout=click_ms)
                        clicked = True
                        break
                except Exception as exc:
                    logger.debug("Thumbnail click on %r failed: %s", selector, exc)
        if not clicked:
            break
        _after_gallery_click(into, page, None, wait_ms=wait_ms)


def step_galleries(
    page: Page,
    *,
    into: PageEmbeds,
    progress: ScanProgressCallback | None = None,
) -> None:
    """Step gallery/carousel widgets to discover additional embed URLs."""
    report = progress or noop_progress
    global_max = max(0, settings.playwright_gallery_max_steps)
    per_widget = max(0, settings.playwright_gallery_steps_per_widget)
    if global_max == 0 or per_widget == 0:
        return

    roots = _widget_roots(page)
    if not roots:
        _step_gallery_generic(page, into=into, progress=progress)
        return

    total_budget = widget_gallery_step_budget(len(roots), global_max, per_widget)
    report(
        "playwright_gallery",
        f"Stepping {len(roots)} gallery widget(s) (up to {total_budget} interactions)…",
    )

    click_ms = settings.playwright_click_timeout_ms
    wait_ms = max(0, settings.playwright_gallery_step_wait_ms)
    global_remaining = global_max

    for widget in roots:
        if global_remaining <= 0:
            break
        try:
            widget.scroll_into_view_if_needed(timeout=click_ms)
        except Exception:
            try:
                widget.evaluate("el => el.scrollIntoView({ block: 'center', behavior: 'instant' })")
            except Exception as exc:
                logger.debug("Widget scroll-into-view fallback failed: %s", exc)
        page.wait_for_timeout(300)
        _merge_widget_embeds(into, widget, page)
        _scroll_widget_internals(widget, page)
        _merge_widget_embeds(into, widget, page)

        widget_budget = min(per_widget, global_remaining)
        used = _step_single_widget(
            widget,
            page,
            into=into,
            steps_budget=widget_budget,
            wait_ms=wait_ms,
            click_ms=click_ms,
        )
        global_remaining -= used
