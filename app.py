import streamlit as st
from validator import ICE_Validator

st.set_page_config(page_title="Lumina ICE Validator", page_icon="🛡️", layout="centered")

# Initialize session state for the reset button
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def reset_app():
    # Incrementing the key forces the file uploader widget to reset instantly
    st.session_state.uploader_key += 1

st.title("ICE/PRS CWR 2.2 Validator")
st.markdown("Strict auditing against ICE manuals and verified approved file structures.")

# Dynamic key allows the widget to be cleared via the reset button
uploaded_file = st.file_uploader(
    "Upload a .V22 file", 
    type=["v22", "txt", "cwr"], 
    key=f"uploader_{st.session_state.uploader_key}"
)

if uploaded_file is not None:
    raw_bytes = uploaded_file.getvalue()
    raw_content = raw_bytes.decode("latin-1") 
    filename = uploaded_file.name
    
    st.markdown("---")
    st.subheader(f"Audit Results: `{filename}`")
    
    # Initialize validator with the filename
    validator = ICE_Validator(raw_content, filename)
    passed = validator.run()
    
    # 1. Top-Level Status Banner
    if passed and not validator.warnings:
        st.success("✅ PASSED: File and filename perfectly match ICE specifications and Chris's blueprint.")
    elif passed:
        st.warning("⚠️ PASSED WITH WARNINGS: File is technically valid, but review notes below.")
    else:
        st.error("❌ FAILED: File violates strict ICE requirements.")
        
    # 2. Compile the Document Report
    report_lines = []
    
    if validator.errors:
        report_lines.append("🔴 CRITICAL ERRORS (ICE Rejection Triggers)")
        report_lines.append("=" * 60)
        for error in validator.errors:
            report_lines.append(f"- {error}")
        report_lines.append("\n")
        
    if validator.warnings:
        report_lines.append("🟡 WARNINGS (Potential Issues)")
        report_lines.append("=" * 60)
        for warning in validator.warnings:
            report_lines.append(f"- {warning}")

    report_text = "\n".join(report_lines)

    # 3. Present Report Document & Download Button
    if report_text:
        st.markdown("### Validation Report Document")
        st.text_area("Copyable Audit Details", value=report_text, height=300)
        
        st.download_button(
            label="📥 Download Audit Report (.txt)",
            data=report_text,
            file_name=f"Audit_Report_{filename}.txt",
            mime="text/plain"
        )

    # 4. View Raw Data Expander
    with st.expander("View Raw File Data"):
        st.text(raw_content)
        
    st.markdown("---")
    
    # 5. Reset Button
    st.button("🔄 Reset Validator / Upload New File", on_click=reset_app)
