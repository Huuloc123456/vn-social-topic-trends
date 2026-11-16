"""Swiss information-grid theme for the dashboard."""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio

FONT_DIR = Path(__file__).parent / "static" / "fonts"

BG = "#FFFFFF"
PANEL = "#F5F5F5"
PANEL_2 = "#EEEEEE"
RULE = "#D4D4D4"
INK = "#171717"
INK_2 = "#525252"
INK_3 = "#737373"
RED = "#404040"
GOLD = "#171717"
TRACK = "#E5E5E5"
SERIES = ["#171717", "#404040", "#525252", "#6B6B6B", "#858585", "#A3A3A3", "#C4C4C4"]
OTHER = "#E5E5E5"


def topic_color(size_rank: int) -> str:
    """Keep a topic's neutral shade stable by its size rank."""
    return SERIES[size_rank] if size_rank < len(SERIES) else OTHER


@lru_cache(maxsize=1)
def _font_face() -> str:
    data = base64.b64encode((FONT_DIR / "dosis-bold.ttf").read_bytes()).decode("ascii")
    return f"@font-face{{font-family:'Dosis';font-style:normal;font-weight:700;src:url(data:font/ttf;base64,{data}) format('truetype');}}"


def page_css() -> str:
    return f"""<style>
{_font_face()}
:root {{
  --bg:{BG}; --panel:{PANEL}; --panel-2:{PANEL_2}; --rule:{RULE}; --track:{TRACK};
  --ink:{INK}; --ink-2:{INK_2}; --ink-3:{INK_3}; --red:{RED}; --gold:{GOLD};
  --sans:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  --display:'Dosis',var(--sans);
  color-scheme:light;
}}
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{ background:var(--bg); color:var(--ink); }}
html, body, [class*="st-"], .stMarkdown, button, input, textarea, select {{ font-family:var(--sans) !important; color:var(--ink); }}
[data-testid="stHeader"] {{ background:transparent; height:0; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {{ display:none !important; }}
.block-container {{ padding:0 2.25rem 3rem !important; max-width:1586px; }}
[data-testid="stAlert"], [role="alert"], [data-testid*="NotificationContent"] {{
  background:var(--panel) !important; border:1px solid var(--rule) !important;
  border-radius:3px !important; color:var(--ink) !important;
}}
[data-testid="stAlert"] > div, [role="alert"] > div, [data-testid*="NotificationContent"] > div {{
  background:var(--panel) !important; color:var(--ink) !important;
}}
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p, [role="alert"] p {{ color:var(--ink) !important; }}
[data-testid="stAlert"] svg, [role="alert"] svg {{ color:var(--ink) !important; fill:var(--ink) !important; }}
.status-message {{ margin:.75rem 0; padding:.75rem 1rem; background:var(--panel); border:1px solid var(--rule);
  border-radius:3px; color:var(--ink); }}
.status-message b {{ font-weight:600; }}
::selection {{ background:#D4D4D4; color:var(--ink); }}
* {{ scrollbar-color:var(--rule) var(--bg); caret-color:var(--ink); }}
:focus-visible {{ outline:2px solid var(--ink) !important; outline-offset:2px; }}
p, li {{ font-size:1.05rem; line-height:1.55; color:var(--ink-2); }}
a {{ color:var(--ink); text-underline-offset:3px; }}

.rundown {{ display:flex; align-items:stretch; gap:0; border-bottom:1px solid var(--rule); margin:0 -2.25rem;
  padding:0 2.25rem; background:var(--bg); min-height:60px; }}
.rundown .show {{ display:flex; align-items:center; gap:.75rem; padding-right:1.25rem; border-right:1px solid var(--rule); }}
.rundown .show b {{ font-family:var(--display); font-weight:700; font-size:1.55rem; line-height:1; }}
.rundown .show span {{ font-size:.9rem; color:var(--ink-2); line-height:1.2; }}
.live {{ display:inline-flex; align-items:center; gap:.4rem; color:var(--ink); font-size:.85rem; font-weight:700; }}
.live i {{ width:.45rem; height:.45rem; background:var(--ink); border-radius:50%; display:inline-block; }}
.clock {{ margin-left:auto; display:flex; flex-direction:column; justify-content:center; align-items:flex-end; padding-left:1.25rem; }}
.clock b {{ font-family:var(--display); font-weight:700; font-size:1.8rem; font-variant-numeric:tabular-nums; line-height:1; }}
.clock span {{ font-size:.75rem; color:var(--ink-3); }}

.st-key-segrow {{ border-bottom:1px solid var(--rule); margin:0 -2.25rem 1rem; padding:.25rem 2.25rem; width:calc(100% + 4.5rem) !important; max-width:none !important; }}
.st-key-segrow [data-testid="stHorizontalBlock"] {{ gap:.35rem !important; flex-wrap:nowrap; align-items:center; }}
.st-key-segrow [data-testid="stColumn"] {{ flex:0 0 auto !important; width:auto !important; min-width:0 !important; }}
.st-key-segrow [data-testid="stColumn"]:last-child {{ margin-left:auto; }}
.st-key-segrow [data-testid="stPageLink"] a, .st-key-segrow [data-testid="stPageLink-NavLink"] {{ border-radius:0 !important; padding:.45rem .7rem !important; background:transparent !important; }}
.st-key-segrow [data-testid="stPageLink"] p, .st-key-segrow [data-testid="stPageLink-NavLink"] p {{ font-size:.95rem !important; color:var(--ink-2) !important; white-space:nowrap; }}
.st-key-segrow [data-testid="stPageLink"] a:hover p {{ color:var(--ink) !important; }}
.st-key-segrow [data-testid="stPageLink-NavLink"][aria-current="page"], .st-key-segrow a[aria-current="page"] {{ border-bottom:2px solid var(--ink) !important; }}
.st-key-segrow a[aria-current="page"] p {{ color:var(--ink) !important; font-weight:700; }}

h1.slug {{ font-family:var(--display); font-weight:700; font-size:3.2rem; line-height:1.05; margin:1.3rem 0 .35rem; letter-spacing:-.02em; text-wrap:balance; color:var(--ink); }}
p.dek {{ font-size:1.05rem; color:var(--ink-2); margin:0 0 1.3rem; max-width:72ch; }}
h2.strap {{ font-family:var(--display); font-weight:700; font-size:1.75rem; margin:2rem 0 .6rem; padding-top:.55rem; border-top:1px solid var(--rule); color:var(--ink); }}
h3.sub {{ font-family:var(--display); font-weight:700; font-size:1.3rem; color:var(--ink); margin:1.1rem 0 .4rem; }}
.overview-header-rule {{ border-top:1px solid var(--rule); margin:1rem 0 1.2rem; }}
.trend-title {{ font-family:var(--display); font-weight:700; font-size:1.75rem; line-height:1.2; color:var(--ink); margin:0 0 .45rem; }}
.chart-unit {{ text-align:right; font-size:.9rem; color:var(--ink-2); margin:0 0 .45rem; }}
.topic-description {{ padding-bottom:.1rem; }}
.insight {{ font-size:1.05rem; color:var(--ink); margin:.35rem 0 .9rem; max-width:75ch; }}
.insight b {{ color:var(--ink); font-weight:700; }}
.sw-inline {{ display:inline-block; width:.65em; height:.65em; margin-right:.35em; vertical-align:baseline; }}
.note {{ font-size:.92rem; color:var(--ink-3); max-width:80ch; }}

.strip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); border-top:1px solid var(--ink); border-bottom:1px solid var(--rule); margin:.5rem 0 1.1rem; }}
.strip > div {{ padding:.65rem .8rem; border-right:1px solid var(--rule); }}
.strip > div:last-child {{ border-right:0; }}
.strip b {{ display:block; font-family:var(--display); font-weight:700; font-size:2rem; font-variant-numeric:tabular-nums; line-height:1; }}
.strip span {{ font-size:.9rem; color:var(--ink-2); }}

.board {{ border-top:1px solid var(--ink); }}
.board .row {{ display:grid; grid-template-columns:minmax(220px,26%) 1fr 86px 80px; align-items:center; column-gap:.9rem; row-gap:.1rem; padding:.45rem 0; border-bottom:1px solid var(--rule); }}
.board .row.sel {{ background:var(--panel); }}
.board .row.sel .lab b {{ color:var(--ink); }}
.board .mv {{ display:flex; align-items:center; justify-content:flex-end; gap:.3rem; font-variant-numeric:tabular-nums; color:var(--ink-2); padding-right:.3rem; }}
.board .mv svg {{ width:12px; height:12px; flex:none; }}
.board .lab {{ display:flex; align-items:center; gap:.55rem; min-width:0; padding-left:.4rem; }}
.board .sw {{ width:12px; height:12px; flex:none; }}
.board .lab b {{ font-weight:650; font-size:1.05rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.board .track {{ height:18px; background:var(--track); position:relative; }}
.board .fill {{ position:absolute; inset:0; transform-origin:left center; transition:transform .35s cubic-bezier(.16,1,.3,1); }}
.board .pct {{ font-family:var(--display); font-weight:700; font-size:1.3rem; text-align:right; font-variant-numeric:tabular-nums; }}
.board .kw {{ grid-column:2 / 5; font-size:.88rem; line-height:1.3; color:var(--ink-3); }}
.board .brk {{ display:inline-block; margin-left:.45rem; border:1px solid var(--ink); color:var(--ink); font-size:.75rem; font-weight:700; padding:0 .3rem; }}

.ticker {{ display:flex; align-items:stretch; margin:1rem -2.25rem 0; border-top:1px solid var(--rule); background:var(--panel); overflow:hidden; }}
.ticker.onair {{ position:fixed; left:0; right:0; bottom:0; margin:0; z-index:999; }}
.onair-pad {{ height:3.6rem; }}
.ticker .tag {{ flex:none; background:var(--ink); color:white; font-weight:700; font-size:.9rem; padding:.5rem .8rem; display:flex; align-items:center; }}
.ticker .lane {{ overflow:hidden; flex:1; display:flex; align-items:center; }}
.ticker .crawl {{ display:inline-flex; gap:2rem; white-space:nowrap; padding-left:100%; animation:crawl var(--dur,60s) linear infinite; }}
.ticker .crawl span {{ font-size:.95rem; color:var(--ink); }}
.ticker .crawl b {{ font-weight:700; font-variant-numeric:tabular-nums; margin-right:.4rem; }}

.rail {{ position:relative; height:40px; margin:-.25rem .5rem .6rem; }}
.rail .tick {{ position:absolute; top:0; height:9px; border-left:1px solid var(--ink-3); }}
.rail .tick span {{ position:absolute; top:11px; left:0; transform:translateX(-50%); font-size:.85rem; color:var(--ink-3); font-variant-numeric:tabular-nums; }}
.rail .pip {{ position:absolute; top:-2px; width:8px; height:12px; background:var(--ink); transform:translateX(-50%); }}
.rail .now {{ position:absolute; top:-5px; width:2px; height:18px; background:var(--ink); transform:translateX(-50%); }}

.call {{ background:var(--panel); border-top:2px solid var(--ink); padding:.85rem 1rem; margin:.4rem 0 1rem; }}
.call b {{ display:block; font-family:var(--display); font-weight:700; font-size:2.2rem; line-height:1.1; color:var(--ink); }}
.call span {{ display:block; margin-top:.4rem; font-size:1rem; color:var(--ink-2); }}
.call em {{ font-style:normal; font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums; }}
.slate {{ display:grid; grid-template-columns:110px 1fr auto; gap:.8rem; align-items:center; padding:.6rem 0; border-bottom:1px solid var(--rule); }}
.slate time {{ font-family:var(--display); font-weight:700; font-size:1.5rem; color:var(--ink); font-variant-numeric:tabular-nums; }}
.slate .what b {{ font-weight:650; font-size:1.05rem; }}
.slate .what span {{ display:block; color:var(--ink-2); font-size:.92rem; }}
.slate .z {{ font-family:var(--display); font-weight:700; font-size:1.15rem; background:var(--panel-2); color:var(--ink); padding:.15rem .5rem; font-variant-numeric:tabular-nums; }}
.funnel .step {{ display:grid; grid-template-columns:minmax(220px,32%) 1fr 120px; gap:.8rem; align-items:center; padding:.45rem 0; border-bottom:1px solid var(--rule); }}
.funnel .step .name {{ font-size:1rem; color:var(--ink); }}
.funnel .step .name span {{ display:block; font-size:.85rem; color:var(--ink-3); }}
.funnel .bar {{ height:18px; background:var(--track); position:relative; }}
.funnel .bar i {{ position:absolute; inset:0 auto 0 0; background:var(--ink-2); }}
.funnel .bar em {{ position:absolute; top:0; bottom:0; background:repeating-linear-gradient(135deg,rgba(23,23,23,.38) 0 5px,rgba(23,23,23,.15) 5px 10px); }}
.funnel .num {{ text-align:right; font-family:var(--display); font-weight:700; font-size:1.1rem; font-variant-numeric:tabular-nums; }}
.funnel .num span {{ display:block; font-size:.85rem; color:var(--ink-2); font-weight:600; }}
.funnel .void {{ display:inline-block; border:1px solid var(--ink-2); color:var(--ink-2); font-size:.75rem; font-weight:700; padding:0 .3rem; margin-left:.4rem; }}
.quote {{ border-top:1px solid var(--rule); padding:.65rem 0; }}
.quote p {{ font-size:1rem; color:var(--ink); margin:0; max-width:80ch; }}
.quote span {{ font-size:.82rem; color:var(--ink-3); font-variant-numeric:tabular-nums; }}
.tbl {{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }}
.tbl th {{ text-align:left; font-weight:650; font-size:.95rem; color:var(--ink-2); border-bottom:1px solid var(--ink); padding:.45rem .55rem; }}
.tbl td {{ border-bottom:1px solid var(--rule); padding:.45rem .55rem; font-size:.95rem; color:var(--ink); }}
.tbl td.num, .tbl th.num {{ text-align:right; }}
.tbl tr.best td {{ background:var(--panel); font-weight:700; }}
.tbl .tag {{ display:inline-block; margin-left:.4rem; background:var(--ink); color:white; font-size:.75rem; font-weight:700; padding:0 .3rem; }}
.hours {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); border-top:1px solid var(--ink); }}
.hourcol {{ border-right:1px solid var(--rule); border-bottom:1px solid var(--rule); padding:.5rem .7rem .7rem; }}
.hourcol time {{ display:block; font-family:var(--display); font-weight:700; font-size:1.6rem; }}
.hourcol ol {{ list-style:none; margin:.3rem 0 0; padding:0; }}
.hourcol li {{ display:grid; grid-template-columns:1.6rem 1fr; font-size:1rem; color:var(--ink); line-height:1.35; padding:.1rem 0; white-space:nowrap; }}
.hourcol li i {{ font-style:normal; color:var(--ink-3); font-variant-numeric:tabular-nums; font-size:.85rem; }}

[data-testid="stSlider"] label p, [data-testid="stSelectSlider"] label p, .stSelectbox label p, .stRadio label p,
.stTextArea label p, .stToggle label p, .stMultiSelect label p {{ font-weight:600; font-size:.9rem !important; color:var(--ink-2) !important; }}
[data-baseweb="slider"] [role="slider"] {{ background:var(--ink) !important; width:18px; height:18px; border-radius:50% !important; box-shadow:none !important; }}
[data-testid="stSliderTickBarMin"], [data-testid="stSliderTickBarMax"] {{ color:var(--ink-3) !important; font-size:.85rem; }}
[data-testid="stThumbValue"] {{ font-weight:650; font-size:.95rem !important; color:var(--ink) !important; }}
.stTextArea textarea {{ background:white !important; border:1px solid var(--rule) !important; border-radius:3px !important; font-size:1rem !important; color:var(--ink) !important; }}
.stButton > button {{ border-radius:3px; background:white; color:var(--ink); border:1px solid var(--rule); font-weight:600; font-size:.95rem; padding:.4rem .85rem; }}
.stButton > button:hover {{ border-color:var(--ink-2); color:var(--ink); background:var(--panel); }}
.stButton > button[kind="primary"] {{ background:var(--ink); border-color:var(--ink); color:white; font-weight:700; }}
.stButton > button:disabled {{ background:var(--panel); color:var(--ink-3); }}
[data-baseweb="select"] > div {{ background:white !important; border-radius:3px !important; border-color:var(--rule) !important; }}
[data-testid="stExpander"] details {{ border-radius:3px; border-color:var(--rule); background:white; }}
[data-baseweb="tag"] {{ border-radius:3px !important; color:var(--ink) !important; background:var(--panel-2) !important; }}
@media (max-width:720px) {{
  .block-container {{ padding:0 1rem 2.5rem !important; }}
  .rundown,.st-key-segrow,.ticker {{ margin-left:-1rem; margin-right:-1rem; padding-left:1rem; padding-right:1rem; }}
  .st-key-segrow [data-testid="stHorizontalBlock"] {{ overflow-x:auto; scrollbar-width:none; }}
  .board .row {{ grid-template-columns:1fr 70px; }}
  .board .lab {{ grid-column:1; grid-row:1; }} .board .pct {{ grid-column:2; grid-row:1; }}
  .board .track {{ grid-column:1; grid-row:2; }} .board .mv {{ grid-column:2; grid-row:2; }} .board .kw {{ grid-column:1 / 3; }}
  .ticker.onair {{ position:static; margin:1rem -1rem 0; }} .onair-pad {{ display:none; }}
  .call b {{ font-size:1.8rem; }} .funnel .step {{ grid-template-columns:1fr 100px; }}
  .funnel .bar {{ grid-column:1 / 3; grid-row:2; }} .slate {{ grid-template-columns:76px 1fr; }}
  .slate .z {{ grid-column:2; justify-self:start; }} h1.slug {{ font-size:2.4rem; }}
}}
@keyframes crawl {{ from {{ transform:translateX(0); }} to {{ transform:translateX(-100%); }} }}
@media (prefers-reduced-motion:reduce) {{ .ticker .crawl {{ animation:none; padding-left:1rem; flex-wrap:wrap; white-space:normal; gap:.35rem 1rem; }} .board .fill {{ transition:none; }} }}
</style>"""


def plotly_template() -> go.layout.Template:
    t = go.layout.Template()
    t.layout = go.Layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="system-ui, sans-serif", size=16, color=INK_2),
        colorway=SERIES,
        margin=dict(l=8, r=8, t=16, b=8),
        xaxis=dict(gridcolor=RULE, linecolor=RULE, zeroline=False,
                   tickfont=dict(size=15, color=INK_3), title=dict(font=dict(size=15, color=INK_3))),
        yaxis=dict(gridcolor=RULE, linecolor=RULE, zeroline=False,
                   tickfont=dict(size=15, color=INK_3), title=dict(font=dict(size=15, color=INK_3))),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=RULE,
                        font=dict(family="system-ui, sans-serif", size=16, color=INK)),
        legend=dict(font=dict(size=15, color=INK_2), bgcolor="rgba(255,255,255,0)", orientation="h", y=-0.15),
        hovermode="x unified",
    )
    return t


pio.templates["swiss_grid"] = plotly_template()
pio.templates.default = "swiss_grid"
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
