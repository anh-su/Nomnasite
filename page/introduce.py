from pathlib import Path
import streamlit as st

_CSS_FILE = Path(__file__).parent.parent / "css" / "introduce.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

    # TITLE
    st.markdown("""
    <div class="intro-main-title">HỆ THỐNG NHẬN DIỆN VÀ DỊCH CHỮ HÁN NÔM</div>
    <div class="intro-sub-title">Ứng dụng Trí Tuệ Nhân Tạo trong bảo tồn và hỗ trợ dịch văn bản Hán Nôm cổ</div>
    """, unsafe_allow_html=True)
    st.divider()

    # GIỚI THIỆU
    st.markdown('<div class="intro-section-label">📖 Giới thiệu đề tài</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="intro-quote">
        Trong kho tàng văn hóa Việt Nam, rất nhiều tài liệu cổ quý giá được viết bằng chữ Hán Nôm như
        <b>Truyện Kiều, Lục Vân Tiên, sắc phong, bia đá, gia phả</b> và các thơ văn lịch sử.
        Tuy nhiên số người có khả năng đọc và hiểu Hán Nôm ngày càng ít, gây khó khăn trong việc
        bảo tồn và khai thác các giá trị văn hóa truyền thống.<br><br>
        Đề tài <b>"Xây dựng hệ thống nhận diện và dịch chữ Hán Nôm"</b> được thực hiện nhằm ứng dụng
        công nghệ AI để hỗ trợ nhận diện chữ từ hình ảnh và dịch nghĩa sang tiếng Việt hiện đại.
    </div>
    """, unsafe_allow_html=True)

    # MỤC TIÊU
    st.markdown('<div class="intro-section-label">🎯 Mục tiêu đề tài</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="goal-grid">
        <div class="goal-card">
            <div class="g-icon">🔍</div>
            <div class="g-text">Nhận diện chữ Hán Nôm từ hình ảnh tài liệu cổ</div>
        </div>
        <div class="goal-card">
            <div class="g-icon">📝</div>
            <div class="g-text">Dịch nghĩa và phiên âm Hán Việt chính xác</div>
        </div>
        <div class="goal-card">
            <div class="g-icon">🤖</div>
            <div class="g-text">Ứng dụng AI vào bảo tồn văn hóa Việt Nam</div>
        </div>
        <div class="goal-card">
            <div class="g-icon">📚</div>
            <div class="g-text">Giúp người dùng tiếp cận văn bản cổ dễ dàng</div>
        </div>
        <div class="goal-card">
            <div class="g-icon">🏛️</div>
            <div class="g-text">Góp phần bảo tồn di sản Hán Nôm dân tộc</div>
        </div>
        <div class="goal-card">
            <div class="g-icon">🌐</div>
            <div class="g-text">Xây dựng nền tảng số hóa tài liệu lịch sử</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CHỨC NĂNG
    st.markdown('<div class="intro-section-label">⚡ Chức năng chính</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="feat-list">
        <div class="feat-item"><div class="f-check">✓</div> Upload ảnh chứa chữ Hán Nôm</div>
        <div class="feat-item"><div class="f-check">✓</div> Tự động phát hiện vùng văn bản (DBNet)</div>
        <div class="feat-item"><div class="f-check">✓</div> Nhận diện chữ bằng mô hình CRNN</div>
        <div class="feat-item"><div class="f-check">✓</div> Dịch nghĩa và phiên âm Hán Việt</div>
        <div class="feat-item"><div class="f-check">✓</div> Hỗ trợ chỉnh sửa và cải thiện kết quả OCR</div>
        <div class="feat-item"><div class="f-check">✓</div> Tra cứu từ điển Hán Nôm tức thì</div>
        <div class="feat-item"><div class="f-check">✓</div> Dịch AI theo ngữ cảnh thơ cổ</div>
        <div class="feat-item"><div class="f-check">✓</div> Lưu lịch sử và học từ phản hồi người dùng</div>
    </div>
    """, unsafe_allow_html=True)

    # CÔNG NGHỆ
    st.markdown('<div class="intro-section-label">🛠️ Công nghệ sử dụng</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="tech-grid">
        <div class="tech-badge"><div class="t-icon">🐍</div>Python</div>
        <div class="tech-badge"><div class="t-icon">🌊</div>Streamlit</div>
        <div class="tech-badge"><div class="t-icon">🧠</div>TensorFlow</div>
        <div class="tech-badge"><div class="t-icon">👁️</div>OpenCV</div>
        <div class="tech-badge"><div class="t-icon">🔤</div>CRNN</div>
        <div class="tech-badge"><div class="t-icon">🗄️</div>SQLite</div>
        <div class="tech-badge"><div class="t-icon">🤖</div>Groq AI</div>
        <div class="tech-badge"><div class="t-icon">🔥</div>Firebase</div>
    </div>
    """, unsafe_allow_html=True)

    # QUY TRÌNH
    st.markdown('<div class="intro-section-label">🔄 Quy trình hoạt động</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="timeline">
        <div class="tl-item" data-num="1">📤 &nbsp;<b>Tải ảnh lên</b> — Người dùng upload ảnh chứa văn bản Hán Nôm</div>
        <div class="tl-item" data-num="2">🔲 &nbsp;<b>Phát hiện vùng chữ</b> — DBNet tự động khoanh vùng các cột văn bản</div>
        <div class="tl-item" data-num="3">🔍 &nbsp;<b>Nhận diện ký tự</b> — Mô hình CRNN nhận dạng từng cột chữ Nôm</div>
        <div class="tl-item" data-num="4">📖 &nbsp;<b>Tra cứu từ điển</b> — Tìm kiếm nghĩa và phiên âm Hán Việt</div>
        <div class="tl-item" data-num="5">🤖 &nbsp;<b>Dịch AI</b> — Dịch nghĩa theo ngữ cảnh bằng Groq LLM nếu không có trong từ điển</div>
        <div class="tl-item" data-num="6">✏️ &nbsp;<b>Chỉnh sửa &amp; lưu</b> — Người dùng hiệu chỉnh để cải thiện dữ liệu training</div>
    </div>
    """, unsafe_allow_html=True)

    # HƯỚNG PHÁT TRIỂN
    st.markdown('<div class="intro-section-label">🚀 Hướng phát triển</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="dev-grid">
        <div class="dev-item"><div class="d-dot">▸</div> Tăng độ chính xác OCR với ảnh mờ và tài liệu cũ</div>
        <div class="dev-item"><div class="d-dot">▸</div> Dịch AI theo ngữ cảnh toàn bài thơ/văn bản</div>
        <div class="dev-item"><div class="d-dot">▸</div> Tự động sửa lỗi OCR dựa trên phản hồi người dùng</div>
        <div class="dev-item"><div class="d-dot">▸</div> Xây dựng kho dữ liệu Hán Nôm quy mô lớn</div>
        <div class="dev-item"><div class="d-dot">▸</div> Hỗ trợ nhận diện chữ viết tay Hán Nôm</div>
        <div class="dev-item"><div class="d-dot">▸</div> Xây dựng thư viện số tài liệu cổ Việt Nam</div>
    </div>
    """, unsafe_allow_html=True)

    # FOOTER
    st.markdown("""
    <div class="intro-footer">
        喃 &nbsp; Đồ án tốt nghiệp — Hệ thống nhận diện và dịch chữ Hán Nôm &nbsp; 喃
    </div>
    """, unsafe_allow_html=True)
