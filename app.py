import streamlit as st
from validator import ICE_Validator

st.set_page_config(page_title="ICE CWR 2.2 Strict Validator", page_icon="🛡️", layout="wide")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_app():
    st.session_state.uploader_key += 1

st.title("ICE CWR 2.2 Strict Validator")

uploaded_file = st.file_uploader(
    "Upload .V22 File", 
    type=["v22", "txt", "cwr"], 
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    raw_content = uploaded_file.getvalue().decode("latin-1") 
    filename = uploaded_file.name
    
    validator = ICE_Validator(raw_content, filename)
    passed = validator.run()
    
    if passed:
        st.success(f"✅ VALID: {filename} passes all CWR v2.2 and ICE requirements.")
    else:
        st.error(f"❌ INVALID: {filename} contains critical structural or data errors.")
        
    report = []
    if validator.errors:
        report.append("🔴 CRITICAL ERRORS (FILE WILL BE REJECTED)")
        report.append("-" * 60)
        report.extend([f"- {e}" for e in validator.errors])

    if report:
        st.text_area("Audit Report", value="\n".join(report), height=500)
        st.download_button("Download Audit Report", data="\n".join(report), file_name=f"Audit_{filename}.txt")

    st.button("🔄 Reset Validator", on_click=reset_app)
