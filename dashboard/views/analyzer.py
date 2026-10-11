"""Phân tích văn bản – the model calls the story of a sentence you type:
KMeans gives one nearest topic (hard), LDA gives a distribution (soft)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from dashboard import data, inference
from dashboard.components import fmt_pct, html, insight, note, num, slug, strap, sub
from dashboard.theme import INK, PLOTLY_CONFIG, RULE, topic_color

topics = data.topics().set_index("topic_id")

slug("Phân tích văn bản mới",
     "Nhập một đoạn tiếng Việt. Mô hình chính (Word2Vec + KMeans) chọn chủ đề gần nhất; mô hình phụ LDA cho biết "
     "câu đó trải trên các chủ đề với tỷ lệ bao nhiêu.")

EXAMPLES = {
    "Công nghệ": "Trí tuệ nhân tạo đang thay đổi cách mọi người học tập và làm việc",
    "Giải trí": "Bộ phim Việt Nam mới có diễn xuất và phần nhạc phim rất ấn tượng",
    "Thể thao": "Đội tuyển Việt Nam chuẩn bị cho trận đấu quan trọng cuối tuần này",
    "Giáo dục": "Học sinh cần được hướng dẫn kỹ năng học tập và chọn ngành phù hợp",
}
if "analyzer_text" not in st.session_state:
    st.session_state["analyzer_text"] = EXAMPLES["Công nghệ"]
ex_cols = st.columns(len(EXAMPLES))
for col, (name, txt) in zip(ex_cols, EXAMPLES.items()):
    if col.button(f"Ví dụ: {name}", key=f"ex_{name}", use_container_width=True):
        st.session_state["analyzer_text"] = txt
text = st.text_area("Văn bản cần phân tích", key="analyzer_text", height=110, max_chars=600)

if not inference.model_ready():
    st.warning("Chưa có bản sao mô hình cục bộ trong thư mục models/. Chạy bước finalize của pipeline.")
    st.stop()
if not text.strip():
    note("Nhập một câu để bắt đầu.")
    st.stop()

with st.spinner("Đang chạy pipeline Spark trên câu này…"):
    res = inference.analyze(text)

km = res["kmeans"]
strap("Mô hình chính · KMeans: một chủ đề gần nhất")
if not km or km.get("empty"):
    insight("Không từ nào của câu này nằm trong từ vựng của mô hình (sau khi bỏ stopwords), nên không gán được "
            "chủ đề. Thử một câu dài hơn hoặc dùng từ phổ biến hơn.")
else:
    tid = km["topic"]
    color = topic_color(int(topics.loc[tid, "size_rank"]))
    sims = km["similarities"]
    ranked = sorted(range(len(sims)), key=lambda i: -sims[i])
    runner = ranked[1]
    html(f'<div class="call"><b>{topics.loc[tid, "topic_label"]}</b>'
         f'<span>Mô hình chọn chủ đề này · cosine tới tâm cụm <em>{num(sims[tid], 2)}</em> · cách chủ đề kế tiếp '
         f'({topics.loc[runner, "topic_label"]}) <em>{num(sims[tid] - sims[runner], 2)}</em></span></div>')
    win_color = color if int(topics.loc[tid, "size_rank"]) < 7 else "#C5D3EE"
    left, right = st.columns([1.2, 1], gap="large")
    with left:
        sub("Độ gần tới tâm từng chủ đề")
        order = ranked[:8][::-1]
        fig = go.Figure(go.Bar(
            x=[sims[i] for i in order], y=[topics.loc[i, "topic_label"] for i in order], orientation="h",
            marker=dict(color=[win_color if i == tid else "#2F4A80" for i in order], line=dict(width=0)),
            text=[num(sims[i], 2) for i in order], textposition="outside", textfont=dict(color=INK, size=15),
            hovertemplate="%{y}: %{x:.3f}<extra></extra>", cliponaxis=False))
        fig.update_layout(height=380, showlegend=False, hovermode="closest",
                          xaxis=dict(title="cosine similarity", range=[min(0, min(sims)), max(sims) * 1.3]),
                          yaxis=dict(tickfont=dict(size=16, color=INK)), margin=dict(r=50))
        st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    with right:
        sub("Từ nào kéo câu về chủ đề này")
        pulls = km["pulls"][:8]
        if pulls:
            rows = "".join(f"<tr><td>{w}</td><td class='num'>{num(s, 2)}</td></tr>" for w, s in pulls)
            html(f"<table class='tbl'><thead><tr><th>Từ</th><th class='num'>Cosine tới tâm</th></tr></thead>"
                 f"<tbody>{rows}</tbody></table>")
        dropped = [t for t in res["tokens"] if t not in {w for w, _ in km["pulls"]}]
        if dropped:
            note("Không có trong từ vựng Word2Vec (bỏ qua): " + ", ".join(dropped[:12]))
    note("Đây là khoảng cách hình học, không phải xác suất: KMeans chỉ biết câu này gần tâm cụm nào nhất.")

lda = res["lda"]
strap("Mô hình phụ · LDA: phân bố chủ đề")
if lda is None:
    note("Chưa có mô hình LDA phụ trong models/secondary.")
elif lda["empty"]:
    insight("Không từ nào của câu nằm trong từ vựng LDA, nên phân bố bằng đều và không mang thông tin.")
else:
    theta = lda["theta"]
    labels = lda["labels"]
    order = sorted(range(len(theta)), key=lambda i: -theta[i])
    top = order[:6]
    fig = go.Figure(go.Bar(x=[theta[i] for i in top][::-1], y=[labels.get(i, f"LDA {i}") for i in top][::-1],
                           orientation="h", marker=dict(color="#9085e9", line=dict(width=0)),
                           text=[fmt_pct(theta[i]) for i in top][::-1], textposition="outside",
                           textfont=dict(color=INK, size=15), hovertemplate="%{y}: %{x:.1%}<extra></extra>",
                           cliponaxis=False))
    fig.update_layout(height=320, showlegend=False, hovermode="closest",
                      xaxis=dict(tickformat=".0%", range=[0, max(theta) * 1.25]),
                      yaxis=dict(tickfont=dict(size=16, color=INK)), margin=dict(r=60))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    insight(f"LDA xem câu này là <b>{fmt_pct(theta[order[0]])}</b> “{labels.get(order[0], order[0])}” và "
            f"{fmt_pct(theta[order[1]])} “{labels.get(order[1], order[1])}”: một câu có thể thuộc nhiều chủ đề, "
            "khác với cách KMeans chỉ chọn một.")
    note("Chủ đề LDA được học riêng nên không trùng khớp một-một với chủ đề KMeans; nhãn là ba từ khóa đầu.")
