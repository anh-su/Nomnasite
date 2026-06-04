from pathlib import Path
import streamlit as st

_CSS_FILE = Path(__file__).parent / "css" / "toolbar.css"


def render_toolbar(key):
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    # ===== TOP OPTIONS =====
    top1, top2, top3 = st.columns(3)

    with top1:
        mode = st.radio(
            'Mode',
            ('Vẽ', 'Chỉnh sửa'),
            horizontal=True,
            label_visibility='collapsed',
            key=f'mode_{key}'
        )

    with top2:
        saved_format = st.radio(
            'Type',
            ('csv', 'json'),
            horizontal=True,
            label_visibility='collapsed'
        )

    with top3:
        # spacer thật
        st.markdown(
            "<div style='height:38px'></div>",
            unsafe_allow_html=True
        )

    # ===== BUTTONS =====
    col11, col12 = st.columns(2)

    with col11:

        st.button(
            '(**) Nhấp đúp vào khung để xoá.',
            disabled=True,
            use_container_width=True
        )

        rec_clicked = st.button(
            'Nhận dạng văn bản',
            type='primary',
            use_container_width=True
        )

    with col12:

        st.download_button(
            label=f'📥 Tải kết quả OCR: data.{saved_format}',
            data=open(
                f'data/data.{saved_format}',
                encoding='utf-8'
            ),
            file_name=f'data.{saved_format}',
            use_container_width=True,
        )

        st.download_button(
            label='🖼️ Tải ảnh cắt từ văn bản',
            data=open('data/patches.zip', 'rb'),
            file_name='patches.zip',
            use_container_width=True,
        )

   

    return mode, rec_clicked