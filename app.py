import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import io
import zipfile

# --- 1. SETTINGS & PATHS (Pre-loaded from your repo) ---
FRONT_TEMPLATE_PATH = "updatedfront.png"
BACK_TEMPLATE_PATH = "BackTemplate.jpg"
MACHINE_IMAGE_FOLDER = "machine_images"
FONT_PATH = "arialbd.ttf" # Ensure this is uploaded to your GitHub

# (Keep your original coordinates from your script)
FRONT_PHOTO_COORDS = (45, 337)
FRONT_PHOTO_SIZE = (190, 217)
FRONT_VEHICLE_COORDS = (758, 503)
FRONT_VEHICLE_SIZE = (240, 135)
FRONT_NAME_COORDS = (430, 333)
FRONT_FATHER_NAME_COORDS = (701, 333)
FRONT_DESIGNATION_COORDS = (532, 370)
FRONT_SR_NO_COORDS = (89.8, 273)
FRONT_START_COORDS = (430, 445)
FRONT_END_COORDS = (630, 445)
BACK_CNIC_COORDS = (300, 175)
BACK_DOB_COORDS = (300, 211)
BACK_ADDRESS_COORDS = (300, 250)
BACK_HOLDER_NO_COORDS = (816, 627)
BACK_QR_COORDS = (775, 118)
BACK_QR_SIZE = (240, 204)
DIPLOMA_PHOTO_BOX = (1188, 208, 1339, 364)
DIPLOMA_QR_BOX = (1154, 772, 1328, 938)

MACHINE_MAP = {
    "Trailer Driver": "trailer.png",
    "Forklifter Operator": "forklifter.png",
    "Excavator Operator": "excavator.png",
    "Mobile Crane Operator": "crane.png",
    "Shovel Operator": "shovel.png",
    "Roller Operator": "roller.png",
    "Damper Driver": "dumper.png",
    "Bulldozer Operator": "doser.png",
    "Car Driver": "car.png",
    "JCB Operator": "jcb.png",
    "Grader Operator": "grader.png",
    "Bobcat Operator": "bobcat.png",
    "Hiace Driver": "hiace.png",
    "Rigger": "rigger.png",
}

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

# --- STREAMLIT UI ---
st.title("🪪 PVC Card Generator")
st.write("Upload your Excel and a ZIP file of diploma scans.")

excel_file = st.file_uploader("1. Upload Students Excel", type="xlsx")
diploma_zip = st.file_uploader("2. Upload Diploma Scans (ZIP file)", type="zip")

if st.button("Generate All Cards"):
    if excel_file and diploma_zip:
        try:
            # Load Excel
            df = pd.read_excel(excel_file, dtype=str).fillna("")
            
            # Unzip scans into memory
            scans = {}
            with zipfile.ZipFile(diploma_zip, 'r') as z:
                for file_info in z.infolist():
                    if not file_info.is_dir():
                        scans[file_info.filename] = z.read(file_info.filename)

            # Prepare Output ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                
                progress_bar = st.progress(0)
                
                for index, row in df.iterrows():
                    sr_no = row['SrNo']
                    scan_filename = row['DiplomaScanPath'] # e.g., "scan1.jpg"
                    
                    if scan_filename not in scans:
                        st.error(f"Scan {scan_filename} not found in ZIP!")
                        continue

                    # --- IMAGE PROCESSING ---
                    # Load Diploma from memory
                    source_diploma = Image.open(io.BytesIO(scans[scan_filename])).convert("RGBA")
                    photo_img = source_diploma.crop(DIPLOMA_PHOTO_BOX).resize(FRONT_PHOTO_SIZE, Image.LANCZOS)
                    qr_img = source_diploma.crop(DIPLOMA_QR_BOX)

                    # Generate Front
                    card_front = Image.open(FRONT_TEMPLATE_PATH).convert("RGBA")
                    card_front.paste(photo_img, FRONT_PHOTO_COORDS, photo_img)
                    
                    # Vehicle Logic
                    m_file = MACHINE_MAP.get(row['Designation'])
                    if m_file:
                        v_img = Image.open(os.path.join(MACHINE_IMAGE_FOLDER, m_file)).convert("RGBA")
                        v_img = v_img.resize(FRONT_VEHICLE_SIZE, Image.LANCZOS)
                        card_front.paste(v_img, FRONT_VEHICLE_COORDS, v_img)

                    # Draw Text (using default font for brevity, you can load your TTFs here)
                    draw_f = ImageDraw.Draw(card_front)
                    draw_f.text(FRONT_NAME_COORDS, row['StudentName'], fill=(0,0,0))
                    # ... (Add your other draw.text lines here) ...

                    # Save Front to ZIP
                    f_buf = io.BytesIO()
                    card_front.save(f_buf, format="PNG")
                    zip_file.writestr(f"{sr_no}_front.png", f_buf.getvalue())

                    # Generate Back
                    card_back = Image.open(BACK_TEMPLATE_PATH).convert("RGBA")
                    # ... (Add back card logic here) ...
                    b_buf = io.BytesIO()
                    card_back.save(b_buf, format="PNG")
                    zip_file.writestr(f"{sr_no}_back.png", b_buf.getvalue())

                    progress_bar.progress((index + 1) / len(df))

            st.success("Cards Created!")
            # --- DOWNLOAD BUTTON ---
            st.download_button(
                label="📥 Download All Cards (.zip)",
                data=zip_buffer.getvalue(),
                file_name="generated_cards.zip",
                mime="application/zip"
            )

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload both files.")
