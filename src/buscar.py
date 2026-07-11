import os
from dotenv import load_dotenv
from pathlib import Path
import cohere
import chromadb

# --- Cargar API key ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key)

# --- Conectar a la base de datos vectorial ya guardada ---
cliente = chromadb.PersistentClient(path="chroma_db")
coleccion = cliente.get_or_create_collection(name="megalamparas_documentos")


# --- Convertir la pregunta del usuario en embedding ---
def embeber_pregunta(pregunta):
    respuesta = co.embed(
        texts=[pregunta],
        model="embed-multilingual-v3.0",
        input_type="search_query",   # <-- distinto a "search_document": esto es una consulta
        embedding_types=["float"]
    )
    return respuesta.embeddings.float[0]


# --- Buscar los chunks más relevantes para una pregunta ---
def buscar_chunks_relevantes(pregunta, n_resultados=3):
    embedding_pregunta = embeber_pregunta(pregunta)

    resultados = coleccion.query(
        query_embeddings=[embedding_pregunta],
        n_results=n_resultados
    )

    return resultados


# --- Prueba ---
if __name__ == "__main__":
    pregunta = "¿Cuál es la misión de la empresa?"

    resultados = buscar_chunks_relevantes(pregunta)

    print(f"Pregunta: {pregunta}\n")
    print("Chunks más relevantes encontrados:\n")

    for i in range(len(resultados["documents"][0])):
        texto = resultados["documents"][0][i]
        metadata = resultados["metadatas"][0][i]
        distancia = resultados["distances"][0][i]

        print(f"--- Resultado {i+1} (distancia: {distancia:.4f}) ---")
        print(f"Archivo: {metadata['archivo']} ({metadata['ubicacion']})")
        print(f"Texto: {texto[:200]}...")
        print()