"""
Firebase Admin SDK — quản lý tài khoản người dùng (khóa / mở khóa / xóa).
Dùng serviceAccountKey.json để xác thực admin.
"""
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, auth as fb_auth
from pathlib import Path

_KEY_PATH = Path(__file__).parent.parent / "serviceAccountKey.json"
_APP_NAME = "nomnasite-admin"


def _load_credentials() -> credentials.Certificate:
    if _KEY_PATH.exists():
        return credentials.Certificate(str(_KEY_PATH))
    # Streamlit Cloud: đọc từ st.secrets["firebase_service_account"]
    try:
        import streamlit as st
        key_dict = dict(st.secrets["firebase_service_account"])
        # private_key cần giữ nguyên ký tự xuống dòng
        key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(key_dict, tmp)
        tmp.flush()
        return credentials.Certificate(tmp.name)
    except Exception as e:
        raise RuntimeError(f"Không tìm thấy serviceAccountKey.json và st.secrets cũng thiếu: {e}")


def _get_app():
    try:
        return firebase_admin.get_app(_APP_NAME)
    except ValueError:
        cred = _load_credentials()
        return firebase_admin.initialize_app(cred, name=_APP_NAME)


def get_user_info(email: str) -> dict | None:
    """Lấy thông tin tài khoản Firebase theo email. Trả về None nếu không tìm thấy."""
    try:
        app = _get_app()
        user = fb_auth.get_user_by_email(email, app=app)
        return {
            "uid":      user.uid,
            "email":    user.email,
            "disabled": user.disabled,
        }
    except Exception:
        return None


def lock_user(email: str) -> bool:
    """Khóa tài khoản (disabled=True). Trả về True nếu thành công."""
    try:
        app  = _get_app()
        user = fb_auth.get_user_by_email(email, app=app)
        fb_auth.update_user(user.uid, disabled=True, app=app)
        return True
    except Exception:
        return False


def unlock_user(email: str) -> bool:
    """Mở khóa tài khoản (disabled=False). Trả về True nếu thành công."""
    try:
        app  = _get_app()
        user = fb_auth.get_user_by_email(email, app=app)
        fb_auth.update_user(user.uid, disabled=False, app=app)
        return True
    except Exception:
        return False


def delete_user(email: str) -> bool:
    """Xóa vĩnh viễn tài khoản. Trả về True nếu thành công."""
    try:
        app  = _get_app()
        user = fb_auth.get_user_by_email(email, app=app)
        fb_auth.delete_user(user.uid, app=app)
        return True
    except Exception:
        return False
