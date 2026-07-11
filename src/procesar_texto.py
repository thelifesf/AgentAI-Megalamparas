import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from leer_documento import leer_todos_los_documentos


# --- Unir letras/bloques cortos que quedaron separados por diseño ---
def unir_letras_espaciadas(texto):
    # Busca 4 o más "palabras" de 1 o 2 letras seguidas (separadas por espacio)
    # y las une sin espacio. Un texto normal en español casi nunca tiene
    # 4+ palabras tan cortas seguidas, por lo que es una señal confiable
    # de que es un título con letras separadas por diseño.
    patron = re.compile(r'(?:\b[\wÁÉÍÓÚÑáéíóúñ]{1,2}\b ){3,}[\wÁÉÍÓÚÑáéíóúñ]{1,2}\b', re.UNICODE)
    return patron.sub(lambda m: m.group(0).replace(" ", ""), texto)


# --- Limpiar texto: quita ruido común de PDFs/Word mal formateados ---
def limpiar_texto(texto):
    texto = unir_letras_espaciadas(texto)

    # Espacios y tabs múltiples -> un solo espacio
    texto = re.sub(r"[ \t]+", " ", texto)

    # Líneas que son solo un número (probable número de página suelto) -> se eliminan
    texto = re.sub(r"^\s*\d{1,4}\s*$", "", texto, flags=re.MULTILINE)

    # Líneas tipo "Página 3 de 10" o "Page 3 of 10" -> se eliminan
    texto = re.sub(r"^\s*(página|pagina|page)\s+\d+\s+(de|of)\s+\d+\s*$", "",
                    texto, flags=re.MULTILINE | re.IGNORECASE)

    # Múltiples líneas vacías seguidas -> una sola
    texto = re.sub(r"\n\s*\n+", "\n", texto)

    # Espacios sueltos al inicio/final de cada línea
    lineas = [linea.strip() for linea in texto.split("\n")]
    texto = "\n".join(linea for linea in lineas if linea != "")

    return texto.strip()


# --- Detectar y eliminar encabezados/pies de página repetidos en un PDF ---
def quitar_encabezados_repetidos(paginas):
    # Si una misma línea aparece en más de la mitad de las páginas, es probable
    # que sea un encabezado o pie de página fijo (ej: nombre de la empresa repetido)
    if len(paginas) < 3:
        return paginas  # con muy pocas páginas no vale la pena analizar patrones

    conteo_lineas = {}
    for pagina in paginas:
        lineas_unicas = set(l.strip() for l in pagina["texto"].split("\n") if l.strip())
        for linea in lineas_unicas:
            conteo_lineas[linea] = conteo_lineas.get(linea, 0) + 1

    umbral = len(paginas) * 0.5
    lineas_a_quitar = {linea for linea, veces in conteo_lineas.items() if veces > umbral}

    paginas_limpias = []
    for pagina in paginas:
        lineas_filtradas = [l for l in pagina["texto"].split("\n") if l.strip() not in lineas_a_quitar]
        paginas_limpias.append({"pagina": pagina["pagina"], "texto": "\n".join(lineas_filtradas)})

    return paginas_limpias


# --- Cortar los documentos en chunks, preservando metadatos y agregando contexto ---
def crear_chunks(documentos_texto):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = []

    for doc in documentos_texto:
        unidades = doc["unidades"]

        # Solo aplica a PDFs (Word no tiene encabezados repetidos por página)
        if doc["tipo"] == "pdf":
            unidades = quitar_encabezados_repetidos(unidades)

        for unidad in unidades:
            texto_limpio = limpiar_texto(unidad["texto"])

            if not texto_limpio:
                continue  # si después de limpiar no queda nada, se salta

            pedazos = splitter.split_text(texto_limpio)

            for pedazo in pedazos:
                # --- Ubicación (página o sección) ---
                if doc["tipo"] == "pdf":
                    ubicacion = f"página {unidad['pagina']}"
                else:
                    ubicacion = f"sección: {unidad['seccion']}"

                # --- Texto con contexto extra para mejorar la búsqueda semántica ---
                nombre_archivo = doc["archivo"].split("\\")[-1].split("/")[-1]
                contexto = f"Documento: {nombre_archivo} | Categoría: {doc['categoria']} | {ubicacion}\n"

                chunk = {
                    "archivo": doc["archivo"],
                    "tipo": doc["tipo"],
                    "categoria": doc["categoria"],
                    "fecha": doc["fecha"],
                    "texto": pedazo,                          # texto limpio, para mostrar al usuario
                    "texto_con_contexto": contexto + pedazo,  # para generar el embedding
                    "ubicacion": ubicacion
                }
                chunks.append(chunk)

    return chunks


# --- Prueba ---
if __name__ == "__main__":
    textos, tablas = leer_todos_los_documentos("Politicas-Negocio")
    chunks = crear_chunks(textos)

    print(f"Se generaron {len(chunks)} chunks en total.\n")

    for i, chunk in enumerate(chunks[:3]):
        print(f"--- Chunk {i+1} (de {chunk['archivo']}, {chunk['ubicacion']}) ---")
        print(chunk["texto"])
        print()