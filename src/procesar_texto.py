import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from leer_documento import leer_todos_los_documentos
 
 
# --- Unir letras/bloques cortos que quedaron separados por diseño ---
def unir_letras_espaciadas(texto):
    patron = re.compile(r'(?:\b[\wÁÉÍÓÚÑáéíóúñ]{1,2}\b ){3,}[\wÁÉÍÓÚÑáéíóúñ]{1,2}\b', re.UNICODE)
    return patron.sub(lambda m: m.group(0).replace(" ", ""), texto)
 
 
# --- Limpiar texto: quita ruido común de PDFs/Word mal formateados ---
def limpiar_texto(texto):
    texto = unir_letras_espaciadas(texto)
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"^\s*\d{1,4}\s*$", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*(página|pagina|page)\s+\d+\s+(de|of)\s+\d+\s*$", "",
                    texto, flags=re.MULTILINE | re.IGNORECASE)
    texto = re.sub(r"\n\s*\n+", "\n", texto)
    lineas = [linea.strip() for linea in texto.split("\n")]
    texto = "\n".join(linea for linea in lineas if linea != "")
    return texto.strip()
 
 
# --- Detectar y eliminar encabezados/pies de página repetidos en un PDF ---
def quitar_encabezados_repetidos(paginas):
    if len(paginas) < 3:
        return paginas
 
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
 
 
# --- Armar un chunk con sus metadatos + texto con contexto ---
def _armar_chunk(doc, pedazo, ubicacion):
    nombre_archivo = doc["archivo"].split("\\")[-1].split("/")[-1]
    contexto = f"Documento: {nombre_archivo} | Categoría: {doc['categoria']} | {ubicacion}\n"
 
    return {
        "archivo": doc["archivo"],
        "tipo": doc["tipo"],
        "categoria": doc["categoria"],
        "fecha": doc["fecha"],
        "texto": pedazo,
        "texto_con_contexto": contexto + pedazo,
        "ubicacion": ubicacion
    }
 
 
# --- Cortar los documentos en chunks, preservando metadatos y agregando contexto ---
def crear_chunks(documentos_texto):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
 
    chunks = []
 
    for doc in documentos_texto:
        unidades = doc["unidades"]
 
        if doc["tipo"] == "pdf":
            unidades = quitar_encabezados_repetidos(unidades)
 
            # --- Unir TODAS las páginas en un solo texto continuo, ---
            # --- para no cortar contenido que cruza el límite entre páginas ---
            textos_limpios = []
            offsets_paginas = []  # lista de (offset_inicio_en_texto_completo, numero_de_pagina)
            offset_actual = 0
 
            for unidad in unidades:
                texto_limpio = limpiar_texto(unidad["texto"])
                if not texto_limpio:
                    continue
                offsets_paginas.append((offset_actual, unidad["pagina"]))
                textos_limpios.append(texto_limpio)
                offset_actual += len(texto_limpio) + 1  # +1 por el separador "\n"
 
            if not textos_limpios:
                continue
 
            texto_completo = "\n".join(textos_limpios)
            pedazos = splitter.split_text(texto_completo)
 
            posicion_busqueda = 0
            for pedazo in pedazos:
                idx = texto_completo.find(pedazo, max(0, posicion_busqueda - 100))
                if idx == -1:
                    idx = posicion_busqueda
                posicion_busqueda = idx
 
                # Determinar a qué página pertenece el inicio de este chunk
                pagina_del_chunk = offsets_paginas[0][1]
                for offset, num_pagina in offsets_paginas:
                    if offset <= idx:
                        pagina_del_chunk = num_pagina
                    else:
                        break
 
                ubicacion = f"página {pagina_del_chunk}"
                chunks.append(_armar_chunk(doc, pedazo, ubicacion))
 
        else:
            # Word: se mantiene por secciones, ya vienen bien delimitadas por título
            for unidad in unidades:
                texto_limpio = limpiar_texto(unidad["texto"])
                if not texto_limpio:
                    continue
 
                pedazos = splitter.split_text(texto_limpio)
                for pedazo in pedazos:
                    ubicacion = f"sección: {unidad['seccion']}"
                    chunks.append(_armar_chunk(doc, pedazo, ubicacion))
 
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