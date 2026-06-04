from pathlib import Path
import streamlit as st
import re

def check_password_strength(password):

    if len(password) < 8:
        return "Mật khẩu phải có ít nhất 8 ký tự"

    if not re.search(r"[A-Z]", password):
        return "Phải có ít nhất 1 chữ in hoa"

    if not re.search(r"[a-z]", password):
        return "Phải có ít nhất 1 chữ thường"

    if not re.search(r"[0-9]", password):
        return "Phải có ít nhất 1 chữ số"

    return None

_CSS_FILE = Path(__file__).parent.parent / "css" / "resetpassword.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)

    if st.button("←"):

        st.session_state["page"] = "forgot_password"

        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(
        '<div class="title">Đặt mật khẩu mới</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="line"></div>',
        unsafe_allow_html=True
    )

    new_password = st.text_input(
        "Mật khẩu mới",
        type="password"
    )

    confirm_password = st.text_input(
        "Xác nhận mật khẩu",
        type="password"
    )

    if st.button(
        "Xác nhận",
        type="primary",
        use_container_width=True
    ):
        error = check_password_strength(new_password)

        if error:

            st.error(error)
        if not new_password.strip() or not confirm_password.strip():

            st.error("Vui lòng nhập đầy đủ thông tin")

        elif new_password != confirm_password:

            st.error("Mật khẩu không khớp")

        else:

            st.success("Đổi mật khẩu thành công")