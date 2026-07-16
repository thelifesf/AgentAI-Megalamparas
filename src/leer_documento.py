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
    avisos_ocr = []
    archivos_con_error = []  # nueva lista para juntar problemas de lectura

    for carpeta_actual, subcarpetas, archivos in os.walk(carpeta_raiz):
        for nombre_archivo in archivos:
            # Ignorar archivos temporales de Word/Excel (empiezan con ~$)
            if nombre_archivo.startswith("~$"):
                continue

            ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
            categoria = os.path.basename(carpeta_actual)

            try:
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

            except PermissionError:
                archivos_con_error.append((ruta_completa, "archivo abierto/bloqueado en otro programa"))
            except Exception as e:
                archivos_con_error.append((ruta_completa, str(e)))

    # --- Resumen de avisos OCR ---
    if avisos_ocr:
        print("\n" + "="*60)
        print("⚠️  ATENCIÓN: posibles páginas escaneadas detectadas")
        print("="*60)
        for aviso in avisos_ocr:
            print(f"  - {aviso}")
        print()

    # --- Resumen de archivos que fallaron ---
    if archivos_con_error:
        print("\n" + "="*60)
        print("⚠️  ATENCIÓN: algunos archivos no se pudieron leer")
        print("="*60)
        for archivo, razon in archivos_con_error:
            print(f"  - {archivo} → {razon}")
        print("Revisa que no estén abiertos en otro programa y vuelve a intentar.")
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