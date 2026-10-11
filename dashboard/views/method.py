"""Dữ liệu & Phương pháp – the evidence behind every number: data-quality
funnel, language mix, experiment registry, model choice, scalability."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard import data
from dashboard.components import fmt_int, fmt_pct, html, insight, note, slug, strap, strip, sub, table
from dashboard.theme import GOLD, INK, PLOTLY_CONFIG, SERIES

dq = data.one("data_quality")
info = data.one("model_info")
reg = data.frame("experiment_results")
scal = data.frame("scalability")
eda = data.one("eda_distributions")

slug("Dữ liệu và phương pháp",
     "Mọi con số trên dashboard đều đi qua pipeline HDFS → Spark → MongoDB. Trang này là bằng chứng: dữ liệu "
     "đã bị loại ở đâu, mô hình được chọn ra sao, và cụm Spark xử lý nhanh tới mức nào.")

strap("Phễu chất lượng dữ liệu")
RULE_VI = {
    "Raw records": ("Bản ghi thô", "JSONL trên HDFS"),
    "Corrupt / parse error (JSON)": ("Lỗi đọc JSON / thời gian không hợp lệ", ""),
    "Duplicate post (uri)": ("Bản ghi trùng (cùng uri)", "uri là khóa duy nhất của bản ghi YouTube"),
    "Missing / empty text": ("Không có nội dung chữ", "bản ghi không có văn bản"),
    "Missing timestamp": ("Thiếu thời gian đăng", ""),
    "Timestamp outside collection window": ("Ngoài khung thu thập", "thời gian nằm ngoài khoảng đã cấu hình"),
    "Non-Vietnamese / unknown language": ("Không phải tiếng Việt", "fastText lid.176, độ tin cậy ≥ 0,5"),
    "Clean dataset for volume statistics": ("Tập sạch cho thống kê", ""),
    "Duplicate text (normalised)": ("Trùng nội dung (sau chuẩn hóa)", "chỉ loại khỏi tập huấn luyện"),
    "Clean dataset for model": ("Tập sạch cho mô hình", ""),
}


def rule_vi(rule: str) -> tuple[str, str]:
    if rule.startswith("Text too short"):
        return "Quá ngắn (< 3 từ sau khi bỏ stopwords)", ""
    return RULE_VI.get(rule, (rule, ""))


raw = dq["raw_records"]
steps = []
for r in dq["rules"]:
    name, why = rule_vi(r["rule"])
    if r["note"] == "checkpoint":
        steps.append(f'<div class="step total"><div class="name">{name}</div><div class="bar">'
                     f'<i style="width:{100 * r["after"] / raw:.1f}%"></i></div>'
                     f'<div class="num">{fmt_int(r["after"])}</div></div>')
        continue
    removed = r["removed"] or 0
    stamp = '<b class="void">HỦY</b>' if removed else ""
    steps.append(
        f'<div class="step"><div class="name">{name}{stamp}<span>{why}</span></div>'
        f'<div class="bar"><i style="width:{100 * r["after"] / raw:.1f}%"></i>'
        f'<em style="left:{100 * r["after"] / raw:.1f}%;width:{100 * removed / raw:.2f}%"></em></div>'
        f'<div class="num">{fmt_int(r["after"])}<span>−{fmt_int(removed)}</span></div></div>')
html(f'<div class="funnel">{"".join(steps)}</div>')
insight(f"Từ {fmt_int(raw)} bản ghi thô còn <b>{fmt_int(dq['clean_volume'])}</b> bản ghi cho thống kê "
        f"({fmt_pct(dq['retention_volume_pct'] / 100)}) và <b>{fmt_int(dq['clean_model'])}</b> bản ghi cho mô hình "
        f"({fmt_pct(dq['retention_model_pct'] / 100)}).")
note("Bản ghi bị loại không biến mất: mỗi bước được đóng dấu HỦY kèm số lượng, theo đúng thứ tự thực thi trong "
     "src/etl/clean.py. Bài trùng nội dung chỉ bị loại khỏi tập huấn luyện, vẫn được đếm trong thống kê.")

left, right = st.columns([1, 1], gap="large")
with left:
    sub("Ngôn ngữ trong tập dữ liệu hợp lệ")
    lang = pd.DataFrame(dq["language_distribution"]).head(10).iloc[::-1]
    fig = go.Figure(go.Bar(x=lang["share_pct"] / 100, y=lang["lang"], orientation="h",
                           marker=dict(color=["#3987e5" if l == "vi" else "#2F4A80" for l in lang["lang"]],
                                       line=dict(width=0)),
                           text=[fmt_pct(v / 100) for v in lang["share_pct"]], textposition="outside",
                           textfont=dict(color=INK, size=15), hovertemplate="%{y}: %{x:.1%}<extra></extra>",
                           cliponaxis=False))
    fig.update_layout(height=400, showlegend=False, hovermode="closest",
                      xaxis=dict(visible=False, range=[0, float(lang["share_pct"].max()) / 100 * 1.2]),
                      yaxis=dict(tickfont=dict(size=16, color=INK)), margin=dict(r=8))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    note("Nhận diện bằng fastText lid.176, giữ bản ghi tiếng Việt có độ tin cậy ≥ 0,5. “unknown”: quá ngắn để nhận diện.")
with right:
    sub("Mức độ hoạt động của tài khoản")
    act = pd.DataFrame(eda.get("author_activity", []))
    order = ["1", "2-5", "6-20", "21-100", ">100"]
    act["o"] = act["posts_per_author"].map({k: i for i, k in enumerate(order)})
    act = act.sort_values("o")
    fig = go.Figure(go.Bar(x=act["posts_per_author"], y=act["count"], marker=dict(color="#3987e5", line=dict(width=0)),
                           text=[fmt_int(c) for c in act["count"]], textposition="outside",
                           textfont=dict(color=INK, size=15), hovertemplate="%{x} bài: %{y:,} tài khoản<extra></extra>",
                           cliponaxis=False))
    fig.update_layout(height=400, showlegend=False, hovermode="closest", yaxis=dict(visible=False),
                      xaxis=dict(title="số bản ghi mỗi tác giả trong khung thu thập", type="category"))
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    note(f"{dq['high_activity_accounts']} tài khoản đăng hơn {int(dq['high_activity_threshold_posts'])} bài được gắn "
         "cờ hoạt động cao (top 0,1%) – chỉ gắn cờ, không gọi là bot và không loại bỏ.")

strap("Thực nghiệm và lựa chọn mô hình")
if reg.empty:
    note("Chưa có kết quả thực nghiệm.")
else:
    view = reg.copy()
    for c in ("k", "npmi", "silhouette", "perplexity", "max_topic_share", "runtime_s"):
        view[c] = pd.to_numeric(view[c], errors="coerce")
    shown = pd.DataFrame({
        "ID": view["id"], "Thí nghiệm": view["exp"], "Dữ liệu": view["data"], "Mô hình": view["model"],
        "k": view["k"].astype("Int64"), "Stopwords miền": view["domain_sw"], "N-gram": view["ngram"],
        "NPMI ↑": view["npmi"].map(lambda v: f"{v:.3f}" if pd.notna(v) else "–"),
        "Silhouette": view["silhouette"].map(lambda v: f"{v:.3f}" if pd.notna(v) else "–"),
        "Log-perplexity": view["perplexity"].map(lambda v: f"{v:.2f}" if pd.notna(v) else "–"),
        "Cụm lớn nhất": view["max_topic_share"].map(lambda v: fmt_pct(v) if pd.notna(v) else "–"),
        "Thời gian (s)": view["runtime_s"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "–"),
    })
    best = view.index[view["id"] == info.get("run_id")]
    table(shown, num_cols={"k", "NPMI ↑", "Silhouette", "Log-perplexity", "Cụm lớn nhất", "Thời gian (s)"},
          best_index=best[0] if len(best) else None, best_tag="MÔ HÌNH CUỐI")
    note("NPMI dùng chung một tập tham chiếu nên so được giữa mọi mô hình. Silhouette chỉ so được giữa các k trong "
         "cùng một không gian đặc trưng; perplexity chỉ so được giữa các LDA cùng từ vựng (kế hoạch, mục 11.5). "
         "Dòng tô đậm là mô hình cuối.")

    sample = view[view["data"] == "sample_20"]
    fig = go.Figure()
    sweep = sample[sample["exp"].isin(["Exp3", "Exp1", "Exp6"])]
    sweep = sweep[sweep.groupby("model")["k"].transform("nunique") >= 2]
    for i, (model, g) in enumerate(sweep.groupby("model")):
        g = g.sort_values("k")
        fig.add_trace(go.Scatter(x=g["k"], y=g["npmi"], mode="lines+markers", name=model,
                                 line=dict(color=SERIES[i], width=2.5), marker=dict(size=10)))
    fig.update_layout(height=360, xaxis=dict(title="số chủ đề k", dtick=5), yaxis=dict(title="NPMI"),
                      hovermode="closest")
    sub("NPMI theo số chủ đề k (mẫu 20%, có stopwords miền)")
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    base = view[(view["exp"] == "Baseline")]
    w2v = view[view["model"] == "Word2Vec+KMeans"]
    if not base.empty and not w2v.empty:
        km0 = base[base["model"] == "KMeans"].iloc[0]
        insight(f"TF-IDF + KMeans gốc dồn <b>{fmt_pct(km0['max_topic_share'])}</b> số bài vào một cụm (NPMI "
                f"{km0['npmi']:.3f}). Đổi sang biểu diễn Word2Vec, NPMI tốt nhất đạt <b>{w2v['npmi'].max():.3f}</b> "
                f"và cụm lớn nhất chỉ còn {fmt_pct(w2v.loc[w2v['npmi'].idxmax(), 'max_topic_share'])}.")

strap("Khả năng mở rộng của cụm Spark")
if scal.empty:
    note("Chưa chạy thí nghiệm khả năng mở rộng (src/model/scalability.py).")
else:
    g = scal.groupby(["workers", "fraction"]).agg(runtime=("runtime_s", "mean"), sd=("runtime_s", "std"),
                                                 docs=("docs", "max"), tasks=("tasks", "max"),
                                                 shuffle=("shuffle_write_mb", "max")).reset_index()
    fig = go.Figure()
    for i, (w, gg) in enumerate(g.groupby("workers")):
        fig.add_trace(go.Scatter(x=gg["docs"], y=gg["runtime"], error_y=dict(type="data", array=gg["sd"].fillna(0)),
                                 mode="lines+markers", name=f"{w} worker", line=dict(color=SERIES[i], width=2.5),
                                 marker=dict(size=10), hovertemplate="%{x:,} bài · %{y:.0f}s<extra></extra>"))
    fig.update_layout(height=360, xaxis=dict(title="số bài xử lý", tickformat=","), yaxis=dict(title="giây (TB ± độ lệch)"),
                      hovermode="closest")
    st.plotly_chart(fig, config=PLOTLY_CONFIG, use_container_width=True)
    table(pd.DataFrame({"Worker": g["workers"], "Tỷ lệ dữ liệu": g["fraction"].map(lambda f: fmt_pct(f, 0)),
                        "Số bài": g["docs"].map(fmt_int), "Thời gian TB (s)": g["runtime"].map(lambda v: f"{v:.1f}"),
                        "Task": g["tasks"], "Shuffle write (MB)": g["shuffle"]}),
          num_cols={"Số bài", "Thời gian TB (s)", "Task", "Shuffle write (MB)"})
    full = g[g["fraction"] == g["fraction"].max()].set_index("workers")["runtime"]
    small = g[g["fraction"] == g["fraction"].min()].set_index("workers")["runtime"]
    if len(full) >= 2:
        w_lo, w_hi = full.index.min(), full.index.max()
        growth = full[w_hi] / small[w_hi]
        size_ratio = g["docs"].max() / g["docs"].min()
        insight(f"Dữ liệu tăng {size_ratio:.0f} lần nhưng thời gian chỉ tăng {growth:.1f} lần".replace(".", ",")
                + f", và {w_hi} worker chỉ nhanh hơn {w_lo} worker "
                f"{fmt_pct(1 - full[w_hi] / full[w_lo])} ở toàn bộ dữ liệu. Với quy mô dữ liệu hiện tại, chi phí cố định "
                "(khởi động JVM, lập lịch job, các vòng lặp KMeans trên driver) chiếm phần lớn thời gian, và hai worker "
                "dùng chung CPU của một laptop, nên thêm worker gần như không có lợi ở quy mô này.")
    note("Mọi worker chạy trên cùng một laptop: đây là cụm logic để quan sát cách Spark chia job/stage/task, "
         "không phải benchmark của nhiều máy vật lý độc lập. Mỗi cấu hình chạy 3 lần; thanh lỗi là độ lệch chuẩn. "
         f"“Số bài” ở 100% là {fmt_int(g['docs'].max())}, ít hơn tập mô hình {fmt_int(dq['clean_model'])} vì thí nghiệm "
         "bỏ các bài không còn từ nào sau khi lọc stopwords miền và từ vựng TF-IDF.")
