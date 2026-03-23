import streamlit as st
from google import genai
import pandas as pd
import io, re
from pypdf import PdfReader
from docx import Document
from docx.shared import Inches

# --- 1. CẤU HÌNH ---
st.set_page_config(page_title="AI Trích xuất Văn bản", layout="wide", page_icon="📝")
st.title("🏛️ Hệ thống Trích xuất Chỉ đạo & Xuất văn bản")

# Khởi tạo AI Client
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Thiếu GEMINI_API_KEY trong Secrets!")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Khởi tạo bộ nhớ tạm
if 'raw_output' not in st.session_state:
    st.session_state['raw_output'] = None
if 'df_result' not in st.session_state:
    st.session_state['df_result'] = None

# --- 2. HÀM HỖ TRỢ ---

def extract_text(file):
    try:
        if file.type == "application/pdf":
            return "\n".join([p.extract_text() for p in PdfReader(file).pages if p.extract_text()])
        else:
            return "\n".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return ""

def parse_md_to_df(md_text):
    """Chuyển bảng Markdown thành DataFrame để xuất Excel"""
    try:
        lines = [l.strip() for l in md_text.split('\n') if '|' in l]
        data_lines = [l for l in lines if not re.match(r'^[|:\-\s]+$', l)]
        if len(data_lines) < 2: return pd.DataFrame([{"Nội dung": md_text}])
        cols = [c.strip() for c in data_lines[0].split('|') if c.strip()]
        rows = [[c.strip() for c in l.split('|') if c.strip()] for l in data_lines[1:]]
        return pd.DataFrame([r for r in rows if len(r) == len(cols)], columns=cols)
    except:
        return pd.DataFrame([{"Kết quả": md_text}])

def create_word_file(df):
    """Tạo file Word từ DataFrame kết quả"""
    doc = Document()
    doc.add_heading('DANH MỤC NHIỆM VỤ, CHỈ ĐẠO', 0)
    
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    
    # Header
    hdr_cells = table.rows[0].cells
    for i, col_name in enumerate(df.columns):
        hdr_cells[i].text = col_name
        
    # Data
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, value in enumerate(row):
            row_cells[i].text = str(value)
            
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# --- 3. GIAO DIỆN ---

uploaded_file = st.file_uploader("Tải lên file văn bản (PDF hoặc DOCX)", type=["pdf", "docx"])

if uploaded_file:
    if st.button("🚀 BẮT ĐẦU PHÂN TÍCH"):
        content = extract_text(uploaded_file)
        if content:
            with st.spinner("AI đang bóc tách chỉ đạo..."):
                try:
                    prompt = (
                        "Bạn là trợ lý hành chính chuyên nghiệp. Hãy trích xuất TẤT CẢ nhiệm vụ từ văn bản. "
                        "Yêu cầu: Không tóm tắt, liệt kê đầy đủ từng nhiệm vụ vào bảng Markdown: "
                        "STT | Nhiệm vụ | Đơn vị thực hiện | Thời hạn.\n\n"
                        f"Nội dung:\n{content[:15000]}"
                    )
                    response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
                    
                    st.session_state['raw_output'] = response.text
                    st.session_state['df_result'] = parse_md_to_df(response.text)
                except Exception as e:
                    st.error(f"Lỗi AI: {e}")

# Hiển thị và Tải về
if st.session_state['raw_output']:
    st.divider()
    st.markdown("### ✅ Kết quả trích xuất")
    st.markdown(st.session_state['raw_output'])
    
    st.subheader("📥 Tải dữ liệu về máy")
    c1, c2 = st.columns(2)
    
    with c1:
        # Xuất Excel
        excel_bio = io.BytesIO()
        with pd.ExcelWriter(excel_bio, engine='openpyxl') as writer:
            st.session_state['df_result'].to_excel(writer, index=False, sheet_name="ChiDao")
        st.download_button(
            label="📊 Tải file Excel (.xlsx)",
            data=excel_bio.getvalue(),
            file_name=f"Trich_xuat_{uploaded_file.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with c2:
        # Xuất Word
        word_data = create_word_file(st.session_state['df_result'])
        st.download_button(
            label="📄 Tải file Word (.docx)",
            data=word_data,
            file_name=f"Bao_cao_{uploaded_file.name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
