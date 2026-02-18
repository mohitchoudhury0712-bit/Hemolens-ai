import streamlit as st
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_cropper import st_cropper
from PIL import Image
import numpy as np

# PDF Library Check
try:
    from fpdf import FPDF
except ImportError:
    os.system('pip install fpdf')
    from fpdf import FPDF

# --- Setup (Badlav 1: Layout Centered for Mobile) ---
st.set_page_config(
    page_title="HemoLens AI", 
    layout="centered", 
    page_icon="🩸",
    initial_sidebar_state="collapsed"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .install-bar {
        background-color: #e3f2fd; border: 1px solid #90caf9; color: #0d47a1;
        padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px;
        font-size: 14px; font-weight: bold;
    }
    .main-header { 
        background: linear-gradient(135deg, #002B5B 0%, #007BFF 100%); 
        padding: 25px; border-radius: 15px; color: white; text-align: center; 
        margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
    }
    .stButton>button { 
        background: #007BFF; color: white; border-radius: 10px; font-weight: 700; 
        height: 3.5rem; width: 100%; border: none; font-size: 16px; transition: 0.3s;
    }
    .stButton>button:hover { background: #0056b3; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .result-card { background: white; padding: 20px; border-radius: 15px; text-align: center; border: 1px solid #E2E8F0; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .hb-val { font-size: 48px; font-weight: 800; color: #007BFF; }
    
    .caution-box {
        background-color: #FFF4F4; border-left: 6px solid #D32F2F;
        padding: 15px; border-radius: 8px; color: #B71C1C;
        font-size: 14px; margin-top: 20px; text-align: left;
    }
    .whatsapp-btn {
        background-color: #25D366; color: white; padding: 12px 20px; 
        border-radius: 10px; text-decoration: none; font-weight: bold; 
        display: block; text-align: center; margin-top: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .whatsapp-btn:hover { background-color: #128C7E; color: white; }

    .dev-footer {
        text-align: center;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid #eee;
        color: #666;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "hemolens_records.csv"

def validate_red_color(roi_array):
    avg_color = np.mean(roi_array, axis=(0, 1))
    r, g, b = avg_color[0], avg_color[1], avg_color[2]
    if r < 60 and g < 60 and b < 60: return False, "Too Dark"
    if r > 190 and g > 190 and b > 190: return False, "Too Bright"
    if g > r or b > r: return False, "Invalid Color"
    if (r - g) < 17: return False, "Skin Tone Detected"
    if r > g and r > b: return True, "Valid"
    return False, "Unknown Object"

def clean_text(text):
    return text.encode('ascii', 'ignore').decode('ascii')

def generate_pdf(name, age, gender, diet, hb, status, diet_plan, advice):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 123, 255); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 25, "HEMOLENS AI - REPORT", ln=True, align='C')
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, f" NAME: {name.upper()}", border=1)
    pdf.cell(95, 10, f" AGE / GENDER: {age} / {gender}", border=1, ln=1)
    pdf.ln(10); pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, "SCREENING RESULTS:", ln=True)
    pdf.set_font("Arial", 'B', 26); pdf.set_text_color(0, 123, 255)
    pdf.cell(190, 20, f"{hb} g/dL", ln=True, align='C')
    pdf.ln(10); pdf.set_text_color(200, 0, 0); pdf.set_font("Arial", 'B', 10)
    pdf.multi_cell(190, 5, "This is an AI Screening Tool, NOT a clinical diagnosis. Results can be +/- 1 g/dL. Please consult a doctor for a laboratory CBC Blood Test.", align='C')
    return pdf.output(dest='S').encode('latin-1', 'replace')

def get_expert_diet(hb_level, diet_type, lang):
    is_anemic = hb_level < 11.5
    is_veg = "Veg" in diet_type or "शाकाहारी" in diet_type
    if lang == "Hindi":
        status = "Swasth (Normal)" if not is_anemic else "Khoon ki kami (Anemia)"
        plan = "आहार: पालक, चुकंदर, गुड़ और खजूर।" if is_veg else "आहार: रेड मीट, कलेजी और अंडा।"
        advice = "खाने के साथ विटामिन सी (नींबू) जरूर लें।"
    else:
        status = "Normal" if not is_anemic else "Anemia Detected"
        plan = "Diet: Spinach, Beetroot, Dates." if is_veg else "Diet: Red Meat & Eggs."
        advice = "Take Vitamin C for absorption."
    return {"status": status, "plan": plan, "advice": advice}

def save_data(name, age, gender, diet, hb, status):
    new_entry = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Name": name.strip().lower(), "Display_Name": name.strip(), "Age": age, "Gender": gender, "Diet": diet, "Hb_Level": hb, "Status": status}
    df = pd.DataFrame([new_entry])
    if not os.path.isfile(DB_FILE): df.to_csv(DB_FILE, index=False)
    else: df.to_csv(DB_FILE, mode='a', header=False, index=False)

# ==========================================
# LANGUAGE & TEXT (Badlav 2: Sidebar hatakar Main Page par)
# ==========================================
st.markdown(f'<div class="install-bar">📲 <b>Install App:</b> Menu (⋮) > Add to Home Screen</div>', unsafe_allow_html=True)
st.markdown(f"""<div class="main-header"><h1>🩺 HemoLens AI</h1><p>Anemia Screening Tool</p></div>""", unsafe_allow_html=True)

p_lang = st.selectbox("Choose Language / भाषा चुनें", ("English", "Hindi"))

if p_lang == "Hindi":
    txt = {
        "sidebar_title": "👤 मरीज की जानकारी", "name_label": "मरीज का नाम", "age_label": "उम्र", "gender_label": "लिंग", "diet_label": "खान-पान", "g_opts": ("पुरुष", "महिला", "अन्य"), "d_opts": ("शाकाहारी", "मांसाहारी"), "hist_title": "📜 रिकॉर्ड खोजें", "search_label": "🔍 नाम खोजें", "graph_title": "Hb का उतार-चढ़ाव", "found_rec": "रिकॉर्ड मिले:", "no_rec": "कोई रिकॉर्ड नहीं मिला", "inst": "💡 **निर्देश:** लाल बॉक्स को पलक पर सेट करें।", "up_l": "बाईं आंख (Left Eye)", "up_r": "दाईं आंख (Right Eye)", "adj_title": "👁️ Adjust Box", "cap_l": "बाईं आंख", "cap_r": "दाईं आंख", "run_btn": "🚀 जांच शुरू करें", "err_name": "नाम लिखें!", "err_eye": "बॉक्स सही करें!", "hb_res": "Hb स्तर", "rec_title": "🥗 आहार सलाह:", "tip_title": "💡 सुझाव:", "table_t": "📊 सामान्य रेंज", "table_m": "👨 पुरुष: 13-17", "table_f": "👩 महिला: 12-15", "caution": "⚠️ AI टूल है, डॉक्टri जांच नहीं। परिणाम +/- 1 हो सकते हैं।", "dl_btn": "📥 रिपोर्ट PDF", "wa_btn": "📲 WhatsApp", "footer_txt": "Developed by <b>Mohit Choudhury</b>"
    }
else:
    txt = {
        "sidebar_title": "👤 Patient Profile", "name_label": "Patient Name", "age_label": "Age", "gender_label": "Gender", "diet_label": "Diet", "g_opts": ("Male", "Female", "Other"), "d_opts": ("Vegetarian", "Non-Vegetarian"), "hist_title": "📜 History", "search_label": "🔍 Search Name", "graph_title": "Hb Trend", "found_rec": "Found:", "no_rec": "None.", "inst": "💡 **Instructions:** Set Red Box on inner eyelid.", "up_l": "Left Eye", "up_r": "Right Eye", "adj_title": "👁️ Adjust Box", "cap_l": "Left Eye", "cap_r": "Right Eye", "run_btn": "🚀 RUN ANALYSIS", "err_name": "Enter Name!", "err_eye": "Adjust Box!", "hb_res": "Hb Level", "rec_title": "🥗 Recommendation:", "tip_title": "💡 Tip:", "table_t": "📊 Normal Range", "table_m": "👨 Male: 13-17", "table_f": "👩 Female: 12-15", "caution": "⚠️ AI tool, NOT diagnosis. Results +/- 1. Consult doctor.", "dl_btn": "📥 Download PDF", "wa_btn": "📲 WhatsApp", "footer_txt": "Developed by <b>Mohit Choudhury</b>"
    }

# Profile Section
col_m1, col_m2 = st.columns(2)
with col_m1: p_name = st.text_input(txt["name_label"])
with col_m2: p_age = st.number_input(txt["age_label"], 1, 100, 25)

col_m3, col_m4 = st.columns(2)
with col_m3: p_gender = st.selectbox(txt["gender_label"], txt["g_opts"])
with col_m4: p_diet = st.radio(txt["diet_label"], txt["d_opts"], horizontal=True)

st.markdown("---")
search_name = st.text_input(txt["search_label"]).strip().lower()

if search_name:
    if os.path.isfile(DB_FILE):
        df_history = pd.read_csv(DB_FILE)
        recs = df_history[df_history['Name'] == search_name]
        if not recs.empty:
            fig = px.line(recs, x='Timestamp', y='Hb_Level', markers=True, title=f"{txt['graph_title']}: {search_name.upper()}")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(recs[['Timestamp', 'Hb_Level', 'Status']], use_container_width=True)
        else: st.warning(txt["no_rec"])

else:
    st.info(txt['inst'])
    # (Badlav 3: Images stacked vertically for mobile)
    st.subheader(txt['up_l'])
    up_l = st.file_uploader("Upload Left Eye", type=["jpg", "png", "jpeg"], key="l")
    if up_l:
        img_l = Image.open(up_l)
        sl_crop = st_cropper(img_l, box_color='#00FF00', key="sl", use_container_width=True)
        cl_crop = st_cropper(img_l, box_color='#FF0000', key="cl", use_container_width=True)

    st.markdown("---")
    st.subheader(txt['up_r'])
    up_r = st.file_uploader("Upload Right Eye", type=["jpg", "png", "jpeg"], key="r")
    if up_r:
        img_r = Image.open(up_r)
        sr_crop = st_cropper(img_r, box_color='#00FF00', key="sr", use_container_width=True)
        cr_crop = st_cropper(img_r, box_color='#FF0000', key="cr", use_container_width=True)

    if up_l and up_r:
        if st.button(txt['run_btn']):
            if not p_name: st.error(txt['err_name'])
            else:
                # Same formula as your version
                def calc_hb(s, c):
                    s_arr, c_arr = np.array(s), np.array(c)
                    ref_w, avg_c = np.mean(s_arr, axis=(0,1)), np.mean(c_arr, axis=(0,1))
                    ratio = (avg_c[0]/(ref_w[0]+1e-6)) / ((avg_c[1]/(ref_w[1]+1e-6) + avg_c[2]/(ref_w[2]+1e-6))/2 + 1e-6)
                    hb_val = 2.0 + (ratio * 6.0)
                    return max(6.0, min(hb_val, 16.5))

                hb_final = round((calc_hb(sl_crop, cl_crop) + calc_hb(sr_crop, cr_crop)) / 2, 1)
                res = get_expert_diet(hb_final, p_diet, p_lang)
                save_data(p_name, p_age, p_gender, p_diet, hb_final, res['status'])

                st.markdown(f'<div class="result-card"><p>{txt["hb_res"]}</p><div class="hb-val">{hb_final}</div><p><b>{res["status"]}</b></p></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="caution-box">{txt["caution"]}</div>', unsafe_allow_html=True)
                
                pdf_bytes = generate_pdf(p_name, p_age, p_gender, p_diet, hb_final, res['status'], res['plan'], res['advice'])
                st.download_button(txt['dl_btn'], pdf_bytes, f"HemoLens_{p_name}.pdf")

st.markdown(f'<div class="dev-footer">{txt["footer_txt"]}</div>', unsafe_allow_html=True)
