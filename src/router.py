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

- "PRODUCTOS": si la pregunta es sobre precios, productos, catálogo, stock, códigos de producto, 
  colores, características técnicas de artículos que vende la empresa (lámparas, apliques, muebles, etc.)
- "POLITICAS": si la pregunta es sobre información institucional, misión, visión, valores, 
  reglamento interno, políticas de privacidad, contratación, RRHH, o cualquier otro tema no relacionado a productos.

Responde ÚNICAMENTE con la palabra "PRODUCTOS" o "POLITICAS", sin explicación adicional.

Pregunta: {pregunta}

Categoría:"""

    respuesta = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    categoria = respuesta.message.content[0].text.strip().upper()

    # Protección: si el modelo responde algo raro, asumimos POLITICAS por defecto
    if "PRODUCTOS" in categoria:
        return "PRODUCTOS"
    else:
        return "POLITICAS"


# --- Punto de entrada único: recibe la pregunta y decide a dónde mandarla ---
def responder(pregunta):
    categoria = clasificar_pregunta(pregunta)

    if categoria == "PRODUCTOS":
        respuesta = responder_pregunta_excel(pregunta, df_precios)
    else:
        respuesta = responder_pregunta(pregunta)

    return respuesta, categoria


# --- Prueba ---
if __name__ == "__main__":
    preguntas_prueba = [
        "¿Cuál es la misión de la empresa?",
        "¿Cuánto cuesta el producto APL-30066?",
        "¿Tienen apliques de pared color negro?",
        "¿Cómo es el proceso de contratación de personal?"
    ]

    for pregunta in preguntas_prueba:
        respuesta, categoria = responder(pregunta)
        print(f"Pregunta: {pregunta}")
        print(f"Categoría detectada: {categoria}")
        print(f"Respuesta:\n{respuesta}")
        print("="*70)
        print()