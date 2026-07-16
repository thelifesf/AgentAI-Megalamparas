import os
from dotenv import load_dotenv
from pathlib import Path
import cohere
from buscar_excel import cargar_precios, buscar_producto

# --- Cargar API key ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key)


# --- Convertir los resultados de pandas en texto simple para el prompt ---
def construir_contexto_productos(resultados, total_encontrados):
    if resultados.empty:
        return "No se encontraron productos que coincidan con la búsqueda."

    lineas = []
    for _, fila in resultados.iterrows():
        lineas.append(f"- Código: {fila['codigo']} | {fila['descripcion']} | Precio: ${fila['precio']:.2f}")

    contexto = "\n".join(lineas)

    if total_encontrados > len(resultados):
        contexto += f"\n\n(Se encontraron {total_encontrados} productos en total, se muestran {len(resultados)})"

    return contexto


# --- Generar la respuesta final usando Cohere Command ---
def responder_pregunta_excel(pregunta, df):
    resultados, total = buscar_producto(pregunta, df)
    contexto = construir_contexto_productos(resultados, total)

    prompt = f"""Eres un asistente de la empresa MEGALÁMPARAS que ayuda a consultar precios y productos.
Responde la pregunta del usuario basándote ÚNICAMENTE en la lista de productos que se muestra abajo.

Si no hay productos que coincidan, dilo claramente y sugiere que el usuario intente con otra descripción.
No inventes productos, códigos ni precios que no estén en la lista.

Productos encontrados:
{contexto}

Pregunta del usuario: {pregunta}

Respuesta:"""

    respuesta = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    return respuesta.message.content[0].text


# --- Prueba ---
if __name__ == "__main__":
    df = cargar_precios()

    pregunta = "¿Cuánto cuesta el producto APL-30066?"
    respuesta = responder_pregunta_excel(pregunta, df)

    print(f"Pregunta: {pregunta}\n")
    print(f"Respuesta:\n{respuesta}")