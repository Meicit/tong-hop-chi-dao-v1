import streamlit as st
from google import genai
import pandas as pd
import io, requests, re
from pypdf import PdfReader
from docx import Document

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="AI Binh Hung 2026", layout="wide", page_icon="🏛️")
st.title("📊 Hệ thống Trích xuất & Báo cáo Chỉ đạo")

# Kiểm tra các khóa bảo mật trong Secrets
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ Thiếu GEMINI_API_KEY trong Secrets!")
    st.stop()

# Khởi tạo AI Client
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Khởi tạo bộ nhớ tạm (Session State)
if 'raw_text' not in st.session_state:
    st.session_state['raw_text'] = None
if 'df_data' not in st.session_state:
    st.session_state['df_data'] = None

# --- 2. CÁC HÀM XỬ LÝ ---

def extract_text_from_file(file):
    """Đọc văn bản từ PDF hoặc Word"""
    try:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
        else:
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return ""

def parse_markdown_to_df(md_text):
    """Chuyển bảng Markdown của AI thành bảng Excel chuẩn"""
    try:
        lines = [l.strip() for l in md_text.split('\n') if '|' in l]
        # Loại bỏ dòng ngăn cách tiêu đề |---|---|
        data_lines = [l for l in lines if not re.match(r'^[|:\-\s]+$', l)]
        if len(data_lines) < 2: 
            return pd.DataFrame([{"Nội dung": md_text}])
        
        cols = [c.strip() for c in data_lines[0].split('|') if c.strip()]
        rows = []
        for l in data_lines[1:]:
            row = [c.strip() for c in l.split('|') if c.strip()]
            if len(row) == len(cols):
                rows.append(row)
        return pd.DataFrame(rows, columns=cols)
    except:
        return pd.DataFrame([{"Kết quả": md_text}])

def send_to_telegram(text):
    """Gửi tin nhắn qua Telegram Bot"""
    token = st.secrets.get("TELE_TOKEN")
    chat_id = st.secrets.get("TELE_CHAT_ID")
    if not token or not chat_id:
        return None
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": f"📢 *CÓ CHỈ ĐẠO MỚI:* \n\n{text}", 
        "parse_mode": "Markdown"
    }
    return requests.post(url, json=payload)

# --- 3. GIAO DIỆN NGƯỜI DÙNG ---

uploaded_file = st.file_uploader("Tải văn bản chỉ đạo (PDF, DOCX)", type=["pdf", "docx"])

if uploaded_file:
    if st.button("🚀 BẮT ĐẦU TRÍCH XUẤT"):
        raw_content = extract_text_from_file(uploaded_file)
        
        if raw_content:
            with st.spinner("AI đang quét chi tiết văn bản..."):
                try:
                    # Prompt yêu cầu trích xuất chi tiết
                    prompt = (
                        "Bạn là trợ lý hành chính. Hãy trích xuất TẤT CẢ các nhiệm vụ trong văn bản sau. "
                        "Yêu cầu: Liệt kê đầy đủ, không tóm tắt, trình bày duy nhất dạng bảng Markdown: "
                        "STT | Nhiệm vụ | Đơn vị thực hiện | Thời hạn.\n\n"
                        f"Nội dung văn bản:\n{raw_content[:15000]}"
                    )
                    
                    response = client.models.generate_content(
                        model="gemini-1.5-flash", 
                        contents=prompt
                    )
                    
                    # Lưu vào Session State để không bị mất khi bấm nút khác
                    st.session_state['raw_text'] = response.text
                    st.session_state['df_data'] = parse_markdown_to_df(response.text)
                    
                except Exception as e:
                    st.error(f"Lỗi gọi AI: {e}")

# Hiển thị kết quả nếu đã có dữ liệu
if st.session_state['raw_text']:
    st.divider()
    st.markdown("### 📋 Kết quả trích xuất chi tiết")
    st.markdown(st.session_state['raw_text'])
    
    # Khu vực các nút chức năng
    col1, col2 = st.columns(2)
    
    with col1:
        # Nút tải file Excel
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine='openpyxl') as writer:
            st.session_state['df_data'].to_excel(writer, index=False, sheet_name="ChiDao")
        
        st.download_button(
            label="📥 Tải về file Excel (Cột chuẩn)",
            data=buf.getvalue(),
            file_name=f"Trich_xuat_{uploaded_file.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col2:
        # Nút gửi Telegram
        if st.button("📲 GỬI BÁO CÁO QUA TELEGRAM"):
            res = send_to_telegram(st.session_state['raw_text'])
            if res and res.status_code == 200:
                st.success("🚀 Đã gửi Telegram thành công!")
                st.balloons()
            else:
                st.error("❌ Lỗi: Kiểm tra lại TELE_TOKEN và TELE_CHAT_ID trong Secrets.")
