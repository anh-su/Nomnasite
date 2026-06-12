import base64
from pathlib import Path
import streamlit as st

_BG_PATH = Path(__file__).parent / "imgs" / "background.webp"

@st.cache_data(show_spinner=False)
def bg_css() -> str:
    """CSS nhúng background.webp — cache sau lần đọc file đầu tiên."""
    try:
        b64 = base64.b64encode(_BG_PATH.read_bytes()).decode()
        return f"""<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/webp;base64,{b64}");
    background-size: 25%;
    background-repeat: repeat;
    background-attachment: fixed;
}}
</style>"""
    except Exception:
        return ""
