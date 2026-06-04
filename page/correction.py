import streamlit as st

ocr_text = "OCR result"

corrected = st.text_area(
    "Correct OCR",
    ocr_text,
    height=300
)

if st.button("Save Correction"):
    st.success("Saved")