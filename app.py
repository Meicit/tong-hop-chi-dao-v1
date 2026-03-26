import streamlit as st
from google import genai
import pandas as pd
import io, re
from pypdf import PdfReader
from docx import Document

# --- PHẦN ADD API KEY AN TOÀN ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("❌ Chưa cấu hình GEMINI_API_KEY trong Secrets!")
    st.stop()

# Khởi tạo Client (Sửa lỗi 404 bằng cách dùng client chuẩn)
client = genai.Client(api_key=api_key)
# -------------------------------

st.title("🏛️ Hệ thống Trích xuất & Xuất văn bản v2026")

# Khởi tạo bộ nhớ tạm
if 'raw_data' not in st.session_state:
    st.session_state['raw_data'] = None

# --- HÀM XỬ LÝ (GIỮ NGUYÊN) ---
def extract_text(file):
    if file.type == "application/pdf":
        return "\n".join([p.extract_text() for p in PdfReader(file).pages if p.extract_text()])
    return "\n".join([p.text for p in Document(file).paragraphs])

def parse_md_to_df(md_text):
    lines = [l.strip() for l in md_text.split('\n') if '|' in l]
    data = [l for l in lines if not any(c in l for c in [':-', '---'])]
    if len(data) < 2: return pd.DataFrame([{"Nội dung": md_text}])
    cols = [c.strip() for c in data[0].split('|') if c.strip()]
    rows = [[c.strip() for c in l.split('|') if c.strip()] for l in data[1:]]
    return pd.DataFrame([r for r in rows if len(r) == len(cols)], columns=cols)

# --- GIAO DIỆN ---
file = st.file_uploader("Tải lên file văn bản", type=["pdf", "docx"])

if file:
    if st.button("🚀 PHÂN TÍCH"):
        content = extract_text(file)
        with st.spinner("AI đang xử lý..."):
            try:
                # FIX LỖI 404: Gọi trực tiếp gemini-1.5-flash không kèm tiền tố thừa
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=f"Trích xuất tất cả nhiệm vụ thành bảng Markdown (STT | Nhiệm vụ | Đơn vị | Thời hạn):\n\n{content[:15000]}"
                )
                st.session_state['raw_data'] = response.text
            except Exception as e:
                st.error(f"Lỗi AI: {e}")

if st.session_state['raw_data']:
    st.markdown(st.session_state['raw_data'])
    df = parse_md_to_df(st.session_state['raw_data'])
    
    # Nút tải Excel
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine='openpyxl') as w:
        df.to_excel(w, index=False)
    st.download_button("📊 Tải Excel", excel_buf.getvalue(), "chidao.xlsx")
