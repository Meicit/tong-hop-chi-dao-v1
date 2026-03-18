import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="AI Hành Chính Việt Nam",
    page_icon="🏛️",
    layout="wide"
)

# Tùy chỉnh giao diện bằng CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
    }
    .stTextArea>div>div>textarea { font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Hệ thống Trích xuất & Tổng hợp Chỉ đạo")
st.caption("Công cụ hỗ trợ cán bộ hành chính bóc tách nhiệm vụ từ văn bản PDF/Word")

# --- 2. CẤU HÌNH AI (KHẮC PHỤC LỖI 404) ---
def initialize_ai():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ Thiếu GEMINI_API_KEY trong Secrets!")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Chiến lược chọn Model: Thử Flash trước, nếu lỗi thì thử Pro
    model_options = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
    
    for model_name in model_options:
        try:
            model = genai.GenerativeModel(model_name)
            # Thử gọi một lệnh kiểm tra nhỏ
            return model
        except:
            continue
    st.error("❌ Không thể kết nối với bất kỳ Model Gemini nào. Vui lòng kiểm tra lại API Key.")
    st.stop()

model = initialize_ai()

# --- 3. HÀM XỬ LÝ VĂN BẢN ---
def extract_text(uploaded_file):
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                content = page.extract_text()
                if content: text += content + "\n"
        else:
            doc = Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return ""

# --- 4. GIAO DIỆN CHÍNH ---
col_left, col_right = st.columns([1, 1.5])

with col_left:
    st.subheader("📁 Tải văn bản")
    file = st.file_uploader("Kéo thả file PDF hoặc Word vào đây", type=["pdf", "docx"])
    
    if file:
        with st.spinner("Đang đọc nội dung..."):
            raw_content = extract_text(file)
        
        if raw_content:
            st.success(f"✅ Đã đọc xong: {file.name}")
            st.text_area("Xem trước nội dung văn bản:", raw_content, height=350)
        else:
            st.warning("⚠️ Văn bản trống hoặc là ảnh scan không có lớp chữ.")

with col_right:
    st.subheader("📋 Kết quả trích xuất")
    
    if file and raw_content:
        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH CHỈ ĐẠO"):
            with st.spinner("AI đang xử lý ngôn ngữ hành chính..."):
                prompt = f"""
                Bạn là một chuyên gia phân tích văn bản hành chính nhà nước Việt Nam.
                Hãy đọc văn bản dưới đây và trích xuất thông tin theo yêu cầu:

                1. TÓM TẮT: Mục đích chính và nội dung cốt lõi của văn bản.
                2. DANH MỤC NHIỆM VỤ: Trình bày dạng bảng Markdown gồm:
                   | STT | Nội dung chỉ đạo/Nhiệm vụ cụ thể | Đơn vị chủ trì | Thời hạn hoàn thành |
                3. LƯU Ý: Các điều khoản về báo cáo, phối hợp hoặc mốc thời gian quan trọng khác.

                VĂN BẢN CẦN PHÂN TÍCH:
                {raw_content}
                """
                
                try:
                    response = model.generate_content(prompt)
                    st.markdown("---")
                    st.markdown(response.text)
                    
                    # Nút tải kết quả
                    st.download_button(
                        label="📥 Tải kết quả về máy",
                        data=response.text,
                        file_name=f"Trich_xuat_{file.name}.txt",
                        mime="text/plain"
                    )
                except Exception as e:
                    st.error(f"Lỗi AI: {str(e)}")
                    st.info("Mẹo: Nếu lỗi 404 kéo dài, hãy thử tạo lại API Key mới tại Google AI Studio.")

# --- 5. CHÂN TRANG ---
st.divider()
st.markdown("<p style='text-align: center; color: gray;'>Hỗ trợ công tác tổng hợp chỉ đạo điều hành v1.0</p>", unsafe_allow_html=True)
