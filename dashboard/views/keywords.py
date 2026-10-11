"""Từ khóa & Hashtag – what words and hashtags drove each hour."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard import data, state
from dashboard.components import fmt_int, html, insight, note, shown, slug, strap, sub
from dashboard.theme import GOLD, INK, INK_3, PLOTLY_CONFIG, RULE, SERIES

safe = state.safe_mode()
kw = data.one("keyword_trend")
eda = data.one("eda_distributions")
overview = data.one("overview")

slug("Từ khóa và hashtag",
     "Mỗi giờ được coi là một văn bản: TF-IDF đẩy lên những từ đặc trưng cho giờ đó, khác với đếm tần suất "
     "chỉ cho ra những từ phổ biến cả ngày.")

tfidf = pd.DataFrame(kw.get("tfidf", []))
freq = pd.DataFrame(kw.get("frequency", []))
if safe:
    tfidf = tfidf[tfidf["term"].map(data.is_safe_term)]
    freq = freq[freq["term"].map(data.is_safe_term)]

strap("Từ khóa nổi bật theo giờ")
method = st.radio("Xếp hạng theo", ["TF-IDF (đặc trưng của giờ)", "Tần suất thô"], horizontal=True, key="kw_mode")
src = tfidf if method.startswith("TF") else freq
hours = sorted(src["hour"].unique())
cols_html = []
score_col = "tfidf" if method.startswith("TF") else "count"
for h in hours:
    rows_h = src[src["hour"] == h].head(10)
    top_score = float(rows_h[score_col].max()) if not rows_h.empty else 1.0
    items = []
    for i, r in enumerate(rows_h.itertuples(), start=1):
        # Weight ramp by score relative to the hour's leader: 400, 500, ..., 800.
        # A term present in every hour has TF-IDF 0, so an hour can score 0.
        ratio = float(getattr(r, score_col)) / top_score if top_score > 0 else 0.0
        weight = 400 + 100 * int(4 * ratio)
        items.append(f'<li><i>{i}</i><span style="font-weight:{min(weight, 800)}">{shown(r.term)}</span></li>')
    cols_html.append(f'<div class="hourcol"><time>{int(h):02d}:00</time><ol>{"".join(items)}</ol></div>')
html(f'<div class="hours">{"".join(cols_html)}</div>')
if not tfidf.empty and not freq.empty:
    common = set(freq.groupby("hour").head(10)["term"])
    full_hours = tfidf[tfidf["hour"].astype(int) >= 8]
    distinct = list(dict.fromkeys(t for t in full_hours.sort_values("tfidf", ascending=False)["term"]
                                  if t not in common))[:6]
    insight("Tần suất thô lặp lại cùng một nhóm từ ở mọi giờ; TF-IDF làm lộ ra từ riêng của từng giờ, ví dụ "
            + ", ".join(f"<b>{shown(t)}</b>" for t in distinct) + ".")
note("Độ đậm của chữ theo điểm TF-IDF (hoặc tần suất) so với từ đứng đầu giờ đó. "
     "Giờ UTC. Chỉ tính từ xuất hiện ít nhất 20 lần trong giờ đó và bỏ qua 344 tài khoản hoạt động cao (top 0,1%): "
     "nếu giữ lại, bảng TF-IDF bị các bot đăng theo lịch chiếm chỗ. Khung 07:00 chỉ có 10 phút dữ liệu.")

strap("Hashtag")
# Safe list excludes every hashtag of a post flagged 18+, not just the
# flagged words themselves.
tags = data.frame("top_hashtags_safe" if safe else "top_hashtags")
trend = data.frame("hashtag_trend")
if safe:
    tags = tags[tags["hashtag"].map(data.is_safe_term)]
    trend = trend[trend["hashtag"].map(data.is_safe_term)]
left, right = st.columns([1, 1.6], gap="large")
with left:
    sub("Hashtag nhiều nhất cả ngày")
    top = tags.head(15).iloc[::-1]
    fig = go.Figure(go.Bar(x=top["count"], y=["#" + h for h in top["hashtag"]], orientation="h",
                           marker=dict(color="#3987e5", line=dict(width=0)),
                           text=[fmt_int(c) for c in top["count"]], textposition="outside",
                           textfont=dict(color=INK, size=15), hovertemplate="%{y}: %{x:,}<extra></extra>",
                           cliponaxis=False))
    fig.update_layout(height=520, showlegend=False, hovermode="closest",
                      xaxis=dict(visible=False, range=[0, float(top["count"].max()) * 1.22]),
                      yaxis=dict(tickfont=dict(size=16, color=INK)), margin=dict(l=8, r=8))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
with right:
    sub("Hashtag theo thời gian")
    choices = [h for h in tags["hashtag"].head(20) if h in set(trend["hashtag"])]
    picked = st.multiselect("Chọn tối đa 4 hashtag", choices, default=choices[:3], max_selections=4,
                            format_func=lambda h: "#" + h, key="tag_pick")
    trend["bucket"] = pd.to_datetime(trend["bucket"])
    gaps = set(pd.to_datetime(data.one("overview").get("gap_bins", [])))
    trend = trend[~trend["bucket"].isin(gaps)]
    fig = go.Figure()
    for i, h in enumerate(picked):
        tt = trend[trend["hashtag"] == h].sort_values("bucket")
        fig.add_trace(go.Scatter(x=tt["bucket"], y=tt["count"], name="#" + h, mode="lines",
                                 line=dict(color=SERIES[i], width=2.5)))
    fig.add_vline(x=state.current_time(), line=dict(color=GOLD, width=2))
    fig.update_layout(height=440, yaxis=dict(title="bài / 5 phút"), xaxis=dict(tickformat="%H:%M"))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
share = overview.get("hashtag_share", 0)
insight(f"Chỉ <b>{100 * share:.1f}%</b>".replace(".", ",") + " số bản ghi có hashtag và có "
        f"{fmt_int(overview.get('distinct_hashtags', 0))} hashtag khác nhau trong văn bản video và bình luận YouTube.")
if safe:
    note("Chế độ trình chiếu đang ẩn các hashtag và từ khóa 18+.")
