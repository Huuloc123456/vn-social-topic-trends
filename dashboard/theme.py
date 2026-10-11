"""Broadcast live-desk theme: tokens, page CSS, Plotly template."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

FONT_DIR = Path(__file__).parent / "static" / "fonts"

# Surfaces and ink
BG = "#0B1B3A"        # broadcast navy ground
PANEL = "#12264D"     # lifted strip / panel
PANEL_2 = "#1A3364"   # hover / selected row
RULE = "#2A4479"      # hairline rules, chart grid
INK = "#FFFFFF"
INK_2 = "#C5D3EE"     # secondary ink, blue-tinted, never gray
INK_3 = "#93A8D2"     # muted labels (>= 4.5:1 on BG)
RED = "#D41E35"       # BREAKING / bursts / primary action only
GOLD = "#F5B800"      # live clock, selected story
TRACK = "#1C3463"     # empty bar track

# Categorical slots, dark steps. The palette's 8th slot (red) is dropped:
# red is reserved for BREAKING and the primary action in this world. The
# 7 slots pass every validator check on the #0B1B3A ground; topics ranked 8+
# fold to OTHER and are always identified by their text label.
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9"]
OTHER = "#5B6F99"     # folded topics ("Khác")


def topic_color(size_rank: int) -> str:
    """Colour follows the topic: fixed by its size rank in the final model."""
    return SERIES[size_rank] if size_rank < len(SERIES) else OTHER


@lru_cache(maxsize=1)
def _font_faces() -> str:
    ranges = {
        "vietnamese": "U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, "
                      "U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB",
        "latin-ext": "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, "
                     "U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, "
                     "U+2C60-2C7F, U+A720-A7FF",
        "latin": "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, "
                 "U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD",
    }
    faces = []
    for subset, urange in ranges.items():
        data = base64.b64encode((FONT_DIR / f"archivo-{subset}.woff2").read_bytes()).decode()
        faces.append(
            "@font-face{font-family:'Archivo';font-style:normal;font-weight:100 900;font-stretch:62% 125%;"
            f"font-display:block;src:url(data:font/woff2;base64,{data}) format('woff2');unicode-range:{urange};}}"
        )
    return "\n".join(faces)


def page_css() -> str:
    return f"""<style>
{_font_faces()}
:root {{
  --bg:{BG}; --panel:{PANEL}; --panel-2:{PANEL_2}; --rule:{RULE}; --track:{TRACK};
  --ink:{INK}; --ink-2:{INK_2}; --ink-3:{INK_3}; --red:{RED}; --gold:{GOLD};
  --cond: 'Archivo', 'Arial Narrow', sans-serif;
  color-scheme: dark;
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{ background: var(--bg); }}
html, body, [class*="st-"], .stMarkdown, button, input, textarea, select {{
  font-family: 'Archivo', system-ui, sans-serif !important; color: var(--ink);
}}
[data-testid="stHeader"] {{ background: transparent; height: 0; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
.block-container {{ padding: 0 2.25rem 4rem !important; max-width: 1680px; }}
::selection {{ background: var(--gold); color: var(--bg); }}
* {{ scrollbar-color: var(--rule) var(--bg); caret-color: var(--gold); }}
:focus-visible {{ outline: 3px solid var(--gold) !important; outline-offset: 2px; }}
p, li {{ font-size: 1.125rem; line-height: 1.55; color: var(--ink-2); }}
a {{ color: var(--ink); text-underline-offset: 3px; }}

/* ---------- rundown bar ---------- */
.rundown {{ display:flex; align-items:stretch; gap:0; border-bottom:2px solid var(--rule);
  margin: 0 -2.25rem 0; padding: 0 2.25rem; background: var(--panel); min-height: 64px; }}
.rundown .show {{ display:flex; align-items:center; gap:.75rem; padding-right:1.5rem; border-right:1px solid var(--rule); }}
.rundown .show b {{ font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:1.65rem;
  letter-spacing:.01em; text-transform:uppercase; line-height:1; }}
.rundown .show span {{ font-size:.95rem; color:var(--ink-3); line-height:1.15; }}
.live {{ display:inline-flex; align-items:center; gap:.4rem; background:var(--red); color:#fff;
  font-family:var(--cond); font-stretch:75%; font-weight:800; font-size:.95rem; letter-spacing:.08em;
  padding:.2rem .55rem; text-transform:uppercase; }}
.live i {{ width:.55rem; height:.55rem; background:#fff; border-radius:50%; display:inline-block; }}
.clock {{ margin-left:auto; display:flex; flex-direction:column; justify-content:center; align-items:flex-end;
  padding-left:1.5rem; border-left:1px solid var(--rule); }}
.clock b {{ font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:2.6rem; color:var(--gold);
  font-variant-numeric:tabular-nums; line-height:.95; }}
.clock span {{ font-size:.85rem; color:var(--ink-3); letter-spacing:.06em; text-transform:uppercase; }}

/* segment tabs (st.page_link) */
.st-key-segrow [data-testid="stPageLink"] a, .st-key-segrow [data-testid="stPageLink-NavLink"] {{
  border-radius:0 !important; padding:.55rem .9rem !important; background:transparent !important; }}
.st-key-segrow [data-testid="stPageLink"] p, .st-key-segrow [data-testid="stPageLink-NavLink"] p {{
  font-family:var(--cond) !important; font-stretch:75%; font-weight:700; font-size:1.15rem !important;
  text-transform:uppercase; letter-spacing:.04em; color:var(--ink-2) !important; }}
.st-key-segrow [data-testid="stPageLink"] a:hover p {{ color:var(--ink) !important; }}
.st-key-segrow [data-testid="stPageLink-NavLink"][aria-current="page"], .st-key-segrow a[aria-current="page"] {{
  background:var(--ink) !important; }}
.st-key-segrow a[aria-current="page"] p {{ color:var(--bg) !important; }}
.st-key-segrow {{ border-bottom:1px solid var(--rule); margin:0 -2.25rem 1.25rem; padding:.35rem 2.25rem;
  width:calc(100% + 4.5rem) !important; max-width:none !important; }}
.st-key-segrow [data-testid="stHorizontalBlock"] {{ gap:.25rem !important; flex-wrap:nowrap; align-items:center; }}
.st-key-segrow [data-testid="stColumn"] {{ flex:0 0 auto !important; width:auto !important; min-width:0 !important; }}
.st-key-segrow [data-testid="stColumn"]:last-child {{ margin-left:auto; }}

/* ---------- headings ---------- */
h1.slug {{ font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:3.4rem; line-height:1;
  text-transform:uppercase; margin:1.4rem 0 .35rem; letter-spacing:.005em; text-wrap:balance; }}
p.dek {{ font-size:1.25rem; color:var(--ink-2); margin:0 0 1.5rem; max-width:70ch; }}
h2.strap {{ font-family:var(--cond); font-stretch:68%; font-weight:800; font-size:2rem; text-transform:uppercase;
  margin:2.75rem 0 .6rem; padding-top:.7rem; border-top:2px solid var(--rule); letter-spacing:.01em; }}
h3.sub {{ font-family:var(--cond); font-stretch:75%; font-weight:700; font-size:1.35rem; text-transform:uppercase;
  color:var(--ink); margin:1.25rem 0 .4rem; letter-spacing:.02em; }}
.insight {{ font-size:1.15rem; color:var(--ink); margin:.35rem 0 1rem; max-width:75ch; }}
.insight b {{ color:var(--ink); font-weight:800; }}
.insight b.story {{ white-space:nowrap; }}
.sw-inline {{ display:inline-block; width:.7em; height:.7em; margin-right:.35em; vertical-align:baseline; }}
.note {{ font-size:.98rem; color:var(--ink-3); max-width:80ch; }}

/* ---------- data strip (broadcast lower-third numbers) ---------- */
.strip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); border-top:2px solid var(--ink);
  border-bottom:1px solid var(--rule); margin:.5rem 0 1.25rem; }}
.strip > div {{ padding:.7rem 1rem .8rem; border-right:1px solid var(--rule); }}
.strip > div:last-child {{ border-right:0; }}
.strip b {{ display:block; font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:2.6rem;
  font-variant-numeric:tabular-nums; line-height:1; }}
.strip span {{ font-size:.98rem; color:var(--ink-2); }}

/* ---------- scoreboard ---------- */
.board {{ border-top:2px solid var(--ink); }}
.board .row {{ display:grid; grid-template-columns:minmax(260px,26%) 1fr 92px 84px; align-items:center; column-gap:1rem;
  row-gap:.1rem; padding:.38rem 0 .42rem; border-bottom:1px solid var(--rule); }}
.board .row.sel {{ background:var(--panel-2); }}
.board .row.sel .lab b {{ color:var(--gold); }}
.board .mv {{ display:flex; align-items:center; justify-content:flex-end; gap:.3rem; font-family:var(--cond);
  font-stretch:70%; font-weight:700; font-size:1.1rem; color:var(--ink-2); font-variant-numeric:tabular-nums; padding-right:.4rem; }}
.board .mv svg {{ width:12px; height:12px; flex:none; }}
.board .lab {{ display:flex; align-items:center; gap:.6rem; min-width:0; padding-left:.6rem; }}
.board .sw {{ width:14px; height:14px; flex:none; }}
.board .lab b {{ font-family:var(--cond); font-stretch:70%; font-weight:700; font-size:1.3rem; text-transform:uppercase;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.board .track {{ height:24px; background:var(--track); position:relative; }}
.board .fill {{ position:absolute; inset:0; transform-origin:left center; transition: transform .35s cubic-bezier(.16,1,.3,1); }}
.board .pct {{ font-family:var(--cond); font-stretch:70%; font-weight:800; font-size:1.55rem; text-align:right;
  font-variant-numeric:tabular-nums; padding-right:.4rem; }}
.board .kw {{ grid-column:2 / 5; font-size:.98rem; line-height:1.3; color:var(--ink-3); }}
.board .brk {{ display:inline-block; margin-left:.5rem; background:var(--red); color:#fff; font-family:var(--cond);
  font-stretch:75%; font-weight:800; font-size:.8rem; letter-spacing:.08em; padding:.05rem .4rem; vertical-align:middle; }}

/* ---------- ticker crawl ---------- */
.ticker {{ display:flex; align-items:stretch; margin:1rem -2.25rem 0; border-top:2px solid var(--red); background:#08142C;
  overflow:hidden; }}
.ticker.onair {{ position:fixed; left:0; right:0; bottom:0; margin:0; z-index:999; }}
.onair-pad {{ height:4.5rem; }}

/* ---------- time rail under the scrubber ---------- */
.rail {{ position:relative; height:46px; margin:-.4rem .55rem .6rem; }}
.rail .tick {{ position:absolute; top:0; height:10px; border-left:1px solid var(--ink-3); }}
.rail .tick span {{ position:absolute; top:12px; left:0; transform:translateX(-50%); font-family:var(--cond); font-stretch:70%;
  font-weight:700; font-size:.95rem; color:var(--ink-3); font-variant-numeric:tabular-nums; }}
.rail .pip {{ position:absolute; top:-2px; width:10px; height:14px; background:var(--red); transform:translateX(-50%); }}
.rail .now {{ position:absolute; top:-6px; width:3px; height:20px; background:var(--gold); transform:translateX(-50%); }}

/* ---------- the call slate (Text Analyzer) ---------- */
.call {{ background:var(--panel-2); border-top:4px solid var(--gold); padding:1rem 1.25rem 1.1rem; margin:.4rem 0 1.25rem; }}
.call b {{ display:block; font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:2.8rem; line-height:1;
  text-transform:uppercase; color:var(--ink); }}
.call span {{ display:block; margin-top:.45rem; font-size:1.05rem; color:var(--ink-2); }}
.call em {{ font-style:normal; font-family:var(--cond); font-stretch:70%; font-weight:800; color:var(--gold);
  font-variant-numeric:tabular-nums; }}
.ticker .tag {{ flex:none; background:var(--red); color:#fff; font-family:var(--cond); font-stretch:70%; font-weight:800;
  font-size:1.2rem; letter-spacing:.06em; text-transform:uppercase; padding:.55rem 1rem; display:flex; align-items:center; }}
.ticker .lane {{ overflow:hidden; flex:1; display:flex; align-items:center; }}
.ticker .crawl {{ display:inline-flex; gap:3rem; white-space:nowrap; padding-left:100%;
  animation: crawl var(--dur, 60s) linear infinite; }}
.ticker .crawl span {{ font-size:1.15rem; color:var(--ink); }}
.ticker .crawl b {{ font-family:var(--cond); font-stretch:70%; font-weight:800; color:var(--gold);
  font-variant-numeric:tabular-nums; margin-right:.5rem; }}
@media (max-width: 720px) {{
  .block-container {{ padding: 0 1rem 3rem !important; }}
  .rundown, .st-key-segrow, .ticker {{ margin-left:-1rem; margin-right:-1rem; padding-left:1rem; padding-right:1rem; }}
  .board .row {{ grid-template-columns: 1fr 70px; }}
  .board .lab {{ grid-column: 1 / 2; grid-row: 1; }}
  .board .pct {{ grid-column: 2 / 3; grid-row: 1; }}
  .board .track {{ grid-column: 1 / 2; grid-row: 2; }}
  .board .mv {{ grid-column: 2 / 3; grid-row: 2; }}
  .board .kw {{ grid-column: 1 / 3; }}
  .ticker.onair {{ position:static; margin:1rem -1rem 0; }}
  .onair-pad {{ display:none; }}
  .st-key-segrow [data-testid="stHorizontalBlock"] {{ overflow-x:auto; scrollbar-width:none; }}
  .st-key-segrow [data-testid="stColumn"]:last-child {{ margin-left:0; }}
  .call b {{ font-size:2rem; }}
  .funnel .step {{ grid-template-columns: 1fr 110px; }}
  .funnel .bar {{ grid-column: 1 / 3; grid-row: 2; }}
  .slate {{ grid-template-columns: 76px 1fr; }}
  .slate .z {{ grid-column: 2; justify-self: start; }}
  h1.slug {{ font-size: 2.5rem; }}
  .clock b {{ font-size: 2rem; }}
}}
@keyframes crawl {{ from {{ transform:translateX(0); }} to {{ transform:translateX(-100%); }} }}
@media (prefers-reduced-motion: reduce) {{
  .ticker .crawl {{ animation:none; padding-left:1rem; flex-wrap:wrap; white-space:normal; gap:.4rem 2rem; }}
  .ticker.onair {{ position:static; margin:1rem -2.25rem 0; }}
  .onair-pad {{ display:none; }}
  .board .fill {{ transition:none; }}
}}

/* ---------- slates: burst log, data-quality funnel ---------- */
.slate {{ display:grid; grid-template-columns:110px 1fr auto; gap:1rem; align-items:center; padding:.6rem 0;
  border-bottom:1px solid var(--rule); }}
.slate time {{ font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:1.9rem; color:var(--gold);
  font-variant-numeric:tabular-nums; }}
.slate .what b {{ font-family:var(--cond); font-stretch:72%; font-weight:700; font-size:1.3rem; text-transform:uppercase; }}
.slate .what span {{ display:block; color:var(--ink-2); font-size:1rem; }}
.slate .z {{ font-family:var(--cond); font-stretch:70%; font-weight:800; font-size:1.4rem; background:var(--red);
  color:#fff; padding:.15rem .6rem; font-variant-numeric:tabular-nums; }}
.funnel .step {{ display:grid; grid-template-columns:minmax(260px,32%) 1fr 130px; gap:1rem; align-items:center;
  padding:.5rem 0; border-bottom:1px solid var(--rule); }}
.funnel .step .name {{ font-size:1.05rem; color:var(--ink); }}
.funnel .step .name span {{ display:block; font-size:.9rem; color:var(--ink-3); }}
.funnel .bar {{ height:24px; background:var(--track); position:relative; }}
.funnel .bar i {{ position:absolute; inset:0 auto 0 0; background:#3987e5; }}
.funnel .bar em {{ position:absolute; top:0; bottom:0; background:repeating-linear-gradient(135deg, rgba(212,30,53,.85) 0 6px, rgba(212,30,53,.45) 6px 12px); }}
.funnel .num {{ text-align:right; font-family:var(--cond); font-stretch:70%; font-weight:800; font-size:1.35rem;
  font-variant-numeric:tabular-nums; }}
.funnel .num span {{ display:block; font-size:.95rem; color:#FF8A98; font-weight:700; }}
.funnel .void {{ display:inline-block; border:2px solid var(--red); color:#FF8A98; font-family:var(--cond); font-stretch:70%;
  font-weight:800; font-size:.8rem; letter-spacing:.1em; padding:0 .35rem; margin-left:.5rem; }}
.funnel .total .name {{ font-weight:700; }}

/* ---------- quotes (representative posts) ---------- */
.quote {{ border-left:0; border-top:1px solid var(--rule); padding:.7rem 0 .7rem; }}
.quote p {{ font-size:1.1rem; color:var(--ink); margin:0; max-width:80ch; }}
.quote span {{ font-size:.88rem; color:var(--ink-3); font-variant-numeric:tabular-nums; }}

/* ---------- tables ---------- */
.tbl {{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }}
.tbl th {{ text-align:left; font-family:var(--cond); font-stretch:75%; font-weight:700; text-transform:uppercase;
  font-size:1rem; color:var(--ink-2); border-bottom:2px solid var(--ink); padding:.45rem .6rem; letter-spacing:.03em; }}
.tbl td {{ border-bottom:1px solid var(--rule); padding:.45rem .6rem; font-size:1.02rem; color:var(--ink); }}
.tbl td.num, .tbl th.num {{ text-align:right; }}
.tbl tr.best td {{ background:var(--panel-2); font-weight:800; }}
.tbl .tag {{ display:inline-block; margin-left:.4rem; background:var(--gold); color:var(--bg); font-family:var(--cond);
  font-stretch:75%; font-weight:800; font-size:.8rem; letter-spacing:.06em; padding:0 .35rem; }}

/* keyword hour lists */
.hours {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); border-top:2px solid var(--ink); }}
.hourcol {{ border-right:1px solid var(--rule); padding:.5rem .8rem .8rem; }}
.hourcol:last-child {{ border-right:0; }}
.hourcol time {{ display:block; font-family:var(--cond); font-stretch:62%; font-weight:800; font-size:2rem; color:var(--gold);
  font-variant-numeric:tabular-nums; }}
.hourcol ol {{ list-style:none; margin:.3rem 0 0; padding:0; }}
.hourcol {{ border-bottom:1px solid var(--rule); }}
.hourcol li {{ display:grid; grid-template-columns:1.6rem 1fr; font-family:var(--cond); font-stretch:72%; font-size:1.15rem;
  color:var(--ink); line-height:1.35; padding:.1rem 0; white-space:nowrap; }}
.hourcol li i {{ font-style:normal; color:var(--ink-3); font-variant-numeric:tabular-nums; font-size:.95rem; }}

/* ---------- Streamlit widgets in the world ---------- */
[data-testid="stSlider"] label p, [data-testid="stSelectSlider"] label p, .stSelectbox label p, .stRadio label p,
.stTextArea label p, .stToggle label p {{ font-family:var(--cond) !important; font-stretch:75%; font-weight:700;
  text-transform:uppercase; letter-spacing:.04em; font-size:1rem !important; color:var(--ink-2) !important; }}
[data-baseweb="slider"] [role="slider"] {{ background:var(--red) !important; width:22px; height:22px; border-radius:0 !important;
  box-shadow:none !important; }}
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ color:var(--ink-3) !important; font-size:.95rem; }}
[data-testid="stThumbValue"] {{ font-family:var(--cond) !important; font-stretch:70%; font-weight:800; font-size:1.2rem !important;
  color:var(--gold) !important; }}
.stTextArea textarea {{ background:var(--panel) !important; border:1px solid var(--rule) !important; border-radius:0 !important;
  font-size:1.2rem !important; color:var(--ink) !important; }}
.stButton > button {{ border-radius:0; background:transparent; color:var(--ink); border:1px solid var(--rule);
  font-family:var(--cond) !important; font-stretch:75%; font-weight:700; text-transform:uppercase; letter-spacing:.05em;
  font-size:1.05rem; padding:.45rem 1rem; }}
.stButton > button:hover {{ border-color:var(--ink-2); color:var(--ink); background:var(--panel); }}
.stButton > button[kind="primary"] {{ background:var(--red); border-color:var(--red); color:#fff; font-weight:800; }}
.stButton > button[kind="primary"]:hover {{ background:#B9182C; }}
.stButton > button:disabled {{ background:var(--track); color:var(--ink-3); }}
[data-baseweb="select"] > div {{ background:var(--panel) !important; border-radius:0 !important; border-color:var(--rule) !important; }}
[data-testid="stExpander"] details {{ border-radius:0; border-color:var(--rule); background:transparent; }}
[data-baseweb="tag"] {{ border-radius:0 !important; color:#fff !important; }}
[data-baseweb="tag"]:nth-of-type(1) {{ background:{SERIES[0]} !important; }}
[data-baseweb="tag"]:nth-of-type(2) {{ background:{SERIES[1]} !important; }}
[data-baseweb="tag"]:nth-of-type(3) {{ background:{SERIES[2]} !important; }}
[data-baseweb="tag"]:nth-of-type(4) {{ background:{SERIES[3]} !important; }}
</style>"""


def plotly_template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Archivo, sans-serif", size=16, color=INK_2),
        colorway=SERIES,
        margin=dict(l=8, r=8, t=16, b=8),
        xaxis=dict(gridcolor=RULE, linecolor=RULE, zeroline=False, tickfont=dict(size=15, color=INK_3),
                   title=dict(font=dict(size=15, color=INK_3))),
        yaxis=dict(gridcolor=RULE, linecolor=RULE, zeroline=False, tickfont=dict(size=15, color=INK_3),
                   title=dict(font=dict(size=15, color=INK_3))),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=RULE, font=dict(family="Archivo, sans-serif", size=16, color=INK)),
        legend=dict(font=dict(size=15, color=INK_2), bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.15),
        hovermode="x unified",
    )
    return t


pio.templates["desk"] = plotly_template()
pio.templates.default = "desk"
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
