"""Render the listening-time report as a self-contained HTML page.

Stacked columns: one per month, segmented by album. Colours come from a
CVD-validated categorical palette; the tail folds into a neutral "Other"
rather than inventing more hues.

Usage:
    python3 -m kglw.minutes all.jsonl --json minutes.json
    python3 -m kglw.chart minutes.json -o listening.html
"""

from __future__ import annotations

import argparse
import html
import json

# Validated categorical slots (light, dark). Assigned to albums by overall
# rank and then held fixed -- colour follows the album, never its row number.
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
# Column width is derived so the whole history fits the card. A fixed width
# pushed the busiest years off the right edge behind a scrollbar, hiding the
# peak: the reader saw a flat chart and no reason to scroll.
PLOT_TARGET_W = 566
# A static export has no tooltip, so it is rendered wider and carries direct
# value labels on its tallest columns instead.
STATIC_TARGET_W = 1080
MIN_COL_W = 3
MAX_COL_W = 24


def nice_ticks(top: float, count: int = 4) -> list[float]:
    """Round tick values to clean numbers at or above the data maximum."""
    if top <= 0:
        return [0]
    rough = top / count
    magnitude = 10 ** (len(str(int(rough))) - 1)
    for multiple in (1, 2, 2.5, 5, 10):
        step = magnitude * multiple
        if step >= rough:
            break
    return [step * i for i in range(count + 1)]


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def pretty_month(month: str) -> str:
    return f"{MONTH_NAMES[int(month[5:7]) - 1]} {month[:4]}"


def build(
    report: dict,
    top_n: int = 6,
    since: str | None = None,
    static: bool = False,
    target_w: int | None = None,
) -> str:
    all_months = report["months"]
    months = [m for m in all_months if not since or m >= since]
    width_budget = target_w or (STATIC_TARGET_W if static else PLOT_TARGET_W)
    col_w = min(MAX_COL_W, max(MIN_COL_W, round(width_budget / max(len(months), 1)) - COL_GAP))
    by_month_album = report["minutes_by_month_album"]
    titles = report["album_titles"]

    ranked = [row for row in report["albums"] if row["minutes"] > 0]
    top_ids = [row["album_id"] for row in ranked[:top_n]]
    colour_of = {album_id: SERIES[i] for i, album_id in enumerate(top_ids)}

    def bucket(album_id: str) -> str:
        return album_id if album_id in colour_of else "__other__"

    # Per-month totals per bucket, ordered so the legend and stack agree.
    order = top_ids + ["__other__"]
    label_of = {aid: titles.get(aid, aid) for aid in top_ids}
    label_of["__other__"] = "Other releases"

    def short(text: str, limit: int = 34) -> str:
        """Legend and tooltip names only -- tables keep the full title.

        Several KGLW albums have subtitles long enough to swallow a legend
        whole ("PetroDragonic Apocalypse; or, Dawn of Eternal Night: ...").
        """
        text = text.split(";")[0].split(":")[0].strip()
        return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"

    stacks: dict[str, dict[str, float]] = {}
    for month in months:
        totals: dict[str, float] = {}
        for album_id, minutes in (by_month_album.get(month) or {}).items():
            key = bucket(album_id)
            totals[key] = totals.get(key, 0) + minutes
        stacks[month] = totals

    month_totals = {m: sum(v.values()) for m, v in stacks.items()}
    peak_month = max(month_totals, key=lambda m: month_totals[m]) if month_totals else None
    y_max = max(month_totals.values()) if month_totals else 0
    ticks = nice_ticks(y_max)
    axis_top = ticks[-1] or 1
    scale = PLOT_H / axis_top

    # --- columns ---
    columns = []
    stack_px: dict[str, float] = {}
    for month in months:
        totals = stacks[month]
        present = [(key, totals.get(key, 0)) for key in order if totals.get(key, 0) > 0]
        segments = []
        for position, (key, minutes) in enumerate(present):
            height = max(minutes * scale, 1.5)
            top_class = " top" if position == len(present) - 1 else ""
            segments.append(
                f'<i class="seg{top_class}" style="height:{height:.2f}px;'
                f'background:var(--c-{key})"></i>'
            )
        breakdown = [
            {"label": short(label_of[key]), "key": key, "min": round(minutes, 1)}
            for key, minutes in sorted(present, key=lambda kv: -kv[1])
        ]
        payload = html.escape(json.dumps({
            "month": month,
            "total": round(month_totals[month], 1),
            "items": breakdown,
        }), quote=True)
        stack_px[month] = sum(
            max(minutes * scale, 1.5) for _, minutes in present
        ) + COL_GAP * max(len(present) - 1, 0)
        columns.append(
            f'<button class="col" type="button" data-d="{payload}" '
            f'aria-label="{month}: {month_totals[month]:,.0f} minutes">'
            f'<span class="stack">{"".join(segments)}</span></button>'
        )

    # --- axes ---
    gridlines = "".join(
        f'<i class="grid" style="bottom:{value * scale:.2f}px"></i>' for value in ticks
    )
    y_labels = "".join(
        f'<i class="ytick" style="bottom:{value * scale:.2f}px">{value:,.0f}</i>'
        for value in ticks
    )
    # Januarys, plus the final month. Labelling only Januarys made the columns
    # after the last tick look like they fell outside the chart's range.
    x_labels = []
    last_left = len(months) * (col_w + COL_GAP)
    for index, month in enumerate(months):
        if month.endswith("-01"):
            left = index * (col_w + COL_GAP)
            if last_left - left < 46:
                continue  # would collide with the end label
            x_labels.append(f'<i class="xtick" style="left:{left}px">{month[:4]}</i>')
    if months:
        x_labels.append(
            f'<i class="xtick end">{html.escape(pretty_month(months[-1]))}</i>'
        )

    # A PNG has no hover, so the extremes are labelled on the mark itself.
    # Selective by design -- a number on every column would be unreadable.
    value_labels = ""
    if static and months:
        peaks = sorted(months, key=lambda m: -month_totals[m])[:3]
        parts = []
        for month in peaks:
            if month_totals[month] <= 0:
                continue
            index = months.index(month)
            centre = index * (col_w + COL_GAP) + col_w / 2
            parts.append(
                f'<i class="vlabel" style="left:{centre:.1f}px;'
                f'bottom:{stack_px[month] + 6:.1f}px">{month_totals[month]:,.0f}</i>'
            )
        value_labels = "".join(parts)

    # --- legend ---
    legend = "".join(
        f'<span class="key"><i style="background:var(--c-{key})"></i>'
        f'{html.escape(short(label_of[key]))}</span>'
        for key in order
    )

    # --- album table (also the contrast-relief table view) ---
    rows = []
    for rank, row in enumerate(ranked[:20], 1):
        key = bucket(row["album_id"])
        swatch = f'<i class="sw" style="background:var(--c-{key})"></i>'
        rows.append(
            f"<tr><td class='n'>{rank}</td><td>{swatch}{html.escape(row['album'])}</td>"
            f"<td class='n'>{row['hours']:,.1f}</td><td class='n'>{row['minutes']:,.0f}</td>"
            f"<td class='n'>{row['distinct_tracks']}</td>"
            f"<td>{html.escape(row['top_track'] or '')}</td></tr>"
        )

    month_rows = "".join(
        f"<tr><td>{m}</td><td class='n'>{month_totals[m]:,.0f}</td></tr>"
        for m in reversed(months)
        if month_totals[m] > 0
    )

    colour_vars_light = "\n".join(
        f"  --c-{aid}: {SERIES[i][0]};" for i, aid in enumerate(top_ids)
    ) + f"\n  --c-__other__: {OTHER[0]};"
    colour_vars_dark = "\n".join(
        f"  --c-{aid}: {SERIES[i][1]};" for i, aid in enumerate(top_ids)
    ) + f"\n  --c-__other__: {OTHER[1]};"

    dropped = sum(
        report["minutes_by_month"].get(m, 0) for m in all_months if m not in set(months)
    )
    if since and dropped:
        window_note = (
            f"{html.escape(pretty_month(months[0]))} onward — "
            f"{dropped:,.0f} earlier minutes "
            f"({dropped / max(report['total_minutes'], 1) * 100:.0f}% of the total) "
            f"predate this window and are not plotted."
        )
    else:
        window_note = ""

    src = report.get("duration_sources", {})
    total_plays = sum(src.values())
    counted = total_plays - src.get("none", 0)

    page = STATIC_TEMPLATE if static else TEMPLATE
    replacements = {
        "__COLOURS_LIGHT__": colour_vars_light,
        "__COLOURS_DARK__": colour_vars_dark,
        "__HOURS__": f"{report['total_hours']:,.0f}",
        "__MINUTES__": f"{report['total_minutes']:,.0f}",
        "__SPAN__": f"{months[0]} – {months[-1]}" if months else "",
        "__PEAK__": peak_month or "—",
        "__PEAK_MIN__": f"{month_totals.get(peak_month, 0):,.0f}" if peak_month else "0",
        "__ALBUM_COUNT__": str(len(ranked)),
        "__COUNTED__": f"{counted:,}",
        "__TOTAL_PLAYS__": f"{total_plays:,}",
        "__TALK__": f"{report['skipped_non_music']:,}",
        "__NODUR__": f"{report['skipped_unknown_count']:,}",
        "__PLOT_H__": str(PLOT_H),
        "__COL_W__": str(col_w),
        "__COL_GAP__": str(COL_GAP),
        "__WIDTH__": str(len(months) * (col_w + COL_GAP)),
        # y-axis (34) + gap (10) + plot + horizontal padding (34 each side)
        "__TOTALW__": str(len(months) * (col_w + COL_GAP) + 34 + 10 + 68),
        "__GRID__": gridlines,
        "__YLAB__": y_labels,
        "__XLAB__": "".join(x_labels),
        "__COLS__": "".join(columns),
        "__LEGEND__": legend,
        "__ROWS__": "".join(rows),
        "__MONTHROWS__": month_rows,
        "__WINDOW__": window_note,
        "__VLAB__": value_labels,
        "__SUBTITLE__": window_note or "Each column is one month.",
    }
    for token, value in replacements.items():
        page = page.replace(token, value)
    return page


TEMPLATE = """<title>Gizzard Hours</title>
<style>
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
    --plane: #0d0d0d;
    --surface: #1a1a19;
    --ink: #ffffff;
    --ink-2: #c3c2b7;
    --muted: #898781;
    --grid: #2c2c2a;
    --rule: #383835;
    --hair: rgba(255,255,255,0.10);
__COLOURS_DARK__
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --plane: #0d0d0d;
  --surface: #1a1a19;
  --ink: #ffffff;
  --ink-2: #c3c2b7;
  --muted: #898781;
  --grid: #2c2c2a;
  --rule: #383835;
  --hair: rgba(255,255,255,0.10);
__COLOURS_DARK__
}

* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--plane);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 74ch; margin: 0 auto; padding: 56px 24px 96px; display: flex; flex-direction: column; gap: 40px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

.eyebrow {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
  color: var(--muted); margin: 0;
}
h1 { font-size: 30px; line-height: 1.15; margin: 6px 0 0; text-wrap: balance; letter-spacing: -0.015em; }
.sub { color: var(--ink-2); margin: 10px 0 0; }

.hero { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
.hero .fig { font-size: 72px; font-weight: 600; letter-spacing: -0.03em; line-height: 1; }
.hero .unit { font-size: 19px; color: var(--ink-2); }

.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1px; background: var(--hair); border: 1px solid var(--hair); border-radius: 10px; overflow: hidden; }
.tile { background: var(--surface); padding: 14px 16px; }
.tile b { display: block; font-size: 21px; font-weight: 600; letter-spacing: -0.01em; }
.tile span { font-size: 12px; color: var(--muted); }

.card { background: var(--surface); border: 1px solid var(--hair); border-radius: 12px; padding: 22px; }
.card h2 { font-size: 15px; margin: 0; letter-spacing: -0.005em; }
.card .note { font-size: 13px; color: var(--ink-2); margin: 6px 0 20px; }

.scroll { overflow-x: auto; overflow-y: hidden; padding: 10px 0 4px; }
.plotwrap { display: flex; gap: 10px; min-width: min-content; }
.yaxis { position: relative; width: 34px; height: __PLOT_H__px; flex: none; }
.ytick {
  position: absolute; right: 0; transform: translateY(50%);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; font-size: 10px; color: var(--muted); font-style: normal;
}
.plot { position: relative; height: __PLOT_H__px; width: __WIDTH__px; flex: none; }
.grid { position: absolute; left: 0; right: 0; height: 1px; background: var(--grid); }
.cols { position: absolute; inset: 0; display: flex; gap: __COL_GAP__px; align-items: flex-end; }
.col {
  width: __COL_W__px; flex: none; height: 100%; padding: 0; border: 0; background: none;
  display: flex; align-items: flex-end; cursor: pointer;
}
.stack { display: flex; flex-direction: column-reverse; gap: 2px; width: 100%; }
.seg { display: block; width: 100%; }
.seg.top { border-radius: 3px 3px 0 0; }
.col:hover .stack, .col:focus-visible .stack { filter: brightness(1.12); }
.col:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; border-radius: 3px; }
.xaxis { position: relative; height: 18px; width: __WIDTH__px; margin-left: 44px; }
.xtick {
  position: absolute; top: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; color: var(--muted); font-style: normal;
}
.xtick.end { right: 0; color: var(--ink-2); }

.legend { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--hair); }
.key { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; color: var(--ink-2); }
.key i { width: 10px; height: 10px; border-radius: 2px; flex: none; }

#tip {
  position: fixed; z-index: 20; pointer-events: none; opacity: 0;
  transition: opacity .1s; background: var(--surface); color: var(--ink);
  border: 1px solid var(--hair); border-radius: 8px; padding: 10px 12px;
  box-shadow: 0 6px 24px rgba(0,0,0,.16); font-size: 12px; min-width: 172px;
}
#tip .m { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; color: var(--muted); font-size: 11px; }
#tip .t { font-size: 17px; font-weight: 600; margin: 2px 0 8px; }
#tip .r { display: flex; align-items: center; gap: 7px; margin-top: 4px; }
#tip .r i { width: 8px; height: 8px; border-radius: 2px; flex: none; }
#tip .r b { margin-left: auto; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; font-weight: 500; }

table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 500; padding: 0 10px 8px 0; border-bottom: 1px solid var(--rule); }
td { padding: 7px 10px 7px 0; border-bottom: 1px solid var(--hair); vertical-align: baseline; }
td.n, th.n { text-align: right; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; }
.sw { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 8px; }
details { border-top: 1px solid var(--hair); padding-top: 14px; margin-top: 20px; }
summary { cursor: pointer; font-size: 13px; color: var(--ink-2); }
.tblscroll { max-height: 340px; overflow: auto; margin-top: 12px; }

.method { font-size: 13px; color: var(--ink-2); }
.method h2 { font-size: 15px; color: var(--ink); margin: 0 0 10px; }
.method li { margin-bottom: 7px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">King Gizzard &amp; the Lizard Wizard · <span class="mono">__SPAN__</span></p>
    <h1>How much Gizzard, actually</h1>
    <p class="sub">Listening time reconstructed from YouTube watch history, on the assumption that every play ran to completion.</p>
  </header>

  <div class="hero">
    <span class="fig">__HOURS__</span>
    <span class="unit">hours · __MINUTES__ minutes of music</span>
  </div>

  <div class="tiles">
    <div class="tile"><b>__COUNTED__</b><span>plays with a known runtime</span></div>
    <div class="tile"><b>__ALBUM_COUNT__</b><span>releases touched</span></div>
    <div class="tile"><b class="mono">__PEAK__</b><span>busiest month · __PEAK_MIN__ min</span></div>
  </div>

  <section class="card">
    <h2>Minutes per month, by album</h2>
    <p class="note">__WINDOW__ Each column is one month. Hover or focus a column for its breakdown.</p>
    <div class="scroll">
      <div class="plotwrap">
        <div class="yaxis">__YLAB__</div>
        <div class="plot">__GRID__<div class="cols">__COLS__</div></div>
      </div>
      <div class="xaxis">__XLAB__</div>
    </div>
    <div class="legend">__LEGEND__</div>
    <details>
      <summary>Table view — minutes per month</summary>
      <div class="tblscroll">
        <table><thead><tr><th>Month</th><th class="n">Minutes</th></tr></thead>
        <tbody>__MONTHROWS__</tbody></table>
      </div>
    </details>
  </section>

  <section class="card">
    <h2>Albums by total listening time</h2>
    <p class="note">Any track counts toward its album, however it was played — studio, live or bootleg.</p>
    <table>
      <thead><tr><th class="n">#</th><th>Album</th><th class="n">Hours</th><th class="n">Minutes</th><th class="n">Tracks</th><th>Most played</th></tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
  </section>

  <section class="method">
    <h2>How this was counted</h2>
    <ul>
      <li>Watch history records <em>that</em> something played, never for how long. Minutes come from MusicBrainz track durations, assuming each play finished — so a skipped track counts the same as a full one.</li>
      <li>Music counts, talk does not: concert footage, bootlegs and drum-cams are listening; __TALK__ plays of interviews, podcasts, reactions and gear rundowns were excluded.</li>
      <li>A live version counts toward the album the song comes from, so a bootleg <em>Robot Stop</em> lands on <em>Nonagon Infinity</em>.</li>
      <li>__NODUR__ plays named no track with a known runtime — mostly full-set uploads and medleys — and contribute nothing rather than a guess.</li>
      <li>Colours are a colourblind-safe categorical set; the tail folds into a neutral "Other" instead of inventing more hues.</li>
    </ul>
  </section>
</div>

<div id="tip" role="status" aria-live="polite"></div>
<script>
(function () {
  var tip = document.getElementById('tip');
  var shown = null;

  function render(col) {
    var d = JSON.parse(col.getAttribute('data-d'));
    var rows = d.items.map(function (it) {
      return '<div class="r"><i style="background:var(--c-' + it.key + ')"></i>' +
             escapeHtml(it.label) + '<b>' + it.min.toLocaleString() + '</b></div>';
    }).join('');
    tip.innerHTML = '<div class="m">' + d.month + '</div><div class="t">' +
      d.total.toLocaleString() + ' min</div>' + rows;
    tip.style.opacity = '1';
    shown = col;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function place(x, y) {
    var r = tip.getBoundingClientRect();
    var left = Math.min(x + 14, window.innerWidth - r.width - 8);
    var top = Math.min(Math.max(y - r.height - 12, 8), window.innerHeight - r.height - 8);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }

  function hide() { tip.style.opacity = '0'; shown = null; }

  document.querySelectorAll('.col').forEach(function (col) {
    col.addEventListener('mouseenter', function () { render(col); });
    col.addEventListener('mousemove', function (e) { place(e.clientX, e.clientY); });
    col.addEventListener('mouseleave', hide);
    col.addEventListener('focus', function () {
      render(col);
      var b = col.getBoundingClientRect();
      place(b.left, b.top);
    });
    col.addEventListener('blur', hide);
  });
  window.addEventListener('scroll', function () { if (shown) hide(); }, true);
})();
</script>
"""



# The static export reuses the page's CSS so both renders stay in step.
_CSS = TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]

_STATIC_CSS = """
body { background: var(--surface); }
.export { width: __TOTALW__px; padding: 30px 34px 26px; background: var(--surface); }
.export h1 { font-size: 21px; margin: 0; letter-spacing: -0.01em; }
.export .sub { font-size: 13px; color: var(--ink-2); margin: 7px 0 0; max-width: 92ch; }
.export .scroll { overflow: visible; padding-top: 22px; }
.yunit {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10px; color: var(--muted); letter-spacing: .08em;
  text-transform: uppercase; margin-bottom: 12px; text-align: right; width: 34px;
}
.vlabel {
  position: absolute; transform: translateX(-50%);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums; font-size: 11px; font-weight: 600;
  color: var(--ink); font-style: normal; white-space: nowrap;
}
.foot {
  margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--hair);
  font-size: 11.5px; color: var(--muted); line-height: 1.5;
}
.export .legend { margin-top: 16px; }
.export .col { cursor: default; }
"""

STATIC_TEMPLATE = (
    "<title>Gizzard Hours</title>\n<style>"
    + _CSS
    + _STATIC_CSS
    + """</style>
<div class="export">
  <h1>King Gizzard &amp; the Lizard Wizard — minutes listened per month</h1>
  <p class="sub">__SUBTITLE__</p>
  <div class="scroll">
    <div class="plotwrap">
      <div>
        <div class="yunit">min</div>
        <div class="yaxis">__YLAB__</div>
      </div>
      <div class="plot">__GRID__<div class="cols">__COLS__</div>__VLAB__</div>
    </div>
    <div class="xaxis">__XLAB__</div>
  </div>
  <div class="legend">__LEGEND__</div>
  <p class="foot">
    Reconstructed from Google Takeout YouTube watch history; track durations from MusicBrainz.
    Watch history records that something played, never for how long, so every play is counted as running
    to completion — these are upper bounds. Concert footage and bootlegs count as listening;
    interviews, reactions and podcasts do not. __TOTAL_PLAYS__ plays analysed.
  </p>
</div>
"""
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="minutes report JSON from kglw.minutes --json")
    ap.add_argument("-o", "--output", default="listening.html")
    ap.add_argument("--top", type=int, default=6, help="albums given their own colour")
    ap.add_argument("--since", help="first month to plot, e.g. 2023-01")
    ap.add_argument("--static", action="store_true",
                    help="chart-only render for image export (adds value labels)")
    ap.add_argument("--width", type=int, help="plot width budget in px")
    args = ap.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as fh:
        report = json.load(fh)

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(build(report, top_n=args.top, since=args.since,
                       static=args.static, target_w=args.width))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
