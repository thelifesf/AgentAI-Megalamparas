import chromadb
from leer_documento import leer_todos_los_documentos
from procesar_texto import crear_chunks
from generar_embeddings import generar_embeddings

cliente = chromadb.PersistentClient(path="chroma_db")

coleccion = cliente.get_or_create_collection(
    name="megalamparas_documentos",
    metadata={"hnsw:space": "cosine"}
)

def guardar_en_chroma(chunks):
    ids = []
    documentos = []
    embeddings = []
    metadatos = []

    for i, chunk in enumerate(chunks):
        ids.append(f"chunk_{i}")                    
        documentos.append(chunk["texto"])             
        embeddings.append(chunk["embedding"])          
        metadatos.append({                              
            "archivo": chunk["archivo"],
            "tipo": chunk["tipo"],
            "categoria": chunk["categoria"],
            "fecha": chunk["fecha"],
            "ubicacion": chunk["ubicacion"]
        })

    coleccion.add(
        ids=ids,
        documents=documentos,
        embeddings=embeddings,
        metadatas=metadatos
    )