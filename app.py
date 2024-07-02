import re

import fitz
import pytesseract
import streamlit as st
from pdf2image import convert_from_bytes


def extract_text_from_image(image):
    return pytesseract.image_to_string(image, lang='spa')


def extract_data(file):
    try:
        file_bytes = file.read()
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        text = ''
        for page in pdf:
            text += page.get_text()
        pdf.close()
        if text == '':
            images = convert_from_bytes(file_bytes)
            for image in images:
                text += extract_text_from_image(image)
        return text
    except fitz.FileDataError as e:
        print(f"Error al abrir el PDF: {e}")
        return ""
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return ""


def parse_data(text):
    data = {}
    rfc_match = re.search(r'RFC:\s*(\w+)', text)
    if rfc_match:
        data['RFC'] = rfc_match.group(1)
    idCIF_match = re.search(r'CIF:\s*(\w+)', text)
    if idCIF_match:
        data['idCIF'] = idCIF_match.group(1)
    return data


st.title('Extract Data from Constancia de Situación Fiscal PDF')

uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
if uploaded_file is not None:
    with st.spinner('Extracting text from PDF...'):
        raw_text = extract_data(uploaded_file)

    with st.spinner('Parsing data...'):
        parsed_data = parse_data(raw_text)
    st.success('Data parsed successfully!')
    st.json(parsed_data)
