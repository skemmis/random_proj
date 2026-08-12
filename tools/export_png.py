"""Render a static chart HTML to PNG for embedding (Substack, docs, slides).

This is the one part of the project with a dependency, kept out of the
`kglw` package so the analysis itself stays standard-library only:

    pip install playwright && playwright install chromium

Usage:
    python3 -m kglw.minutes all.jsonl --json minutes.json
    python3 -m kglw.chart minutes.json --since 2023-01 --static -o static.html
    python3 tools/export_png.py static.html -o chart.png
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys


def export(html_path: str, out_path: str, scale: int = 2, theme: str = "light",
           selector: str = ".export", executable: str | None = None) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is required: pip install playwright && playwright install chromium")

    url = pathlib.Path(html_path).resolve().as_uri()
    launch: dict = {}
    # Honour a preinstalled browser when the environment provides one.
    executable = executable or os.environ.get("CHROMIUM_PATH")
    if executable:
        launch["executable_path"] = executable

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page(device_scale_factor=scale, color_scheme=theme)
        page.goto(url)
        page.wait_for_timeout(300)
        page.locator(selector).first.screenshot(path=out_path)
        browser.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="static chart HTML (kglw.chart --static)")
    ap.add_argument("-o", "--output", default="chart.png")
    ap.add_argument("--scale", type=int, default=2, help="pixel density (2 = retina)")
    ap.add_argument("--theme", choices=("light", "dark"), default="light")
    ap.add_argument("--browser", help="path to a chromium binary")
    args = ap.parse_args(argv)

    export(args.input, args.output, scale=args.scale, theme=args.theme,
           executable=args.browser)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
