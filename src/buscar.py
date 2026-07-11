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
coleccion = cliente.get_or_create_collection(
    name="megalamparas_documentos",
    metadata={"hnsw:space": "cosine"}
)


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

# --- Reordenar los resultados usando Cohere Rerank para mayor precisión ---
def rerankear_resultados(pregunta, resultados):
    documentos = resultados["documents"][0]

    respuesta_rerank = co.rerank(
        query=pregunta,
        documents=documentos,
        top_n=3,
        model="rerank-multilingual-v3.0"
    )

    resultados_finales = []
    for item in respuesta_rerank.results:
        indice_original = item.index
        resultados_finales.append({
            "texto": documentos[indice_original],
            "metadata": resultados["metadatas"][0][indice_original],
            "score_relevancia": item.relevance_score
        })

    return resultados_finales

if __name__ == "__main__":
    pregunta = "¿Cuál es la misión de la empresa?"

    # Traemos un grupo más amplio primero (top 10), luego rerankeamos a los 3 mejores
    resultados = buscar_chunks_relevantes(pregunta, n_resultados=10)
    resultados_finales = rerankear_resultados(pregunta, resultados)

    print(f"Pregunta: {pregunta}\n")
    print("Chunks más relevantes (después de rerank):\n")

    for i, r in enumerate(resultados_finales):
        print(f"--- Resultado {i+1} (relevancia: {r['score_relevancia']:.4f}) ---")
        print(f"Archivo: {r['metadata']['archivo']} ({r['metadata']['ubicacion']})")
        print(f"Texto: {r['texto'][:200]}...")
        print()