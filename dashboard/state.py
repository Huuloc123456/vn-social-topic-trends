"""Shared session state: the day scrubber (one control drives every page) and
presentation mode."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import data

KEY = "scrub"


def bins() -> list[pd.Timestamp]:
    """Valid 5-minute bins (collection gaps at the tail are excluded)."""
    tr = data.trend()
    valid = tr[~tr["in_gap"]]["bucket"].drop_duplicates().sort_values()
    return list(valid)


def current_time() -> pd.Timestamp:
    """The scrubbed time. Read from the widget key, so the clock in the
    rundown bar (drawn before the page) already shows the new value."""
    b = bins()
    # Streamlit drops a widget's key on pages that do not draw it, so the
    # value is mirrored in a plain key that survives page switches.
    value = st.session_state.get(KEY, st.session_state.get("t_keep"))
    if value not in b:
        value = b[-1]
    st.session_state[KEY] = value
    st.session_state["t_keep"] = value
    return value


def scrubber() -> pd.Timestamp:
    current_time()
    return st.select_slider(
        "Chọn thời điểm (giờ UTC) – kéo để xem bảng điểm tại từng thời điểm",
        options=bins(), format_func=lambda x: x.strftime("%H:%M"), key=KEY,
    )


def safe_mode() -> bool:
    return st.session_state.get("safe", True)
