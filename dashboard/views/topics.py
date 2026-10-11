"""Các câu chuyện – the rundown of topics; pick one to open its file:
keywords, size, peak, bursts and representative posts."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from dashboard import data, state
from dashboard.components import (
    burst_log,
    fmt_int,
    fmt_pct,
    hhmm,
    insight,
    note,
    quotes,
    scoreboard,
    shown,
    slug,
    story,
    strap,
    strip,
    sub,
)
from dashboard.theme import GOLD, PLOTLY_CONFIG, RULE, topic_color

topics = data.topics()
info = data.one("model_info")
trend = data.trend()
bursts = data.bursts()

slug("Các câu chuyện trong ngày",
     f"{len(topics)} chủ đề do mô hình {info.get('model', '')} tìm ra trên {fmt_int(info.get('posts_assignable', 0))} "
     f"bài gán được chủ đề (trong {fmt_int(info.get('posts_scored', 0))} bài hợp lệ; số còn lại không có từ nào "
     "trong từ vựng của mô hình). Xếp theo tỷ trọng cả ngày; chọn một chủ đề để mở hồ sơ.")

labels = {int(r.topic_id): r.topic_label for r in topics.itertuples()}
scoreboard(topics.assign(value=topics["share"]), "value",
           selected=st.session_state.get("topic_pick", int(topics.iloc[0]["topic_id"])))
lead = topics.iloc[0]
smallest = topics.iloc[-1]
insight(f"Chủ đề lớn nhất là {story(lead['topic_label'])} ({fmt_pct(lead['share'])}), nhỏ nhất là "
        f"{story(smallest['topic_label'])} ({fmt_pct(smallest['share'])}). Không chủ đề nào chiếm quá "
        f"{fmt_pct(topics['share'].max(), 0)}, nên mô hình không dồn dữ liệu vào một cụm rác.")

strap("Hồ sơ chủ đề")
chosen = st.selectbox("Chủ đề", list(labels), format_func=lambda i: labels[i], key="topic_pick")
row = topics.set_index("topic_id").loc[chosen]
color = topic_color(int(row["size_rank"]))

topic_bursts = bursts[bursts["topic_id"] == chosen] if not bursts.empty else bursts
strip([
    ("tỷ trọng cả ngày", fmt_pct(row["share"])),
    ("số bài (ước tính)", fmt_int(row["size"])),
    ("đỉnh trong ngày", f"{hhmm(row['peak_bucket'])} · {fmt_pct(row['peak_ratio'])}"),
    ("sự kiện bùng nổ", str(len(topic_bursts))),
    ("độ mạch lạc NPMI", f"{row['npmi']:.3f}".replace(".", ",")),
])

left, right = st.columns([1, 1.25], gap="large")
with left:
    sub("Từ khóa đặc trưng")
    kws = [shown(k) for k in row["keywords"] if not state.safe_mode() or data.is_safe_term(k)]
    weights = list(range(len(kws), 0, -1))
    fig = go.Figure(go.Bar(x=weights, y=kws, orientation="h", marker=dict(color=color, line=dict(width=0)),
                           text=kws, textposition="inside", insidetextanchor="start",
                           textfont=dict(size=17, color="#FFFFFF"), hoverinfo="skip", cliponaxis=False))
    fig.update_layout(height=40 * len(kws) + 20, showlegend=False, bargap=0.18,
                      xaxis=dict(visible=False), yaxis=dict(visible=False, autorange="reversed"))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    note("Thứ hạng từ khóa, từ trên xuống. Với Word2Vec + KMeans, từ khóa được xếp bằng c-TF-IDF: "
         "từ xuất hiện nhiều trong chủ đề này nhưng hiếm ở các chủ đề khác.")

with right:
    sub("Diễn biến trong ngày")
    tt = trend[trend["topic_id"] == chosen].sort_values("bucket")
    tt = tt[~tt["in_gap"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tt["bucket"], y=tt["ratio"], mode="lines", line=dict(color=color, width=2.5),
                             name=row["topic_label"], hovertemplate="%{x|%H:%M} · %{y:.1%}<extra></extra>"))
    for e in topic_bursts.itertuples():
        fig.add_vrect(x0=e.start, x1=e.end + (tt["bucket"].iloc[1] - tt["bucket"].iloc[0]),
                      fillcolor="#D41E35", opacity=0.22, line_width=0)
    fig.update_layout(height=320, showlegend=False, yaxis=dict(tickformat=".0%", title="tỷ trọng / 5 phút",
                                                               rangemode="tozero"),
                      xaxis=dict(tickformat="%H:%M"))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    insight(f"{story(row['topic_label'])} đạt đỉnh lúc <b>{hhmm(row['peak_bucket'])}</b> với "
            f"{fmt_pct(row['peak_ratio'])} số bài của khung 5 phút đó. Vùng đỏ là các sự kiện bùng nổ.")
    if not topic_bursts.empty:
        burst_log(topic_bursts)

sub("Bài đăng tiêu biểu (gần tâm cụm nhất)")
posts = data.representative(chosen)
if posts.empty:
    note("Chưa có bài tiêu biểu cho chủ đề này.")
else:
    quotes(posts.head(8))
    note("Mỗi nội dung chỉ lấy một lần (bỏ bản sao spam). Bài có nội dung 18+ không bao giờ được chọn làm bài "
         "tiêu biểu, nhưng vẫn được tính trong mọi thống kê.")
