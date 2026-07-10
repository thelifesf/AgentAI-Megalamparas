from pypdf import PdfReader
from docx import Document
import pandas as pd

# PDF
def leer_pdf(ruta):
    reader = PdfReader(ruta)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

# WORD
def leer_word(ruta):
    doc = Document(ruta)
    texto = ""
    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"
    return texto

# EXCEL
def leer_excel(ruta):
    df = pd.read_excel(ruta)
    return df

# PRUEBAS UNITARIAS DE LECTOR
#print(leer_pdf("Politicas-Negocio/Estrategico/Megalamparas_Mision_Vision.pdf"))
#print(leer_word("Politicas-Negocio/Legal/3_Politica_Privacidad_Proteccion_Datos.docx"))
#print(leer_excel("Politicas-Negocio/Operacional/PRECIOS MEGALAMPARAS.xlsx"))