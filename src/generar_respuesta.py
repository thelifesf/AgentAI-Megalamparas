import os
from dotenv import load_dotenv
from pathlib import Path
import cohere
from buscar import buscar_chunks_relevantes, rerankear_resultados

# --- Cargar API key ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key)


# --- Armar el contexto final con los chunks encontrados ---
def construir_contexto(resultados_finales):
    partes = []
    for r in resultados_finales:
        fuente = f"[Fuente: {r['metadata']['archivo']}, {r['metadata']['ubicacion']}]"
        partes.append(f"{fuente}\n{r['texto']}")
    return "\n\n---\n\n".join(partes)


# --- Generar la respuesta final usando Cohere Command ---
def responder_pregunta(pregunta):
    # 1. Buscar candidatos por similitud
    resultados = buscar_chunks_relevantes(pregunta, n_resultados=10)

    # 2. Rerankear para quedarnos con los 3 más precisos
    resultados_finales = rerankear_resultados(pregunta, resultados)

    # 3. Armar el contexto de texto que le vamos a dar al modelo
    contexto = construir_contexto(resultados_finales)

    # 4. Construir el prompt con instrucciones claras
    prompt = f"""Eres un asistente de la empresa MEGALÁMPARAS. Responde la pregunta del usuario 
basándote ÚNICAMENTE en la información de los fragmentos de documentos que se muestran abajo.

Si la información no está en los fragmentos, di claramente que no tienes esa información 
en los documentos disponibles, no inventes nada.

Al final de tu respuesta, menciona de qué documento(s) sacaste la información.

Fragmentos de documentos:
{contexto}

Pregunta del usuario: {pregunta}

Respuesta:"""

    # 5. Llamar al modelo de chat de Cohere
    respuesta = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    return respuesta.message.content[0].text


# --- Prueba ---
if __name__ == "__main__":
    pregunta = "¿Cuál es la misión de la empresa?"
    respuesta = responder_pregunta(pregunta)

    print(f"Pregunta: {pregunta}\n")
    print(f"Respuesta:\n{respuesta}")