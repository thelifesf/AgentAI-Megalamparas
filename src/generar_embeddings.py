from dotenv import load_dotenv
import os
import cohere
from leer_documento import leer_todos_los_documentos
from procesar_texto import crear_chunks

# --- Cargar la API key desde el .env ---
load_dotenv()
api_key = os.getenv("COHERE_API_KEY")

# --- Conectar con Cohere ---
co = cohere.ClientV2(api_key)

# --- Generar embeddings para una lista de chunks ---
def generar_embeddings(chunks):
    textos = [chunk["texto_con_contexto"] for chunk in chunks]  # sacamos solo el texto de cada chunk

    respuesta = co.embed(
        texts=textos,
        model="embed-multilingual-v3.0",   # modelo multilingüe (sirve para español)
        input_type="search_document",       # le decimos que estos textos son "documentos" a buscar
        embedding_types=["float"]
    )

    embeddings = respuesta.embeddings.float

    # Juntamos cada chunk con su embedding correspondiente
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i]

    return chunks

