import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import io
import zipfile
import re

# --- CONFIGURATION (Pre-loaded from GitHub) ---
FRONT_TEMPLATE_PATH = "updatedfront.png"
BACK_TEMPLATE_PATH = "BackTemplate.jpg"
MACHINE_IMAGE_FOLDER = "machine_images"
FONT_PATH = "arialbd.ttf" 

# Original Coordinates Preserved
FRONT_PHOTO_COORDS = (45, 337); FRONT_PHOTO_SIZE = (190, 217)
FRONT_VEHICLE_COORDS = (758, 503); FRONT_VEHICLE_SIZE = (240, 135)
FRONT_NAME_COORDS = (430, 333); FRONT_FATHER_NAME_COORDS = (701, 333)
FRONT_DESIGNATION_COORDS = (532, 370); FRONT_SR_NO_COORDS = (89.8, 273)
BACK_CNIC_COORDS = (300, 175); BACK_DOB_COORDS = (300, 211)
BACK_ADDRESS_COORDS = (300, 250); BACK_HOLDER_NO_COORDS = (816, 627)
BACK_QR_COORDS = (775, 118); BACK_QR_SIZE = (240, 204)
DIPLOMA_PHOTO_BOX = (1188, 208, 1339, 364); DIPLOMA_QR_BOX = (1154, 772, 1328, 938)

MACHINE_MAP = {
    "Trailer Driver": "trailer.png", "Forklifter Operator": "forklifter.png",
    "Excavator Operator": "excavator.png", "Mobile Crane Operator": "crane.png",
    "Shovel Operator": "shovel.png", "Roller Operator": "roller.png",
    "Damper Driver": "dumper.png", "Bulldozer Operator": "doser.png",
    "Car Driver": "car.png", "JCB Operator": "jcb.png",
    "Grader Operator": "grader.png", "Bobcat Operator": "bobcat.png",
    "Hiace Driver": "hiace.png", "Rigger": "rigger.png"
}

def convert_google_sheet_url(url):
    # This helper converts a standard "Share" link into a "Direct Download" link for Pandas
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern, url)
    if match:
        spreadsheet_id = match.group(1)
        return f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx'
    return url

def remove_white_background(image):
    img = image.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)
    return img

# --- APP UI ---
st.set_page_config(page_title="PVC Card Gen", layout="wide")
st.title("🪪 Smart PVC Generator")

# 1. Google Sheets Link
sheet_url = st.text_input("1. Paste Google Sheets Share Link", placeholder="https://docs.google.com/spreadsheets/d/...")

# 2. Multi-Scan Uploader
uploaded_scans = st.file_uploader("2. Select Diploma Scans from Gallery", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if st.button("🚀 Generate Cards"):
    if not (sheet_url and uploaded_scans):
        st.error("Please provide both the link and the scans.")
    else:
        try:
            # Convert URL and Load Data
            download_url = convert_google_sheet_url(sheet_url)
            df = pd.read_excel(download_url, dtype=str).fillna("")
            
            scans_dict = {file.name: file for file in uploaded_scans}
            output_zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(output_zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_out:
                progress_bar = st.progress(0)
                status = st.empty()

                for index, row in df.iterrows():
                    sr_no = str(row['SrNo'])
                    scan_filename = str(row['DiplomaScanPath'])
                    
                    if scan_filename not in scans_dict:
                        st.warning(f"Scan '{scan_filename}' missing. Skipping {sr_no}.")
                        continue

                    # Processing
                    source_diploma = Image.open(scans_dict[scan_filename]).convert("RGBA")
                    photo_img = source_diploma.crop(DIPLOMA_PHOTO_BOX).resize(FRONT_PHOTO_SIZE, Image.LANCZOS)
                    qr_img = source_diploma.crop(DIPLOMA_QR_BOX)

                    # --- FRONT ---
                    card_front = Image.open(FRONT_TEMPLATE_PATH).convert("RGBA")
                    card_front.paste(photo_img, FRONT_PHOTO_COORDS, photo_img)
                    
                    m_filename = MACHINE_MAP.get(row['Designation'])
                    if m_filename:
                        m_path = os.path.join(MACHINE_IMAGE_FOLDER, m_filename)
                        if os.path.exists(m_path):
                            m_img = Image.open(m_path).convert("RGBA").resize(FRONT_VEHICLE_SIZE, Image.LANCZOS)
                            card_front.paste(m_img, FRONT_VEHICLE_COORDS, m_img)

                    draw_f = ImageDraw.Draw(card_front)
                    try:
                        font_main = ImageFont.truetype(FONT_PATH, size=22)
                    except:
                        font_main = ImageFont.load_default()

                    draw_f.text(FRONT_NAME_COORDS, str(row['StudentName']), font=font_main, fill=(0,0,0))
                    draw_f.text(FRONT_FATHER_NAME_COORDS, str(row['FatherName']), font=font_main, fill=(0,0,0))
                    draw_f.text(FRONT_SR_NO_COORDS, sr_no, fill=(255, 0, 0))

                    f_buf = io.BytesIO()
                    card_front.save(f_buf, format="PNG")
                    zip_out.writestr(f"{sr_no}_front.png", f_buf.getvalue())

                    # --- BACK ---
                    card_back = Image.open(BACK_TEMPLATE_PATH).convert("RGBA")
                    qr_clean = remove_white_background(qr_img).resize(BACK_QR_SIZE, Image.LANCZOS)
                    card_back.paste(qr_clean, BACK_QR_COORDS, qr_clean)
                    
                    draw_b = ImageDraw.Draw(card_back)
                    draw_b.text(BACK_CNIC_COORDS, str(row['CNIC']), font=font_main, fill=(0,0,0))
                    
                    b_buf = io.BytesIO()
                    card_back.save(b_buf, format="PNG")
                    zip_out.writestr(f"{sr_no}_back.png", b_buf.getvalue())

                    progress_bar.progress((index + 1) / len(df))
                
            status.success("✅ Success!")
            st.download_button("📥 Download ZIP", output_zip_buffer.getvalue(), "cards.zip", "application/zip")

        except Exception as e:
            st.error(f"Critical Error: {e}")
