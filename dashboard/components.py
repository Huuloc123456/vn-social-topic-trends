"""HTML building blocks of the live-desk world (rendered with st.markdown)."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from dashboard import data
from dashboard.theme import topic_color


def safe_mode() -> bool:
    return st.session_state.get("safe", True)


def shown(term: str) -> str:
    """Term as displayed: profanity masked in presentation mode."""
    return data.mask(term) if safe_mode() else term


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def fmt_int(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}".replace(".", ",") + "%"


def hhmm(ts) -> str:
    return pd.Timestamp(ts).strftime("%H:%M")


def slug(title: str, dek: str | None = None) -> None:
    html(f'<h1 class="slug">{escape(title)}</h1>' + (f'<p class="dek">{dek}</p>' if dek else ""))


def strap(title: str) -> None:
    html(f'<h2 class="strap">{escape(title)}</h2>')


def sub(title: str) -> None:
    html(f'<h3 class="sub">{escape(title)}</h3>')


def insight(text: str) -> None:
    """One data-driven sentence under a chart (plan section 23)."""
    html(f'<p class="insight">{text}</p>')


def note(text: str) -> None:
    html(f'<p class="note">{text}</p>')


def strip(items: list[tuple[str, str]]) -> None:
    cells = "".join(f"<div><b>{escape(v)}</b><span>{escape(k)}</span></div>" for k, v in items)
    html(f'<div class="strip">{cells}</div>')


UP = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M6 1 L11 10 L1 10 Z" fill="#C5D3EE"/></svg>'
DOWN = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M1 2 L11 2 L6 11 Z" fill="#93A8D2"/></svg>'


def story(label: str) -> str:
    """A topic name inside a sentence: white bold ink plus its colour swatch
    (text never wears the series colour)."""
    t = data.topics()
    hit = t[t["topic_label"] == label]
    sw = (f'<i class="sw-inline" style="background:{topic_color(int(hit.iloc[0]["size_rank"]))}"></i>'
          if not hit.empty else "")
    return f'<b class="story">{sw}{escape(label)}</b>'


def scoreboard(rows: pd.DataFrame, value_col: str, selected: int | None = None,
               burst_topics: set[int] | None = None, show_keywords: bool = True,
               movers: dict | None = None) -> None:
    """One bar per topic, largest first; bar length relative to the leader.
    `movers` maps topic_id -> change in share (percentage points) shown with
    a drawn up/down mark."""
    burst_topics = burst_topics or set()
    movers = movers or {}
    rows = rows.sort_values(value_col, ascending=False)
    top = max(float(rows[value_col].max()), 1e-9)
    out = []
    for r in rows.itertuples():
        val = float(getattr(r, value_col))
        color = topic_color(int(r.size_rank))
        sel = " sel" if selected is not None and int(r.topic_id) == selected else ""
        brk = '<span class="brk">BREAKING</span>' if int(r.topic_id) in burst_topics else ""
        terms = [shown(t) for t in list(r.keywords) if not safe_mode() or data.is_safe_term(t)][:6]
        kw = (f'<div class="kw">{escape(", ".join(terms))}</div>' if show_keywords else "")
        d = movers.get(int(r.topic_id))
        mv = ""
        if d is not None and abs(d) >= 0.0005:
            mv = (UP if d > 0 else DOWN) + f'<span>{"+" if d > 0 else "−"}{num(abs(d) * 100)}</span>'
        out.append(
            f'<div class="row{sel}"><div class="lab"><i class="sw" style="background:{color}"></i>'
            f'<b title="{escape(r.topic_label)}">{escape(r.topic_label)}</b>{brk}</div>'
            f'<div class="track"><div class="fill" style="transform:scaleX({val / top:.4f});background:{color}"></div></div>'
            f'<div class="pct">{fmt_pct(val)}</div><div class="mv">{mv}</div>{kw}</div>'
        )
    html(f'<div class="board" role="list">{"".join(out)}</div>')


def rail(bins: list, events: pd.DataFrame, t) -> None:
    """Broadcast time rail under the scrubber: hour ticks, a red pip at every
    burst peak and the gold 'now' mark, on the same 0–100% scale as the slider."""
    n = max(len(bins) - 1, 1)
    pos = {pd.Timestamp(b): 100 * i / n for i, b in enumerate(bins)}
    marks = []
    for b in bins:
        b = pd.Timestamp(b)
        if b.minute == 0:
            marks.append(f'<div class="tick" style="left:{pos[b]:.2f}%"><span>{b:%H:%M}</span></div>')
    for e in events.itertuples():
        p = pos.get(pd.Timestamp(e.peak))
        if p is not None:
            marks.append(f'<div class="pip" style="left:{p:.2f}%" title="{escape(e.topic_label)} {hhmm(e.peak)}"></div>')
    if pd.Timestamp(t) in pos:
        marks.append(f'<div class="now" style="left:{pos[pd.Timestamp(t)]:.2f}%"></div>')
    html(f'<div class="rail" aria-hidden="true">{"".join(marks)}</div>')


def ticker(events: pd.DataFrame, label: str = "Breaking", onair: bool = False) -> None:
    if events.empty:
        items = '<span>Chưa có sự kiện bùng nổ nào tới thời điểm này.</span>'
    else:
        items = "".join(
            f'<span><b>{hhmm(e.peak)}</b>{escape(e.topic_label.upper())} tăng vọt: {fmt_pct(e.peak_ratio)} '
            f'(nền {fmt_pct(e.baseline_ratio)}, z = {num(e.max_burst_score)})</span>'
            for e in events.itertuples())
    dur = max(30, 9 * max(len(events), 1))
    cls = "ticker onair" if onair else "ticker"
    html(f'<div class="{cls}" aria-label="Sự kiện bùng nổ"><div class="tag">{escape(label)}</div>'
         f'<div class="lane"><div class="crawl" style="--dur:{dur}s">{items}</div></div></div>'
         + ('<div class="onair-pad"></div>' if onair else ""))


def burst_log(events: pd.DataFrame) -> None:
    rows = []
    for e in events.itertuples():
        rows.append(
            f'<div class="slate"><time>{hhmm(e.peak)}</time><div class="what"><b>{escape(e.topic_label)}</b>'
            f'<span>Từ {hhmm(e.start)} đến {hhmm(e.end)} · tỷ trọng {fmt_pct(e.peak_ratio)} so với nền '
            f'{fmt_pct(e.baseline_ratio)} của 60 phút trước</span></div><div class="z">z {num(e.max_burst_score)}</div></div>')
    html("".join(rows) or '<p class="note">Không có sự kiện nào vượt ngưỡng.</p>')


def quotes(posts: pd.DataFrame) -> None:
    out = []
    for p in posts.itertuples():
        text = data.mask_text(p.text) if safe_mode() else p.text
        out.append(f'<div class="quote"><p>{escape(text)}</p><span>{hhmm(p.created_at)} UTC · '
                   f'độ gần tâm cụm {num(p.score, 2)}</span></div>')
    html("".join(out))


def table(df: pd.DataFrame, num_cols: set[str] | None = None, best_index=None, best_tag: str = "") -> None:
    num_cols = num_cols or set()
    head = "".join(f'<th class="{"num" if c in num_cols else ""}">{escape(str(c))}</th>' for c in df.columns)
    body = []
    for idx, r in df.iterrows():
        cls = ' class="best"' if best_index is not None and idx == best_index else ""
        cells = "".join(
            f'<td class="{"num" if c in num_cols else ""}">{escape(str(r[c]))}'
            + (f'<span class="tag">{escape(best_tag)}</span>' if cls and best_tag and i == 0 else "") + "</td>"
            for i, c in enumerate(df.columns))
        body.append(f"<tr{cls}>{cells}</tr>")
    html(f'<table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>')
