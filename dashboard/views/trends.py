"""Diễn biến – how every topic rose and fell through the day: stacked share,
fixed-scale small multiples, and the BREAKING log."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard import data, state
from dashboard.components import burst_log, fmt_pct, hhmm, insight, note, num, slug, story, strap, sub
from dashboard.theme import GOLD, INK_2, OTHER, PLOTLY_CONFIG, SERIES, topic_color

topics = data.topics()
trend = data.trend()
trend = trend[~trend["in_gap"]]
bursts = data.bursts()
cfg = data.one("model_info").get("config_trend", {})

slug("Diễn biến trong ngày",
     "Tỷ trọng của từng chủ đề theo khung 5 phút. Một khung được gọi là bùng nổ khi tỷ trọng vượt trung bình "
     f"60 phút trước đó hơn {num(cfg.get('burst_zscore_threshold', 2.5))} độ lệch chuẩn, cao hơn mức nền ít nhất "
     f"{int(round(100 * (cfg.get('burst_min_lift', 1.2) - 1)))}% và có ít nhất {cfg.get('burst_min_volume', 100)} bài.")

t = state.scrubber()

strap("Cơ cấu chủ đề theo thời gian")
order = topics.sort_values("size_rank")
named = order[order["size_rank"] < len(SERIES)]
folded = order[order["size_rank"] >= len(SERIES)]
fig = go.Figure()
for r in named.itertuples():
    tt = trend[trend["topic_id"] == r.topic_id].sort_values("bucket")
    fig.add_trace(go.Scatter(x=tt["bucket"], y=tt["ratio"], name=r.topic_label, stackgroup="one", mode="lines",
                             line=dict(width=0.5, color="#0B1B3A"), fillcolor=topic_color(int(r.size_rank)),
                             hovertemplate=f"{r.topic_label}: %{{y:.1%}}<extra></extra>"))
if not folded.empty:
    other = trend[trend["topic_id"].isin(folded["topic_id"])].groupby("bucket")["ratio"].sum().reset_index()
    fig.add_trace(go.Scatter(x=other["bucket"], y=other["ratio"], name=f"Khác ({len(folded)} chủ đề)",
                             stackgroup="one", mode="lines", line=dict(width=0.5, color="#0B1B3A"), fillcolor=OTHER,
                             hovertemplate="Khác: %{y:.1%}<extra></extra>"))
fig.add_vline(x=t, line=dict(color=GOLD, width=3))
fig.update_layout(height=430, yaxis=dict(tickformat=".0%", range=[0, 1], title="tỷ trọng"),
                  xaxis=dict(tickformat="%H:%M"), legend=dict(y=-0.18))
st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)

first_bin, last_bin = trend["bucket"].min(), trend["bucket"].max()
start = trend[trend["bucket"] == first_bin].set_index("topic_id")["ratio"]
end = trend[trend["bucket"] == last_bin].set_index("topic_id")["ratio"]
gain = (end - start).dropna()
up, down = gain.idxmax(), gain.idxmin()
lab = topics.set_index("topic_id")["topic_label"]
insight(f"Từ {hhmm(first_bin)} tới {hhmm(last_bin)}, {story(lab[up])} tăng từ {fmt_pct(start[up])} lên "
        f"{fmt_pct(end[up])}, còn {story(lab[down])} giảm từ {fmt_pct(start[down])} xuống {fmt_pct(end[down])}.")

strap("Từng chủ đề, cùng một thang đo")
ymax = float(trend["ratio"].max()) * 1.08
x0, x1 = trend["bucket"].min(), trend["bucket"].max()
items = list(order.itertuples())
for start_i in range(0, len(items), 3):
    cols = st.columns(3, gap="medium")
    for col, r in zip(cols, items[start_i:start_i + 3]):
        tt = trend[trend["topic_id"] == r.topic_id].sort_values("bucket")
        fig = go.Figure(go.Scatter(x=tt["bucket"], y=tt["ratio"], mode="lines", showlegend=False,
                                   line=dict(color=topic_color(int(r.size_rank)), width=2),
                                   hovertemplate=f"%{{x|%H:%M}} · %{{y:.1%}}<extra></extra>"))
        tb = bursts[bursts["topic_id"] == r.topic_id] if not bursts.empty else bursts
        for e in tb.itertuples():
            fig.add_vrect(x0=e.start, x1=e.end + pd.Timedelta(minutes=5), fillcolor="#D41E35", opacity=0.3,
                          line_width=0)
        fig.update_layout(height=190, hovermode="closest", margin=dict(l=8, r=8, t=8, b=8),
                          yaxis=dict(range=[0, ymax], tickformat=".0%", nticks=4),
                          xaxis=dict(range=[x0, x1], tickformat="%H:%M", nticks=5))
        with col:
            sub(r.topic_label)
            st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
note("Mọi ô dùng chung trục tung từ 0 đến tỷ trọng lớn nhất trong ngày, nên chiều cao so sánh trực tiếp được. "
     "Vùng đỏ là sự kiện bùng nổ.")

strap("Nhật ký bùng nổ")
if bursts.empty:
    note("Không có khung nào vượt ngưỡng bùng nổ với cấu hình hiện tại.")
else:
    top = bursts.sort_values("max_burst_score", ascending=False).iloc[0]
    insight(f"Có <b>{len(bursts)}</b> sự kiện bùng nổ. Mạnh nhất: {story(top['topic_label'])} lúc "
            f"<b>{hhmm(top['peak'])}</b>, tỷ trọng {fmt_pct(top['peak_ratio'])} so với mức nền "
            f"{fmt_pct(top['baseline_ratio'])} (z = {num(top['max_burst_score'])}).")
    burst_log(bursts.sort_values("peak"))
