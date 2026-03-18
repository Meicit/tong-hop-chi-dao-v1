import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# 1. Cấu hình giao diện App
st.set_page_config(page_title="AI Hành Chính", page_icon="🏛️")
st.title("🏛️ Trợ lý Phân tích Văn bản Hành chính")

# 2. Kết nối Gemini API (Lấy key từ Secrets để bảo mật)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # Sử dụng model 'gemini-1.5-flash' hoặc 'models/gemini-1.5-flash'
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Chưa cấu hình API Key trong phần Secrets!")

# 3. Hàm đọc nội dung file
def get_text_from_any(uploaded_file):
    text = ""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            text += page.extract_text()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    return text

# 4. Giao diện Upload
uploaded_file = st.file_uploader("Tải lên văn bản (PDF hoặc Word)", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner('Đang đọc tài liệu...'):
        content = get_text_from_any(uploaded_file)
    
    if st.button("Bắt đầu phân tích chỉ đạo"):
        prompt = f"""
        Bạn là một trợ lý hành chính chuyên nghiệp. Hãy đọc văn bản sau và trích xuất:
        1. Tóm tắt ngắn gọn nội dung văn bản.
        2. Danh sách các nhiệm vụ/chỉ đạo cụ thể (Trình bày dạng bảng: STT | Nhiệm vụ | Đơn vị thực hiện | Thời hạn).
        3. Các lưu ý quan trọng khác (nếu có).
        
        Nội dung văn bản:
        {content}
        """
        
        try:
            response = model.generate_content(prompt)
            st.markdown("### 📝 Kết quả phân tích")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Lỗi khi gọi AI: {e}")
