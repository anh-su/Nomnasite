"""
Quản lý role người dùng qua Firebase Realtime Database.

Cấu trúc DB:
  roles/
    <email_sanitized>/   (dấu . thay bằng ,)
      role: "admin" | "user"
"""

import pyrebase
from firebase_config import firebaseConfig

_firebase = pyrebase.initialize_app(firebaseConfig)
_db = _firebase.database()

_EMAIL_SAFE = str.maketrans(".", ",")


def _key(email: str) -> str:
    """Firebase key không chứa dấu chấm."""
    return email.translate(_EMAIL_SAFE)


def get_role(email: str, id_token: str) -> str:
    """Lấy role của user. Trả về 'admin' hoặc 'user'."""
    try:
        res = _db.child("roles").child(_key(email)).child("role").get(id_token)
        val = res.val()
        return val if val in ("admin", "user") else "user"
    except Exception:
        return "user"


def set_role(email: str, role: str, id_token: str) -> None:
    """Gán role cho user (gọi từ admin panel)."""
    _db.child("roles").child(_key(email)).set({"role": role}, id_token)


def is_admin_role(email: str, id_token: str) -> bool:
    return get_role(email, id_token) == "admin"
