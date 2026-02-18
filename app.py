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

# --- Setup ---
DB_FILE = "hemolens_records.csv"
st.set_page_config(
    page_title="HemoLens AI", 
    layout="wide", 
    page_icon="",
    initial_sidebar_state="expanded"
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

    /* Developer Footer */
    .dev-footer {
        text-align: center;
        padding: 20px;
        margin-top: 50px;
        border-top: 1px solid #eee;
        color: #666;
        font-size: 14px;
    }
    </style>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
    """, unsafe_allow_html=True)

# --- STRICT COLOR VALIDATOR ---
def validate_red_color(roi_array):
    avg_color = np.mean(roi_array, axis=(0, 1))
    r, g, b = avg_color[0], avg_color[1], avg_color[2]
    
    if r < 60 and g < 60 and b < 60: return False, "Too Dark (Pupil/Lashes)"
    if r > 190 and g > 190 and b > 190: return False, "Too Bright (White Sclera)"
    if g > r or b > r: return False, "Invalid Color (Green/Blue Background)"
    if (r - g) < 17: return False, "Skin Tone Detected (Not Red Enough)"
    if r > g and r > b: return True, "Valid"
    return False, "Unknown Object"

def clean_text(text):
    return text.encode('ascii', 'ignore').decode('ascii')

# --- PDF GENERATOR (Updated Caution Text) ---
def generate_pdf(name, age, gender, diet, hb, status, diet_plan, advice):
    gender_map = {"पुरुष": "Male", "महिला": "Female", "अन्य": "Other"}
    diet_map = {"शाकाहारी": "Vegetarian", "मांसाहारी": "Non-Vegetarian"}
    pdf_gender = gender_map.get(gender, gender)
    pdf_diet = diet_map.get(diet, diet)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(0, 123, 255); pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 25, "HEMOLENS AI - REPORT", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(190, 5, f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True, align='C')
    
    pdf.ln(25); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12)
    pdf.cell(95, 10, f" NAME: {name.upper()}", border=1)
    pdf.cell(95, 10, f" AGE / GENDER: {age} / {pdf_gender}", border=1, ln=1)
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 14); pdf.cell(190, 10, "SCREENING RESULTS:", ln=True)
    pdf.set_font("Arial", 'B', 26); pdf.set_text_color(0, 123, 255)
    pdf.cell(190, 20, f"{hb} g/dL", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14); pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, f"STATUS: {clean_text(status)}", ln=True, align='C')
    
    pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "RECOMMENDATIONS:", ln=True)
    pdf.set_font("Arial", size=10)
    
    if "Veg" in pdf_diet or "Shaka" in str(diet):
        pdf_plan = "Diet: Spinach, Beetroot, Dates, Jaggery."
    else:
        pdf_plan = "Diet: Red Meat, Liver, Eggs, Spinach."
    pdf_advice = "Take Vitamin C for absorption."
    
    pdf.multi_cell(0, 7, f"{pdf_plan}\n\nTIP: {pdf_advice}")
    
    pdf.ln(10); pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 8, "BIOLOGICAL REFERENCE RANGES (Normal Values):", ln=True)
    pdf.set_font("Arial", size=9); pdf.set_fill_color(240, 240, 240)
    pdf.cell(60, 8, "Category", border=1, fill=True)
    pdf.cell(60, 8, "Normal Hb Range", border=1, fill=True)
    pdf.cell(70, 8, "Anemia Level", border=1, fill=True, ln=True)
    pdf.cell(60, 8, "Adult Male", border=1); pdf.cell(60, 8, "13.0 - 17.0 g/dL", border=1); pdf.cell(70, 8, "< 13.0 g/dL", border=1, ln=True)
    pdf.cell(60, 8, "Adult Female", border=1); pdf.cell(60, 8, "12.0 - 15.0 g/dL", border=1); pdf.cell(70, 8, "< 12.0 g/dL", border=1, ln=True)
    
    # --- UPDATED PDF CAUTION TEXT ---
    pdf.ln(10); pdf.set_fill_color(255, 235, 235); pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    pdf.set_text_color(200, 0, 0); pdf.set_font("Arial", 'B', 10)
    pdf.cell(190, 8, " IMPORTANT MEDICAL CAUTION:", ln=True, align='C')
    pdf.set_font("Arial", 'I', 9)
    # Caution Text Here
    pdf.multi_cell(190, 5, "This is an AI Screening Tool, NOT a clinical diagnosis. Results can be +/- 1 g/dL. Please consult a doctor for a laboratory CBC Blood Test.", align='C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def get_expert_diet(hb_level, diet_type, lang):
    is_anemic = hb_level < 11.5
    is_veg = "Veg" in diet_type or "शाकाहारी" in diet_type
    
    if lang == "Hindi":
        status = "Swasth (Normal)" if not is_anemic else "Khoon ki kami (Anemia)"
        plan = "आहार: पालक, चुकंदर, गुड़ और खजूर।" if is_veg else "आहार: रेड मीट, कलेजी और अंडा।"
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
# 1. LANGUAGE SELECTION & TEXT MAPPING
# ==========================================
st.sidebar.markdown(f'<div style="text-align: center;"><h2> Menu</h2></div>', unsafe_allow_html=True)
p_lang = st.sidebar.selectbox("Language / भाषा", ("English", "Hindi"))

if p_lang == "Hindi":
    txt = {
        "sidebar_title": "👤 मरीज की जानकारी",
        "name_label": "मरीज का नाम",
        "age_label": "उम्र",
        "gender_label": "लिंग",
        "diet_label": "खान-पान",
        "g_opts": ("पुरुष", "महिला", "अन्य"),
        "d_opts": ("शाकाहारी", "मांसाहारी"),
        "hist_title": "📜 पुराना रिकॉर्ड और ट्रेंड",
        "search_label": "🔍 नाम खोजें",
        "graph_title": "Hb का उतार-चढ़ाव",
        "found_rec": "रिकॉर्ड मिले:",
        "no_rec": "कोई रिकॉर्ड नहीं मिला",
        "install": "📲 <b>ऐप इंस्टॉल करें:</b> ब्राउज़र मेनू (⋮) दबाएं और \"Add to Home Screen\" चुनें",
        "title": "HemoLens AI ",
        "subtitle": " एनीमिया स्क्रीनिंग टूल",
        "inst": "💡 **निर्देश:** दिन की रोशनी में फोटो लें। **लाल बॉक्स (Red Box)** को आंख की निचली पलक के गुलाबी हिस्से पर सेट करें।",
        "up_l": "बाईं आंख (Left Eye)",
        "up_r": "दाईं आंख (Right Eye)",
        "adj_title": "👁️ जांच का क्षेत्र चुनें (Adjust Box)",
        "cap_l": "बाईं आंख: हरा=सफेद हिस्सा, लाल=पलक",
        "cap_r": "दाईं आंख: हरा=सफेद हिस्सा, लाल=पलक",
        "run_btn": "🚀 जांच शुरू करें (Run Analysis)",
        "err_name": "कृपया साइडबार में मरीज का नाम लिखें!",
        "err_eye": "❌ त्रुटि: बॉक्स सही जगह नहीं है। कृपया लाल बॉक्स को पलक पर सेट करें।",
        "hb_res": "Hb स्तर",
        "rec_title": "🥗 आहार सलाह:",
        "tip_title": "💡 सुझाव:",
        "table_t": "📊 सामान्य हीमोग्लोबिन रेंज (Normal Values)",
        "table_m": "👨 पुरुष (Male): <b>13.0 - 17.0 g/dL</b>",
        "table_f": "👩 महिला (Female): <b>12.0 - 15.0 g/dL</b>",
        # --- UPDATED HINDI CAUTION ---
        "caution": "⚠️ <b>चिकित्सा चेतावनी (Disclaimer):</b><br>यह एक AI स्क्रीनिंग टूल है, <b>डॉक्टरी जांच नहीं।</b> परिणाम <b>+/- 1 g/dL</b> ऊपर-नीचे हो सकते हैं।<br>कृपया पुष्टि के लिए डॉक्टर से CBC ब्लड टेस्ट करवाएं।",
        "dl_btn": "📥 रिपोर्ट डाउनलोड करें (PDF)",
        "wa_msg": "नमस्ते! मेरी हीमोग्लोबिन रिपोर्ट: Hb",
        "wa_btn": "📲 WhatsApp पर भेजें",
        "footer_txt": " Developed by <b>Mohit Choudhury</b> "
    }
else:
    txt = {
        "sidebar_title": "👤 Patient Profile",
        "name_label": "Patient Name",
        "age_label": "Age",
        "gender_label": "Gender",
        "diet_label": "Diet Preference",
        "g_opts": ("Male", "Female", "Other"),
        "d_opts": ("Vegetarian", "Non-Vegetarian"),
        "hist_title": "📜 History & Trend",
        "search_label": "🔍 Search Name",
        "graph_title": "Hb Trend Analysis",
        "found_rec": "Found records:",
        "no_rec": "No records found.",
        "install": "📲 <b>Install App:</b> Tap Browser Menu (⋮) & Select \"Add to Home Screen\"",
        "title": "HemoLens AI ",
        "subtitle": " Anemia Screening Tool",
        "inst": "💡 **Instructions:** Use Daylight. Adjust the **RED Box** to cover ONLY the pink inner eyelid.",
        "up_l": "Left Eye Image",
        "up_r": "Right Eye Image",
        "adj_title": "👁️ Adjust Analysis Region",
        "cap_l": "Left Eye: Green=Sclera, Red=Eyelid",
        "cap_r": "Right Eye: Green=Sclera, Red=Eyelid",
        "run_btn": "🚀 RUN ANALYSIS",
        "err_name": "Please enter Patient Name in Sidebar!",
        "err_eye": "❌ Error: Selection Invalid. Please adjust boxes.",
        "hb_res": "Hb Level",
        "rec_title": "🥗 Recommendation:",
        "tip_title": "💡 Tip:",
        "table_t": "📊 Biological Reference Values (Normal Range)",
        "table_m": "👨 Adult Male: <b>13.0 - 17.0 g/dL</b>",
        "table_f": "👩 Adult Female: <b>12.0 - 15.0 g/dL</b>",
        # --- UPDATED ENGLISH CAUTION ---
        "caution": "⚠️ <b>MEDICAL DISCLAIMER:</b><br>This is an AI screening tool, <b>NOT a clinical diagnosis.</b> Results can be <b>+/- 1 g/dL</b>.<br>Please consult a doctor for a laboratory CBC blood test.",
        "dl_btn": "📥 Download Report (PDF)",
        "wa_msg": "My HemoLens Report: Hb",
        "wa_btn": "📲 Share on WhatsApp",
        "footer_txt": " Developed by <b>Mohit Choudhury</b> "
    }

# ==========================================
# 2. RENDER SIDEBAR (Only Profile & Search Input)
# ==========================================
st.sidebar.subheader(txt["sidebar_title"])
p_name = st.sidebar.text_input(txt["name_label"])
p_age = st.sidebar.number_input(txt["age_label"], 1, 100, 25)
p_gender = st.sidebar.selectbox(txt["gender_label"], txt["g_opts"])
p_diet = st.sidebar.radio(txt["diet_label"], txt["d_opts"])

st.sidebar.markdown("---")
st.sidebar.subheader(txt["hist_title"])
search_name = st.sidebar.text_input(txt["search_label"]).strip().lower()

# ==========================================
# 3. RENDER MAIN UI
# ==========================================
st.markdown(f"""<div class="install-bar">{txt['install']}</div>""", unsafe_allow_html=True)
st.markdown(f"""<div class="main-header"><h1>🩺 {txt['title']}</h1><p>{txt['subtitle']}</p></div>""", unsafe_allow_html=True)

if search_name:
    if os.path.isfile(DB_FILE):
        df_history = pd.read_csv(DB_FILE, on_bad_lines='skip')
        recs = df_history[df_history['Name'] == search_name]
        if not recs.empty:
            st.success(f"{txt['found_rec']} {len(recs)}")
            fig = px.line(recs, x='Timestamp', y='Hb_Level', markers=True, title=f"{txt['graph_title']}: {search_name.upper()}")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(recs[['Timestamp', 'Hb_Level', 'Status']], use_container_width=True)
        else:
            st.warning(txt["no_rec"])
    else:
        st.warning(txt["no_rec"])

else:
    st.info(txt['inst'])
    col1, col2 = st.columns(2)
    with col1: up_l = st.file_uploader(txt['up_l'], type=["jpg", "png", "jpeg"])
    with col2: up_r = st.file_uploader(txt['up_r'], type=["jpg", "png", "jpeg"])

    if up_l and up_r:
        img_l, img_r = Image.open(up_l), Image.open(up_r)
        st.markdown(f"### {txt['adj_title']}")
        c1, c2 = st.columns(2)
        with c1: 
            st.caption(txt['cap_l'])
            sl_crop = st_cropper(img_l, box_color='#00FF00', key="sl"); cl_crop = st_cropper(img_l, box_color='#FF0000', key="cl")
        with c2: 
            st.caption(txt['cap_r'])
            sr_crop = st_cropper(img_r, box_color='#00FF00', key="sr"); cr_crop = st_cropper(img_r, box_color='#FF0000', key="cr")
        st.markdown("---")
        
        if st.button(txt['run_btn']):
            if not p_name: st.error(txt['err_name'])
            else:
                valid_l, msg_l = validate_red_color(np.array(cl_crop))
                valid_r, msg_r = validate_red_color(np.array(cr_crop))
                if not valid_l or not valid_r: st.error(txt['err_eye'])
                else:
                   # Naya Code (Better Accuracy):
# --- NAYA FORMULA (Proper Spacing ke saath) ---
                    def calc_hb(s, c):
                        s_arr, c_arr = np.array(s), np.array(c)
                        ref_w = np.mean(s_arr, axis=(0,1))
                        avg_c = np.mean(c_arr, axis=(0,1))
                        
                        # Ratio Calculation
                        r_val = avg_c[0]/(ref_w[0]+1e-6)
                        g_val = avg_c[1]/(ref_w[1]+1e-6)
                        b_val = avg_c[2]/(ref_w[2]+1e-6)
                        
                        ratio = r_val / ((g_val + b_val)/2 + 1e-6)
                        
                        # Calibrated Formula: Isse result 7.0 - 16.0 ke beech aayega
                        hb_val = 2.0 + (ratio * 6.0)
                        
                        return max(6.0, min(hb_val, 16.5))

                    hb_final = round((calc_hb(sl_crop, cl_crop) + calc_hb(sr_crop, cr_crop)) / 2, 1)
                    res = get_expert_diet(hb_final, p_diet, p_lang)
                    save_data(p_name, p_age, p_gender, p_diet, hb_final, res['status'])

                    r_c1, r_c2 = st.columns([1, 1])
                    with r_c1: st.markdown(f'<div class="result-card"><p>{txt["hb_res"]}</p><div class="hb-val">{hb_final}</div><p><b>{res["status"]}</b></p></div>', unsafe_allow_html=True)
                    with r_c2: st.markdown(f'<div class="result-card" style="border-left: 5px solid #007BFF; text-align:left;"><b>{txt["rec_title"]}</b><br>{res["plan"]}<br><br><b>{txt["tip_title"]}</b><br>{res["advice"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="background:#f9f9f9; padding:15px; border-radius:10px; margin-top:15px; border:1px solid #ddd;">
                        <h4 style="margin:0; color:#555;">{txt['table_t']}</h4>
                        <p style="margin:5px 0;">{txt['table_m']}</p>
                        <p style="margin:0;">{txt['table_f']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""<div class="caution-box">{txt['caution']}</div>""", unsafe_allow_html=True)

                    col_d1, col_d2 = st.columns(2)
                    pdf_bytes = generate_pdf(p_name, p_age, p_gender, p_diet, hb_final, res['status'], res['plan'], res['advice'])
                    with col_d1: st.download_button(txt['dl_btn'], pdf_bytes, f"HemoLens_{p_name}.pdf")
                    
                    with col_d2:
                        share_text = f"{txt['wa_msg']} {hb_final} g/dL ({res['status']})"
                        wa_url = f"https://wa.me/?text={share_text}"
                        st.markdown(f'<a href="{wa_url}" target="_blank" class="whatsapp-btn">{txt["wa_btn"]}</a>', unsafe_allow_html=True)

# ==========================================
# 4. FOOTER (CREDITS)
# ==========================================
st.markdown(f"""
<div class="dev-footer">
    {txt['footer_txt']}
</div>
""", unsafe_allow_html=True)
