import os
from dotenv import load_dotenv
from pathlib import Path
import cohere

import time
from cohere.errors.too_many_requests_error import TooManyRequestsError
from generar_respuesta import responder_pregunta
from generar_respuesta_excel import responder_pregunta_excel
from buscar_excel import cargar_precios

# --- Reintentar una llamada a Cohere si se excede el límite de rate ---
def llamar_con_reintento(funcion, *args, intentos=3, **kwargs):
    for intento in range(intentos):
        try:
            return funcion(*args, **kwargs)
        except TooManyRequestsError:
            if intento < intentos - 1:
                print("⏳ Límite de Cohere alcanzado, esperando 15 segundos...")
                time.sleep(15)
            else:
                raise

# --- Cargar API key ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key)

# --- Cargar el Excel una sola vez al iniciar (no en cada pregunta) ---
df_precios = cargar_precios()


# --- Clasificar la pregunta: ¿es sobre productos/precios o sobre políticas/info general? ---
def clasificar_pregunta(pregunta):
    prompt = f"""Clasifica la siguiente pregunta de un usuario en UNA sola categoría:

- "PRODUCTOS": si la pregunta es ÚNICAMENTE sobre precios, productos, catálogo, stock, códigos, 
  colores o características técnicas de ARTÍCULOS FÍSICOS que vende la empresa (lámparas, apliques, muebles, etc.).
- "POLITICAS": si la pregunta es ÚNICAMENTE sobre información institucional, misión, visión, valores, 
  reglamento interno, políticas de privacidad, contratación, RRHH, o cualquier tema de la empresa que no sea de productos.
- "AMBOS": si la pregunta combina en una sola cosas de PRODUCTOS y de POLITICAS a la vez.
- "OTRO": si es un saludo, despedida, agradecimiento, o algo sin relación con MEGALÁMPARAS.

IMPORTANTE: la palabra "precio" no siempre implica PRODUCTOS. Si preguntan por el "precio", "costo" 
o "valor" de un documento, reglamento, política o trámite (no de un artículo físico), es POLITICAS, 
no PRODUCTOS. Los documentos internos de la empresa no tienen precio.

Responde ÚNICAMENTE con una palabra: "PRODUCTOS", "POLITICAS", "AMBOS" u "OTRO".

Pregunta: {pregunta}

Categoría:"""

    respuesta = llamar_con_reintento(
        co.chat,
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    categoria = respuesta.message.content[0].text.strip().upper()

    if "AMBOS" in categoria:
        return "AMBOS"
    elif "PRODUCTOS" in categoria:
        return "PRODUCTOS"
    elif "OTRO" in categoria:
        return "OTRO"
    else:
        return "POLITICAS"


# --- Separar una pregunta mixta en dos sub-preguntas independientes ---
def separar_pregunta(pregunta):
    prompt = f"""La siguiente pregunta combina un tema de POLÍTICAS/información institucional 
y un tema de PRODUCTOS/precios en una sola frase. Sepárala en dos preguntas independientes y completas.

Responde ÚNICAMENTE en este formato exacto, sin explicación adicional:
POLITICAS: [pregunta de políticas aquí]
PRODUCTOS: [pregunta de productos aquí]

Pregunta original: {pregunta}"""

    respuesta = llamar_con_reintento(
        co.chat,
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    texto = respuesta.message.content[0].text.strip()

    # Por defecto, si algo falla al separar, usamos la pregunta original en ambas
    pregunta_politicas = pregunta
    pregunta_productos = pregunta

    for linea in texto.split("\n"):
        if linea.upper().startswith("POLITICAS:"):
            pregunta_politicas = linea.split(":", 1)[1].strip()
        elif linea.upper().startswith("PRODUCTOS:"):
            pregunta_productos = linea.split(":", 1)[1].strip()

    return pregunta_politicas, pregunta_productos


# --- Punto de entrada único: recibe la pregunta y decide a dónde mandarla ---
def responder(pregunta):
    categoria = clasificar_pregunta(pregunta)

    if categoria == "PRODUCTOS":
        respuesta = responder_pregunta_excel(pregunta, df_precios)

    elif categoria == "AMBOS":
        # Separamos la pregunta mixta en dos preguntas limpias e independientes,
        # para que cada búsqueda (RAG y Excel) reciba una consulta enfocada
        pregunta_politicas, pregunta_productos = separar_pregunta(pregunta)

        respuesta_politicas = responder_pregunta(pregunta_politicas)
        respuesta_productos = responder_pregunta_excel(pregunta_productos, df_precios)

        respuesta = (
            f"{respuesta_politicas}\n\n"
            f"---\n\n"
            f"Sobre la parte de productos:\n{respuesta_productos}"
        )

    elif categoria == "OTRO":
        respuesta = ("¡Hola! Soy el asistente virtual de MEGALÁMPARAS. "
                     "Puedo ayudarte con información sobre nuestros productos, precios, "
                     "o políticas de la empresa (misión, visión, RRHH, privacidad, etc.). "
                     "¿En qué puedo ayudarte?")
    else:
        respuesta = responder_pregunta(pregunta)

    return respuesta, categoria


# --- Prueba ---
# --- Prueba rápida de verificación ---
if __name__ == "__main__":
    preguntas_prueba = [
        "¿Cuál es la misión de la empresa?",
        "¿Cuánto cuesta el producto APL-30066?",
    ]

    for pregunta in preguntas_prueba:
        respuesta, categoria = responder(pregunta)
        print(f"Pregunta: {pregunta}")
        print(f"Categoría detectada: {categoria}")
        print(f"Respuesta:\n{respuesta}")
        print("="*70)
        print()
        time.sleep(3)
