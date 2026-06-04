import json
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
import pyrebase
from firebase_config import firebaseConfig
from services.firebase_roles import get_role

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

_CSS_FILE = Path(__file__).parent.parent / "css" / "login.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    # ── Đọc credentials từ localStorage ──────────────────────────────────────
    # Chỉ chạy khi chưa prefill (lần đầu vào login sau khi logout / fresh load).
    # Tách riêng khỏi phần render form để đảm bảo widget chưa tồn tại khi ta
    # gán session_state → tránh StreamlitAPIException của Streamlit 1.21.
    if "login_prefilled" not in st.session_state:
        saved_raw = st_javascript(
            "JSON.stringify({e:localStorage.getItem('nomnasite_saved_email')||'',"
            "p:localStorage.getItem('nomnasite_saved_pwd')||''})"
        )

        if not isinstance(saved_raw, str):
            # JS chưa phản hồi (render đầu tiên) → hiện tiêu đề, chờ rerun
            col1, _ = st.columns([1.2, 1])
            with col1:
                st.markdown('<div class="fb-title">Nomnasite</div>', unsafe_allow_html=True)
                st.markdown(
                    '<div class="fb-desc">Đăng nhập để sử dụng hệ thống dịch Hán Nôm sang Quốc Ngữ.</div>',
                    unsafe_allow_html=True,
                )
            return  # Dừng sớm, chờ JS phản hồi → Streamlit sẽ tự rerun

        # JS đã phản hồi → parse và prefill TRƯỚC khi bất kỳ widget nào render
        st.session_state["login_prefilled"] = True
        try:
            creds = json.loads(saved_raw)
            if creds.get("e"):
                st.session_state["_login_email_k"] = creds["e"]
                st.session_state["_login_pwd_k"]   = creds.get("p", "")
                st.session_state["remember_me"]    = True   # an toàn vì widget chưa render
        except Exception:
            pass

    # ── Form đăng nhập ───────────────────────────────────────────────────────
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<div class="fb-title">Nomnasite</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="fb-desc">Đăng nhập để sử dụng hệ thống dịch Hán Nôm sang Quốc Ngữ.</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="lg-title">Đăng nhập</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        email = st.text_input(
            "Email",
            key="_login_email_k",
            label_visibility="collapsed",
            placeholder="Email hoặc số điện thoại",
        )
        password = st.text_input(
            "Mật khẩu",
            type="password",
            key="_login_pwd_k",
            label_visibility="collapsed",
            placeholder="Mật khẩu",
        )
        remember = st.checkbox("Nhớ mật khẩu", key="remember_me")

        login_btn = st.button(
            "Đăng nhập", key="login_btn", type="primary", use_container_width=True
        )

        if login_btn:
            if not email.strip() or not password.strip():
                st.error("Vui lòng nhập đầy đủ thông tin")
            else:
                try:
                    email    = email.strip()
                    password = password.strip()
                    user         = auth.sign_in_with_email_and_password(email, password)
                    account_info = auth.get_account_info(user["idToken"])
                    user_data    = account_info["users"][0]
                    name         = user_data.get("displayName") or email.split("@")[0]

                    # Lưu hoặc xóa credentials trong localStorage
                    if remember:
                        components.html(
                            f"<script>"
                            f"localStorage.setItem('nomnasite_saved_email',{json.dumps(email)});"
                            f"localStorage.setItem('nomnasite_saved_pwd',{json.dumps(password)});"
                            f"</script>",
                            height=0,
                        )
                    else:
                        components.html(
                            "<script>"
                            "localStorage.removeItem('nomnasite_saved_email');"
                            "localStorage.removeItem('nomnasite_saved_pwd');"
                            "</script>",
                            height=0,
                        )

                    # Xóa flag prefill để lần logout → login tiếp theo đọc lại localStorage
                    st.session_state.pop("login_prefilled", None)

                    role = get_role(user["email"], user["idToken"])

                    st.session_state["user"]             = user["email"]
                    st.session_state["username"]         = name
                    st.session_state["id_token"]         = user["idToken"]
                    st.session_state["role"]             = role
                    st.session_state["need_sync_local"]  = True
                    st.session_state["_fb_verified"]     = True

                    st.experimental_set_query_params(
                        user=user["email"], name=name, page="home"
                    )
                    st.session_state["page"] = "home"
                    st.experimental_rerun()

                except Exception as e:
                    msg = str(e)
                    if "USER_DISABLED" in msg:
                        st.error("🔒 Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên để được hỗ trợ.")
                    elif "EMAIL_NOT_FOUND" in msg or "INVALID_EMAIL" in msg:
                        st.error("Email không tồn tại trong hệ thống.")
                    elif "INVALID_PASSWORD" in msg or "INVALID_LOGIN_CREDENTIALS" in msg:
                        st.error("Sai email hoặc mật khẩu.")
                    else:
                        st.error("Đăng nhập thất bại. Vui lòng thử lại.")

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Quên mật khẩu?", key="forgot_btn"):
            st.session_state["previous_page"] = st.session_state.get("page", "login")
            st.session_state["page"] = "forgot_password"
            st.experimental_rerun()

        if st.button("Tạo tài khoản mới", key="register_btn"):
            st.session_state["page"] = "register"
            st.experimental_rerun()
