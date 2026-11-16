"""Shared session state: one time scrubber drives every page and presentation mode."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import data

KEY = "scrub"


def bins() -> list[pd.Timestamp]:
    """Valid daily bins, excluding collection gaps."""
    tr = data.trend()
    valid = tr[~tr["in_gap"]]["bucket"].drop_duplicates().sort_values()
    return list(valid)


def current_time() -> pd.Timestamp:
    """Return the selected timestamp while keeping only its integer index in the widget."""
    b = bins()
    value = st.session_state.get(KEY, st.session_state.get("t_keep"))
    if isinstance(value, int) and not isinstance(value, bool) and 0 <= value < len(b):
        index = value
    else:
        kept = st.session_state.get("t_keep")
        index = b.index(kept) if kept in b else len(b) - 1
    selected = b[index]
    # The timestamp mirror survives Streamlit pages where the slider is absent.
    st.session_state["t_keep"] = selected
    return selected


def scrubber() -> pd.Timestamp:
    selected = current_time()
    options = bins()
    if len(options) == 1:
        st.caption(f"Chỉ có một mốc dữ liệu: {selected:%d/%m/%Y %H:%M} giờ Việt Nam")
        return selected
    index = st.slider(
        "Chọn thời điểm (giờ Việt Nam)",
        min_value=0,
        max_value=len(options) - 1,
        value=options.index(selected),
        step=1,
        format="%d",
        key=KEY,
        help="Kéo để xem dữ liệu tại từng ngày. Ngày/tháng hiển thị theo giờ Việt Nam.",
    )
    selected = options[index]
    st.session_state["t_keep"] = selected
    st.caption(f"Mốc đang chọn: {selected:%d/%m/%Y %H:%M} giờ Việt Nam")
    return selected


def safe_mode() -> bool:
    return st.session_state.get("safe", True)
