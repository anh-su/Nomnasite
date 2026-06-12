import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from services.firebase_roles import get_role, set_role
from services.ocr_session import _USE_CLOUD, _supa as _supa_client
from style import bg_css

load_dotenv(Path(__file__).parent.parent / ".env", override=True)



_DB = "database/dictionary.db"
_DICT_DB = _DB
_OCR_DB  = _DB
_CSS_FILE = Path(__file__).parent.parent / "css" / "admin.css"


def _is_admin() -> bool:
    """Kiểm tra admin: role == 'admin' (được set lúc login hoặc restore từ ADMIN_EMAILS)."""
    return st.session_state.get("role") == "admin"


def _dict_conn():
    return sqlite3.connect(_DICT_DB)


def _ocr_conn():
    return sqlite3.connect(_OCR_DB)


def _tbl(conn, name: str) -> bool:
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


# ── Data helpers ──────────────────────────────────────────────────────────

def _get_stats() -> dict:
    s = {}
    if _USE_CLOUD and _supa_client:
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            sess_all  = _supa_client.table("ocr_sessions").select("id, username, created_at").execute().data
            boxes_all = _supa_client.table("ocr_boxes").select("id, session_id, saved").execute().data
            s['sessions']   = len(sess_all)
            s['boxes']      = len(boxes_all)
            s['saved']      = sum(1 for b in boxes_all if b.get('saved'))
            s['users']      = len({r['username'] for r in sess_all})
            s['today_sess'] = sum(1 for r in sess_all if (r.get('created_at') or '')[:10] == today)
        except Exception:
            s.setdefault('sessions', 0); s.setdefault('boxes', 0)
            s.setdefault('saved', 0);    s.setdefault('users', 0)
            s.setdefault('today_sess', 0)
    else:
        with _ocr_conn() as c:
            s['sessions']   = c.execute("SELECT COUNT(*) FROM ocr_sessions").fetchone()[0]
            s['boxes']      = c.execute("SELECT COUNT(*) FROM ocr_boxes").fetchone()[0]
            s['saved']      = c.execute("SELECT COUNT(*) FROM ocr_boxes WHERE saved=1").fetchone()[0]
            s['users']      = c.execute("SELECT COUNT(DISTINCT username) FROM ocr_sessions").fetchone()[0]
            s['today_sess'] = c.execute(
                "SELECT COUNT(*) FROM ocr_sessions WHERE DATE(created_at)=DATE('now')"
            ).fetchone()[0]
    with _ocr_conn() as c:
        s['logs'] = c.execute("SELECT COUNT(*) FROM translation_log").fetchone()[0] if _tbl(c, 'translation_log') else 0
    with _dict_conn() as c:
        s['dict_main'] = c.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
        s['dict_ai']   = c.execute("SELECT COUNT(*) FROM ai_translations").fetchone()[0]
    return s


def _top_docs(n=8):
    if _USE_CLOUD and _supa_client:
        try:
            rows = _supa_client.table("ocr_sessions").select("doc_name, image_name").execute().data
            freq: dict = defaultdict(int)
            for r in rows:
                name = (r.get('doc_name') or '').strip() or (r.get('image_name') or '').strip() or 'Không tên'
                freq[name] += 1
            return sorted(freq.items(), key=lambda x: -x[1])[:n]
        except Exception:
            return []
    with _ocr_conn() as c:
        return c.execute("""
            SELECT COALESCE(NULLIF(TRIM(doc_name),''), NULLIF(TRIM(image_name),''), 'Không tên') AS ten,
                   COUNT(*) AS so_phien
            FROM ocr_sessions
            GROUP BY 1 ORDER BY 2 DESC LIMIT ?
        """, (n,)).fetchall()


def _activity_7d():
    cut = (datetime.now(timezone.utc) - timedelta(days=6)).strftime('%Y-%m-%d')
    if _USE_CLOUD and _supa_client:
        try:
            rows = _supa_client.table("ocr_sessions").select("created_at").gte("created_at", cut).execute().data
            day_cnt: dict = defaultdict(int)
            for r in rows:
                day = (r.get('created_at') or '')[:10]
                if day:
                    day_cnt[day] += 1
            return sorted(day_cnt.items())
        except Exception:
            return []
    with _ocr_conn() as c:
        return c.execute("""
            SELECT DATE(created_at) AS ngay, COUNT(*) AS phien
            FROM ocr_sessions WHERE DATE(created_at) >= ?
            GROUP BY 1 ORDER BY 1
        """, (cut,)).fetchall()


def _accuracy_dist():
    if _USE_CLOUD and _supa_client:
        try:
            rows = _supa_client.table("ocr_boxes").select("accuracy").limit(5000).execute().data
            raw = [(r['accuracy'],) for r in rows if r.get('accuracy')]
        except Exception:
            raw = []
    else:
        with _ocr_conn() as c:
            raw = c.execute("SELECT accuracy FROM ocr_boxes WHERE accuracy != '' LIMIT 5000").fetchall()
    buckets = {'≥90%': 0, '70–89%': 0, '50–69%': 0, '<50%': 0}
    for (a,) in raw:
        try:
            v = float(str(a).replace('%', '').strip())
            if   v >= 90: buckets['≥90%']   += 1
            elif v >= 70: buckets['70–89%'] += 1
            elif v >= 50: buckets['50–69%'] += 1
            else:         buckets['<50%']   += 1
        except Exception:
            pass
    return buckets


def _accuracy_trend():
    if _USE_CLOUD and _supa_client:
        try:
            rows = _supa_client.table("ocr_boxes").select("updated_at, accuracy").limit(2000).execute().data
            raw = [(r.get('updated_at', '')[:10], r['accuracy']) for r in rows if r.get('accuracy')]
        except Exception:
            raw = []
    else:
        with _ocr_conn() as c:
            raw = c.execute("""
                SELECT DATE(updated_at), accuracy FROM ocr_boxes
                WHERE accuracy != '' ORDER BY updated_at DESC LIMIT 2000
            """).fetchall()
    day_vals: dict = {}
    for ngay, a in raw:
        try:
            v = float(str(a).replace('%', '').strip())
            day_vals.setdefault(ngay, []).append(v)
        except Exception:
            pass
    return sorted((d, sum(vs) / len(vs)) for d, vs in day_vals.items())


def _user_list():
    if _USE_CLOUD and _supa_client:
        try:
            sess  = _supa_client.table("ocr_sessions").select("id, username, updated_at").execute().data
            boxes = _supa_client.table("ocr_boxes").select("session_id, saved").execute().data
            saved_map: dict = defaultdict(int)
            for b in boxes:
                if b.get('saved'):
                    saved_map[b['session_id']] += 1
            user_info: dict = defaultdict(lambda: {'phien': 0, 'da_luu': 0, 'lan_cuoi': ''})
            for s in sess:
                u = s['username']
                user_info[u]['phien'] += 1
                user_info[u]['da_luu'] += saved_map.get(s['id'], 0)
                t = s.get('updated_at') or ''
                if t > user_info[u]['lan_cuoi']:
                    user_info[u]['lan_cuoi'] = t
            # Gộp thêm user đã đăng nhập nhưng chưa OCR
            try:
                logins = _supa_client.table("user_logins").select("username, last_login").execute().data
                for row in logins:
                    u = row['username']
                    if u not in user_info:
                        user_info[u] = {'phien': 0, 'da_luu': 0, 'lan_cuoi': row.get('last_login', '')}
            except Exception:
                pass
            return sorted(
                [(u, d['phien'], d['da_luu'], d['lan_cuoi']) for u, d in user_info.items()],
                key=lambda x: -x[1]
            )
        except Exception:
            return []
    with _ocr_conn() as c:
        return c.execute("""
            SELECT username,
                   COUNT(DISTINCT s.id)          AS phien,
                   COALESCE(SUM(b.saved), 0)     AS da_luu,
                   MAX(COALESCE(s.updated_at, l.last_login)) AS lan_cuoi
            FROM user_logins l
            LEFT JOIN ocr_sessions s ON s.username = l.username
            LEFT JOIN ocr_boxes b ON b.session_id = s.id
            GROUP BY l.username ORDER BY phien DESC
        """).fetchall()


# ── Dictionary helpers ───────────────────────────────────────────────────

def _search_trans(kw: str, limit=60):
    lk = f"%{kw}%"
    with _dict_conn() as c:
        return c.execute("""
            SELECT id, vietnamese, han_nom, han_viet, meaning
            FROM translations
            WHERE vietnamese LIKE ? OR han_nom LIKE ? OR han_viet LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (lk, lk, lk, limit)).fetchall()


def _add_trans(vn, hn, hv, mg):
    with _dict_conn() as c:
        c.execute("INSERT INTO translations (vietnamese,han_nom,han_viet,meaning) VALUES (?,?,?,?)",
                  (vn, hn, hv, mg))
        c.commit()


def _del_trans(rid: int):
    with _dict_conn() as c:
        c.execute("DELETE FROM translations WHERE id=?", (rid,))
        c.commit()


def _get_trans(rid: int):
    with _dict_conn() as c:
        return c.execute(
            "SELECT id, vietnamese, han_nom, han_viet, meaning FROM translations WHERE id=?", (rid,)
        ).fetchone()


def _update_trans(rid: int, vn, hn, hv, mg):
    with _dict_conn() as c:
        c.execute(
            "UPDATE translations SET vietnamese=?, han_nom=?, han_viet=?, meaning=? WHERE id=?",
            (vn, hn, hv, mg, rid)
        )
        c.commit()


def _search_ai(kw: str, limit=60):
    lk = f"%{kw}%"
    with _dict_conn() as c:
        return c.execute("""
            SELECT id, nom_text, meaning, vi_meaning
            FROM ai_translations
            WHERE nom_text LIKE ? OR meaning LIKE ? OR vi_meaning LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (lk, lk, lk, limit)).fetchall()


def _add_ai(nom, phienam, nghia):
    with _dict_conn() as c:
        c.execute("INSERT OR REPLACE INTO ai_translations (nom_text,meaning,vi_meaning) VALUES (?,?,?)",
                  (nom, phienam, nghia))
        c.commit()


def _del_ai(rid: int):
    with _dict_conn() as c:
        c.execute("DELETE FROM ai_translations WHERE id=?", (rid,))
        c.commit()


def _get_ai(rid: int):
    with _dict_conn() as c:
        return c.execute(
            "SELECT id, nom_text, meaning, vi_meaning FROM ai_translations WHERE id=?", (rid,)
        ).fetchone()


def _update_ai(rid: int, nom, phienam, nghia):
    with _dict_conn() as c:
        c.execute(
            "UPDATE ai_translations SET nom_text=?, meaning=?, vi_meaning=? WHERE id=?",
            (nom, phienam, nghia, rid)
        )
        c.commit()


# ── Pending review helpers ───────────────────────────────────────────────

def _load_pending_items() -> list:
    """Trả về danh sách (filename, label) từ pending/labels.txt."""
    lbl = "ai/datasets/pending/labels.txt"
    if not os.path.exists(lbl):
        return []
    try:
        items = []
        for line in open(lbl, encoding="utf-8"):
            line = line.strip()
            if "|" in line:
                fname, label = line.split("|", 1)
                items.append((fname.strip(), label.strip()))
        return items
    except Exception:
        return []


def _remove_from_pending_labels(filename: str):
    lbl = "ai/datasets/pending/labels.txt"
    if not os.path.exists(lbl):
        return
    lines = open(lbl, encoding="utf-8").readlines()
    kept = [l for l in lines if not l.startswith(filename + "|")]
    with open(lbl, "w", encoding="utf-8") as f:
        f.writelines(kept)


def _approve_item(filename: str, label: str) -> bool:
    import shutil
    src_img = os.path.join("ai/datasets/pending/images", filename)
    dst_img = os.path.join("ai/datasets/approved/images", filename)
    dst_lbl = "ai/datasets/approved/labels.txt"
    try:
        os.makedirs("ai/datasets/approved/images", exist_ok=True)
        if os.path.exists(src_img):
            shutil.copy(src_img, dst_img)
        with open(dst_lbl, "a", encoding="utf-8") as f:
            f.write(f"{filename}|{label}\n")
        _remove_from_pending_labels(filename)
        if os.path.exists(src_img):
            os.remove(src_img)
        return True
    except Exception:
        return False


def _reject_item(filename: str) -> bool:
    import shutil
    src_img = os.path.join("ai/datasets/pending/images", filename)
    dst_img = os.path.join("ai/datasets/rejected/images", filename)
    rej_lbl = "ai/datasets/rejected/labels.txt"
    pnd_lbl = "ai/datasets/pending/labels.txt"
    try:
        # Lấy label trước khi xóa khỏi pending
        label = ""
        if os.path.exists(pnd_lbl):
            for line in open(pnd_lbl, encoding="utf-8"):
                if line.startswith(filename + "|"):
                    label = line.split("|", 1)[1].strip()
                    break

        os.makedirs("ai/datasets/rejected/images", exist_ok=True)
        if os.path.exists(src_img):
            shutil.move(src_img, dst_img)
        with open(rej_lbl, "a", encoding="utf-8") as f:
            f.write(f"{filename}|{label}\n")
        _remove_from_pending_labels(filename)
        return True
    except Exception:
        return False


# ── Tab renderers ─────────────────────────────────────────────────────────

def _render_dashboard(stats):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Phiên OCR",       f"{stats['sessions']:,}")
    c2.metric("Người dùng",      f"{stats['users']:,}")
    c3.metric("Lượt dịch",       f"{stats['logs']:,}")
    c4.metric("Từ điển",         f"{stats['dict_main'] + stats['dict_ai']:,}")
    c5.metric("Hôm nay",         f"{stats['today_sess']:,} phiên")

    st.markdown("---")

    col_a, col_b = st.columns([1.4, 1])

    with col_a:
        st.markdown("##### 📅 Phiên OCR 7 ngày gần nhất")
        act = _activity_7d()
        if act:
            df = pd.DataFrame(act, columns=['Ngày', 'Phiên'])
            _ymax = max(int(df['Phiên'].max()), 10)
            _c = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X('Ngày:T', title=None),
                    y=alt.Y('Phiên:Q', title='Phiên',
                            scale=alt.Scale(domain=[0, _ymax]),
                            axis=alt.Axis(format='d', labelOverlap=False,
                                          values=list(range(0, _ymax + 1)))),
                    tooltip=['Ngày:T', 'Phiên:Q'],
                )
                .properties(height=440)
                .configure_legend(labelFontSize=10, titleFontSize=10)
                .configure_axis(labelFontSize=11)
            )
            st.altair_chart(_c, use_container_width=True)
        else:
            st.caption("Chưa có dữ liệu.")

    with col_b:
        st.markdown("##### 📚 Tài liệu nhận diện nhiều nhất")
        docs = _top_docs(8)
        if docs:
            df2 = pd.DataFrame(docs, columns=['Tài liệu', 'Phiên'])
            df2.index = range(1, len(df2) + 1)
            df2.index.name = 'STT'
            st.dataframe(
                df2.style.set_properties(**{'text-align': 'center'})
                         .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
                use_container_width=True, height=230,
            )
        else:
            st.caption("Chưa có dữ liệu.")


def _render_stats(stats):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### ✅ Tỉ lệ chỉnh sửa boxes")
        pct = stats['saved'] / stats['boxes'] * 100 if stats['boxes'] else 0
        st.metric("Boxes đã lưu", f"{stats['saved']:,} / {stats['boxes']:,}")
        st.progress(min(pct / 100, 1.0))
        st.caption(f"{pct:.1f}% boxes đã được correction")

        st.markdown("##### 📖 Từ điển")
        st.metric("translations (chính)", f"{stats['dict_main']:,}")
        st.metric("ai_translations (AI)", f"{stats['dict_ai']:,}")

    with col2:
        st.markdown("##### 🤖 Độ chính xác CRNN")
        dist = _accuracy_dist()
        total = sum(dist.values())
        if total:
            good = dist['≥90%'] + dist['70–89%']
            st.metric("Nhận diện tốt (≥70%)", f"{good/total*100:.1f}%",
                      help="Tỉ lệ boxes có accuracy ≥ 70%")
            df_d = pd.DataFrame({
                'Khoảng': list(dist.keys()),
                'Ký tự': list(dist.values()),
            })
            df_d.index = range(1, len(df_d) + 1)
            df_d.index.name = 'STT'
            st.dataframe(
                df_d.style.set_properties(**{'text-align': 'center'})
                          .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
                use_container_width=True,
            )
        else:
            st.caption("Chưa có dữ liệu accuracy.")

    st.markdown("---")
    st.markdown("##### 👤 Hoạt động người dùng")
    users = _user_list()
    if users:
        df_u = pd.DataFrame(users, columns=['Username', 'Phiên OCR', 'Boxes đã lưu', 'Lần cuối'])
        df_u.index = range(1, len(df_u) + 1)
        df_u.index.name = 'STT'
        st.dataframe(
            df_u.style.set_properties(**{'text-align': 'center'})
                      .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
            use_container_width=True,
        )
    else:
        st.info("Chưa có dữ liệu.")


def _render_dictionary():
    dtype = st.radio(
        "Chọn từ điển:",
        ["translations  (Quốc ngữ ↔ Hán Nôm)", "ai_translations  (cụm Hán Nôm)"],
        horizontal=True, key="adm_dtype",
    )
    st.markdown("---")

    if dtype.startswith("translations"):
        kw = st.text_input("🔍 Tìm kiếm", placeholder="Quốc ngữ / Hán Nôm / Hán Việt...", key="adm_kw_t")
        rows = _search_trans(kw)
        if rows:
            st.caption(f"Hiển thị {len(rows)} kết quả (tối đa 60)")
            df = pd.DataFrame(rows, columns=['ID', 'Quốc ngữ', 'Hán Nôm', 'Hán Việt', 'Nghĩa'])
            df.index = range(1, len(df) + 1)
            df.index.name = 'STT'
            st.dataframe(
                df.style.set_properties(**{'text-align': 'center'})
                        .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
                use_container_width=True, height=300,
            )
            c_del, _ = st.columns([1, 3])
            rid = c_del.number_input("Xóa theo ID", min_value=0, value=0, step=1, key="adm_del_t")
            if st.button("🗑️ Xóa", key="adm_del_t_btn"):
                if rid > 0:
                    _del_trans(int(rid))
                    st.success(f"Đã xóa ID={rid}")
                    st.experimental_rerun()
        else:
            st.info("Không tìm thấy kết quả." if kw else "Nhập từ khóa để tìm kiếm.")

        with st.expander("➕ Thêm từ mới vào translations"):
            with st.form("f_add_trans"):
                r1c1, r1c2 = st.columns(2)
                vn = r1c1.text_input("Quốc ngữ *")
                hn = r1c2.text_input("Hán Nôm *")
                r2c1, r2c2 = st.columns(2)
                hv = r2c1.text_input("Hán Việt")
                mg = r2c2.text_input("Nghĩa")
                if st.form_submit_button("➕ Thêm"):
                    if vn.strip() and hn.strip():
                        _add_trans(vn.strip(), hn.strip(), hv.strip(), mg.strip())
                        st.success(f"Đã thêm: {vn} → {hn}")
                        st.experimental_rerun()
                    else:
                        st.warning("Quốc ngữ và Hán Nôm là bắt buộc.")

        with st.expander("✏️ Sửa từ trong translations"):
            load_col, _ = st.columns([1, 3])
            edit_id = load_col.number_input("ID cần sửa", min_value=0, value=0, step=1, key="adm_edit_t_id")
            if st.button("📂 Tải", key="adm_load_t_btn"):
                if edit_id > 0:
                    row = _get_trans(int(edit_id))
                    if row:
                        st.session_state["_edit_t"] = {"id": row[0], "vn": row[1], "hn": row[2], "hv": row[3], "mg": row[4]}
                    else:
                        st.warning(f"Không tìm thấy ID={edit_id}")
            et = st.session_state.get("_edit_t")
            if et:
                with st.form("f_edit_trans"):
                    st.caption(f"Đang sửa ID = **{et['id']}**")
                    ec1, ec2 = st.columns(2)
                    e_vn = ec1.text_input("Quốc ngữ *", value=et["vn"])
                    e_hn = ec2.text_input("Hán Nôm *",  value=et["hn"])
                    ec3, ec4 = st.columns(2)
                    e_hv = ec3.text_input("Hán Việt",   value=et["hv"] or "")
                    e_mg = ec4.text_input("Nghĩa",       value=et["mg"] or "")
                    if st.form_submit_button("💾 Lưu"):
                        if e_vn.strip() and e_hn.strip():
                            _update_trans(et["id"], e_vn.strip(), e_hn.strip(), e_hv.strip(), e_mg.strip())
                            st.session_state.pop("_edit_t", None)
                            st.success(f"Đã cập nhật ID={et['id']}")
                            st.experimental_rerun()
                        else:
                            st.warning("Quốc ngữ và Hán Nôm là bắt buộc.")

    else:
        kw = st.text_input("🔍 Tìm kiếm", placeholder="Cụm Hán Nôm / phiên âm / nghĩa...", key="adm_kw_ai")
        rows = _search_ai(kw)
        if rows:
            st.caption(f"Hiển thị {len(rows)} kết quả (tối đa 60)")
            df = pd.DataFrame(rows, columns=['ID', 'Hán Nôm', 'Phiên âm', 'Nghĩa tiếng Việt'])
            df.index = range(1, len(df) + 1)
            df.index.name = 'STT'
            st.dataframe(
                df.style.set_properties(**{'text-align': 'center'})
                        .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
                use_container_width=True, height=300,
            )
            c_del, _ = st.columns([1, 3])
            rid = c_del.number_input("Xóa theo ID", min_value=0, value=0, step=1, key="adm_del_ai")
            if st.button("🗑️ Xóa", key="adm_del_ai_btn"):
                if rid > 0:
                    _del_ai(int(rid))
                    st.success(f"Đã xóa ID={rid}")
                    st.experimental_rerun()
        else:
            st.info("Không tìm thấy kết quả." if kw else "Nhập từ khóa để tìm kiếm.")

        with st.expander("➕ Thêm cụm từ mới vào ai_translations"):
            with st.form("f_add_ai"):
                nom = st.text_input("Cụm Hán Nôm *")
                rc1, rc2 = st.columns(2)
                pa  = rc1.text_input("Phiên âm Hán Việt")
                vn2 = rc2.text_input("Nghĩa tiếng Việt")
                if st.form_submit_button("➕ Thêm"):
                    if nom.strip():
                        _add_ai(nom.strip(), pa.strip(), vn2.strip())
                        st.success(f"Đã thêm: {nom}")
                        st.experimental_rerun()
                    else:
                        st.warning("Cụm Hán Nôm là bắt buộc.")

        with st.expander("✏️ Sửa cụm từ trong ai_translations"):
            ai_load_col, _ = st.columns([1, 3])
            edit_ai_id = ai_load_col.number_input("ID cần sửa", min_value=0, value=0, step=1, key="adm_edit_ai_id")
            if st.button("📂 Tải", key="adm_load_ai_btn"):
                if edit_ai_id > 0:
                    row = _get_ai(int(edit_ai_id))
                    if row:
                        st.session_state["_edit_ai"] = {"id": row[0], "nom": row[1], "pa": row[2], "vn": row[3]}
                    else:
                        st.warning(f"Không tìm thấy ID={edit_ai_id}")
            eai = st.session_state.get("_edit_ai")
            if eai:
                with st.form("f_edit_ai"):
                    st.caption(f"Đang sửa ID = **{eai['id']}**")
                    e_nom = st.text_input("Cụm Hán Nôm *", value=eai["nom"])
                    eac1, eac2 = st.columns(2)
                    e_pa  = eac1.text_input("Phiên âm",        value=eai["pa"] or "")
                    e_vn2 = eac2.text_input("Nghĩa tiếng Việt", value=eai["vn"] or "")
                    if st.form_submit_button("💾 Lưu"):
                        if e_nom.strip():
                            _update_ai(eai["id"], e_nom.strip(), e_pa.strip(), e_vn2.strip())
                            st.session_state.pop("_edit_ai", None)
                            st.success(f"Đã cập nhật ID={eai['id']}")
                            st.experimental_rerun()
                        else:
                            st.warning("Cụm Hán Nôm là bắt buộc.")


def _render_users():
    if _USE_CLOUD and _supa_client:
        try:
            rows = _supa_client.table("ocr_sessions").select("username, updated_at").execute().data
            today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            week_str  = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')
            total = len({r['username'] for r in rows})
            today = len({r['username'] for r in rows if (r.get('updated_at') or '')[:10] == today_str})
            week  = len({r['username'] for r in rows if (r.get('updated_at') or '')[:10] >= week_str})
        except Exception:
            total = today = week = 0
    else:
        with _ocr_conn() as c:
            total  = c.execute("SELECT COUNT(DISTINCT username) FROM ocr_sessions").fetchone()[0]
            today  = c.execute(
                "SELECT COUNT(DISTINCT username) FROM ocr_sessions WHERE DATE(updated_at)=DATE('now')"
            ).fetchone()[0]
            week   = c.execute(
                "SELECT COUNT(DISTINCT username) FROM ocr_sessions WHERE DATE(updated_at)>=DATE('now','-7 days')"
            ).fetchone()[0]

    ca, cb, cc = st.columns(3)
    ca.metric("Tổng người dùng", total)
    cb.metric("Hoạt động 7 ngày", week)
    cc.metric("Hoạt động hôm nay", today)

    st.markdown("---")
    st.markdown("##### Phân quyền")
    with st.form("f_set_role"):
        r1, r2, r3 = st.columns([2, 1, 1])
        target_email = r1.text_input("Email người dùng")
        new_role     = r2.selectbox("Role", ["user", "admin"])
        r3.markdown("<br>", unsafe_allow_html=True)
        if r3.form_submit_button("✅ Gán"):
            if target_email.strip():
                id_token = st.session_state.get("id_token", "")
                try:
                    set_role(target_email.strip(), new_role, id_token)
                    st.success(f"Đã gán role **{new_role}** cho `{target_email.strip()}`")
                except Exception as e:
                    st.error(f"Lỗi: {e}")
            else:
                st.warning("Nhập email trước.")

    st.markdown("---")
    st.markdown("##### Khóa / Mở khóa / Xóa tài khoản")

    from services.firebase_admin_service import get_user_info, lock_user, unlock_user, delete_user as fb_delete_user

    with st.form("f_manage_account"):
        ma_email = st.text_input("Email tài khoản cần quản lý")
        ma_col1, ma_col2, ma_col3, ma_col4 = st.columns([2, 1, 1, 1])
        ma_col1.markdown("<br>", unsafe_allow_html=True)
        check_btn  = ma_col1.form_submit_button("🔍 Kiểm tra")
        lock_btn   = ma_col2.form_submit_button("🔒 Khóa")
        unlock_btn = ma_col3.form_submit_button("🔓 Mở khóa")
        del_btn    = ma_col4.form_submit_button("🗑️ Xóa")

        if ma_email.strip():
            if check_btn:
                info = get_user_info(ma_email.strip())
                if info:
                    status = "🔒 Đang bị khóa" if info["disabled"] else "✅ Hoạt động bình thường"
                    st.info(f"**{info['email']}** — {status}")
                else:
                    st.warning("Không tìm thấy tài khoản này trong Firebase.")

            elif lock_btn:
                if lock_user(ma_email.strip()):
                    st.success(f"Đã khóa tài khoản `{ma_email.strip()}`. Người dùng sẽ không đăng nhập được.")
                else:
                    st.error("Khóa thất bại. Kiểm tra email hoặc quyền admin.")

            elif unlock_btn:
                if unlock_user(ma_email.strip()):
                    st.success(f"Đã mở khóa tài khoản `{ma_email.strip()}`.")
                else:
                    st.error("Mở khóa thất bại.")

            elif del_btn:
                st.session_state["_pending_delete_email"] = ma_email.strip()

    # Xác nhận xóa (ngoài form để tránh double-submit)
    pending_del = st.session_state.get("_pending_delete_email")
    if pending_del:
        st.warning(f"⚠️ Xác nhận xóa vĩnh viễn tài khoản **`{pending_del}`**? Hành động này không thể hoàn tác.")
        c_yes, c_no, _ = st.columns([1, 1, 4])
        if c_yes.button("✅ Xác nhận xóa", key="confirm_del_btn"):
            if fb_delete_user(pending_del):
                st.success(f"Đã xóa vĩnh viễn tài khoản `{pending_del}`.")
            else:
                st.error("Xóa thất bại.")
            st.session_state.pop("_pending_delete_email", None)
            st.experimental_rerun()
        if c_no.button("❌ Hủy", key="cancel_del_btn"):
            st.session_state.pop("_pending_delete_email", None)
            st.experimental_rerun()

    st.markdown("---")
    st.markdown("##### Danh sách người dùng")
    users = _user_list()
    if users:
        search_kw = st.text_input(
            "🔍 Tìm kiếm người dùng",
            placeholder="Nhập username hoặc email...",
            key="user_search_kw"
        )
        df = pd.DataFrame(users, columns=['Username / Email', 'Phiên OCR', 'Boxes đã lưu', 'Lần cuối'])
        if search_kw.strip():
            mask = df['Username / Email'].str.contains(search_kw.strip(), case=False, na=False)
            df = df[mask].reset_index(drop=True)
            st.caption(f"Tìm thấy {len(df)} kết quả cho \"{search_kw.strip()}\"")
        if df.empty:
            st.info("Không tìm thấy người dùng phù hợp.")
        else:
            df.insert(0, 'STT', range(1, len(df) + 1))
            df = df.set_index('STT')
            st.dataframe(
                df.style.set_properties(**{'text-align': 'center'})
                        .set_table_styles([{'selector': 'th', 'props': [('text-align', 'center')]}]),
                use_container_width=True,
            )
    else:
        st.info("Chưa có dữ liệu.")


def _render_performance():
    assets = Path(__file__).parent.parent / "assets"

    ca, cb, cc = st.columns(3)
    for col, name in zip((ca, cb, cc), ("DBNet.h5", "CRNN.h5", "vocab.txt")):
        p = assets / name
        if p.exists():
            bytes_ = p.stat().st_size
            if bytes_ >= 1024 * 1024:
                col.metric(name, f"{bytes_ / (1024*1024):.1f} MB")
            else:
                col.metric(name, f"{bytes_ / 1024:.1f} KB")

    st.markdown("---")

    dist  = _accuracy_dist()
    total = sum(dist.values())

    if not total:
        st.info("Chưa có dữ liệu độ chính xác từ các phiên OCR.")
        return

    with _ocr_conn() as c:
        raw = c.execute(
            "SELECT accuracy FROM ocr_boxes WHERE accuracy != '' LIMIT 5000"
        ).fetchall()
    vals = []
    for (a,) in raw:
        try:
            vals.append(float(a.replace('%', '').strip()))
        except Exception:
            pass

    col1, col2, col3 = st.columns(3)
    col1.metric("Trung bình",   f"{sum(vals)/len(vals):.1f}%" if vals else "N/A")
    col2.metric("Cao nhất",     f"{max(vals):.1f}%" if vals else "N/A")
    col3.metric("Thấp nhất",    f"{min(vals):.1f}%" if vals else "N/A")

    st.markdown("##### Phân bố độ chính xác CRNN")
    df_d = pd.DataFrame({'Khoảng': list(dist.keys()), 'Số ký tự': list(dist.values())})
    _bar = (
        alt.Chart(df_d)
        .mark_bar()
        .encode(
            x=alt.X('Khoảng:N', sort=None, title='Khoảng'),
            y=alt.Y('Số ký tự:Q', scale=alt.Scale(domainMin=0), title='Số ký tự'),
            tooltip=['Khoảng:N', 'Số ký tự:Q'],
        )
        .properties(height=500)
        .configure_legend(labelFontSize=10, titleFontSize=10)
        .configure_axis(labelFontSize=11)
    )
    st.altair_chart(_bar, use_container_width=True)

    trend = _accuracy_trend()
    if len(trend) > 1:
        st.markdown("##### Xu hướng độ chính xác theo ngày")
        df_t = pd.DataFrame(trend, columns=['Ngày', 'Accuracy (%)'])
        _line = (
            alt.Chart(df_t)
            .mark_line(point=True)
            .encode(
                x=alt.X('Ngày:T', title='Ngày'),
                y=alt.Y('Accuracy (%):Q', scale=alt.Scale(domainMin=0), title='Accuracy (%)'),
                tooltip=['Ngày:T', 'Accuracy (%):Q'],
            )
            .properties(height=440)
            .configure_legend(labelFontSize=10, titleFontSize=10)
            .configure_axis(labelFontSize=11)
        )
        st.altair_chart(_line, use_container_width=True)



def _render_training():
    from services.dataset_service import get_dataset_stats, approve_all_pending

    st.markdown("##### 📦 Dataset hiện tại")
    ds = get_dataset_stats()
    total = sum(ds.values())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Approved",  ds["approved"])
    c2.metric("⏳ Pending",   ds["pending"])
    c3.metric("🤖 Generated", ds["generated"])
    c4.metric("❌ Rejected",  ds["rejected"])
    st.caption(f"Tổng: **{total}** mẫu — cần ít nhất **~200** mẫu approved để retrain hiệu quả.")

    st.markdown("---")

    # ── Duyệt từng mẫu ────────────────────────────────────────────────────
    st.markdown("##### 🔍 Duyệt từng mẫu Pending")
    items = _load_pending_items()

    if not items:
        st.info("Không có mẫu pending nào cần duyệt.")
    else:
        PAGE_SIZE = 5
        total_pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
        cur_page = st.session_state.get("_pending_page", 0)
        cur_page = min(cur_page, total_pages - 1)
        st.session_state["_pending_page"] = cur_page

        page_items = items[cur_page * PAGE_SIZE: (cur_page + 1) * PAGE_SIZE]
        st.caption(f"Trang {cur_page + 1}/{total_pages} — tổng {len(items)} mẫu đang chờ duyệt")

        for fname, label in page_items:
            img_path = os.path.join("ai/datasets/pending/images", fname)
            col_img, col_lbl, col_apv, col_rej = st.columns([2, 4, 1, 1])

            with col_img:
                if os.path.exists(img_path):
                    try:
                        from PIL import Image as _PILImg
                        st.image(_PILImg.open(img_path), use_column_width=True)
                    except Exception:
                        st.caption("(ảnh lỗi)")
                else:
                    st.caption("(không có ảnh)")

            with col_lbl:
                st.markdown(f"**Nhãn đề xuất:**")
                st.markdown(
                    f"<span style='font-size:1.6em; font-family:serif'>{label}</span>",
                    unsafe_allow_html=True,
                )
                st.caption(fname)

            safe = str(abs(hash(fname)))
            with col_apv:
                if st.button("✅", key=f"apv_{safe}", help="Duyệt → approved"):
                    if _approve_item(fname, label):
                        st.experimental_rerun()

            with col_rej:
                if st.button("❌", key=f"rej_{safe}", help="Từ chối → xoá"):
                    if _reject_item(fname):
                        st.experimental_rerun()

            st.markdown("---")

        # Pagination
        pg_l, pg_m, pg_r = st.columns([1, 2, 1])
        with pg_l:
            if cur_page > 0:
                if st.button("◀ Trước", key="pg_prev"):
                    st.session_state["_pending_page"] -= 1
                    st.experimental_rerun()
        with pg_m:
            st.caption(f"Trang {cur_page + 1} / {total_pages}")
        with pg_r:
            if cur_page < total_pages - 1:
                if st.button("Tiếp ▶", key="pg_next"):
                    st.session_state["_pending_page"] += 1
                    st.experimental_rerun()

    st.markdown("---")

    # ── Duyệt tất cả ──────────────────────────────────────────────────────
    st.markdown("##### ✅ Duyệt tất cả")
    st.info(f"Hiện có **{ds['pending']}** mẫu đang chờ duyệt.")
    if st.button("✅ Duyệt tất cả pending → approved", key="approve_all_btn"):
        n = approve_all_pending()
        if n:
            st.success(f"Đã duyệt {n} mẫu.")
            st.session_state["_pending_page"] = 0
            st.experimental_rerun()
        else:
            st.info("Không có mẫu pending nào.")

    st.markdown("---")

    # ── Retrain ────────────────────────────────────────────────────────────
    st.markdown("##### 🔁 Retrain CRNN")
    assets = Path(__file__).parent.parent / "assets"
    retrained_path = assets / "CRNN_retrained.h5"

    col_train, col_apply = st.columns(2)

    with col_train:
        if ds["approved"] < 10:
            st.warning("Cần ít nhất 10 mẫu approved để retrain.")
        else:
            if st.button("🚀 Bắt đầu Retrain", key="retrain_btn", type="primary"):
                try:
                    import sys
                    root = str(Path(__file__).parent.parent)
                    if root not in sys.path:
                        sys.path.insert(0, root)
                    from ai.training.retrain_crnn import retrain_crnn

                    status_box  = st.empty()
                    chart_box   = st.empty()
                    loss_history = []

                    def _on_epoch(ep, total, loss):
                        loss_history.append({"Epoch": ep, "Loss": loss})
                        status_box.caption(f"⏳ Epoch {ep}/{total} — loss: **{loss:.4f}**")
                        if len(loss_history) > 1:
                            df_loss = pd.DataFrame(loss_history).set_index("Epoch")
                            chart_box.line_chart(df_loss, height=180)

                    status_box.caption("⏳ Đang khởi động...")
                    retrain_crnn(on_epoch_end=_on_epoch)
                    status_box.empty()

                    # Hiển thị biểu đồ loss cuối cùng
                    if loss_history:
                        st.markdown("**📉 Loss theo epoch**")
                        df_final = pd.DataFrame(loss_history).set_index("Epoch")
                        st.line_chart(df_final, height=200)
                        best = min(loss_history, key=lambda x: x["Loss"])
                        st.caption(f"Loss tốt nhất: **{best['Loss']:.4f}** tại epoch {best['Epoch']}")

                    st.success("Retrain xong! Model mới: `assets/CRNN_retrained.h5`")
                except Exception as e:
                    st.error(f"Lỗi retrain: {e}")

    with col_apply:
        if retrained_path.exists():
            sz = retrained_path.stat().st_size / (1024 * 1024)
            st.info(f"Model mới đã sẵn sàng: **{sz:.1f} MB**")
            if st.button("🔄 Áp dụng model mới", key="apply_model_btn"):
                import shutil
                try:
                    shutil.copy(str(retrained_path), str(assets / "CRNN.h5"))
                    st.cache_resource.clear()
                    st.success("Model CRNN đã được cập nhật! App sẽ load model mới ở lần dùng tiếp theo.")
                except Exception as e:
                    st.error(f"Lỗi áp dụng model: {e}")
        else:
            st.caption("Chưa có model được retrain.")

    st.markdown("---")

    # ── Thông tin vòng lặp ────────────────────────────────────────────────
    st.markdown("##### ℹ️ Vòng lặp tự học")
    st.markdown("""
    ```
    User lưu correction
         ↓
    auto_approve() kiểm tra (rỗng / ASCII / tỉ lệ Hán Nôm < 80%)
         ↓
    ┌─ không hợp lệ → rejected/ (bỏ qua)
    └─ hợp lệ      → pending/  (admin duyệt thủ công)
         ↓
    Admin duyệt từng mẫu ✅/❌ hoặc "Duyệt tất cả"
         ↓
    Admin nhấn "Retrain" → CRNN fine-tune trên approved/
         ↓
    Admin nhấn "Áp dụng" → CRNN.h5 được thay thế
         ↓
    App reload → model mới có hiệu lực
    ```
    """)


# ── Entry point ───────────────────────────────────────────────────────────

def show():
    if "username" not in st.session_state:
        st.warning("Vui lòng đăng nhập để truy cập trang này.")
        return

    if not _is_admin():
        st.error("🚫 Bạn không có quyền truy cập trang quản trị.")
        st.caption(f"Tài khoản hiện tại: {st.session_state.get('user', '')}")
        return

    if _CSS_FILE.exists():
        st.markdown(
            f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    st.markdown(bg_css(), unsafe_allow_html=True)

    st.markdown(f"""
    <div class="adm-header">
        <h2>⚙️ Quản trị hệ thống</h2>
        <p>Xin chào <b>{st.session_state.get("username", "Admin")}</b> &nbsp;—&nbsp; NomNaSite Admin Panel</p>
    </div>
    """, unsafe_allow_html=True)

    stats = _get_stats()

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Tổng quan",
        "📈 Thống kê",
        "📖 Từ điển",
        "👤 Người dùng",
        "🤖 Hiệu suất mô hình",
        "🔬 Huấn luyện",
    ])

    with tab1: _render_dashboard(stats)
    with tab2: _render_stats(stats)
    with tab3: _render_dictionary()
    with tab4: _render_users()
    with tab5: _render_performance()
    with tab6: _render_training()
