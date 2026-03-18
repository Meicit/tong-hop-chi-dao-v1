import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="AI Phân Tích Văn Bản Hành Chính",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🏛️ Hệ thống Trích xuất Chỉ đạo Văn bản")
st.info("Hỗ trợ đọc file PDF và Word để lập bảng nhiệm vụ tự động.")

# --- 2. CẤU HÌNH AI (GEMINI) ---
try:
    # Lấy API Key từ Secrets của Streamlit Cloud
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Sử dụng tên model ổn định nhất để tránh lỗi 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    else:
        st.error("❌ Thiếu API Key! Hãy cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ Lỗi cấu hình hệ thống: {e}")
    st.stop()

# --- 3. CÁC HÀM XỬ LÝ FILE ---
def extract_text_from_pdf(file):
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return f"Lỗi đọc file PDF: {e}"

def extract_text_from_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Lỗi đọc file Word: {e}"

# --- 4. GIAO DIỆN NGƯỜI DÙNG ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📁 Tải văn bản")
    uploaded_file = st.file_uploader("Chọn file (PDF hoặc DOCX)", type=["pdf", "docx"])
    
    if uploaded_file:
        file_type = uploaded_file.type
        st.success(f"Đã tải file: {uploaded_file.name}")
        
        with st.spinner("Đang trích xuất văn bản..."):
            if "pdf" in file_type:
                raw_text = extract_text_from_pdf(uploaded_file)
            else:
                raw_text = extract_text_from_docx(uploaded_file)
        
        if len(raw_text.strip()) < 10:
            st.warning("⚠️ Không tìm thấy nội dung văn bản (có thể là file ảnh scan).")
        else:
            st.text_area("Nội dung gốc (trích đoạn):", raw_text[:500] + "...", height=200)

with col2:
    st.subheader("📋 Kết quả phân tích")
    
    if uploaded_file and st.button("🚀 Bắt đầu Phân tích & Trích xuất"):
        with st.spinner("AI đang xử lý chỉ đạo..."):
            prompt = f"""
            Bạn là một trợ lý thư ký hành chính nhà nước dày dạn kinh nghiệm. 
            Nhiệm vụ của bạn là đọc văn bản sau và lọc ra các nội dung chỉ đạo trọng tâm.
            
            HÃY TRÌNH BÀY THEO CẤU TRÚC SAU:
            1. Tóm tắt ngắn gọn mục đích văn bản (2-3 dòng).
            2. Danh sách nhiệm vụ cụ thể dưới dạng BẢNG gồm các cột:
               - STT
               - Nội dung chỉ đạo/Nhiệm vụ
               - Đơn vị/Cá nhân thực hiện
               - Thời hạn hoàn thành (Nếu không có ghi 'Thường xuyên' hoặc 'Theo quy định')
            3. Các mốc thời gian quan trọng cần lưu ý (dạng danh sách).

            NỘI DUNG VĂN BẢN:
            {raw_text}
            """
            
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
                
                # Nút copy/tải về (giả lập đơn giản)
                st.download_button(
                    label="📥 Tải kết quả về máy",
                    data=response.text,
                    file_name=f"ket_qua_phan_tich_{uploaded_file.name}.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"❌ Lỗi khi gọi AI: {e}")
                st.info("Mẹo: Hãy kiểm tra xem API Key có bị giới hạn vùng địa lý không.")

# --- 5. CHÂN TRANG ---
st.divider()
st.caption("Ứng dụng hỗ trợ công tác hành chính - Phát triển bởi Gemini AI.")
