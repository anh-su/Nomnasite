from pathlib import Path
import streamlit as st

_CSS_FILE = Path(__file__).parent.parent / "css" / "usermanual.css"


def show():
    st.markdown(f"<style>{_CSS_FILE.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)



    # TITLE
    st.markdown("""
    <div class="main-title">
        HƯỚNG DẪN SỬ DỤNG  HỆ THỐNG 
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sub-title">
        Hướng dẫn sử dụng website nhận diện và dịch chữ Hán Nôm
    </div>
    """, unsafe_allow_html=True)

    st.divider()



    # GIỚI THIỆU
    st.markdown("""
    <div class="section-title">
        Giới thiệu đề tài
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="text-content">

    Trong kho tàng văn hóa Việt Nam, rất nhiều tài liệu cổ quý giá được viết bằng chữ Hán Nôm như:
    Truyện Kiều, Lục Vân Tiên, sắc phong, bia đá, gia phả, thơ văn cổ và các tài liệu lịch sử.

    Tuy nhiên hiện nay số người có khả năng đọc và hiểu Hán Nôm ngày càng ít,
    gây khó khăn trong việc bảo tồn và khai thác các giá trị văn hóa truyền thống.

    Đề tài “Xây dựng hệ thống nhận diện và dịch chữ Hán Nôm”
    được thực hiện nhằm ứng dụng công nghệ trí tuệ nhân tạo (AI)
    để hỗ trợ nhận diện chữ từ hình ảnh và dịch nghĩa sang tiếng Việt hiện đại.

    </div>
    """, unsafe_allow_html=True)

    st.divider()



    # MỤC TIÊU
    st.markdown("""
    <div class="section-title">
        Mục tiêu của đề tài
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    - Hỗ trợ nhận diện chữ Hán Nôm từ hình ảnh

    - Hỗ trợ dịch nghĩa và phiên âm Hán Việt

    - Giúp người dùng tiếp cận văn bản cổ dễ dàng hơn

    - Ứng dụng AI vào lĩnh vực ngôn ngữ và văn hóa Việt Nam

    - Góp phần bảo tồn di sản Hán Nôm
    """)

    st.divider()



    # CHỨC NĂNG
    st.markdown("""
    <div class="section-title">
        Chức năng chính
    </div>
    """, unsafe_allow_html=True)

    st.success("Upload ảnh chứa chữ Hán Nôm")
    st.success("Tự động phát hiện vùng văn bản")
    st.success("Nhận diện chữ bằng mô hình CRNN")
    st.success("Dịch nghĩa và phiên âm Hán Việt")
    st.success("Hỗ trợ chỉnh sửa kết quả OCR")
    st.success("Tra cứu từ điển Hán Nôm")
    st.success("Hỗ trợ dịch cụm từ và thơ cổ")

    st.divider()



    # CÔNG NGHỆ
    st.markdown("""
    <div class="section-title">
        Công nghệ sử dụng
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        st.info("Python")
        st.info("Streamlit")
        st.info("CRNN")
        st.info("OpenCV")

    with col2:

        st.info("TensorFlow")
        st.info("SQLite")
        st.info("Firebase")
        st.info("Machine Learning")

    st.divider()



    # QUY TRÌNH
    st.markdown("""
    <div class="section-title">
        Quy trình hoạt động
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="text-content">

    1. Người dùng tải ảnh chứa văn bản Hán Nôm lên hệ thống

    2. Hệ thống xử lý ảnh và phát hiện vùng chứa chữ

    3. Mô hình CRNN tiến hành nhận diện ký tự

    4. Hệ thống tra cứu từ điển và phrase Hán Việt

    5. Hiển thị kết quả OCR, phiên âm và dịch nghĩa

    6. Người dùng có thể chỉnh sửa để cải thiện dữ liệu

    </div>
    """, unsafe_allow_html=True)

    st.divider()



    # HƯỚNG PHÁT TRIỂN
    st.markdown("""
    <div class="section-title">
        Hướng phát triển
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="text-content">

    - Xây dựng model OCR Hán Nôm riêng cho văn bản cổ Việt Nam

    - Tăng độ chính xác với ảnh mờ và tài liệu cũ

    - Hỗ trợ AI dịch theo ngữ cảnh

    - Tự động sửa lỗi OCR

    - Xây dựng kho dữ liệu Hán Nôm lớn

    - Hỗ trợ dịch thơ và văn bản cổ chính xác hơn

    </div>
    """, unsafe_allow_html=True)

    st.divider()



    # Ý NGHĨA
    st.markdown("""
    <div class="section-title">
        Ý nghĩa thực tiễn
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="text-content">

    Đề tài mang ý nghĩa thực tiễn trong việc hỗ trợ bảo tồn và số hóa di sản Hán Nôm Việt Nam,
    giúp các tài liệu cổ được lưu trữ và khai thác hiệu quả hơn trong thời đại công nghệ số.

    Hệ thống hỗ trợ người học, nhà nghiên cứu và những người quan tâm đến Hán Nôm
    dễ dàng tiếp cận, tra cứu và dịch các văn bản cổ mà không cần phải có kiến thức chuyên sâu về Hán Nôm.

    Ngoài ra, đề tài còn góp phần ứng dụng trí tuệ nhân tạo vào lĩnh vực ngôn ngữ học,
    mở ra hướng phát triển cho các hệ thống AI hỗ trợ dịch thuật và bảo tồn văn hóa dân tộc.

    Việc xây dựng hệ thống nhận diện và dịch chữ Hán Nôm cũng giúp giảm thời gian xử lý tài liệu thủ công,
    tăng khả năng số hóa dữ liệu lịch sử và hỗ trợ lưu trữ lâu dài các văn bản cổ quý giá.

    Trong tương lai, hệ thống có thể được mở rộng để phục vụ:

    - Công tác nghiên cứu lịch sử và văn hóa

    - Hỗ trợ học tập Hán Nôm

    - Xây dựng thư viện số Hán Nôm

    - Hỗ trợ dịch tài liệu cổ tự động

    - Bảo tồn và phát huy giá trị văn hóa truyền thống Việt Nam

    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.caption("Đồ án tốt nghiệp - Hệ thống nhận diện và dịch chữ Hán Nôm")