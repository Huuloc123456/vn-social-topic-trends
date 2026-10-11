"""Bảng điểm – the first viewport: the running scoreboard of topic share,
the day scrubber under it, and the BREAKING crawl pinned to the bottom edge."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard import data, state
from dashboard.components import (
    fmt_int,
    fmt_pct,
    hhmm,
    insight,
    note,
    rail,
    scoreboard,
    slug,
    story,
    strap,
    strip,
    ticker,
)
from dashboard.theme import GOLD, PLOTLY_CONFIG

topics = data.topics()
trend = data.trend()
bursts = data.bursts()
dq = data.one("data_quality")
overview = data.one("overview")
info = data.one("model_info")

MODES = ["Tích lũy tới thời điểm này", "Trong 5 phút này"]
t = state.current_time()
mode = st.session_state.get("board_mode", MODES[0])

slug("YouTube Việt Nam đang thảo luận gì",
     f"{len(topics)} chủ đề từ {fmt_int(overview['posts'])} video và bình luận tiếng Việt. Kéo thanh thời gian bên dưới "
     "để xem diễn biến theo thời gian.")

earlier = t - pd.Timedelta(minutes=60)
prev = trend[trend["bucket"] == earlier].set_index("topic_id")["ratio"]
cur = trend[trend["bucket"] == t].set_index("topic_id")["ratio"]
if mode == MODES[0]:
    upto = trend[trend["bucket"] <= t]
    agg = upto.groupby("topic_id")["count"].sum()
    share = agg / agg.sum()
    agg_prev = trend[trend["bucket"] <= earlier].groupby("topic_id")["count"].sum()
    share_prev = agg_prev / agg_prev.sum() if not agg_prev.empty else pd.Series(dtype=float)
    label_now = f"tích lũy từ {hhmm(trend['bucket'].min())} tới {hhmm(t)}"
else:
    share, share_prev = cur, prev
    label_now = f"trong khung {hhmm(t)}–{hhmm(t + pd.Timedelta(minutes=5))}"
movers = (share - share_prev).dropna().to_dict() if not share_prev.empty else {}

board = topics.set_index("topic_id").assign(value=share).fillna({"value": 0}).reset_index()
live = bursts[(bursts["start"] <= t) & (bursts["end"] >= t)] if not bursts.empty else bursts
scoreboard(board, "value", burst_topics=set(live["topic_id"]) if not live.empty else set(),
           show_keywords=False, movers=movers)

c1, c2 = st.columns([3, 1.1], vertical_alignment="top")
with c1:
    state.scrubber()
    rail(state.bins(), bursts, t)
with c2:
    st.radio("Cách đếm", MODES, key="board_mode")

leader = board.sort_values("value", ascending=False).iloc[0]
sentence = f"Dẫn đầu {label_now}: {story(leader['topic_label'])} với {fmt_pct(leader['value'])} số bài."
if not prev.empty:
    delta = (cur - prev).dropna()
    mover = delta.idxmax()
    mover_label = topics.set_index("topic_id").loc[mover, "topic_label"]
    sentence += (f" So với {hhmm(earlier)}, chủ đề tăng mạnh nhất trong khung 5 phút là {story(mover_label)} "
                 f"({fmt_pct(prev[mover])} → {fmt_pct(cur[mover])}).")
insight(sentence)
note("Mũi tên: thay đổi tỷ trọng (điểm phần trăm) so với 60 phút trước. Vạch đỏ trên thanh thời gian: các sự kiện "
     "bùng nổ. Tỷ trọng tính trên các bài gán được chủ đề.")

strip([
    ("bài đăng thô thu thập", fmt_int(dq["raw_records"])),
    ("bản ghi tiếng Việt hợp lệ", fmt_int(dq["clean_volume"])),
    ("tài khoản", fmt_int(overview["authors"])),
    ("chủ đề (" + info.get("model", "") + ")", str(len(topics))),
    ("sự kiện bùng nổ", str(len(bursts))),
])

strap("Nhịp đăng bài trong ngày")
ppb = data.posts_per_bin()
fig = go.Figure()
fig.add_trace(go.Bar(x=ppb["bucket"], y=ppb["posts"], name="Bài / 5 phút",
                     marker=dict(color=["#5B6F99" if g else "#3987e5" for g in ppb["is_gap"]], line=dict(width=0)),
                     hovertemplate="%{x|%H:%M} · %{y:,} bài<extra></extra>"))
fig.add_vline(x=t, line=dict(color=GOLD, width=3))
fig.update_layout(height=300, bargap=0.12, showlegend=False, hovermode="closest",
                  yaxis=dict(title="bài mỗi 5 phút", tickformat=","), xaxis=dict(tickformat="%H:%M"))
st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
valid = ppb[~ppb["is_gap"]]
peak = valid.sort_values("posts").iloc[-1]
first = valid.iloc[1]
insight(f"Lượng bài tăng dần khi trời sáng ở Bắc Mỹ (07:50 UTC là 02:50 giờ New York): từ {fmt_int(first['posts'])} "
        f"bài/5 phút lúc {hhmm(first['bucket'])} lên đỉnh <b>{fmt_int(peak['posts'])}</b> lúc {hhmm(peak['bucket'])}. "
        f"Các khung xám sau {hhmm(ppb[ppb['is_gap']]['bucket'].min())} là lúc bộ thu thập dừng, không phải lúc "
        "người dùng ngừng đăng.")

ticker(bursts[bursts["peak"] <= t] if not bursts.empty else bursts, onair=True)
