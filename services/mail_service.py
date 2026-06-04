import smtplib
import random

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# EMAIL CỦA BẠN
SENDER_EMAIL = "nomnasite@gmail.com"

# APP PASSWORD GOOGLE
SENDER_PASSWORD = "djgq xyhs qtre yzzt"


def generate_otp():

    return str(random.randint(100000, 999999))


def send_otp_email(receiver_email, otp):

    subject = "Mã xác nhận OTP"

    body = f"""
    Xin chào,

    Mã xác nhận của bạn là: {otp}

    Mã sẽ hết hạn sau 5 phút.
    """

    msg = MIMEMultipart()

    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(
        SENDER_EMAIL,
        SENDER_PASSWORD
    )

    server.send_message(msg)

    server.quit()