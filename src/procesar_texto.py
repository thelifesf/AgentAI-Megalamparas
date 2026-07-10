from langchain_text_splitters import RecursiveCharacterTextSplitter
from leer_documento import leer_todos_los_documentos

# --- Cortar los documentos de texto en pedazos pequeños ---
def crear_chunks(documentos_texto):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # tamaño aproximado de cada pedazo (en caracteres)
        chunk_overlap=50      # cuánto se "repite" entre un pedazo y el siguiente
    )

    chunks = []  # aquí van a ir todos los pedacitos de todos los documentos

    for doc in documentos_texto:
        pedazos = splitter.split_text(doc["contenido"])

        for pedazo in pedazos:
            chunks.append({
                "archivo": doc["archivo"],
                "tipo": doc["tipo"],
                "texto": pedazo
            })

    return chunks


# --- Prueba ---
if __name__ == "__main__":
    textos, tablas = leer_todos_los_documentos("Politicas-Negocio")
    chunks = crear_chunks(textos)

    print(f"Se generaron {len(chunks)} chunks en total.\n")

    # Mostramos los primeros 3 como ejemplo
    for i, chunk in enumerate(chunks[:3]):
        print(f"--- Chunk {i+1} (de {chunk['archivo']}) ---")
        print(chunk["texto"])
        print()