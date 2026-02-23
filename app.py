import streamlit as st
from validator import ICE_Validator

st.set_page_config(page_title="Lumina ICE Validator", page_icon="🛡️", layout="centered")

st.title("ICE/PRS CWR 2.2 Validator")
st.markdown("Strict auditing against ICE manuals and verified approved file structures.")

uploaded_file = st.file_uploader("Upload a .V22 or .TXT file", type=["v22", "txt", "cwr"])

if uploaded_file is not None:
    raw_bytes = uploaded_file.getvalue()
    raw_content = raw_bytes.decode("latin-1") 
    
    st.markdown("---")
    st.subheader(f"Audit Results: `{uploaded_file.name}`")
    
    validator = ICE_Validator(raw_content)
    passed = validator.run()
    
    if passed and not validator.warnings:
        st.success("✅ PASSED: File perfectly matches ICE specifications and Chris's blueprint.")
    elif passed:
        st.warning("⚠️ PASSED WITH WARNINGS: File is valid, but review notes below.")
    else:
        st.error("❌ FAILED: File violates strict ICE requirements.")
        
    if validator.errors:
        st.markdown("### 🔴 Critical Errors (ICE Rejection Triggers)")
        for error in validator.errors:
            st.error(error)
            
    if validator.warnings:
        st.markdown("### 🟡 Warnings")
        for warning in validator.warnings:
            st.warning(warning)

    with st.expander("View Raw File Data"):
        st.text(raw_content)
