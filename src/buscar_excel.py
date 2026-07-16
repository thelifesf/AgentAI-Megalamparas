import re
import pandas as pd
from leer_documento import leer_todos_los_documentos


# --- Cargar el Excel de precios una sola vez ---
def cargar_precios(carpeta_raiz="Politicas-Negocio"):
    _, tablas = leer_todos_los_documentos(carpeta_raiz)

    if not tablas:
        return None

    df = tablas[0]["contenido"]
    df.columns = ["codigo", "descripcion", "precio"]

    df = df.dropna(subset=["codigo", "descripcion"]).copy()
    df["codigo"] = df["codigo"].astype(str)
    df["descripcion"] = df["descripcion"].astype(str)

    return df


# --- Buscar productos por código exacto o por texto en la descripción ---
def buscar_producto(pregunta, df):
    pregunta_lower = pregunta.lower()

    # --- Detectar si el usuario quiere ver TODOS los resultados ---
    quiere_todos = any(palabra in pregunta_lower for palabra in
                        ["todos", "todas", "lista completa", "cuántos hay", "cuantos hay"])

    # 1. Buscar si la pregunta contiene un código exacto
    coincidencias_codigo = df[df["codigo"].str.lower().apply(lambda c: c in pregunta_lower)]
    if not coincidencias_codigo.empty:
        return coincidencias_codigo, len(coincidencias_codigo)

    # 2. Buscar por palabras clave en la descripción
    pregunta_limpia = re.sub(r"[^\wáéíóúñ ]", " ", pregunta_lower)

    palabras_vacias = {
        "tienen", "tiene", "hay", "cual", "cuales", "que", "para",
        "con", "los", "las", "del", "color", "producto", "productos",
        "todos", "todas", "completa", "lista", "cuántos", "cuantos",
        "muéstrame", "muestrame", "mostrar", "dame", "dime", "quiero",
        "busco", "buscar", "necesito", "puedes", "podrías", "podrias"
    }

    palabras = [p for p in pregunta_limpia.split() if len(p) > 3 and p not in palabras_vacias]

    if not palabras:
        return pd.DataFrame(), 0

    coincidencias = df[df["descripcion"].str.lower().apply(
        lambda desc: all(palabra in desc or palabra.rstrip("s") in desc for palabra in palabras)
    )]

    total_encontrados = len(coincidencias)

    # --- Límite dinámico según intención ---
    if quiere_todos:
        limite = 50  # tope de seguridad, incluso pidiendo "todos" (evita respuestas gigantes)
    else:
        limite = 10

    resultados_mostrados = coincidencias.head(limite)

    return resultados_mostrados, total_encontrados

# --- Prueba ---
if __name__ == "__main__":
    df = cargar_precios()
    print(f"Excel cargado: {len(df)} productos\n")

    pregunta = "muéstrame todos los apliques de pared color negro"
    resultado, total = buscar_producto(pregunta, df)

    print(f"Pregunta: {pregunta}")
    print(f"Se encontraron {total} productos en total (mostrando hasta 10):\n")
    print(resultado)