import streamlit as st
from validator import ICE_Validator

st.set_page_config(page_title="Lumina ICE Validator", page_icon="🛡️", layout="centered")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_app():
    st.session_state.uploader_key += 1

st.title("ICE CWR 2.2 Validator")
st.markdown("Objective validation against ICE Berlin v2.2 Manual and Approved Blueprints.")

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
        st.success(f"✅ VALID: {filename}")
    else:
        st.error(f"❌ INVALID: {filename}")
        
    report_lines = []
    if validator.errors:
        report_lines.append("🔴 CRITICAL ERRORS")
        report_lines.append("=" * 60)
        for error in validator.errors:
            report_lines.append(f"- {error}")
            
    if validator.warnings:
        report_lines.append("\n🟡 WARNINGS")
        report_lines.append("=" * 60)
        for warning in validator.warnings:
            report_lines.append(f"- {warning}")

    if report_lines:
        st.text_area("Validation Report", value="\n".join(report_lines), height=400)
        st.download_button("Download Report", data="\n".join(report_lines), file_name=f"Report_{filename}.txt")

    st.button("🔄 Reset / New Upload", on_click=reset_app)
