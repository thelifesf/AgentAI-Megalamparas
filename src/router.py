import os
from dotenv import load_dotenv
from pathlib import Path
import cohere

from generar_respuesta import responder_pregunta
from generar_respuesta_excel import responder_pregunta_excel
from buscar_excel import cargar_precios

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
  colores o características técnicas de artículos que vende la empresa.
- "POLITICAS": si la pregunta es ÚNICAMENTE sobre información institucional, misión, visión, valores, 
  reglamento interno, políticas de privacidad, contratación, RRHH, u otro tema de la empresa que no sea de productos.
- "AMBOS": si la pregunta combina en una sola cosas de PRODUCTOS y de POLITICAS a la vez 
  (ej: pregunta por valores de la empresa Y por productos en la misma frase).
- "OTRO": si es un saludo, despedida, agradecimiento, o algo sin relación con MEGALÁMPARAS.

Responde ÚNICAMENTE con una palabra: "PRODUCTOS", "POLITICAS", "AMBOS" u "OTRO".

Pregunta: {pregunta}

Categoría:"""

    respuesta = co.chat(
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


def responder(pregunta):
    categoria = clasificar_pregunta(pregunta)

    if categoria == "PRODUCTOS":
        respuesta = responder_pregunta_excel(pregunta, df_precios)

    elif categoria == "AMBOS":
        respuesta_politicas = responder_pregunta(pregunta)
        respuesta_productos = responder_pregunta_excel(pregunta, df_precios)
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
if __name__ == "__main__":
    preguntas_prueba = [
        "¿Cuál es la misión de la empresa?",
        "¿Cuánto cuesta el producto APL-30066?",
        "¿Tienen apliques de pared color negro?",
        "¿Cómo es el proceso de contratación de personal?",
        "Hola, ¿cómo estás?",
        "¿Cuáles son los valores de la empresa y qué lámparas recomiendan para exteriores?",
        "¿Cuál es la capital de Ecuador?",
        "¿Cuáles son los valores de la empresa?",
        "Necesito saber el precio del reglamento interno" 
    ]

    for pregunta in preguntas_prueba:
        respuesta, categoria = responder(pregunta)
        print(f"Pregunta: {pregunta}")
        print(f"Categoría detectada: {categoria}")
        print(f"Respuesta:\n{respuesta}")
        print("="*70)
        print()