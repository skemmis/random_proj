"""Render listening reports as self-contained HTML (and, via tools/, as PNG).

Four views, because they answer different questions:

  volume  - minutes per period, stacked by album. "How much did I listen?"
  totals  - minutes per period, one series. Same question, less noise.
  share   - 100% stacked. "Of what I did listen to, what was it?"
  line    - each album's share as its own series. "How did that change?"

Periods are months or quarters. Quarters exist for legibility: 15 wide columns
survive being scaled down on a phone where 44 thin ones do not.

Static renders are laid out at the width they will actually be displayed at.
Composing wider and letting the platform downscale shrinks every label along
with the canvas -- that is how 10px axis type arrives at 6px on screen. Layout
width governs legibility; export scale governs sharpness.

Usage:
    python3 -m kglw.chart minutes.json --page -o page.html
    python3 -m kglw.chart minutes.json --since 2023-01 --totals -o totals.html
    python3 -m kglw.chart minutes.json --period quarter --share -o share.html
"""

from __future__ import annotations

import argparse
import html
import json

# Validated categorical slots (light, dark). Assigned to albums by overall rank
# and then held fixed -- colour follows the album, never its row number.
SERIES = [
    ("#2a78d6", "#3987e5"),
    ("#eb6834", "#d95926"),
    ("#1baf7a", "#199e70"),
    ("#eda100", "#c98500"),
    ("#e87ba4", "#d55181"),
    ("#008300", "#008300"),
]
OTHER = ("#898781", "#898781")

PLOT_H = 340
COL_GAP = 2
MIN_COL_W = 3
MAX_COL_W = 24
SEG_GAP = 2

PAGE_TARGET_W = 566
EXPORT_TARGET_W = 600

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pretty_month(month: str) -> str:
    if "Q" in month:
        return month.replace("-", " ")
    return f"{MONTH_NAMES[int(month[5:7]) - 1]} {month[:4]}"


def quarter_of(month: str) -> str:
    year, mon = int(month[:4]), int(month[5:7])
    return f"{year}-Q{(mon - 1) // 3 + 1}"


def nice_ticks(top: float, count: int = 4) -> list[float]:
    """Round tick values to clean numbers at or above the data maximum."""
    if top <= 0:
        return [0]
    rough = top / count
    magnitude = 10 ** (len(str(int(rough))) - 1)
    # Finer steps than the usual 1/2/5 ladder: with only those, a 1,186 max
    # rounds up to a 2,000 axis and the tallest bar uses 59% of the plot.
    for multiple in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        step = magnitude * multiple
        if step >= rough:
            break
    return [step * i for i in range(count + 1)]


def short(text: str, limit: int = 32) -> str:
    """Display name. Tables keep the full title; legends and tooltips cannot.

    Several KGLW albums carry subtitles long enough to swallow a legend whole
    ("PetroDragonic Apocalypse; or, Dawn of Eternal Night: ...").
    """
    text = text.split(";")[0].split(":")[0].strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def series_for(report: dict, top_n: int):
    """Colour assignment: top albums by total time, everything else neutral."""
    ranked = [row for row in report["albums"] if row["minutes"] > 0]
    top_ids = [row["album_id"] for row in ranked[:top_n]]
    titles = report["album_titles"]
    label_of = {aid: titles.get(aid, aid) for aid in top_ids}
    label_of["__other__"] = "Other releases"
    return top_ids, top_ids + ["__other__"], label_of


def colour_vars(top_ids: list[str], totals: bool) -> tuple[str, str]:
    if totals:
        return f"  --c-__total__: {SERIES[0][0]};", f"  --c-__total__: {SERIES[0][1]};"
    light = "\n".join(f"  --c-{a}: {SERIES[i][0]};" for i, a in enumerate(top_ids))
    dark = "\n".join(f"  --c-{a}: {SERIES[i][1]};" for i, a in enumerate(top_ids))
    return (light + f"\n  --c-__other__: {OTHER[0]};",
            dark + f"\n  --c-__other__: {OTHER[1]};")


def bucketed(report: dict, top_ids: list[str], since: str | None,
             period: str, totals: bool):
    """Fold the monthly series into (periods, per-period buckets, totals)."""
    months = [m for m in report["months"] if not since or m >= since]
    by_month_album = report["minutes_by_month_album"]

    periods: list[str] = []
    raw: dict[str, dict[str, float]] = {}
    for month in months:
        key_period = quarter_of(month) if period == "quarter" else month
        if key_period not in raw:
            raw[key_period] = {}
            periods.append(key_period)
        for album_id, minutes in (by_month_album.get(month) or {}).items():
            if totals:
                key = "__total__"
            elif album_id in top_ids:
                key = album_id
            else:
                key = "__other__"
            raw[key_period][key] = raw[key_period].get(key, 0) + minutes

    return periods, raw, {p: sum(v.values()) for p, v in raw.items()}


def layout(count: int, budget: int) -> tuple[int, int, int]:
    """Column width and gap. Bars cap at 24px; leftover width goes to the gaps."""
    col_w = min(MAX_COL_W, max(MIN_COL_W, round(budget / max(count, 1)) - COL_GAP))
    col_gap = COL_GAP
    if count > 1:
        # Gaps absorb the leftover, but never grow past a bar's own width --
        # with only a handful of columns that would strand them far apart.
        col_gap = max(COL_GAP, min(MAX_COL_W, round((budget - col_w * count) / (count - 1))))
    return col_w, col_gap, col_w * count + col_gap * max(count - 1, 0)


def axis_labels(periods: list[str], col_w: int, col_gap: int, plot_w: int) -> str:
    """Year ticks; for months also the final period, so the range end is clear."""
    if periods and "Q" in periods[0]:
        parts = []
        for index, period in enumerate(periods):
            centre = index * (col_w + col_gap) + col_w / 2
            parts.append(f'<i class="xtick q" style="left:{centre:.1f}px">{period[-2:]}</i>')
            if period.endswith("Q1"):
                parts.append(f'<i class="xtick yr" style="left:{centre:.1f}px">{period[:4]}</i>')
        return "".join(parts)

    parts = []
    for index, period in enumerate(periods):
        if period.endswith("-01"):
            left = index * (col_w + col_gap)
            if plot_w - left < 46:
                continue  # would collide with the end label
            parts.append(f'<i class="xtick" style="left:{left}px">{period[:4]}</i>')
    if periods:
        parts.append(f'<i class="xtick end">{html.escape(pretty_month(periods[-1]))}</i>')
    return "".join(parts)


def chart_fragment(report: dict, top_n: int = 6, since: str | None = None,
                   period: str = "month", totals: bool = False,
                   share: bool = False, budget: int = PAGE_TARGET_W) -> str:
    """Axes, columns and legend. The same markup serves page and export."""
    top_ids, order, label_of = series_for(report, top_n)
    if totals:
        order, label_of = ["__total__"], {"__total__": "Minutes"}
    periods, raw, period_totals = bucketed(report, top_ids, since, period, totals)
    if not periods:
        return ""

    col_w, col_gap, plot_w = layout(len(periods), budget)

    if share:
        ticks: list[float] = [0, 25, 50, 75, 100]
        scale = PLOT_H / 100
    else:
        ticks = nice_ticks(max(period_totals.values(), default=0))
        scale = PLOT_H / (ticks[-1] or 1)

    columns, over_labels = [], []
    for index, key_period in enumerate(periods):
        buckets, total = raw[key_period], period_totals[key_period]
        present = [(k, buckets.get(k, 0)) for k in order if buckets.get(k, 0) > 0]

        segments = []
        if present and (total > 0 or not share):
            # Reserve the inter-segment gaps up front so a stack lands on the
            # value it represents rather than that value plus its separators.
            available = PLOT_H - SEG_GAP * max(len(present) - 1, 0)
            for position, (key, minutes) in enumerate(present):
                if share:
                    height = minutes / total * available if total else 0
                else:
                    height = max(minutes * scale, 1.5)
                cap = " top" if position == len(present) - 1 else ""
                segments.append(
                    f'<i class="seg{cap}" style="height:{height:.2f}px;'
                    f'background:var(--c-{key})"></i>'
                )

        payload = html.escape(json.dumps({
            "month": key_period,
            "total": round(total, 1),
            "share": bool(share),
            "items": [
                {"label": short(label_of[k]), "key": k, "min": round(v, 1),
                 "pct": round(v / total * 100) if total else 0}
                for k, v in sorted(present, key=lambda kv: -kv[1])
            ],
        }), quote=True)
        columns.append(
            f'<button class="col" type="button" data-d="{payload}" '
            f'aria-label="{key_period}: {total:,.0f} minutes">'
            f'<span class="stack">{"".join(segments)}</span></button>'
        )
        if share:
            # Normalising hides the denominator: a quarter with 8 minutes would
            # render exactly as tall as one with 1,500. Each column carries its
            # real total so a quiet stretch cannot pass for a busy one.
            centre = index * (col_w + col_gap) + col_w / 2
            over_labels.append(
                f'<i class="qtot" style="left:{centre:.1f}px">{total:,.0f}</i>'
            )

    grid = "".join(f'<i class="grid" style="bottom:{v * scale:.2f}px"></i>' for v in ticks)
    y_labels = "".join(
        f'<i class="ytick" style="bottom:{v * scale:.2f}px">'
        f'{(f"{v:.0f}%" if share else f"{v:,.0f}")}</i>'
        for v in ticks
    )
    # A single series needs no legend -- the title already names what is plotted.
    legend = "" if totals else "".join(
        f'<span class="key"><i style="background:var(--c-{k})"></i>'
        f'{html.escape(short(label_of[k]))}</span>'
        for k in order
    )
    tier = " tiers" if period == "quarter" else ""

    return (
        f'<div class="scroll{" sharepad" if share else ""}">'
        f'<div class="plotwrap">'
        f'<div class="yaxis">{y_labels}</div>'
        f'<div class="plot" style="width:{plot_w}px">{grid}'
        f'<div class="cols" style="gap:{col_gap}px">{"".join(columns)}</div>'
        f'{"".join(over_labels)}</div></div>'
        f'<div class="xaxis{tier}" style="width:{plot_w}px">'
        f'{axis_labels(periods, col_w, col_gap, plot_w)}</div>'
        f'</div>'
        + (f'<div class="legend">{legend}</div>' if legend else "")
    )


def smooth_path(points: list[tuple[float, float]]) -> str:
    """SVG path through the points, monotone-cubic smoothed.

    Fritsch-Carlson rather than a plain Catmull-Rom spline: an ordinary spline
    overshoots between points, which on a percentage axis would swing a series
    below 0% between two small values and invent a dip nobody listened to.
    Monotone cubic is guaranteed to stay within each pair of adjacent values,
    so the curve can only ever be a smoother reading of the real numbers.
    """
    count = len(points)
    if count < 2:
        return ""
    if count == 2:
        return (f"M{points[0][0]:.1f},{points[0][1]:.1f}"
                f"L{points[1][0]:.1f},{points[1][1]:.1f}")

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    widths = [xs[i + 1] - xs[i] for i in range(count - 1)]
    slopes = [(ys[i + 1] - ys[i]) / widths[i] if widths[i] else 0.0
              for i in range(count - 1)]

    tangents = [slopes[0]]
    for i in range(1, count - 1):
        if slopes[i - 1] * slopes[i] <= 0:
            # A local peak or trough: flatten, so the curve turns at the point
            # rather than sailing past it.
            tangents.append(0.0)
        else:
            left, right = widths[i - 1], widths[i]
            tangents.append(
                3 * (left + right) / ((2 * right + left) / slopes[i - 1]
                                      + (right + 2 * left) / slopes[i])
            )
    tangents.append(slopes[-1])

    parts = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(count - 1):
        third = widths[i] / 3
        parts.append(
            f"C{xs[i] + third:.1f},{ys[i] + tangents[i] * third:.1f} "
            f"{xs[i + 1] - third:.1f},{ys[i + 1] - tangents[i + 1] * third:.1f} "
            f"{xs[i + 1]:.1f},{ys[i + 1]:.1f}"
        )
    return " ".join(parts)


def line_fragment(report: dict, top_n: int = 5, since: str | None = None,
                  period: str = "quarter", min_base: float = 30.0,
                  budget: int = PAGE_TARGET_W, smooth: bool = True) -> str:
    """Each album's share of a period's listening, as lines.

    A share is a ratio, and a ratio computed on a tiny base is noise: a quarter
    carrying a handful of minutes swings by tens of percent on a single play.
    The lines run continuously through those periods, but the periods are
    shaded, so a dip to 0% is legible as "hardly any listening at all" rather
    than "none of these albums".
    """
    top_ids, _, label_of = series_for(report, top_n)
    periods, raw, totals = bucketed(report, top_ids, since, period, False)
    if len(periods) < 2:
        return ""

    plot_w = budget
    step_x = plot_w / (len(periods) - 1)
    xs = [index * step_x for index in range(len(periods))]

    shares: dict[str, list[float]] = {}
    for album_id in top_ids:
        shares[album_id] = [
            (raw[p].get(album_id, 0) / totals[p] * 100) if totals[p] else 0.0
            for p in periods
        ]

    peak = max((v for pts in shares.values() for v in pts), default=0)
    ticks = nice_ticks(peak, 5)
    axis_top = ticks[-1] or 1

    def y_of(value: float) -> float:
        return PLOT_H - value / axis_top * PLOT_H

    # Shade the periods with too little listening to support a share.
    bands = []
    for index, key_period in enumerate(periods):
        if totals[key_period] >= min_base:
            continue
        left = max(xs[index] - step_x / 2, 0)
        right = min(xs[index] + step_x / 2, plot_w)
        bands.append(
            f'<rect x="{left:.1f}" y="0" width="{right - left:.1f}" '
            f'height="{PLOT_H}" fill="var(--grid)" opacity="0.55"/>'
        )

    grid = "".join(
        f'<line x1="0" y1="{y_of(v):.1f}" x2="{plot_w}" y2="{y_of(v):.1f}" '
        f'stroke="var(--grid)" stroke-width="1"/>' for v in ticks
    )

    paths = []
    for album_id in top_ids:
        colour = f"var(--c-{album_id})"
        points = [(xs[i], y_of(v)) for i, v in enumerate(shares[album_id])]
        if smooth:
            paths.append(
                f'<path d="{smooth_path(points)}" fill="none" stroke="{colour}" '
                f'stroke-width="2.25" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        else:
            d = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
            paths.append(
                f'<polyline points="{d}" fill="none" stroke="{colour}" '
                f'stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        for x, y in points:
            # Markers anchor the curve to the quarters that were actually
            # measured -- smoothing invents the path between them, not the
            # points themselves. 2px surface ring keeps overlaps legible.
            paths.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{colour}" '
                f'stroke="var(--surface)" stroke-width="2"/>'
            )

    y_labels = "".join(
        f'<i class="ytick" style="bottom:{PLOT_H - y_of(v):.1f}px">{v:.0f}%</i>'
        for v in ticks
    )
    x_labels = []
    for index, key_period in enumerate(periods):
        x_labels.append(
            f'<i class="xtick q" style="left:{xs[index]:.1f}px">{key_period[-2:]}</i>'
        )
        # Year on each Q1, and on the first column when the range opens
        # mid-year -- otherwise the opening quarter carries no year at all.
        if key_period.endswith("Q1") or index == 0:
            x_labels.append(
                f'<i class="xtick yr" style="left:{xs[index]:.1f}px">{key_period[:4]}</i>'
            )
    legend = "".join(
        f'<span class="key"><i style="background:var(--c-{a})"></i>'
        f'{html.escape(short(label_of[a]))}</span>'
        for a in top_ids
    )

    return (
        f'<div class="scroll"><div class="plotwrap">'
        f'<div class="yaxis">{y_labels}</div>'
        f'<div class="plot" style="width:{plot_w}px">'
        f'<svg width="{plot_w}" height="{PLOT_H}" viewBox="0 0 {plot_w} {PLOT_H}" '
        f'role="img" aria-label="Share of listening per {period} for the top '
        f'{len(top_ids)} albums">'
        f'{"".join(bands)}{grid}{"".join(paths)}</svg>'
        f'</div></div>'
        f'<div class="xaxis tiers" style="width:{plot_w}px">{"".join(x_labels)}</div>'
        f'</div>'
        f'<div class="legend">{legend}</div>'
    )


CSS = """
:root {
  color-scheme: light;
  --plane: #f9f9f7;
  --surface: #fcfcfb;
  --ink: #0b0b0b;
  --ink-2: #52514e;
  --muted: #898781;
  --grid: #e1e0d9;
  --rule: #c3c2b7;
  --hair: rgba(11,11,11,0.10);
__COLOURS_LIGHT__
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --plane: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --rule: #383835;
    --hair: rgba(255,255,255,0.10);
__COLOURS_DARK__
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plane: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
  --muted: #898781; --grid: #2c2c2a; --rule: #383835;
  --hair: rgba(255,255,255,0.10);
__COLOURS_DARK__
}

* { box-sizing: border-box; }
body {
  margin: 0; background: var(--plane); color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 1.55; -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 74ch; margin: 0 auto; padding: 56px 24px 96px;
        display: flex; flex-direction: column; gap: 36px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.eyebrow { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  color: var(--muted); margin: 0; }
h1 { font-size: 30px; line-height: 1.15; margin: 6px 0 0; text-wrap: balance;
     letter-spacing: -0.015em; }
.sub { color: var(--ink-2); margin: 10px 0 0; }
.hero { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
.hero .fig { font-size: 72px; font-weight: 600; letter-spacing: -0.03em; line-height: 1; }
.hero .unit { font-size: 19px; color: var(--ink-2); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1px; background: var(--hair); border: 1px solid var(--hair);
  border-radius: 10px; overflow: hidden; }
.tile { background: var(--surface); padding: 14px 16px; }
.tile b { display: block; font-size: 21px; font-weight: 600; letter-spacing: -0.01em; }
.tile span { font-size: 12px; color: var(--muted); }
.card { background: var(--surface); border: 1px solid var(--hair);
        border-radius: 12px; padding: 22px; }
.card h2 { font-size: 15px; margin: 0; letter-spacing: -0.005em; }
.card .note { font-size: 13px; color: var(--ink-2); margin: 6px 0 18px; }

.scroll { overflow-x: auto; overflow-y: hidden; padding: 10px 0 4px; }
.scroll.sharepad { padding-top: 24px; }
.plotwrap { display: flex; gap: 10px; min-width: min-content; }
.yaxis { position: relative; width: 40px; height: __PLOT_H__px; flex: none; }
.ytick { position: absolute; right: 0; transform: translateY(50%);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; font-size: 10px; color: var(--muted);
  font-style: normal; }
.plot { position: relative; height: __PLOT_H__px; flex: none; }
.grid { position: absolute; left: 0; right: 0; height: 1px; background: var(--grid); }
.cols { position: absolute; inset: 0; display: flex; align-items: flex-end; }
.col { flex: 1 1 0; min-width: 0; height: 100%; padding: 0; border: 0;
       background: none; display: flex; align-items: flex-end; cursor: pointer; }
.stack { display: flex; flex-direction: column-reverse; gap: 2px; width: 100%; }
.seg { display: block; width: 100%; }
.seg.top { border-radius: 3px 3px 0 0; }
.col:hover .stack, .col:focus-visible .stack { filter: brightness(1.12); }
.col:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; border-radius: 3px; }
.xaxis { position: relative; height: 18px; margin-left: 50px; }
.xaxis.tiers { height: 34px; }
.xtick { position: absolute; top: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; color: var(--muted); font-style: normal; }
.xtick.end { right: 0; color: var(--ink-2); }
.xtick.q { transform: translateX(-50%); }
.xtick.yr { top: 17px; transform: translateX(-50%); color: var(--ink-2); }
.qtot { position: absolute; bottom: __QTOT__px; transform: translateX(-50%);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; font-size: 10px; color: var(--muted);
  font-style: normal; white-space: nowrap; }

.legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 16px;
  padding-top: 14px; border-top: 1px solid var(--hair); }
.key { display: inline-flex; align-items: center; gap: 7px; font-size: 12px;
       color: var(--ink-2); }
.key i { width: 10px; height: 10px; border-radius: 2px; flex: none; }

#tip { position: fixed; z-index: 20; pointer-events: none; opacity: 0;
  transition: opacity .1s; background: var(--surface); color: var(--ink);
  border: 1px solid var(--hair); border-radius: 8px; padding: 10px 12px;
  box-shadow: 0 6px 24px rgba(0,0,0,.16); font-size: 12px; min-width: 180px; }
#tip .m { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--muted); font-size: 11px; }
#tip .t { font-size: 17px; font-weight: 600; margin: 2px 0 8px; }
#tip .r { display: flex; align-items: center; gap: 7px; margin-top: 4px; }
#tip .r i { width: 8px; height: 8px; border-radius: 2px; flex: none; }
#tip .r b { margin-left: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; font-weight: 500; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
  color: var(--muted); font-weight: 500; padding: 0 10px 8px 0;
  border-bottom: 1px solid var(--rule); }
td { padding: 7px 10px 7px 0; border-bottom: 1px solid var(--hair); vertical-align: baseline; }
td.n, th.n { text-align: right; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; }
.sw { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 8px; }
details { border-top: 1px solid var(--hair); padding-top: 14px; margin-top: 18px; }
summary { cursor: pointer; font-size: 13px; color: var(--ink-2); }
.tblscroll { max-height: 340px; overflow: auto; margin-top: 12px; }
.method { font-size: 13px; color: var(--ink-2); }
.method h2 { font-size: 15px; color: var(--ink); margin: 0 0 10px; }
.method li { margin-bottom: 7px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

TOOLTIP_JS = """
<div id="tip" role="status" aria-live="polite"></div>
<script>
(function () {
  var tip = document.getElementById('tip'), shown = null;
  function esc(s){return s.replace(/[&<>"]/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function render(col) {
    var d = JSON.parse(col.getAttribute('data-d'));
    var rows = d.items.map(function (it) {
      var val = d.share ? it.pct + '%' : it.min.toLocaleString();
      return '<div class="r"><i style="background:var(--c-' + it.key + ')"></i>' +
             esc(it.label) + '<b>' + val + '</b></div>';
    }).join('');
    tip.innerHTML = '<div class="m">' + d.month + '</div><div class="t">' +
      d.total.toLocaleString() + ' min</div>' + rows;
    tip.style.opacity = '1'; shown = col;
  }
  function place(x, y) {
    var r = tip.getBoundingClientRect();
    tip.style.left = Math.min(x + 14, window.innerWidth - r.width - 8) + 'px';
    tip.style.top = Math.min(Math.max(y - r.height - 12, 8),
                             window.innerHeight - r.height - 8) + 'px';
  }
  function hide() { tip.style.opacity = '0'; shown = null; }
  document.querySelectorAll('.col').forEach(function (col) {
    col.addEventListener('mouseenter', function () { render(col); });
    col.addEventListener('mousemove', function (e) { place(e.clientX, e.clientY); });
    col.addEventListener('mouseleave', hide);
    col.addEventListener('focus', function () {
      render(col);
      var b = col.getBoundingClientRect(); place(b.left, b.top);
    });
    col.addEventListener('blur', hide);
  });
  window.addEventListener('scroll', function () { if (shown) hide(); }, true);
})();
</script>
"""

EXPORT_CSS = """
body { background: var(--surface); }
.export { width: __TOTALW__px; padding: 26px 24px 20px; background: var(--surface); }
.export h1 { font-size: 20px; line-height: 1.25; margin: 0; letter-spacing: -0.015em; }
.export .measure { font-size: 14.5px; color: var(--ink-2); margin: 3px 0 0; }
.export .scroll { overflow: visible; padding-top: 20px; }
.export .scroll.sharepad { padding-top: 34px; }
.export .col { cursor: default; }
.export .yaxis { width: 42px; }
.export .xaxis { margin-left: 52px; height: 20px; }
.export .xaxis.tiers { height: 36px; }
.export .ytick, .export .xtick { font-size: 12px; }
.export .qtot { font-size: 11px; }
.export .key { font-size: 12.5px; }
.export .seg.top { border-radius: 2px 2px 0 0; }
.export .legend { margin-top: 14px; }
"""

TABLE_CSS = """
.export { width: 716px; padding: 26px 24px 20px; background: var(--surface); }
.export h1 { font-size: 20px; margin: 0 0 3px; letter-spacing: -0.015em; }
.export .sub { font-size: 14px; color: var(--ink-2); margin: 0 0 18px; }
.export table { font-size: 14.5px; }
.export th { font-size: 11.5px; }
.export td { padding: 9px 10px 9px 0; white-space: nowrap; }
.export .bar { display: inline-block; height: 7px; border-radius: 2px; vertical-align: middle; }
.foot { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--hair);
        font-size: 11.5px; color: var(--muted); line-height: 1.5; }
"""


def _fill(page: str, mapping: dict) -> str:
    for token, value in mapping.items():
        page = page.replace(token, value)
    return page


def _shell(extra_css: str, body: str, top_ids: list[str], totals: bool = False) -> str:
    light, dark = colour_vars(top_ids, totals)
    return _fill(
        "<title>Gizzard Hours</title>\n<style>" + CSS + extra_css + "</style>\n" + body,
        {
            "__COLOURS_LIGHT__": light,
            "__COLOURS_DARK__": dark,
            "__PLOT_H__": str(PLOT_H),
            "__QTOT__": str(PLOT_H + 6),
            "__TOTALW__": str(EXPORT_TARGET_W + 100),
        },
    )


def build_export(report: dict, top_n: int = 6, since: str | None = None,
                 period: str = "month", totals: bool = False,
                 share: bool = False, line: bool = False, smooth: bool = True,
                 measure: str | None = None, title: str | None = None) -> str:
    """Chart-only render, laid out for a newsletter column."""
    top_ids, _, _ = series_for(report, top_n)
    if line:
        fragment = line_fragment(report, top_n, since, period,
                                 budget=EXPORT_TARGET_W, smooth=smooth)
    else:
        fragment = chart_fragment(report, top_n, since, period, totals, share,
                                  budget=EXPORT_TARGET_W)
    if measure is None:
        if line:
            measure = f"Top {top_n} albums — share of listening per {period}"
        else:
            unit = "Share of listening" if share else "Minutes listened"
            measure = f"{unit} per {period}"
    # An empty measure drops the second line entirely, for a chart whose
    # title already carries the measure.
    heading = html.escape(title) if title else "King Gizzard &amp; the Lizard Wizard"
    sub = f'\n  <p class="measure">{html.escape(measure)}</p>' if measure else ""
    body = (f'<div class="export">\n'
            f'  <h1>{heading}</h1>{sub}\n'
            f'  {fragment}\n</div>')
    return _shell(EXPORT_CSS, body, top_ids, totals)


# Older entry point, kept for callers and the render tests.
def build(report: dict, top_n: int = 6, since: str | None = None,
          static: bool = False, target_w: int | None = None,
          totals: bool = False, **kw) -> str:
    return build_export(report, top_n=top_n, since=since, totals=totals, **kw)


def build_page(report: dict, cards: list[tuple[str, str, str]], top_n: int = 6) -> str:
    """The full interactive page: hero, stat tiles, chart cards, ranking."""
    top_ids, _, _ = series_for(report, top_n)
    months = report["months"]
    by_month = report["minutes_by_month"]
    peak = max(by_month, key=lambda m: by_month[m]) if by_month else None
    ranked = [r for r in report["albums"] if r["minutes"] > 0]

    rows = "".join(
        f"<tr><td class='n'>{rank}</td>"
        f"<td><i class='sw' style='background:var(--c-"
        f"{r['album_id'] if r['album_id'] in top_ids else '__other__'})'></i>"
        f"{html.escape(short(r['album'], 44))}</td>"
        f"<td class='n'>{r['hours']:,.1f}</td><td class='n'>{r['minutes']:,.0f}</td>"
        f"<td class='n'>{r['distinct_tracks']}</td>"
        f"<td>{html.escape(r['top_track'] or '')}</td></tr>"
        for rank, r in enumerate(ranked[:20], 1)
    )
    month_rows = "".join(
        f"<tr><td>{m}</td><td class='n'>{by_month[m]:,.0f}</td></tr>"
        for m in reversed(months) if by_month.get(m, 0) > 0
    )
    card_html = "".join(
        f'<section class="card"><h2>{html.escape(title)}</h2>'
        + (f'<p class="note">{note}</p>' if note else '<div style="height:14px"></div>')
        + f'{frag}</section>'
        for title, note, frag in cards
    )
    src = report.get("duration_sources", {})
    counted = sum(src.values()) - src.get("none", 0)

    body = f"""<div class="wrap">
  <header>
    <p class="eyebrow">King Gizzard &amp; the Lizard Wizard · <span class="mono">{months[0]} – {months[-1]}</span></p>
    <h1>How much Gizzard, actually</h1>
    <p class="sub">Listening time reconstructed from YouTube watch history, on the assumption that every play ran to completion.</p>
  </header>
  <div class="hero">
    <span class="fig">{report['total_hours']:,.0f}</span>
    <span class="unit">hours · {report['total_minutes']:,.0f} minutes of music</span>
  </div>
  <div class="tiles">
    <div class="tile"><b>{counted:,}</b><span>plays with a known runtime</span></div>
    <div class="tile"><b>{len(ranked)}</b><span>releases touched</span></div>
    <div class="tile"><b class="mono">{peak or '—'}</b><span>busiest month · {by_month.get(peak, 0):,.0f} min</span></div>
  </div>
  {card_html}
  <section class="card">
    <h2>Albums by total listening time</h2>
    <p class="note">Any track counts toward its album, however it was played — studio, live or bootleg.</p>
    <table>
      <thead><tr><th class="n">#</th><th>Album</th><th class="n">Hours</th><th class="n">Minutes</th><th class="n">Tracks</th><th>Most played</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <details>
      <summary>Table view — minutes per month</summary>
      <div class="tblscroll">
        <table><thead><tr><th>Month</th><th class="n">Minutes</th></tr></thead>
        <tbody>{month_rows}</tbody></table>
      </div>
    </details>
  </section>
  <section class="method">
    <h2>How this was counted</h2>
    <ul>
      <li>Watch history records <em>that</em> something played, never for how long. Minutes come from MusicBrainz track durations, assuming each play finished — so a skipped track counts the same as a full one.</li>
      <li>Music counts, talk does not: concert footage, bootlegs and drum-cams are listening; {report['skipped_non_music']:,} plays of interviews, podcasts, reactions and gear rundowns were excluded.</li>
      <li>A live version counts toward the album the song comes from, so a bootleg <em>Robot Stop</em> lands on <em>Nonagon Infinity</em>.</li>
      <li>{report['skipped_unknown_count']:,} plays named no track with a known runtime — mostly full-set uploads and medleys — and contribute nothing rather than a guess.</li>
    </ul>
  </section>
</div>
{TOOLTIP_JS}"""
    return _shell("", body, top_ids)


def build_table(report: dict, top_n: int = 6, rows: int = 12) -> str:
    """The ranking as a standalone image, styled to match the charts."""
    ranked = [row for row in report["albums"] if row["minutes"] > 0]
    top_ids = [row["album_id"] for row in ranked[:top_n]]

    peak = max((r["hours"] for r in ranked[:rows]), default=1) or 1
    out = []
    for rank, row in enumerate(ranked[:rows], 1):
        key = row["album_id"] if row["album_id"] in top_ids else "__other__"
        width = max(row["hours"] / peak * 132, 3)
        out.append(
            f"<tr><td class='n'>{rank}</td>"
            f"<td><i class='sw' style='background:var(--c-{key})'></i>"
            f"{html.escape(short(row['album'], 30))}</td>"
            f"<td><i class='bar' style='width:{width:.0f}px;background:var(--c-{key})'></i></td>"
            f"<td class='n'>{row['hours']:,.1f}</td>"
            f"<td>{html.escape(short(row['top_track'] or '', 18))}</td></tr>"
        )

    body = f"""<div class="export">
  <h1>King Gizzard &amp; the Lizard Wizard — albums by listening time</h1>
  <p class="sub">Top {min(rows, len(ranked))} of {len(ranked)} releases · {report['total_hours']:,.0f} hours total</p>
  <table>
    <thead><tr><th class="n">#</th><th>Album</th><th></th><th class="n">Hours</th><th>Most played</th></tr></thead>
    <tbody>{"".join(out)}</tbody>
  </table>
  <p class="foot">Reconstructed from Google Takeout YouTube watch history; track durations from
  MusicBrainz. Every play is counted as running to completion, so these are upper bounds.</p>
</div>"""
    return _shell(TABLE_CSS, body, top_ids)


def build_list(report: dict, rows: int = 12) -> str:
    """A ranked list in plain text, for editors with no table support."""
    ranked = [row for row in report["albums"] if row["minutes"] > 0][:rows]
    return "\n".join(
        f"{rank}. {short(row['album'], 60)} — {row['hours']:,.1f} hours"
        f" (most played: {row['top_track']})"
        for rank, row in enumerate(ranked, 1)
    ) + "\n"


def build_tsv(report: dict, rows: int = 20) -> str:
    """Tab-separated, for a spreadsheet or a Datawrapper embed."""
    ranked = [row for row in report["albums"] if row["minutes"] > 0][:rows]
    lines = ["#\tAlbum\tHours\tMinutes\tMost played"]
    for rank, row in enumerate(ranked, 1):
        lines.append(
            f"{rank}\t{short(row['album'], 60)}\t{row['hours']:,.1f}"
            f"\t{row['minutes']:,.0f}\t{row['top_track'] or ''}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="minutes report JSON from kglw.minutes --json")
    ap.add_argument("-o", "--output", default="chart.html")
    ap.add_argument("--top", type=int, default=6, help="albums given their own colour")
    ap.add_argument("--since", help="first month to plot, e.g. 2023-01")
    ap.add_argument("--period", choices=("month", "quarter"), default="month")
    ap.add_argument("--totals", action="store_true", help="one series, no legend")
    ap.add_argument("--share", action="store_true", help="100%% stacked composition")
    ap.add_argument("--line", action="store_true",
                    help="multi-series lines of each album's share")
    ap.add_argument("--page", action="store_true", help="full interactive page")
    ap.add_argument("--table", action="store_true", help="render the ranking instead")
    ap.add_argument("--rows", type=int, default=12)
    ap.add_argument("--title", help="override the chart heading")
    ap.add_argument("--no-measure", action="store_true",
                    help="drop the line under the title")
    ap.add_argument("--straight", action="store_true",
                    help="line view: straight segments instead of smoothed")
    ap.add_argument("--tsv", help="also write the ranking as TSV")
    ap.add_argument("--list", dest="list_out", help="also write the ranking as a list")
    args = ap.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    if args.list_out:
        with open(args.list_out, "w", encoding="utf-8") as fh:
            fh.write(build_list(report, rows=args.rows))
        print(f"wrote {args.list_out}")
    if args.tsv:
        with open(args.tsv, "w", encoding="utf-8") as fh:
            fh.write(build_tsv(report, rows=max(args.rows, 20)))
        print(f"wrote {args.tsv}")

    if args.table:
        page = build_table(report, top_n=args.top, rows=args.rows)
    elif args.page:
        if args.line:
            frag = line_fragment(report, args.top, args.since, args.period,
                                 smooth=not args.straight)
            label = f"Top {args.top} albums — share of listening"
        else:
            frag = chart_fragment(report, args.top, args.since, args.period,
                                  args.totals, args.share)
            label = "Share of listening" if args.share else "Minutes"
        page = build_page(report, [(f"{label} per {args.period}", "", frag)],
                          top_n=args.top)
    else:
        page = build_export(report, top_n=args.top, since=args.since,
                            period=args.period, totals=args.totals,
                            share=args.share, line=args.line,
                            smooth=not args.straight, title=args.title,
                            measure="" if args.no_measure else None)

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
