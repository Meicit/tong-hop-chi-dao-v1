import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document
import io

# Cấu hình giao diện
st.set_page_config(page_title="AI Hành Chính", layout="wide")
st.title("🏛️ Phân tích Chỉ đạo Văn bản Hành chính")

# Lấy API Key từ Secrets của Streamlit
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

def read_pdf(file):
    reader = PdfReader(file)
    return " ".join([page.extract_text() for page in reader.pages])

def read_docx(file):
    doc = Document(file)
    return " ".join([para.text for para in doc.paragraphs])

uploaded_file = st.file_uploader("Tải lên file PDF hoặc Word", type=["pdf", "docx"])

if uploaded_file:
    with st.spinner('Đang đọc dữ liệu...'):
        if uploaded_file.type == "application/pdf":
            content = read_pdf(uploaded_file)
        else:
            content = read_docx(uploaded_file)
            
    if st.button("Trích xuất nội dung chỉ đạo"):
        prompt = f"""
        Bạn là một chuyên gia hành chính. Hãy đọc văn bản sau và trích xuất các thông tin dưới dạng bảng:
        - STT
        - Nội dung chỉ đạo/Nhiệm vụ cụ thể
        - Đơn vị/Cá nhân chủ trì thực hiện
        - Thời hạn hoàn thành (nếu không có thì ghi 'Theo quy định')
        - Ghi chú (Yêu cầu kèm theo nếu có)
        
        Văn bản: {content}
        """
        response = model.generate_content(prompt)
        st.markdown(response.text)
