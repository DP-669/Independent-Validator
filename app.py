import streamlit as st
from validator import ICE_Validator

st.set_page_config(page_title="Lumina ICE Validator", page_icon="🛡️", layout="centered")

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_app():
    st.session_state.uploader_key += 1

st.title("ICE/PRS CWR 2.2 Validator")
st.markdown("Strict auditing against ICE Berlin manual v2.2 and verified approved file structures.")

uploaded_file = st.file_uploader(
    "Upload a .V22 file", 
    type=["v22", "txt", "cwr"], 
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    raw_content = uploaded_file.getvalue().decode("latin-1") 
    filename = uploaded_file.name
    
    st.markdown("---")
    validator = ICE_Validator(raw_content, filename)
    passed = validator.run()
    
    if passed and not validator.warnings:
        st.success(f"✅ PASSED: {filename}")
    elif passed:
        st.warning(f"⚠️ PASSED WITH WARNINGS: {filename}")
    else:
        st.error(f"❌ FAILED: {filename}")
        
    report_lines = []
    if validator.errors:
        report_lines.append("🔴 CRITICAL ERRORS (ICE Rejection Triggers)")
        report_lines.append("=" * 60)
        for error in validator.errors:
            report_lines.append(f"- {error}")
        report_lines.append("\n")
        
    if validator.warnings:
        report_lines.append("🟡 WARNINGS (Data Cleaning Issues)")
        report_lines.append("=" * 60)
        for warning in validator.warnings:
            report_lines.append(f"- {warning}")

    report_text = "\n".join(report_lines)

    if report_text:
        st.markdown("### Validation Report Document")
        st.text_area("Audit Details", value=report_text, height=300)
        st.download_button("📥 Download Report", data=report_text, file_name=f"Audit_{filename}.txt")

    with st.expander("View Raw File Data"):
        st.text(raw_content)
        
    st.button("🔄 Reset / Upload New File", on_click=reset_app)
