"""Full-page screenshots of every dashboard page (for the report and review).

    python scripts/capture_dashboard.py [--out .impeccable/review] [--width 1440]

Uses the locally installed Microsoft Edge through Playwright (channel="msedge").
"""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGES = ["", "cau-chuyen", "dien-bien", "tu-khoa", "phan-tich", "phuong-phap"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://127.0.0.1:8501")
    p.add_argument("--out", default=".impeccable/review")
    p.add_argument("--width", type=int, default=1440)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--suffix", default="desktop")
    p.add_argument("--pages", nargs="*", default=PAGES)
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport={"width": a.width, "height": a.height}, device_scale_factor=1,
                                  reduced_motion="reduce")
        page = ctx.new_page()
        for name in a.pages:
            page.goto(f"{a.base}/{name}", wait_until="networkidle")
            page.wait_for_selector("h1.slug", timeout=120_000)
            # Wait until Streamlit stops running the script and charts are drawn.
            page.wait_for_function("!document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=120_000)
            page.wait_for_timeout(2500)
            # Streamlit scrolls an inner container, so grow the viewport to the
            # content height instead of relying on full_page.
            h = page.evaluate("Math.max(...['[data-testid=\"stMain\"]','[data-testid=\"stAppViewContainer\"]']"
                              ".map(s => document.querySelector(s)?.scrollHeight || 0))")
            page.set_viewport_size({"width": a.width, "height": min(int(h) + 40, 16000)})
            page.wait_for_timeout(2000)
            path = out / f"{name or 'bang-diem'}-{a.suffix}.png"
            page.screenshot(path=str(path), full_page=True)
            page.set_viewport_size({"width": a.width, "height": a.height})
            print("saved", path)
        browser.close()


if __name__ == "__main__":
    main()
