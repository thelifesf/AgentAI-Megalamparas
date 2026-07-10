from pypdf import PdfReader
from docx import Document
import pandas as pd
import os

from pypdf import PdfReader
from docx import Document
import pandas as pd
import os

# Leer PDF
def leer_pdf(ruta):
    reader = PdfReader(ruta)
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text()
    return texto

# Word
def leer_word(ruta):
    doc = Document(ruta)
    texto = ""
    for parrafo in doc.paragraphs:
        texto += parrafo.text + "\n"
    return texto

# Excel 
def leer_excel(ruta):
    df = pd.read_excel(ruta)
    return df


def leer_todos_los_documentos(carpeta_raiz):
    documentos_texto = []   # PDF y Word (RAG)
    documentos_tabla = []   # Excel (consulta directa de precios)

    for carpeta_actual, subcarpetas, archivos in os.walk(carpeta_raiz):
        for nombre_archivo in archivos:
            ruta_completa = os.path.join(carpeta_actual, nombre_archivo)

            if nombre_archivo.endswith(".pdf"):
                contenido = leer_pdf(ruta_completa)
                documentos_texto.append({"archivo": ruta_completa, "tipo": "pdf", "contenido": contenido})

            elif nombre_archivo.endswith(".docx"):
                contenido = leer_word(ruta_completa)
                documentos_texto.append({"archivo": ruta_completa, "tipo": "word", "contenido": contenido})

            elif nombre_archivo.endswith(".xlsx"):
                contenido = leer_excel(ruta_completa)
                documentos_tabla.append({"archivo": ruta_completa, "tipo": "excel", "contenido": contenido})

    return documentos_texto, documentos_tabla



textos, tablas = leer_todos_los_documentos("Politicas-Negocio")

print(f"Documentos de TEXTO (PDF/Word): {len(textos)}")
for doc in textos:
    print(f"  - {doc['archivo']} ({doc['tipo']})")

print(f"\nDocumentos de TABLA (Excel): {len(tablas)}")
for doc in tablas:
    print(f"  - {doc['archivo']} ({doc['tipo']})")