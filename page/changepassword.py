from pathlib import Path
import streamlit as st
import pyrebase
import requests
from firebase_config import firebaseConfig
import re

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()




# ===== CHECK PASSWORD STRONG =====
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

_CSS_FILE = Path(__file__).parent.parent / "css" / "changepassword.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    st.markdown(
        '<div class="main-title">🔒 Đổi mật khẩu</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Bảo mật tài khoản của bạn</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="fb-card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Thông tin mật khẩu</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="line"></div>',
        unsafe_allow_html=True
    )

    email = st.text_input(
        "Email",
        placeholder="Nhập email của bạn"
    )

    current_password = st.text_input(
        "Mật khẩu hiện tại",
        type="password",
        placeholder="Nhập mật khẩu hiện tại"
    )

    new_password = st.text_input(
        "Mật khẩu mới",
        type="password",
        placeholder="Nhập mật khẩu mới"
    )

    confirm_password = st.text_input(
        "Xác nhận mật khẩu mới",
        type="password",
        placeholder="Nhập lại mật khẩu mới"
    )

    change_btn = st.button(
        "Lưu thay đổi",
        type="primary",
        use_container_width=True
    )
    if st.button(
    "Quên mật khẩu?",
    use_container_width=True
):

        st.session_state["page"] = "forgot_password"

        # UPDATE URL
        if "username" in st.session_state:

            st.experimental_set_query_params(
                user=st.session_state["user"],
                name=st.session_state["username"],
                page="forgot_password"
            )

        else:

            st.experimental_set_query_params(
                page="forgot_password"
            )

        st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if change_btn:

        if (
            not email.strip()
            or not current_password.strip()
            or not new_password.strip()
            or not confirm_password.strip()
        ):

            st.error("Vui lòng nhập đầy đủ thông tin")

        elif new_password != confirm_password:

            st.error("Mật khẩu mới không khớp")

        else:

            error = check_password_strength(new_password)

            if error:

                st.error(error)

            else:

                try:

                    user = auth.sign_in_with_email_and_password(
                        email,
                        current_password
                    )

                    API_KEY = firebaseConfig["apiKey"]

                    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEY}"

                    payload = {
                        "idToken": user["idToken"],
                        "password": new_password,
                        "returnSecureToken": True
                    }

                    requests.post(url, json=payload)

                    st.success("Đổi mật khẩu thành công!")

                except requests.exceptions.HTTPError as e:

                    error_json = e.response.json()

                    error_message = error_json['error']['message']

                    if error_message == "EMAIL_NOT_FOUND":

                        st.error("Email không tồn tại")

                    elif error_message == "INVALID_PASSWORD":

                        st.error("Mật khẩu hiện tại không đúng")

                    else:

                        st.error("Đã xảy ra lỗi: " + error_message)