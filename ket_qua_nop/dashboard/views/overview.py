"""Daily and monthly issues found in the Vietnamese YouTube sample."""
from __future__ import annotations

import calendar
from collections import Counter

import pandas as pd
import streamlit as st

from dashboard import data
from dashboard.components import fmt_int, note, slug, strap


def summarize(rows: pd.DataFrame) -> dict[int, dict]:
    result = {}
    for topic_id, group in rows.groupby("topic_id"):
        words: dict[str, float] = {}
        labels: Counter[str] = Counter()
        examples = []
        channels = set()
        for row in group.itertuples():
            channels.update(row.channel_ids or [])
            if row.label and row.label != "Chủ đề chưa rõ":
                labels[row.label] += int(row.count)
            for rank, word in enumerate(row.keywords or []):
                words[word] = words.get(word, 0) + float(row.count) / (rank + 1)
            examples.extend(
                {**example, "created_at": example.get("created_at") or str(row.date)}
                for example in row.examples or []
            )
        keywords = sorted(words, key=words.get, reverse=True)[:6]
        result[int(topic_id)] = {
            "issue": labels.most_common(1)[0][0] if labels else "Chủ đề chưa rõ",
            "count": int(group["count"].sum()),
            "channel_count": len(channels),
            "keywords": keywords,
            "examples": sorted(examples, key=lambda item: item.get("view_count") or 0, reverse=True),
        }
    return result


def ranking(current: dict[int, dict], previous: dict[int, dict]) -> pd.DataFrame:
    rows = []
    for topic_id, issue in current.items():
        before = previous.get(topic_id, {}).get("count", 0)
        delta = issue["count"] - before
        rows.append({
            "Vấn đề nổi bật": issue["issue"],
            "Số bài": issue["count"],
            "Số kênh": issue["channel_count"],
            "Kỳ trước": before,
            "Tăng/giảm": f"{delta:+,}".replace(",", "."),
            "Tăng trưởng": f"{(100 * delta / before):+.0f}%" if before else ("Mới" if issue["count"] else "–"),
            "_growth": delta / before if before else float("inf"),
            "_delta": delta,
            "topic_id": topic_id,
        })
    return pd.DataFrame(rows)


issues = data.daily_issues()
slug("Vấn đề xã hội nổi bật theo thời gian",
     "Tóm tắt theo ngày hoặc tháng từ tiêu đề video từ các kênh thời sự Việt Nam. "
     "Tên vấn đề lấy từ video đại diện trong từng kỳ; từ khóa và nội dung mẫu giúp đối chiếu.")
note("Số bài và số kênh được tính cho cả cụm chủ đề. Tiêu đề minh họa không có nghĩa mọi video trong cụm đều nói về đúng một sự kiện.")
overview = data.one("overview")
last_video = pd.to_datetime(overview["last_post"], utc=True).tz_convert("Asia/Ho_Chi_Minh")
st.caption(f"Nguồn hiện tại: {fmt_int(overview['posts'])} video từ {overview['authors']} kênh; "
           f"video mới nhất lúc {last_video:%d/%m/%Y %H:%M} giờ Việt Nam. Ngày/tháng cuối chưa đủ cả kỳ.")

if issues.empty:
    st.info("Chưa có phân tích theo ngày. Hãy chạy lại bước tổng hợp cuối và nạp kết quả vào dashboard.")
    st.stop()

issues["date"] = pd.to_datetime(issues["date"])
available_days = sorted(issues["date"].dt.normalize().unique())
period = st.radio("Xem theo", ["Ngày", "Tháng"], horizontal=True, key="issue_period")
if period == "Ngày":
    selected = pd.Timestamp(st.selectbox(
        "Ngày (giờ Việt Nam)", available_days, index=len(available_days) - 1,
        format_func=lambda value: pd.Timestamp(value).strftime("%d/%m/%Y"), key="issue_day"))
    start, end = selected, selected + pd.Timedelta(days=1)
    previous_start, previous_end = start - pd.Timedelta(days=1), start
    period_name = selected.strftime("%d/%m/%Y")
else:
    available_months = sorted(issues["date"].dt.to_period("M").unique())
    month = st.selectbox("Tháng (giờ Việt Nam)", available_months,
                         index=len(available_months) - 1,
                         format_func=lambda value: f"{calendar.month_name[value.month]} {value.year}",
                         key="issue_month")
    start = month.start_time.normalize()
    end = (month + 1).start_time.normalize()
    previous_start = (month - 1).start_time.normalize()
    previous_end = start
    period_name = f"{calendar.month_name[month.month]} {month.year}"

current_rows = issues[(issues["date"] >= start) & (issues["date"] < end)]
previous_rows = issues[(issues["date"] >= previous_start) & (issues["date"] < previous_end)]
current = summarize(current_rows)
previous = summarize(previous_rows)
if not current:
    st.info("Kỳ này chưa có bài được gán chủ đề.")
    st.stop()

strap(f"{period_name}: chủ đề được đưa tin nhiều nhất trong mẫu")
popular = ranking(current, previous).sort_values(["Số bài", "topic_id"], ascending=[False, True]).head(5)
st.dataframe(popular.drop(columns=["topic_id", "_growth", "_delta"]), hide_index=True, use_container_width=True)

strap(f"{period_name}: vấn đề tăng nhanh nhất so với kỳ trước")
if not previous:
    note("Chưa có dữ liệu kỳ trước để tính mức tăng.")
else:
    movers = ranking(current, previous)
    movers = movers[(movers["Kỳ trước"] > 0) & (movers["Số bài"] >= 5) & (movers["_delta"] > 0)]
    if movers.empty:
        note("Chưa có vấn đề đủ dữ liệu ở cả hai kỳ để tính tốc độ tăng.")
    else:
        movers = movers.sort_values(["_growth", "_delta"], ascending=False).head(5)
        st.dataframe(movers.drop(columns=["topic_id", "_growth", "_delta"]),
                     hide_index=True, use_container_width=True)

if period == "Tháng":
    strap("Vấn đề dẫn đầu từng ngày trong tháng")
    daily_rows = []
    for day, group in current_rows.groupby("date"):
        daily = summarize(group)
        topic_id, issue = max(daily.items(), key=lambda item: item[1]["count"])
        daily_rows.append({"Ngày": day.strftime("%d/%m/%Y"), "Vấn đề nổi bật": issue["issue"],
                           "Số bài": issue["count"]})
    st.dataframe(pd.DataFrame(daily_rows), hide_index=True, use_container_width=True)

strap("Bài và video minh họa")
issue_options = sorted(current, key=lambda topic_id: current[topic_id]["count"], reverse=True)
chosen = st.selectbox("Chọn vấn đề", issue_options,
                      format_func=lambda topic_id: current[topic_id]["issue"], key="issue_example")
issue = current[chosen]
note("Từ khóa đặc trưng: " + (", ".join(issue["keywords"]) or "chưa đủ từ khóa để đặt tên rõ ràng"))
shown = 0
for example in issue["examples"]:
    text = str(example.get("text", "")).strip()
    if not text:
        continue
    created = pd.to_datetime(example["created_at"], utc=True).tz_convert("Asia/Ho_Chi_Minh").strftime("%d/%m/%Y %H:%M")
    st.markdown(f"**{example.get('author', '')} · {created} giờ Việt Nam**")
    views, likes = example.get("view_count"), example.get("like_count")
    st.caption(f"Lượt xem: {fmt_int(views) if views is not None else 'không có số liệu'} · "
               f"Lượt thích: {fmt_int(likes) if likes is not None else 'không có số liệu'} · số tích lũy lúc crawl")
    st.write(text[:700] + ("…" if len(text) > 700 else ""))
    post_id = str(example.get("post_id", ""))
    if post_id.startswith("youtube:video:"):
        video_id = post_id.rsplit(":", 1)[-1]
        st.markdown(f"[Mở video trên YouTube](https://www.youtube.com/watch?v={video_id})")
    shown += 1
    if shown == 3:
        break

note("Mức tăng so với ngày hoặc tháng liền trước, tính trên cùng cụm chủ đề. "
     "Nhãn dựa trên tiêu đề video đại diện, không phải khẳng định rằng toàn xã hội chỉ thảo luận các vấn đề này. "
     "Dữ liệu được chọn theo kênh báo/đài; mức độ đưa tin trong mẫu không đại diện toàn bộ Việt Nam.")
