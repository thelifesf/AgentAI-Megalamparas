import os
from dotenv import load_dotenv
from pathlib import Path
import cohere
from buscar_excel import cargar_precios, buscar_producto, detectar_orden_precio

# --- Cargar API key ---
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
api_key = os.getenv("COHERE_API_KEY")
co = cohere.ClientV2(api_key)


# --- Convertir los resultados de pandas en texto simple para el prompt ---
def construir_contexto_productos(resultados, total_encontrados, esta_ordenado=False):
    if resultados.empty:
        return "No se encontraron productos que coincidan con la búsqueda."

    lineas = []
    for _, fila in resultados.iterrows():
        lineas.append(f"- Código: {fila['codigo']} | {fila['descripcion']} | Precio: ${fila['precio']:.2f}")

    contexto = "\n".join(lineas)

    if esta_ordenado:
        contexto += "\n\n(Nota: estos productos ya están ordenados por precio según lo solicitado por el usuario)"

    if total_encontrados > len(resultados):
        contexto += f"\n\n(Se encontraron {total_encontrados} productos en total, se muestran {len(resultados)})"

    return contexto


# --- Generar la respuesta final usando Cohere Command ---
def responder_pregunta_excel(pregunta, df):
    resultados, total = buscar_producto(pregunta, df)

    hubo_orden = detectar_orden_precio(pregunta.lower()) is not None
    contexto = construir_contexto_productos(resultados, total, esta_ordenado=hubo_orden)

    prompt = f"""Eres un asistente de la empresa MEGALÁMPARAS que ayuda a consultar precios y productos.
Responde la pregunta del usuario basándote ÚNICAMENTE en la lista de productos que se muestra abajo.

Reglas obligatorias:
1. Debes listar TODOS los productos de la sección "Productos encontrados", sin omitir ninguno, aunque sean muchos.
2. No resumas la lista ni muestres solo "algunos ejemplos" — muestra cada producto con su código, descripción y precio.
3. Si el texto indica que hay más productos de los que se muestran (ej: "se encontraron 19, se muestran 10"), 
   menciona ese número exacto al final, invitando al usuario a pedir más detalle o afinar la búsqueda.
4. No inventes productos, códigos ni precios que no estén en la lista.
5. Si no hay productos que coincidan, dilo claramente.
6. Si el contexto indica que los productos ya están ordenados por precio, preséntalos en ese mismo 
   orden con seguridad, sin disculparte ni decir que no puedes hacerlo — la búsqueda ya se hizo correctamente.

Productos encontrados:
{contexto}

Pregunta del usuario: {pregunta}

Respuesta:"""

    respuesta = co.chat(
        model="command-r-plus-08-2024",
        messages=[{"role": "user", "content": prompt}]
    )

    return respuesta.message.content[0].text

