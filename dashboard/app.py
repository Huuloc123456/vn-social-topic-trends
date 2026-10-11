"""Dashboard xu hướng chủ đề YouTube – Streamlit entry point.

    streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dashboard import data, state  # noqa: E402
from dashboard.components import html  # noqa: E402
from dashboard.theme import page_css  # noqa: E402

st.set_page_config(page_title="YouTube Việt Nam – Xu hướng chủ đề", layout="wide", initial_sidebar_state="collapsed")
html(page_css())

PAGES = [
    st.Page("views/overview.py", title="Bảng điểm", url_path="bang-diem", default=True),
    st.Page("views/topics.py", title="Các câu chuyện", url_path="cau-chuyen"),
    st.Page("views/trends.py", title="Diễn biến", url_path="dien-bien"),
    st.Page("views/keywords.py", title="Từ khóa & Hashtag", url_path="tu-khoa"),
    st.Page("views/analyzer.py", title="Phân tích văn bản", url_path="phan-tich"),
    st.Page("views/method.py", title="Dữ liệu & Phương pháp", url_path="phuong-phap"),
]
nav = st.navigation(PAGES, position="hidden")
# Streamlit 1.39 marks the current page link only with a generated class, so
# the on-air tab slab is keyed on the link's href instead.
html(f'<style>.st-key-segrow a[href="{nav.url_path}"] {{ background:var(--ink) !important; }}'
     f'.st-key-segrow a[href="{nav.url_path}"] p {{ color:var(--bg) !important; }}</style>')

if not data.available():
    html('<div class="rundown"><div class="show"><b>YouTube Việt Nam</b></div></div>')
    st.error("Chưa có dữ liệu trong MongoDB. Chạy pipeline (README, mục 'Chạy toàn bộ pipeline') rồi tải lại trang.")
    st.stop()

t = state.current_time()
html(
    '<div class="rundown">'
    '<div class="show"><span class="live"><i></i>Phát lại</span>'
    '<div><b>YouTube Việt Nam</b><br><span>Video và bình luận tiếng Việt</span></div></div>'
    f'<div class="clock"><b>{t:%H:%M}</b><span>giờ UTC đang xem</span></div>'
    '</div>'
)

with st.container(key="segrow"):
    cols = st.columns(len(PAGES) + 1, gap="small", vertical_alignment="center")
    for col, page in zip(cols[:-1], PAGES):
        with col:
            st.page_link(page, label=page.title)
    with cols[-1]:
        st.toggle("Trình chiếu", value=state.safe_mode(), key="safe",
                  help="Chế độ trình chiếu: ẩn bài đăng và hashtag 18+, che từ chửi thề trên màn hình. "
                       "Số liệu thống kê không thay đổi.")

nav.run()
