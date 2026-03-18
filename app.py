import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from docx import Document

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="AI Hành Chính", layout="wide")
st.title("🏛️ Hệ thống Trích xuất Chỉ đạo")

# --- KẾT NỐI AI (CƠ CHẾ TỰ QUÉT) ---
def get_working_model():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("❌ Thiếu API Key trong Secrets!")
        return None
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # Lấy danh sách tất cả model mà Key này được phép dùng
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            st.error("❌ API Key này không có quyền truy cập vào bất kỳ model nào.")
            return None
        
        # Ưu tiên các model theo thứ tự tốt nhất
        priority = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-1.0-pro']
        for p in priority:
            if p in available_models:
                return genai.GenerativeModel(p)
        
        # Nếu không có trong ưu tiên, lấy cái đầu tiên khả dụng
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"❌ Lỗi kết nối API: {e}")
        return None

model = get_working_model()

# --- XỬ LÝ FILE ---
def extract_text(file):
    text = ""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
        return text.strip()
    except: return ""

# --- GIAO DIỆN ---
uploaded_file = st.file_uploader("Tải lên PDF/Word", type=["pdf", "docx"])

if uploaded_file and model:
    content = extract_text(uploaded_file)
    if st.button("🚀 Phân tích ngay"):
        with st.spinner("AI đang làm việc..."):
            prompt = f"Trích xuất các chỉ đạo, đơn vị thực hiện và thời hạn từ văn bản sau dưới dạng bảng:\n\n{content}"
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Lỗi thực thi: {e}")
