"""Generic semantic selectors for gallery/carousel/widget stepping.

Intentionally library-agnostic (class/aria/role substring matches) so the
stepping logic in ``gallery`` works across arbitrary sites with no
per-site code.
"""

_GALLERY_LOAD_MORE_SELECTORS = (
    'button:has-text("Load more")',
    'a:has-text("Load more")',
    '[class*="load-more"]',
)

_GALLERY_NEXT_SELECTORS = (
    '[aria-label*="next" i]',
    'button[aria-label*="next" i]',
    'a[rel="next"]',
    '[class*="carousel"] [class*="next"]',
    '[class*="gallery"] [class*="next"]',
    "[class*='arrow-right']",
    "[class*='next-button']",
    '[role="button"][class*="next"]',
)

_GALLERY_PAGINATION_SELECTORS = (
    '[class*="pagination"] a:not([class*="active"])',
    '[class*="pagination"] button:not([disabled]):not([class*="active"])',
)

_GALLERY_THUMB_SELECTORS = (
    '[class*="gallery"] [class*="thumb"]',
    '[class*="carousel"] [class*="slide"]:not([class*="active"])',
)

_WIDGET_ROOT_SELECTORS = (
    '[class*="gallery"]',
    '[class*="carousel"]',
    '[class*="slider"]',
    '[role="tablist"]',
)
