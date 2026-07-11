import chromadb
from leer_documento import leer_todos_los_documentos
from procesar_texto import crear_chunks
from generar_embeddings import generar_embeddings

cliente = chromadb.PersistentClient(path="chroma_db")

coleccion = cliente.get_or_create_collection(name="megalamparas_documentos")

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

if __name__ == "__main__":
    textos, tablas = leer_todos_los_documentos("Politicas-Negocio")
    chunks = crear_chunks(textos)
    chunks_con_embeddings = generar_embeddings(chunks)

    guardar_en_chroma(chunks_con_embeddings)

    print(f"Se guardaron {len(chunks_con_embeddings)} chunks en ChromaDB.")
    print(f"Total de elementos en la colección ahora: {coleccion.count()}")