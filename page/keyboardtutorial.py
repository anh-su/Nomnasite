import streamlit as st

def show():
    st.markdown("""
    <style>
    .kb-hero {
        background: linear-gradient(135deg, #1a1a50 0%, #262660 60%, #f69322 160%);
        border-radius: 18px; padding: 28px 36px; margin-bottom: 28px;
        display: flex; align-items: center; gap: 20px;
    }
    .kb-hero-icon {
        font-size: 52px; background: rgba(255,255,255,0.12);
        border-radius: 14px; width: 72px; height: 72px;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .kb-hero-title { color: white; font-size: 30px; font-weight: 900; margin: 0 0 4px 0; letter-spacing: 2px; }
    .kb-hero-sub   { color: rgba(255,255,255,0.75); font-size: 14px; margin: 0; }

    .kb-section {
        background: white; border-radius: 14px;
        box-shadow: 0 2px 12px rgba(38,38,96,0.08);
        padding: 22px 26px; margin-bottom: 20px;
        border-left: 4px solid #f69322;
    }
    .kb-section-title {
        font-size: 18px; font-weight: 800; color: #262660;
        margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px;
    }
    .kb-section p { color: #444; font-size: 14px; line-height: 1.7; margin: 0 0 8px 0; }

    .kb-group-title {
        font-size: 13px; font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; margin: 20px 0 10px 0;
        padding: 6px 14px; border-radius: 20px; display: inline-block;
    }
    .g-phil  { background: #fff3e0; color: #e65100; }
    .g-strok { background: #e8f5e9; color: #2e7d32; }
    .g-body  { background: #e3f2fd; color: #1565c0; }
    .g-shape { background: #f3e5f5; color: #6a1b9a; }
    .g-spec  { background: #fce4ec; color: #880e4f; }

    .key-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 10px; margin-bottom: 6px;
    }
    .key-card {
        border-radius: 10px; padding: 12px 10px; text-align: center;
        box-shadow: 0 1px 6px rgba(0,0,0,0.07);
        transition: transform .15s, box-shadow .15s;
        position: relative; overflow: hidden;
    }
    .key-card:hover { transform: translateY(-2px); box-shadow: 0 4px 14px rgba(0,0,0,0.13); }
    .key-badge {
        display: inline-block; width: 34px; height: 34px; line-height: 34px;
        border-radius: 8px; font-size: 16px; font-weight: 900;
        margin-bottom: 6px; color: white;
    }
    .key-char  { font-size: 22px; display: block; margin-bottom: 2px; line-height: 1; }
    .key-name  { font-size: 11px; font-weight: 700; color: #555; margin-bottom: 4px; }
    .key-desc  { font-size: 10px; color: #888; line-height: 1.4; text-align: left; }

    .c-phil  { background: #fff8f0; }
    .c-strok { background: #f1faf2; }
    .c-body  { background: #f0f7ff; }
    .c-shape { background: #faf0ff; }
    .c-spec  { background: #fff0f5; }

    .b-phil  { background: #e65100; }
    .b-strok { background: #2e7d32; }
    .b-body  { background: #1565c0; }
    .b-shape { background: #6a1b9a; }
    .b-spec  { background: #880e4f; }

    .example-box {
        background: #f8f9ff; border: 1px solid #e0e4f7;
        border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
    }
    .example-box .ex-title { font-size: 13px; font-weight: 700; color: #262660; margin-bottom: 8px; }
    .ex-step {
        display: inline-flex; align-items: center; gap: 6px;
        background: white; border: 1px solid #dde; border-radius: 8px;
        padding: 6px 12px; margin: 4px 4px 4px 0; font-size: 14px;
    }
    .ex-key {
        background: #262660; color: white; border-radius: 5px;
        padding: 2px 8px; font-family: monospace; font-size: 13px; font-weight: 700;
    }
    .ex-char { font-size: 22px; color: #f69322; font-weight: bold; }
    .ex-arrow { color: #f69322; font-size: 18px; }

    .tip-box {
        background: linear-gradient(90deg, #fff8e1, #fffde7);
        border-left: 4px solid #ffc107; border-radius: 0 10px 10px 0;
        padding: 12px 16px; margin: 14px 0; font-size: 13px; color: #555;
    }
    .tip-box strong { color: #e65100; }

    .wildcard-box {
        background: #f0f4ff; border-radius: 10px; padding: 14px 18px;
        border: 1px solid #c5cff7; font-size: 13px; color: #333; margin-top: 10px;
    }
    .wildcard-box .wc-key {
        display: inline-block; background: #262660; color: white;
        border-radius: 6px; padding: 2px 10px; font-weight: 900;
        font-size: 16px; margin-right: 8px; vertical-align: middle;
    }

    .tool-link-box {
        background: linear-gradient(135deg, #262660, #3a3a8a);
        border-radius: 14px; padding: 20px 24px; text-align: center; margin-top: 20px;
    }
    .tool-link-box p  { color: rgba(255,255,255,0.8); font-size: 14px; margin: 0 0 12px 0; }
    .tool-link-box a  {
        background: #f69322; color: white; font-weight: 700; font-size: 15px;
        padding: 10px 28px; border-radius: 8px; text-decoration: none;
        display: inline-block; transition: background .2s;
    }
    .tool-link-box a:hover { background: #e07d10; }
    </style>
    """, unsafe_allow_html=True)

    # ── HERO ──
    st.markdown("""
    <div class="kb-hero">
        <div class="kb-hero-icon">⌨️</div>
        <div>
            <div class="kb-hero-title">HƯỚNG DẪN BỘ GÕ CHỮ NÔM</div>
            <div class="kb-hero-sub">Bộ gõ Thương Hiệt (Cangjie) · Nhập chữ Hán Nôm bằng bàn phím tiêu chuẩn</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PHẦN I: GIỚI THIỆU ──
    st.markdown("""
    <div class="kb-section">
        <div class="kb-section-title">📖 I. Bộ gõ Thương Hiệt là gì?</div>
        <p>Bộ gõ <strong>Thương Hiệt</strong> được sáng tạo năm <strong>1976</strong> bởi <strong>Châu Bang Phục (朱邦復)</strong>,
        hỗ trợ gõ chữ Hán vào máy tính bằng bàn phím tiêu chuẩn.</p>
        <p>Thay vì dựa vào ngữ âm (Pinyin, âm Hán Việt…), người dùng dựa vào <strong>tự dạng</strong> (hình dạng của chữ)
        để gõ — giúp xử lý được cả những chữ lạ chưa biết cách đọc.</p>
        <p>Mỗi chữ được phân tích thành các <strong>"tự căn"</strong> (字根) — 24 thành phần cơ bản,
        mỗi thành phần ứng với một phím trên bàn phím QWERTY. Các phím được chia thành 4 nhóm chính:</p>
    </div>
    """, unsafe_allow_html=True)

    # ── NHÓM 1: TRIẾT LÝ ──
    st.markdown('<div class="kb-group-title g-phil">🌞 Nhóm Triết lý — Philosophical Set (A → G)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="key-grid">
        <div class="key-card c-phil">
            <div class="key-badge b-phil">A</div>
            <span class="key-char">日</span>
            <div class="key-name">Nhật</div>
            <div class="key-desc">日, 曰 và các biến thể xoay 90°</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">B</div>
            <span class="key-char">月</span>
            <div class="key-name">Nguyệt</div>
            <div class="key-desc">4 nét trên của 目, 冂, 爫, 冖</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">C</div>
            <span class="key-char">金</span>
            <div class="key-name">Kim</div>
            <div class="key-desc">金, 八, 儿, ソ, ハ, 丷</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">D</div>
            <span class="key-char">木</span>
            <div class="key-name">Mộc</div>
            <div class="key-desc">木, 2 nét đầu của 寸, 才, 也, 皮</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">E</div>
            <span class="key-char">水</span>
            <div class="key-name">Thủy</div>
            <div class="key-desc">氵, 又, 氺</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">F</div>
            <span class="key-char">火</span>
            <div class="key-name">Hỏa</div>
            <div class="key-desc">小, 灬, 3 nét đầu của 當, 光</div>
        </div>
        <div class="key-card c-phil">
            <div class="key-badge b-phil">G</div>
            <span class="key-char">土</span>
            <div class="key-name">Thổ</div>
            <div class="key-desc">土, 士</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── NHÓM 2: BÚT HOẠCH ──
    st.markdown('<div class="kb-group-title g-strok">✒️ Nhóm Bút hoạch — Strokes Set (H → N)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="key-grid">
        <div class="key-card c-strok">
            <div class="key-badge b-strok">H</div>
            <span class="key-char">竹</span>
            <div class="key-name">Trúc</div>
            <div class="key-desc">Nét xiên ㄏ, 丿, ノ; bộ trúc 竹</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">I</div>
            <span class="key-char">戈</span>
            <div class="key-name">Qua</div>
            <div class="key-desc">Nét chấm 、, 广, 厶</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">J</div>
            <span class="key-char">十</span>
            <div class="key-name">Thập</div>
            <div class="key-desc">十, 宀</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">K</div>
            <span class="key-char">大</span>
            <div class="key-name">Đại</div>
            <div class="key-desc">Nét chữ X: 乂 ㄨ ナ 犭 疒 廴</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">L</div>
            <span class="key-char">中</span>
            <div class="key-name">Trung</div>
            <div class="key-desc">Nét sổ 丨, 衤</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">M</div>
            <span class="key-char">一</span>
            <div class="key-name">Nhất</div>
            <div class="key-desc">Nét ngang 一, 厂, 工</div>
        </div>
        <div class="key-card c-strok">
            <div class="key-badge b-strok">N</div>
            <span class="key-char">弓</span>
            <div class="key-name">Cung</div>
            <div class="key-desc">Nét cung, móc: フ ク 乙 亅 ㄱ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── NHÓM 3: NHÂN THỂ ──
    st.markdown('<div class="kb-group-title g-body">🧍 Nhóm Nhân thể — Body Set (O → R)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="key-grid">
        <div class="key-card c-body">
            <div class="key-badge b-body">O</div>
            <span class="key-char">人</span>
            <div class="key-name">Nhân</div>
            <div class="key-desc">Bộ nhân 人, 2 nét đầu của 丘, 知</div>
        </div>
        <div class="key-card c-body">
            <div class="key-badge b-body">P</div>
            <span class="key-char">心</span>
            <div class="key-name">Tâm</div>
            <div class="key-desc">忄, 匕, 七, 勹</div>
        </div>
        <div class="key-card c-body">
            <div class="key-badge b-body">Q</div>
            <span class="key-char">手</span>
            <div class="key-name">Thủ</div>
            <div class="key-desc">手, ヰ, 扌</div>
        </div>
        <div class="key-card c-body">
            <div class="key-badge b-body">R</div>
            <span class="key-char">口</span>
            <div class="key-name">Khẩu</div>
            <div class="key-desc">Bộ khẩu 口</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── NHÓM 4: TỰ HÌNH ──
    st.markdown('<div class="kb-group-title g-shape">🔷 Nhóm Tự hình — Shapes Set (S → Y)</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="key-grid">
        <div class="key-card c-shape">
            <div class="key-badge b-shape">S</div>
            <span class="key-char">尸</span>
            <div class="key-name">Thi</div>
            <div class="key-desc">匚, 2 nét đầu của 己 (コ)</div>
        </div>
        <div class="key-card c-shape">
            <div class="key-badge b-shape">T</div>
            <span class="key-char">廿</span>
            <div class="key-name">Trấp</div>
            <div class="key-desc">卄, 廾, 艸, 艹 (bộ thảo)</div>
        </div>
        <div class="key-card c-shape">
            <div class="key-badge b-shape">U</div>
            <span class="key-char">山</span>
            <div class="key-name">Sơn</div>
            <div class="key-desc">Ba mặt đóng trên: ㄩ 乚 屮</div>
        </div>
        <div class="key-card c-shape">
            <div class="key-badge b-shape">V</div>
            <span class="key-char">女</span>
            <div class="key-name">Nữ</div>
            <div class="key-desc">Móc bên phải hình V: ㄴ ㄑ &lt; レ</div>
        </div>
        <div class="key-card c-shape">
            <div class="key-badge b-shape">W</div>
            <span class="key-char">田</span>
            <div class="key-name">Điền</div>
            <div class="key-desc">Đóng 4 phía, trong có nét: 囗</div>
        </div>
        <div class="key-card c-shape">
            <div class="key-badge b-shape">Y</div>
            <span class="key-char">卜</span>
            <div class="key-name">Bốc</div>
            <div class="key-desc">卜, ㅏ, 亠, 辶</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PHÍM ĐẶC BIỆT ──
    st.markdown('<div class="kb-group-title g-spec">⚡ Phím đặc biệt</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="key-grid">
        <div class="key-card c-spec">
            <div class="key-badge b-spec">X</div>
            <span class="key-char">難</span>
            <div class="key-name">Nan / Trùng</div>
            <div class="key-desc">Chữ khó, dễ nhầm lẫn, trùng lặp</div>
        </div>
        <div class="key-card c-spec">
            <div class="key-badge b-spec">Z</div>
            <span class="key-char">符</span>
            <div class="key-name">Ký tự đặc biệt</div>
            <div class="key-desc">Dấu câu: 。、「」『』</div>
        </div>
        <div class="key-card c-spec">
            <div class="key-badge b-spec">*</div>
            <span class="key-char">?</span>
            <div class="key-name">Wildcard</div>
            <div class="key-desc">Thay thế bất kỳ phím từ vị trí 2–5</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── WILDCARD TIP ──
    st.markdown("""
    <div class="wildcard-box">
        <span class="wc-key">*</span>
        <strong>Ký tự đại diện (Wildcard):</strong>
        Có thể thay thế bất kỳ phím nào từ vị trí thứ 2 đến 5.
        Hữu ích khi chắc chắn về phím đầu và cuối.
        <br><br>
        <strong>Ví dụ:</strong> Nhập <code>竹 * 竹</code> → danh sách: 身, 物, 秒, 第
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── PHẦN II: BỘ GÕ CHỮ NÔM ──
    st.markdown("""
    <div class="kb-section">
        <div class="kb-section-title">🖊️ II. Bộ gõ Thương Hiệt cho chữ Nôm</div>
        <p>Bộ gõ Thương Hiệt được áp dụng để nhập liệu chữ Nôm trên nền tảng web,
        hỗ trợ chuyển tự chữ Nôm sang chữ Quốc ngữ tự động.</p>
        <p>Nguyên tắc phân tích <strong>tự căn</strong> hoàn toàn giống với chữ Hán thông thường —
        người dùng quan sát hình dạng chữ, xác định các thành phần, rồi gõ phím tương ứng.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── VÍ DỤ ──
    st.markdown("""
    <div class="tip-box">
        <strong>💡 Cách đọc ví dụ:</strong>
        Mỗi phím tương ứng một "tự căn" (thành phần của chữ). Gõ lần lượt các phím,
        công cụ sẽ đề xuất danh sách chữ phù hợp để chọn.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="example-box">
        <div class="ex-title">📌 Ví dụ 1 — Chữ "𤾓" (trăm · hundred)</div>
        <div class="ex-step"><span class="ex-key">m</span><span>一 nhất</span></div>
        <div class="ex-step"><span class="ex-key">a</span><span>日 nhật</span></div>
        <div class="ex-step"><span class="ex-key">d</span><span>木 mộc</span></div>
        <div class="ex-step"><span class="ex-key">d</span><span>木 mộc</span></div>
        <div class="ex-step"><span class="ex-key">1</span><span>chọn 1</span></div>
        <span class="ex-arrow">→</span>
        <span class="ex-char">𤾓</span>
    </div>
    <div class="example-box">
        <div class="ex-title">📌 Ví dụ 2 — Chữ "𥪝" (trong · inside)</div>
        <div class="ex-step"><span class="ex-key">y</span><span>卜 bốc</span></div>
        <div class="ex-step"><span class="ex-key">u</span><span>山 sơn</span></div>
        <div class="ex-step"><span class="ex-key">l</span><span>中 trung</span></div>
        <div class="ex-step"><span class="ex-key">1</span><span>chọn số</span></div>
        <span class="ex-arrow">→</span>
        <span class="ex-char">𥪝</span>
    </div>
    <div class="example-box">
        <div class="ex-title">📌 Ví dụ 3 — Hai câu thơ đầu Truyện Kiều (Nguyễn Du)</div>
        <p style="color:#555;font-size:13px;margin:0 0 8px 0;">
        Gõ từng chữ Nôm bằng tự căn, chọn kết quả phù hợp từ danh sách đề xuất:
        </p>
        <div style="font-size:22px;color:#262660;font-weight:bold;letter-spacing:3px;margin-bottom:6px;">
            百年𥪝𡎝人才
        </div>
        <div style="font-size:14px;color:#888;font-style:italic;">
            Trăm năm trong cõi người ta,
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── LINK CÔNG CỤ ──
    st.markdown("""
    <div class="tool-link-box">
        <p>Thực hành gõ và dịch chữ Hán Nôm ngay trên NomNaSite:</p>
        <a href="/?page=home" target="_self">⌨️ Đến trang gõ chữ</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TÓM TẮT NHANH ──
    with st.expander("📋 Bảng tóm tắt 24 tự căn"):
        st.markdown("""
| Phím | Tự căn | Nhóm | Mô tả chính |
|------|--------|------|-------------|
| **A** | 日 Nhật | Triết lý | Mặt trời, 日, 曰 |
| **B** | 月 Nguyệt | Triết lý | Mặt trăng, 冖, 冂 |
| **C** | 金 Kim | Triết lý | Vàng, 八, 儿 |
| **D** | 木 Mộc | Triết lý | Gỗ, 木 |
| **E** | 水 Thủy | Triết lý | Nước, 氵, 又 |
| **F** | 火 Hỏa | Triết lý | Lửa, 灬, 小 |
| **G** | 土 Thổ | Triết lý | Đất, 土, 士 |
| **H** | 竹 Trúc | Bút hoạch | Nét xiên, 丿 |
| **I** | 戈 Qua | Bút hoạch | Nét chấm, 广 |
| **J** | 十 Thập | Bút hoạch | Nét chữ thập, 宀 |
| **K** | 大 Đại | Bút hoạch | Nét chữ X |
| **L** | 中 Trung | Bút hoạch | Nét sổ 丨 |
| **M** | 一 Nhất | Bút hoạch | Nét ngang 一 |
| **N** | 弓 Cung | Bút hoạch | Nét móc, cung |
| **O** | 人 Nhân | Nhân thể | Bộ nhân 人 |
| **P** | 心 Tâm | Nhân thể | Bộ tâm 忄 |
| **Q** | 手 Thủ | Nhân thể | Tay, 扌 |
| **R** | 口 Khẩu | Nhân thể | Miệng, 口 |
| **S** | 尸 Thi | Tự hình | 匚, コ |
| **T** | 廿 Trấp | Tự hình | Bộ thảo 艹 |
| **U** | 山 Sơn | Tự hình | Núi, 乚, 屮 |
| **V** | 女 Nữ | Tự hình | Hình chữ V, ㄴ |
| **W** | 田 Điền | Tự hình | Khung đóng 囗 |
| **Y** | 卜 Bốc | Tự hình | 卜, 辶, 亠 |
        """)
