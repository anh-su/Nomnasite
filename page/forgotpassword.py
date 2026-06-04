from pathlib import Path
import streamlit as st
import pyrebase
import time
from firebase_config import firebaseConfig

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
from services.mail_service import generate_otp, send_otp_email
from streamlit_autorefresh import st_autorefresh


_CSS_FILE = Path(__file__).parent.parent / "css" / "forgotpassword.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    st.markdown('<div class="back-btn">', unsafe_allow_html=True)

    if st.button("←"):

        previous = st.session_state.get(
            "previous_page",
            "login"
        )

        st.session_state["page"] = previous

        st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="title">Xác nhận tài khoản</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="sub">
            Chúng tôi đã gửi mã đến email của bạn.
            Hãy nhập mã đó để xác nhận tài khoản.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="line"></div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    email = st.text_input("Email:", placeholder="Nhập email của bạn")

    code = st.text_input(
        "Mã xác nhận", placeholder="Nhập mã", label_visibility="collapsed"
    )
    otp_sent = st.session_state.get("otp_sent", False)
    remain = 0
    
 

    
    if "otp_rerun" not in st.session_state:
        st.session_state["otp_rerun"] = False

    if st.session_state["otp_rerun"]:
        st.session_state["otp_rerun"] = False
    

    if otp_sent:

        otp_expire = st.session_state.get("otp_expire", 0)

        remain = int(otp_expire - time.time())

        if remain <= 0:

            st.session_state["otp_sent"] = False
            st.session_state.pop("otp", None)
            otp_sent = False

            remain = 0
        else:

            countdown_html = ""

            if otp_sent:

                st_autorefresh(
                    interval=1000,
                    key="otp_refresh"
                )

                countdown_html = f"""
                <div style="
                    text-align:right;
                    color:#666;
                    font-size:13px;
                    margin-top:-10px;
                    margin-bottom:6px;
                ">
                    Bạn có thể gửi lại sau {remain}s
                </div>
                """

            st.markdown(
                countdown_html,
                unsafe_allow_html=True
            )
    # TEXT BUTTON
    

    send_text = "Gửi mã xác nhận"

    # BUTTON
    send_btn = st.button(
        send_text,
        type="primary",
        use_container_width=True,
        disabled=otp_sent,
        key="send_otp_btn",
    )
    

    continue_btn = st.button(
        "Tiếp tục",
        type="primary",
        use_container_width=True,
        disabled=(not otp_sent),
        key="continue_btn",
    )

    if continue_btn:

        if time.time() > st.session_state["otp_expire"]:

            st.error("Mã OTP đã hết hạn")

            st.session_state["otp_sent"] = False

        elif not code.strip():

            st.error("Vui lòng nhập mã xác nhận")

        elif code == st.session_state.get("otp"):

            st.session_state["verified_email"] = (
            st.session_state["reset_email"]
            )

            st.session_state["page"] = "resetpassword"

            st.experimental_rerun()

        else:

            st.error("Mã OTP không đúng")
            
            
    if send_btn:
        if st.session_state["otp_rerun"]:
            st.stop()

        if otp_sent:

            st.warning(f"Vui lòng đợi {remain}s để gửi lại OTP")

            st.stop()
        if not email.strip():

            st.error("Vui lòng nhập email")

        else:

            try:

                otp = generate_otp()

                st.session_state["otp"] = otp

                st.session_state["reset_email"] = email

                send_otp_email(email, otp)

                st.session_state["otp_sent"] = True

                st.session_state["otp_expire"] = time.time() + 180
                otp_sent = True

                st.success("Đã gửi mã OTP tới email")
                
                
                
            except:

                st.error("Không gửi được email")

    st.markdown('</div>', unsafe_allow_html=True)
