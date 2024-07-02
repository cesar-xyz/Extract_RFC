# This is a script for extract the data from the "Constancia de Situación Fiscal" PDF file

import re
import ssl
import warnings
from io import BytesIO

import fitz
import pytesseract
import requests
import urllib3
from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes
from requests.adapters import HTTPAdapter
from unidecode import unidecode


class Ssl3HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.set_ciphers("DEFAULT@SECLEVEL=1")
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(Ssl3HttpAdapter, self).init_poolmanager(*args, **kwargs)


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


def extraer_datos(datos_identificacion):
    datos = {'datos_identificacion': {}, 'datos_ubicacion': {}, 'caracteristicas_fiscales': []}
    caracteristicas = {}
    for dato in datos_identificacion:
        etiquetas_td = dato.find_all('td')
        if len(etiquetas_td) == 2:
            etiqueta = unidecode(etiquetas_td[0].text.strip()[:-1]).lower().replace(' ', '_')
            valor = unidecode(etiquetas_td[1].text.strip())
            if etiqueta != '':
                if etiqueta == 'curp':
                    datos['datos_identificacion']['tipo_persona'] = 'fisica'
                if etiqueta == 'denominacion_o_razon_social':
                    datos['datos_identificacion']['tipo_persona'] = 'moral'
                if etiqueta == 'curp' or etiqueta == 'nombre' or etiqueta == 'apellido_paterno' or etiqueta == 'apellido_materno' or etiqueta == 'fecha_nacimiento':
                    if etiqueta == 'fecha_nacimiento':
                        fecha_lista = valor.split('-')
                        valor = fecha_lista[2] + '-' + fecha_lista[1] + '-' + fecha_lista[0]
                    datos['datos_identificacion'][etiqueta] = valor
                elif etiqueta == 'denominacion_o_razon_social' or etiqueta == 'regimen_de_capital' or etiqueta == 'fecha_de_constitucion':
                    if etiqueta == 'fecha_de_constitucion':
                        fecha_lista = valor.split('-')
                        valor = fecha_lista[2] + '-' + fecha_lista[1] + '-' + fecha_lista[0]
                    datos['datos_identificacion'][etiqueta] = valor
                elif etiqueta == 'fecha_de_inicio_de_operaciones' or etiqueta == 'situacion_del_contribuyente' or etiqueta == 'fecha_del_ultimo_cambio_de_situacion':
                    if etiqueta == 'fecha_de_inicio_de_operaciones' or etiqueta == 'fecha_del_ultimo_cambio_de_situacion':
                        fecha_lista = valor.split('-')
                        valor = fecha_lista[2] + '-' + fecha_lista[1] + '-' + fecha_lista[0]
                    datos['datos_identificacion'][etiqueta] = valor
                elif etiqueta == 'entidad_federativa' or etiqueta == 'municipio_o_delegacion' or etiqueta == 'colonia' or etiqueta == 'tipo_de_vialidad' or etiqueta == 'nombre_de_la_vialidad' or etiqueta == 'numero_exterior' or etiqueta == 'numero_interior' or etiqueta == 'cp' or etiqueta == 'correo_electronico' or etiqueta == 'al':
                    datos['datos_ubicacion'][etiqueta] = valor
                elif etiqueta == 'regimen':
                    caracteristicas['regimen'] = valor
                elif etiqueta == 'fecha_de_alta':
                    fecha_lista = valor.split('-')
                    fecha_de_alta = fecha_lista[2] + '-' + fecha_lista[1] + '-' + fecha_lista[0]
                    caracteristicas['fecha_de_alta'] = fecha_de_alta
                    datos['caracteristicas_fiscales'].append(caracteristicas)
                    caracteristicas = {}
    return datos


def check_existence(data):
    rfc = data.get('RFC')
    id_cif = data.get('idCIF')
    url = f'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={id_cif}_{rfc}'

    session = requests.Session()
    session.mount('https://', Ssl3HttpAdapter())
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = session.get(url, verify=False)
    html = response.content
    warnings.filterwarnings("ignore", category=UserWarning)
    soup = BeautifulSoup(html, 'html.parser')
    datos_identificacion = soup.find_all('tr', {'class': 'ui-widget-content'})
    datos = extraer_datos(datos_identificacion)
    return datos


if __name__ == '__main__':
    file_path = 'Constancia_de_Situacion_Fiscal.pdf'
    raw_text = extract_data(file_path)
    if raw_text:
        parsed_data = parse_data(raw_text)
        if parsed_data:
            print(parsed_data)
            existence_data = check_existence(parsed_data)
            print(existence_data)
        else:
            print("No se encontraron datos en el texto extraído.")
    else:
        print("No se pudo extraer texto del PDF.")
