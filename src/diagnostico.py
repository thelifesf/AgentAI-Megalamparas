import chromadb
import numpy as np
from buscar import embeber_pregunta
from leer_documento import leer_pdf

avisos = []
paginas = leer_pdf("Politicas-Negocio/Estrategico/Megalamparas_Mision_Vision.pdf", avisos)

for pagina in paginas:
    print(f"--- Página {pagina['pagina']} ---")
    print(repr(pagina["texto"]))  # repr() nos muestra saltos de línea y espacios exactos
    print()

cliente = chromadb.PersistentClient(path="chroma_db")
coleccion = cliente.get_or_create_collection(
    name="megalamparas_documentos",
    metadata={"hnsw:space": "cosine"}
)

# --- Traer el chunk de la Misión con su embedding guardado ---
resultado = coleccion.get(ids=["chunk_0"], include=["documents", "embeddings"])
embedding_chunk0 = np.array(resultado["embeddings"][0])

# --- Generar el embedding de la pregunta ---
pregunta = "¿Cuál es la misión de la empresa?"
embedding_pregunta = np.array(embeber_pregunta(pregunta))

# --- Calcular similitud coseno manualmente ---
similitud = np.dot(embedding_chunk0, embedding_pregunta) / (
    np.linalg.norm(embedding_chunk0) * np.linalg.norm(embedding_pregunta)
)
distancia_coseno = 1 - similitud

print(f"Similitud coseno con chunk_0: {similitud:.4f}")
print(f"Distancia coseno con chunk_0: {distancia_coseno:.4f}")

# --- Comparar contra el ranking que da ChromaDB ---
resultados_busqueda = coleccion.query(
    query_embeddings=[embedding_pregunta.tolist()],
    n_results=69  # traer TODOS para ver en qué puesto queda chunk_0
)

ids_ordenados = resultados_busqueda["ids"][0]
posicion = ids_ordenados.index("chunk_0") + 1
print(f"\nchunk_0 quedó en la posición #{posicion} de 69 resultados")
print(f"Distancia que le asignó ChromaDB: {resultados_busqueda['distances'][0][ids_ordenados.index('chunk_0')]:.4f}")