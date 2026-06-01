"""Unit tests for gallery/carousel stepping helpers."""

from backend.services.playwright.gallery import widget_gallery_step_budget


def test_widget_gallery_step_budget_caps_global():
    assert widget_gallery_step_budget(7, 32, 6) == 32


def test_widget_gallery_step_budget_fewer_widgets():
    assert widget_gallery_step_budget(3, 32, 6) == 18


def test_widget_gallery_step_budget_zero_widgets():
    assert widget_gallery_step_budget(0, 32, 6) == 0
