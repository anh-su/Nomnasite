import os
import sys
import types

# pyrebase4 phụ thuộc nhiều package Google App Engine cổ không tương thích cloud
# → mock tất cả trước khi pyrebase được import bất kỳ đâu

# 1. Mock gcloud (2016, deprecated)
try:
    import gcloud as _gcloud_test  # noqa
except Exception:
    _gcloud_mod = types.ModuleType('gcloud')
    _storage_mod = types.ModuleType('gcloud.storage')
    class _FakeStorageClient:
        def __init__(self, *a, **kw): pass
    _storage_mod.Client = _FakeStorageClient
    _gcloud_mod.storage = _storage_mod
    sys.modules['gcloud'] = _gcloud_mod
    sys.modules['gcloud.storage'] = _storage_mod

# 2. Mock requests_toolbelt GAE modules (requires App Engine SDK)
_gaecontrib = types.ModuleType('requests_toolbelt._compat.gaecontrib')
sys.modules['requests_toolbelt._compat.gaecontrib'] = _gaecontrib

_rtb_appengine = types.ModuleType('requests_toolbelt.adapters.appengine')
_rtb_appengine.is_appengine_sandbox = lambda: False
_rtb_appengine.is_appengine = lambda: False
class _FakeAppEngineAdapter:
    def __init__(self, *a, **kw): pass
_rtb_appengine.AppEngineAdapter = _FakeAppEngineAdapter
sys.modules['requests_toolbelt.adapters.appengine'] = _rtb_appengine

import streamlit as st
st.set_page_config(
    'Nomnasite',
    '🇻🇳',
    'wide'
)
import base64
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)
# Streamlit Cloud: inject st.secrets vào os.environ (chỉ khi file secrets tồn tại)
_secrets_file = (Path.home() / ".streamlit" / "secrets.toml")
_local_secrets = Path(__file__).parent / ".streamlit" / "secrets.toml"
if _secrets_file.exists() or _local_secrets.exists():
    try:
        for _k, _v in st.secrets.items():
            if isinstance(_v, str) and _k not in os.environ:
                os.environ[_k] = _v
    except Exception:
        pass
import streamlit.components.v1 as components

_han_nom_input = components.declare_component(
    "han_nom_input",
    path=str(Path(__file__).parent / "components" / "han_nom_input")
)

@st.cache_data(show_spinner=False)
def _load_cangjie_data() -> dict:
    p = Path(__file__).parent / "static" / "cangjie5.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}
from streamlit_javascript import st_javascript
from handler.init_database import init_database
from handler.dictionary_handler import translate_vi_to_hn, detect_language, _get_translations
from handler.translator import db_hanviet, db_meaning, _load_db
from style import bg_css

@st.cache_resource(show_spinner=False)
def _init_db_once():
    init_database()

_init_db_once()

from services.translation_log import create_table as _create_log_table, save_entry, get_entries, get_entry_by_id, sync_from_local, delete_entry, toggle_star
_create_log_table()
from page import admin as admin_page          # cần sớm để check _is_admin() trong sidebar

@st.cache_data(show_spinner=False)
def _read_css(name: str) -> str:
    return (Path(__file__).parent / "css" / name).read_text(encoding="utf-8")

def _load_css(name: str) -> None:
    st.markdown(f"<style>{_read_css(name)}</style>", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def _nom_font_b64() -> str:
    """Base64 của NomNaTong.otf — dùng cho cả CSS inline lẫn component prop."""
    p = Path(__file__).parent / "static" / "NomNaTong.otf"
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

@st.cache_data(show_spinner=False)
def _font_face_css() -> str:
    """Embed cả NomNaTong + HanaMinA dưới dạng base64 để hiện ký tự ngay lập tức."""
    css = ""
    for fname, family, urange in [
        ("NomNaTong.otf", "NomNaTong",
         "U+F0000-U+FFFFF"),
        ("HanaMinA.otf",  "HanaMin",
         "U+3400-4DBF,U+20000-2A6DF,U+2A700-2B73F,"
         "U+2B740-2B81F,U+2B820-2CEAF,U+F900-FAFF,U+2F800-2FA1F"),
    ]:
        p = Path(__file__).parent / "static" / fname
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            css += (f"@font-face{{font-family:'{family}';"
                    f"src:url('data:font/opentype;base64,{b64}') format('opentype');"
                    f"unicode-range:{urange};}}")
    return css

st.markdown(f"<style>{_font_face_css()}</style>", unsafe_allow_html=True)
_load_css("app.css")

# _load_db() và _get_translations() tự cache bằng Python global — không cần preload

# RESTORE LOGIN KHI RELOAD
params = st.experimental_get_query_params()
page   = params.get("page", ["home"])[0]

# Nếu đang có user/name trên URL (link cũ) → dọn sạch, chuyển vào session_state
if params.get("user") or params.get("name"):
    _u = params.get("user", [None])[0]
    _n = params.get("name", [None])[0]
    if _u:
        st.session_state["user"]     = _u
        st.session_state["username"] = _n or _u.split("@")[0]
    st.experimental_set_query_params(page=page)
    st.experimental_rerun()

# Restore session từ localStorage (giữ login sau khi server restart)
if "user" not in st.session_state:
    _stored = st_javascript(
        "JSON.stringify({u:localStorage.getItem('nom_u'),n:localStorage.getItem('nom_n'),r:localStorage.getItem('nom_r')})"
    )
    if isinstance(_stored, str):
        try:
            _d = json.loads(_stored)
            if _d.get("u"):
                st.session_state["user"]     = _d["u"]
                st.session_state["username"] = _d.get("n") or _d["u"].split("@")[0]
                st.session_state["role"]     = _d.get("r", "user")
        except Exception:
            pass

user = st.session_state.get("user")
name = st.session_state.get("username")
action = params.get("action",    [None])[0]
act_id = params.get("action_id", [None])[0]

# xử lý star/delete/load từ journal HTML component
if action and act_id:
    try:
        if action == "star":
            toggle_star(int(act_id))
        elif action == "del":
            delete_entry(int(act_id))
        elif action == "load":
            _e = get_entry_by_id(int(act_id))
            if _e:
                st.session_state["input_han_nom"]  = _e["input"]
                st.session_state["output_text"]    = _e["output"]
                st.session_state["output_is_error"] = False
                st.session_state["translate_mode"] = _e.get("direction", "vi_to_hn")
                st.session_state["page"] = "home"
    except Exception:
        pass
    clean = {k: v for k, v in params.items() if k not in ("action", "action_id")}
    st.experimental_set_query_params(**clean)
    st.experimental_rerun()

# xử lý load từ localStorage (khách vãng lai)
_load_inp = params.get("load_inp", [None])[0]
_load_out = params.get("load_out", [None])[0]
if _load_inp:
    import base64 as _b64
    try:
        def _pad(s): return s + "=" * ((4 - len(s) % 4) % 4)
        _inp = _b64.b64decode(_pad(_load_inp)).decode("utf-8")
        _out = _b64.b64decode(_pad(_load_out)).decode("utf-8") if _load_out else ""
        st.session_state["input_han_nom"]   = _inp
        st.session_state["output_text"]     = _out
        st.session_state["output_is_error"] = False
        st.session_state["page"] = "home"
    except Exception:
        pass
    _clean2 = {k: v for k, v in params.items() if k not in ("load_inp", "load_out")}
    st.experimental_set_query_params(**_clean2)
    st.experimental_rerun()

# restore session — bỏ qua nếu vừa đăng xuất (URL params chưa cleared kịp)
_just_logged_out = st.session_state.pop("_just_logged_out", False)
if user and name and not _just_logged_out:
    st.session_state["user"]     = user
    st.session_state["username"] = name
    # Khôi phục role từ ADMIN_EMAILS khi reload (không cần Firebase call)
    if "role" not in st.session_state:
        _admin_list = [e.strip() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()]
        st.session_state["role"] = "admin" if user in _admin_list else "user"
    # Cho phép vào trang admin nếu role đã được xác nhận là admin
    restored_page = page if page != "admin" or st.session_state.get("role") == "admin" else "home"
    st.session_state["page"]     = restored_page
        
    
# ===== USER HEADER =====
if "username" in st.session_state:

    st.markdown(
        f'<div class="user-box">👤 {st.session_state["username"]}</div>',
        unsafe_allow_html=True
    )

# ===== SIDEBAR =====

with st.sidebar:

    # LINK HOME
    if "username" in st.session_state:

        home_link = (
            f'/?user={st.session_state["user"]}'
            f'&name={st.session_state["username"]}'
            f'&page=home'
        )

    else:

        home_link = "/?page=home"

    st.markdown(
        f"""
        <h1 style="margin:0;">
            <a href="{home_link}"
               target="_self"
               class="sidebar-title"
               tabindex="-1">
                NOMNASITE
            </a>
        </h1>
        """,
        unsafe_allow_html=True
    )
    


# Trang mặc định
if "page" not in st.session_state:
    st.session_state["page"] = page if page else "home"

# chiều dịch
if "translate_mode" not in st.session_state:
    st.session_state.translate_mode = "vi_to_hn"

def _nav(key, label, page_key=None):
    """Render một nút điều hướng sidebar."""
    target = page_key or key
    if st.button(label, key=f"nav_{key}"):
        st.session_state["page"] = target
        if "username" in st.session_state:
            st.experimental_set_query_params(page=target)
        else:
            st.experimental_set_query_params(page=target)
        st.experimental_rerun()


_logged_in = "username" in st.session_state

with st.sidebar:

    # 1. Quản trị viên (admin only)
    if _logged_in and admin_page._is_admin():
        _nav("admin", "🛡️ Quản trị viên")

    # 2. Trang chủ
    _nav("home", "🏠 Trang chủ")

    # 3. Nhận diện hình ảnh (login)
    if _logged_in:
        _nav("nomnasite", "🔍 Nhận diện hình ảnh")

    # 4. Lịch sử dịch (login)
    if _logged_in:
        _nav("history", "📜 Lịch sử dịch")

    # 5-7. Giới thiệu / Hướng dẫn (tất cả)
    _nav("introduce",       "ℹ️ Giới thiệu")
    _nav("keyboardtutorial","⌨️ Hướng dẫn bộ gõ")
    _nav("usermanual",      "📊 Hướng dẫn sử dụng")

    # 8. Đổi mật khẩu (login)
    if _logged_in:
        _nav("change_password", "🔑 Đổi mật khẩu")

    # 9. Đăng xuất / Đăng nhập
    if _logged_in:
        if st.button("🚪 Đăng xuất", key="nav_logout"):
            st_javascript("localStorage.removeItem('nom_u');localStorage.removeItem('nom_n');localStorage.removeItem('nom_r');0")
            st.session_state.clear()
            st.session_state["app_initialized"] = True
            st.session_state["page"] = "login"
            st.session_state["_just_logged_out"] = True
            st.experimental_set_query_params()
            st.experimental_rerun()
    else:
        _nav("login", "⚙️ Đăng nhập")
        
# PAGE
page = st.session_state.get("page", "home")

# BACKGROUND — áp dụng cho mọi trang
st.markdown(bg_css(), unsafe_allow_html=True)

# HIỂN THỊ TRANG

if page == "home":

    # ===== HERO =====
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-glyph">喃</div>
        <div>
            <div class="hero-title">NOMNASITE</div>
            <div class="hero-sub">Hệ thống nhận diện &amp; dịch chữ Hán Nôm ứng dụng trí tuệ nhân tạo</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== LANGUAGE HEADERS =====
    is_vi = st.session_state.translate_mode == "vi_to_hn"
    left_label  = "🇻🇳&nbsp; QUỐC NGỮ"  if is_vi else "喃&nbsp; HÁN NÔM"
    right_label = "喃&nbsp; HÁN NÔM"    if is_vi else "🇻🇳&nbsp; QUỐC NGỮ"

    col1, col_mid, col2 = st.columns([5, 1, 5])
    with col1:
        st.markdown(f'<div class="lang-label">{left_label}</div>', unsafe_allow_html=True)
    with col_mid:
        st.markdown("<div style='padding-top:6px'></div>", unsafe_allow_html=True)
        if st.button("⇄", key="switch_lang"):
            st.session_state.translate_mode = "hn_to_vi" if is_vi else "vi_to_hn"
            st.experimental_rerun()
    with col2:
        st.markdown(f'<div class="lang-label">{right_label}</div>', unsafe_allow_html=True)

    st.markdown(
        '<hr style="border:none;height:2px;background:#f69322;margin:0 0 8px 0;opacity:1">',
        unsafe_allow_html=True
    )

    # ===== TEXT AREAS =====
    def handle_translate():
        text = st.session_state.input_han_nom
        if not text:
            st.session_state.output_text = ""
            st.session_state.output_is_error = False
            return
        lang = detect_language(text)
        if lang == "han_nom":
            st.session_state.translate_mode = "hn_to_vi"
            phienam = db_hanviet(text.strip())
            nghia   = db_meaning(text.strip())
            # Không dịch được nếu cả phiên âm lẫn nghĩa đều không tìm thấy
            pa_fail = not phienam.replace("[?]", "").strip() or phienam == "Không tìm thấy."
            ng_fail = not nghia.replace("[UNK]", "").strip() or nghia == "Không tìm thấy trong bộ dữ liệu."
            if pa_fail and ng_fail:
                st.session_state.output_text = ""
                st.session_state.output_is_error = True
            else:
                st.session_state.output_text = f"Phiên âm: {phienam}\nDịch nghĩa: {nghia}"
                st.session_state.output_is_error = False
        else:
            st.session_state.translate_mode = "vi_to_hn"
            result = translate_vi_to_hn(text)
            # Không dịch được nếu tất cả từ vẫn giữ nguyên như input
            input_words  = set(text.lower().split())
            result_words = set(result.split())
            if input_words and input_words == result_words:
                st.session_state.output_text = ""
                st.session_state.output_is_error = True
            else:
                st.session_state.output_text = result
                st.session_state.output_is_error = False

    if "output_text" not in st.session_state:
        st.session_state.output_text = ""
    if "output_is_error" not in st.session_state:
        st.session_state.output_is_error = False

    cangjie_on = st.checkbox(
        "⌨️ Gõ Hán Nôm (Thương Hiệt)",
        key="cangjie_mode",
        help="Bật bộ gõ Thương Hiệt: gõ a-y rồi chọn số để nhập ký tự Hán Nôm"
    )

    col1, col2 = st.columns(2)
    with col1:
        # key để force reload component
        if "input_version" not in st.session_state:
            st.session_state.input_version = 0

        old_text = st.session_state.get("input_han_nom", "")

        new_text = _han_nom_input(
            value=old_text,
            cangjie=cangjie_on,
            cangjie_data=_load_cangjie_data(),
            nom_font_b64=_nom_font_b64(),
            key=f"han_nom_comp_{st.session_state.input_version}",
            default=old_text
        )
        if new_text is not None and new_text != old_text:
            st.session_state["input_han_nom"] = new_text
            handle_translate()
            st.experimental_rerun()
        text_input = st.session_state.get("input_han_nom", "")

    with col2:
        _out = st.session_state.get("output_text", "")
        _err = st.session_state.get("output_is_error", False)
        _out_js = json.dumps(_out if not _err else "Văn bản không hợp lệ.")
        _bg = "#f1f3f4"
        _clr = "#e74c3c" if _err else "#1a1a2e"
        _fw = "font-weight:600;font-size:16px;display:flex;align-items:center;justify-content:center;" if _err else "white-space:pre-wrap;word-break:break-word;"
        components.html(f"""<style>
*{{box-sizing:border-box;margin:0;padding:0}}
@font-face{{font-family:'NomNaTong';src:url('/app/static/NomNaTong.otf')}}
body{{background:transparent;overflow:hidden}}
#out{{width:100%;height:224px;border:1px solid rgba(49,51,63,.2);border-radius:.5rem;
      padding:8px 12px;font-size:14px;background:{_bg};
      font-family:'NomNaTong',serif;line-height:1.6;color:{_clr};
      overflow-y:auto;{_fw}}}
</style>
<div id="out"></div>
<script>document.getElementById('out').textContent={_out_js};</script>
""", height=240, scrolling=False)


    # ===== COUNTER + ACTION BUTTONS =====
    count = len(text_input) if text_input else 0
    pct   = min(count / 500, 1.0) * 100
    bar_color = "#e74c3c" if count > 450 else "#f69322"
    warn  = "⚠️ " if count > 450 else ""

    _out_js     = json.dumps(st.session_state.get("output_text", ""))
    _inp_val    = text_input or ""
    _out_val    = st.session_state.get("output_text", "")
    _content_js = json.dumps(f"=== Văn bản gốc ===\n{_inp_val}\n\n=== Bản dịch ===\n{_out_val}")

    components.html(f"""<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:transparent;font-family:sans-serif;overflow:hidden;
      display:flex;align-items:center;gap:10px}}
.bar-wrap{{flex:1;min-width:0}}
.bar{{height:4px;background:#eee;border-radius:4px;margin-bottom:3px;overflow:hidden}}
.fill{{height:100%;border-radius:4px;background:{bar_color};width:{pct:.1f}%}}
.lbl{{font-size:12px;color:#999}}
.btns{{display:flex;align-items:center;gap:6px;flex-shrink:0}}
.btn{{background:none;border:1px solid #e0e0e0;border-radius:6px;cursor:pointer;
      width:26px;height:26px;display:flex;align-items:center;justify-content:center;
      color:#bbb;padding:0;transition:.15s;}}
.btn:hover{{background:#f5f5f5;border-color:#bbb;color:#262660}}
.msg{{font-size:11px;color:#e74c3c;white-space:nowrap;min-width:12px}}
</style>
<div class="bar-wrap">
  <div class="bar"><div class="fill"></div></div>
  <div class="lbl">{warn}{count}/500 ký tự</div>
</div>
<div class="btns">
  <button class="btn" onclick="doCopy()" title="Sao chép bản dịch">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  </button>
  <span class="msg" id="m1"></span>
  <button class="btn" onclick="doSave()" title="Lưu bản dịch về máy">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="7 10 12 15 17 10"/>
      <line x1="12" y1="15" x2="12" y2="3"/>
    </svg>
  </button>
  <span class="msg" id="m2"></span>
</div>
<script>
var out={_out_js},content={_content_js};
function setMsg(id,t,c){{var e=document.getElementById(id);e.textContent=t;e.style.color=c;}}
function doCopy(){{
  if(!out){{setMsg('m1','⚠','#e74c3c');return;}}
  var span=document.createElement('span');
  span.textContent=out;
  span.style.cssText='white-space:pre;position:fixed;left:0;top:0;opacity:0.01;';
  document.body.appendChild(span);
  var range=document.createRange();range.selectNodeContents(span);
  var sel=window.getSelection();sel.removeAllRanges();sel.addRange(range);
  var ok=false;try{{ok=document.execCommand('copy');}}catch(e){{}}
  sel.removeAllRanges();document.body.removeChild(span);
  if(ok){{setMsg('m1','✓','green');return;}}
  if(navigator.clipboard&&navigator.clipboard.writeText){{
    navigator.clipboard.writeText(out)
      .then(function(){{setMsg('m1','✓','green');}})
      .catch(function(){{setMsg('m1','❌','#e74c3c');}});
  }}else{{setMsg('m1','❌','#e74c3c');}}
}}
function doSave(){{
  if(!out){{setMsg('m2','⚠','#e74c3c');return;}}
  try{{
    var blob=new Blob([content],{{type:'text/plain;charset=utf-8'}});
    var url=URL.createObjectURL(blob);
    var a=document.createElement('a');a.href=url;a.download='ban_dich.txt';
    document.body.appendChild(a);a.click();
    setTimeout(function(){{document.body.removeChild(a);URL.revokeObjectURL(url);}},100);
    setMsg('m2','✓','green');
  }}catch(e){{setMsg('m2','❌','#e74c3c');}}
}}
</script>""", height=32, scrolling=False)

    # ===== NHẬT KÝ DỊCH =====
    is_logged_in = "username" in st.session_state

    # --- SYNC localStorage → DB khi vừa đăng nhập ---
    # st_javascript trả về 0 (int) trên lần render đầu (JS chưa phản hồi),
    # trả về chuỗi thực sự từ render tiếp theo khi JS đã gửi kết quả về.
    # → chỉ pop flag sau khi nhận được chuỗi hợp lệ, không pop sớm.
    if st.session_state.get("need_sync_local"):
        raw = st_javascript("localStorage.getItem('nomnasite_history') || '[]'")
        if isinstance(raw, str):          # JS đã phản hồi
            if raw not in ("[]", "", "0"):
                n = sync_from_local(st.session_state["username"], raw)
                if n > 0:
                    st.success(f"Đã đồng bộ {n} bản dịch từ thiết bị này lên máy chủ ✓")
            components.html(
                "<script>localStorage.removeItem('nomnasite_history');</script>",
                height=0
            )
            st.session_state.pop("need_sync_local", None)
        # raw == 0 (int): JS chưa phản hồi, giữ flag → render tiếp sẽ retry

    # --- LƯU entry mới ---
    cur_input  = st.session_state.get("input_han_nom", "")
    cur_output = st.session_state.get("output_text", "")
    cur_dir    = st.session_state.get("translate_mode", "vi_to_hn")
    last_logged = st.session_state.get("_last_logged", ("", ""))

    if cur_input and cur_output and (cur_input, cur_output) != last_logged:
        st.session_state["_last_logged"] = (cur_input, cur_output)
        if is_logged_in:
            save_entry(st.session_state["username"], cur_input, cur_output, cur_dir)
        else:
            # Lưu vào localStorage qua JS
            entry_js = json.dumps({"input": cur_input, "output": cur_output,
                                   "direction": cur_dir, "starred": False},
                                  ensure_ascii=False)
            components.html(f"""<script>
(function(){{
    var k='nomnasite_history';
    var h=JSON.parse(localStorage.getItem(k)||'[]');
    var e={entry_js};
    if(h.length===0||h[0].input!==e.input||h[0].output!==e.output){{
        if(h.length>=30){{
            var toRm=-1;
            for(var j=h.length-1;j>=0;j--){{if(!h[j].starred){{toRm=j;break;}}}}
            if(toRm<0)return;
            h.splice(toRm,1);
        }}
        h.unshift(e);
        localStorage.setItem(k,JSON.stringify(h));
    }}
}})();
</script>""", height=0)

    # --- HIỂN THỊ nhật ký ---
    st.markdown('<div class="journal-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="journal-label">📓 Nhật ký dịch'
        + (' <span class="journal-badge">Máy chủ · Đa thiết bị</span>' if is_logged_in
           else ' <span class="journal-badge">Trình duyệt này</span>')
        + '</div>',
        unsafe_allow_html=True
    )

    if is_logged_in:
        entries = get_entries(st.session_state["username"], limit=6)
        if not entries:
            st.markdown(
                '<div style="color:#bbb;font-size:13px;text-align:center;padding:16px 0;">'
                'Chưa có bản dịch nào được lưu.</div>',
                unsafe_allow_html=True
            )
        else:
            import html as _htmllib, urllib.parse as _urlparse
            _uq = (
                f"user={_urlparse.quote(str(st.session_state['user']))}"
                f"&name={_urlparse.quote(str(st.session_state['username']))}"
                f"&page=home"
            )
            st.markdown("""
<style>
.jentry-wrap{display:flex;align-items:center;background:white;border-radius:10px;
  box-shadow:0 1px 6px rgba(38,38,96,0.08);padding:10px 14px;margin-bottom:8px;
  gap:10px;font-size:13px;font-family:sans-serif;transition:background .15s,box-shadow .15s;}
.jentry-wrap:hover{background:#f0f4ff;box-shadow:0 2px 10px rgba(38,38,96,0.13);}
.jentry-main{display:flex;flex:1;align-items:center;gap:10px;min-width:0;overflow:hidden;}
.jentry-inp{color:#262660;font-weight:600;flex:1;overflow:hidden;
  white-space:nowrap;text-overflow:ellipsis;min-width:0;}
.jentry-out{color:#444;flex:1;overflow:hidden;white-space:nowrap;
  text-overflow:ellipsis;min-width:0;}
.jentry-arrow{color:#f69322;font-size:16px;flex-shrink:0;}
.jentry-acts{display:flex;gap:4px;flex-shrink:0;align-items:center;}
.jbtn-a{border:1px solid #eee!important;background:white!important;font-size:14px;
  padding:3px 7px;border-radius:7px;line-height:1.5;color:#888!important;
  transition:.15s;text-decoration:none!important;display:inline-block;}
.jbtn-a:hover{background:#f5f5f5!important;border-color:#ccc!important;color:#262660!important;}
</style>
""", unsafe_allow_html=True)
            for _je in entries:
                _id       = _je["id"]
                _inp_raw  = _je["input"] or ""
                _out_raw  = _je["output"] or ""
                _inp_disp = _htmllib.escape(_inp_raw[:40])
                _out_disp = _htmllib.escape(_out_raw[:40])
                _star_ico = "⭐" if _je.get("starred") else "☆"
                _star_href = f"?{_uq}&action=star&action_id={_id}"
                _del_href  = f"?{_uq}&action=del&action_id={_id}"
                st.markdown(f"""
<div class="jentry-wrap">
  <div class="jentry-main">
    <span class="jentry-inp">{_inp_disp}</span>
    <span class="jentry-arrow">→</span>
    <span class="jentry-out">{_out_disp}</span>
  </div>
  <div class="jentry-acts">
    <a href="{_star_href}" target="_self" class="jbtn-a" title="Lưu lại">{_star_ico}</a>
    <a href="{_del_href}" target="_self" class="jbtn-a" title="Xóa">🗑️</a>
  </div>
</div>""", unsafe_allow_html=True)
    else:
        # Hiển thị từ localStorage qua JS component
        components.html("""
<style>
*{box-sizing:border-box;}
body{margin:0;padding:0;}
.jentry{background:white;border-radius:10px;box-shadow:0 1px 6px rgba(38,38,96,0.08);
        padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;
        gap:10px;font-size:13px;font-family:sans-serif;
        transition:background .15s,box-shadow .15s;}
.jentry:hover{background:#f0f4ff;box-shadow:0 2px 10px rgba(38,38,96,0.13);}
.jentry-inp{color:#262660;font-weight:600;flex:1;overflow:hidden;
            white-space:nowrap;text-overflow:ellipsis;min-width:0;}
.jentry-out{color:#444;flex:1;overflow:hidden;white-space:nowrap;
            text-overflow:ellipsis;min-width:0;}
.jentry-arrow{color:#f69322;font-size:16px;flex-shrink:0;}
.jentry-actions{display:flex;gap:4px;flex-shrink:0;align-items:center;}
.jbtn{border:1px solid #eee;background:white;cursor:pointer;font-size:14px;
      padding:3px 7px;border-radius:7px;line-height:1.5;color:#888;
      transition:0.15s;font-family:sans-serif;}
.jbtn:hover{background:#f5f5f5;border-color:#ccc;color:#262660;}
.empty-note{color:#bbb;font-size:13px;text-align:center;padding:16px 0;}
</style>
<div id="journal-root"></div>
<script>
(function(){
    var K='nomnasite_history';
    function load(){return JSON.parse(localStorage.getItem(K)||'[]');}
    function save(h){localStorage.setItem(K,JSON.stringify(h));}
    function render(){
        var h=load();
        var root=document.getElementById('journal-root');
        if(!root)return;
        if(h.length===0){
            root.innerHTML='<div class="empty-note">Chưa có bản dịch nào. Hãy thử dịch một câu!</div>';
            return;
        }
        var html='';
        function b64enc(s){return btoa(unescape(encodeURIComponent(s)));}
        h.slice(0,6).forEach(function(e,i){
            var star=e.starred?'⭐':'☆';
            html+='<div class="jentry" style="cursor:pointer"'
                +' data-inp="'+b64enc(e.input||'')+'"'
                +' data-out="'+b64enc(e.output||'')+'">'
                +'<span class="jentry-inp">'+(e.input||'').substring(0,40)+'</span>'
                +'<span class="jentry-arrow">→</span>'
                +'<span class="jentry-out">'+(e.output||'').substring(0,40)+'</span>'
                +'<div class="jentry-actions">'
                +'<button class="jbtn" onclick="jStar('+i+')" title="Lưu lại">'+star+'</button>'
                +'<button class="jbtn" onclick="jDel('+i+')" title="Xóa">🗑️</button>'
                +'</div>'
                +'</div>';
        });
        root.innerHTML=html;
        // click để tải lên ô dịch qua URL param (tránh cross-frame textarea access)
        root.querySelectorAll('.jentry[data-inp]').forEach(function(je){
            je.addEventListener('click',function(ev){
                if(ev.target.closest('.jbtn')) return;
                var p=new URLSearchParams(window.parent.location.search);
                p.set('page','home');
                p.set('load_inp',je.dataset.inp);
                if(je.dataset.out) p.set('load_out',je.dataset.out);
                window.parent.location.search=p.toString();
            });
        });
    }
    window.jStar=function(i){
        var h=load();
        if(!h[i])return;
        h[i].starred=!h[i].starred;
        save(h);render();
    };
    window.jDel=function(i){
        var h=load();
        h.splice(i,1);
        save(h);render();
    };
    render();
})();
</script>
""", height=380, scrolling=False)

        st.markdown(
            '<p class="journal-guest-note">🔒 '
            '<a href="/?page=login" target="_self">Đăng nhập</a> '
            'để lưu nhật ký lên máy chủ và đồng bộ đa thiết bị.</p>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ===== FEATURE CARDS =====
    st.markdown('<div class="section-label">⚡ Tính năng nổi bật</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="feat-grid">
        <div class="feat-card">
            <div class="feat-icon">🔍</div>
            <div class="feat-title">OCR Hán Nôm</div>
            <div class="feat-desc">Nhận diện chữ từ ảnh bằng mô hình CRNN chuyên biệt</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">📖</div>
            <div class="feat-title">Từ điển</div>
            <div class="feat-desc">Tra cứu nghĩa Hán Nôm – Quốc ngữ tức thì</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">🤖</div>
            <div class="feat-title">Dịch AI</div>
            <div class="feat-desc">Dịch thơ cổ và văn bản cổ theo ngữ cảnh</div>
        </div>
        <div class="feat-card">
            <div class="feat-icon">📜</div>
            <div class="feat-title">Lịch sử</div>
            <div class="feat-desc">Lưu và xem lại kết quả nhận dạng trước đó</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif page == "introduce":
    from page import introduce
    introduce.show()

elif page == "keyboardtutorial":
    from page import keyboardtutorial
    keyboardtutorial.show()

elif page == "usermanual":
    from page import usermanual
    usermanual.show()

elif page == "login":
    from page import login
    login.show()

elif page == "register":
    from page import register
    register.show()

elif page == "nomnasite":
    from page import nomnasite
    nomnasite.show()

elif page == "change_password":
    from page import changepassword
    changepassword.show()

elif page == "forgot_password":
    from page import forgotpassword
    forgotpassword.show()

elif page == "resetpassword":
    from page import resetpassword
    resetpassword.show()

elif page == "history":
    from page import history
    history.show()

elif page == "admin":
    admin_page.show()

# BOX END
