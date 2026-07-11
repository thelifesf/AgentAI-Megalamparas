from pypdf import PdfReader
from docx import Document
import pandas as pd
import os
from datetime import datetime

# --- Leer PDF, extrayendo por página (para poder citar la página exacta) ---
def leer_pdf(ruta, avisos_ocr):
    reader = PdfReader(ruta)
    paginas = []

    for i, pagina in enumerate(reader.pages, start=1):
        texto = pagina.extract_text() or ""

        # Detectar posible PDF escaneado: si una página casi no tiene texto
        if len(texto.strip()) < 20:
            avisos_ocr.append(f"{ruta} (página {i})")

        paginas.append({"pagina": i, "texto": texto})

    return paginas


# --- Leer Word, dividiendo por secciones usando los títulos (Heading) ---
def leer_word(ruta):
    doc = Document(ruta)
    secciones = []
    titulo_actual = "Introducción"
    texto_actual = ""

    for parrafo in doc.paragraphs:
        if parrafo.style is not None and parrafo.style.name.startswith("Heading"):
            if texto_actual.strip():
                secciones.append({"seccion": titulo_actual, "texto": texto_actual})
            titulo_actual = parrafo.text.strip() or titulo_actual
            texto_actual = ""
        else:
            texto_actual += parrafo.text + "\n"

    if texto_actual.strip():
        secciones.append({"seccion": titulo_actual, "texto": texto_actual})

    return secciones


# --- Leer Excel ---
def leer_excel(ruta):
    df = pd.read_excel(ruta)
    return df


# --- Recorrer todas las carpetas y separar en texto vs tablas ---
def leer_todos_los_documentos(carpeta_raiz):
    documentos_texto = []
    documentos_tabla = []
    avisos_ocr = []  # aquí juntamos todas las páginas sospechosas de estar escaneadas

    for carpeta_actual, subcarpetas, archivos in os.walk(carpeta_raiz):
        for nombre_archivo in archivos:
            ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
            categoria = os.path.basename(carpeta_actual)
            timestamp = os.path.getmtime(ruta_completa)
            fecha_modificacion = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

            if nombre_archivo.endswith(".pdf"):
                paginas = leer_pdf(ruta_completa, avisos_ocr)
                documentos_texto.append({
                    "archivo": ruta_completa,
                    "tipo": "pdf",
                    "categoria": categoria,
                    "fecha": fecha_modificacion,
                    "unidades": paginas
                })

            elif nombre_archivo.endswith(".docx"):
                secciones = leer_word(ruta_completa)
                documentos_texto.append({
                    "archivo": ruta_completa,
                    "tipo": "word",
                    "categoria": categoria,
                    "fecha": fecha_modificacion,
                    "unidades": secciones
                })

            elif nombre_archivo.endswith(".xlsx"):
                contenido = leer_excel(ruta_completa)
                documentos_tabla.append({
                    "archivo": ruta_completa,
                    "tipo": "excel",
                    "categoria": categoria,
                    "fecha": fecha_modificacion,
                    "contenido": contenido
                })

    # --- Resumen final de avisos OCR, si los hubo ---
    if avisos_ocr:
        print("\n" + "="*60)
        print("⚠️  ATENCIÓN: posibles páginas escaneadas detectadas")
        print("Estas páginas tienen muy poco texto extraíble.")
        print("Este proyecto NO incluye OCR todavía (ver README).")
        print("="*60)
        for aviso in avisos_ocr:
            print(f"  - {aviso}")
        print()

    return documentos_texto, documentos_tabla


# --- Prueba ---
if __name__ == "__main__":
    textos, tablas = leer_todos_los_documentos("Politicas-Negocio")

    print(f"Documentos de TEXTO (PDF/Word): {len(textos)}")
    for doc in textos:
        print(f"  - {doc['archivo']} ({doc['tipo']}) — {len(doc['unidades'])} unidades (páginas/secciones)")

    print(f"\nDocumentos de TABLA (Excel): {len(tablas)}")
    for doc in tablas:
        print(f"  - {doc['archivo']} ({doc['tipo']})")