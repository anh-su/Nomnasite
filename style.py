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


custom_css = '''
    <style>
        .block-container > div >
        [data-testid="stVerticalBlock"] >
        [data-testid="stHorizontalBlock"] >
        [data-testid="column"]:nth-of-type(1) {
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.25rem;
            padding: calc(1em - 1px);
        }
        button:disabled, button:disabled:hover, button:disabled:active {
            border-color: transparent!important;
            color: unset!important;
            cursor: auto!important;
            padding-left: 0px;
        }
        thead {
            display: none;
        }
    </style>
'''
