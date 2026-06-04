import json
from pathlib import Path
import streamlit as st
import pyrebase
import re
from firebase_config import firebaseConfig

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


_CSS_FILE = Path(__file__).parent.parent / "css" / "register.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    
    
    st.markdown('<div class="title">Tạo tài khoản</div>', unsafe_allow_html=True)
    st.markdown("""
<hr style="
    border: none;
    height: 1px;
    background: #ddd;
    margin: 0px 0 8px 0;
">
""", unsafe_allow_html=True)

    # ===== INPUT =====
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Mật khẩu", type="password", key="reg_pass")
    confirm = st.text_input("Nhập lại mật khẩu", type="password", key="reg_confirm")

    # ===== BUTTON =====
    st.markdown('<div class="register-area">', unsafe_allow_html=True)
    
    register_btn = st.button(
    "Đăng ký",
    key="register_btn",
    type="primary",
    use_container_width=True
)
   
    if register_btn:

        # 1. CHECK RỖNG
        if not email.strip() or not password.strip() or not confirm.strip():
            st.error("Vui lòng nhập đầy đủ thông tin")

        # 2. CHECK PASSWORD MATCH
        elif password != confirm:
            st.error("Mật khẩu không khớp")
            
        elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            st.error("Email không đúng định dạng")

        else:
            # 3. CHECK PASSWORD STRONG
            error = check_password_strength(password)

            if error:
                st.error(error)

            else:
                try:
                    auth.create_user_with_email_and_password(email.strip(), password)
                    st.success("Tạo tài khoản thành công! Hãy đăng nhập để tiếp tục.")

                except Exception as e:
                    msg = str(e)
                    try:
                        # Firebase trả lỗi dạng JSON trong message
                        detail = json.loads(msg.split(":", 1)[1].strip()) if ":" in msg else {}
                        code = detail.get("error", {}).get("message", "")
                    except Exception:
                        code = ""

                    if "EMAIL_EXISTS" in code or "EMAIL_EXISTS" in msg:
                        st.error("Email này đã được đăng ký. Vui lòng đăng nhập hoặc dùng email khác.")
                    elif "WEAK_PASSWORD" in code or "WEAK_PASSWORD" in msg:
                        st.error("Mật khẩu quá yếu. Hãy dùng mật khẩu mạnh hơn.")
                    elif "INVALID_EMAIL" in code or "INVALID_EMAIL" in msg:
                        st.error("Email không hợp lệ.")
                    elif "TOO_MANY_ATTEMPTS" in code or "TOO_MANY_ATTEMPTS" in msg:
                        st.warning("Quá nhiều lần thử. Vui lòng thử lại sau.")
                    else:
                        st.error("Đăng ký thất bại. Kiểm tra lại thông tin hoặc thử lại sau.")
    if st.button("Đã có tài khoản? Đăng nhập ngay", use_container_width=True):
            st.session_state["page"] = "login"
            st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)