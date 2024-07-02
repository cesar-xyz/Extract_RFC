# This is a script for extract the data from the "Constancia de Situación Fiscal" PDF file

import re

import fitz
import pytesseract
from pdf2image import convert_from_bytes

def extract_text_from_image(image):
    return pytesseract.image_to_string(image, lang='spa')


def extract_data(file_path):
    try:
        with open(file_path, 'rb') as file:
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

    # Extract RFC
    rfc_match = re.search(r'RFC:\s*(\w+)', text)
    if rfc_match:
        data['RFC'] = rfc_match.group(1)

    # Extract idCIF
    idCIF_match = re.search(r'CIF:\s*(\w+)', text)
    if idCIF_match:
        data['idCIF'] = idCIF_match.group(1)

    return data


if __name__ == '__main__':
    file_path = 'Constancia_de_Situacion_Fiscal.pdf'
    raw_text = extract_data(file_path)
    if raw_text:
        parsed_data = parse_data(raw_text)
        if parsed_data:
            print(parsed_data)
        else:
            print("No se encontraron datos en el texto extraído.")
    else:
        print("No se pudo extraer texto del PDF.")
