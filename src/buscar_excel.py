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
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")
    df = df.dropna(subset=["precio"]).copy()

    return df


# --- Detectar si la pregunta pide ordenar por precio (más barato/caro) ---
def detectar_orden_precio(pregunta_lower):
    # \w* al final captura variaciones de género/número: barato, barata, baratos, baratas
    if re.search(r"m[aá]s\s+(barat|econ[oó]mic)\w*", pregunta_lower) or "menor precio" in pregunta_lower:
        return "asc"
    if re.search(r"m[aá]s\s+(car|costos)\w*", pregunta_lower) or "mayor precio" in pregunta_lower:
        return "desc"
    return None


# --- Detectar cuántos resultados pide el usuario (ej: "las 20 más baratas") ---
def detectar_cantidad(pregunta_lower):
    match = re.search(r"\b(\d{1,3})\b", pregunta_lower)
    if match:
        cantidad = int(match.group(1))
        if 1 <= cantidad <= 100:  # límite razonable de seguridad
            return cantidad
    return None


# --- Detectar filtro de precio máximo/mínimo (ej: "menos de 15 dólares") ---
def detectar_rango_precio(pregunta_lower):
    precio_max = None
    precio_min = None

    match_max = re.search(r"(?:menos de|hasta|máximo|maximo|no más de|no mas de)\s*\$?\s*(\d+(?:\.\d+)?)", pregunta_lower)
    if match_max:
        precio_max = float(match_max.group(1))

    match_min = re.search(r"(?:más de|mas de|mínimo|minimo|desde)\s*\$?\s*(\d+(?:\.\d+)?)", pregunta_lower)
    if match_min:
        precio_min = float(match_min.group(1))

    # Patrón "entre X y Y"
    match_entre = re.search(r"entre\s*\$?\s*(\d+(?:\.\d+)?)\s*y\s*\$?\s*(\d+(?:\.\d+)?)", pregunta_lower)
    if match_entre:
        precio_min = float(match_entre.group(1))
        precio_max = float(match_entre.group(2))

    return precio_min, precio_max


# --- Buscar productos por código exacto o por texto en la descripción ---
def buscar_producto(pregunta, df):
    pregunta_lower = pregunta.lower()

    # 1. Código exacto tiene prioridad sobre todo lo demás
    coincidencias_codigo = df[df["codigo"].str.lower().apply(lambda c: c in pregunta_lower)]
    if not coincidencias_codigo.empty:
        return coincidencias_codigo, len(coincidencias_codigo)

    resultado = df.copy()

    # 2. Filtro por texto en la descripción (si hay palabras clave relevantes)
    pregunta_limpia = re.sub(r"[^\wáéíóúñ ]", " ", pregunta_lower)

    palabras_vacias = {
        "tienen", "tiene", "hay", "cual", "cuales", "que", "para",
        "con", "los", "las", "del", "color", "producto", "productos",
        "todos", "todas", "completa", "lista", "cuántos", "cuantos",
        "muéstrame", "muestrame", "mostrar", "dame", "dime", "quiero",
        "busco", "buscar", "necesito", "puedes", "podrías", "podrias",
        "cuanto", "cuánto", "cuesta", "vale", "porfa", "porfavor",
        "favor", "gracias", "oye", "amigo", "mas", "más", "barato",
        "baratos", "barata", "baratas", "caro", "caros", "cara", "caras",
        "economico", "económico", "economicos", "económicos", "menos",
        "hasta", "maximo", "máximo", "minimo", "mínimo", "entre",
        "algo", "regalar", "regalo", "regalos",
        "costoso", "costosos",
        "dolares", "dólares", "venden", "que", "hay", "en", "stock", "el"
    }

    # Términos genéricos de iluminación: no acotan a un producto específico,
    # así que si son la única "palabra de producto" en la pregunta, no filtramos
    # por texto y se interpreta como "todo el catálogo"
    terminos_genericos = {"lampara", "lamparas", "iluminacion", "iluminación", "luces", "luz"}

    palabras = [p for p in pregunta_limpia.split() if len(p) > 3 and p not in palabras_vacias]
    palabras_especificas = [p for p in palabras if p.rstrip("s") not in terminos_genericos]

    if palabras_especificas:
        resultado = resultado[resultado["descripcion"].str.lower().apply(
            lambda desc: all(palabra in desc or palabra.rstrip("s") in desc for palabra in palabras_especificas)
        )]
    # Si palabras_especificas está vacío (solo había términos genéricos o ninguna palabra
    # de producto), no se filtra por texto: se conserva todo el catálogo y solo se aplican
    # los filtros de precio/orden más abajo

    # 3. Filtro por rango de precio, si aplica
    precio_min, precio_max = detectar_rango_precio(pregunta_lower)
    if precio_min is not None:
        resultado = resultado[resultado["precio"] >= precio_min]
    if precio_max is not None:
        resultado = resultado[resultado["precio"] <= precio_max]

    # 4. Ordenar por precio, si lo pidieron
    orden = detectar_orden_precio(pregunta_lower)

    # Si se filtró por precio máximo pero no se pidió orden explícito,
    # ordenamos por precio ascendente de todas formas (tiene más sentido para el usuario)
    if precio_max is not None and orden is None:
        orden = "asc"

    if orden == "asc":
        resultado = resultado.sort_values("precio", ascending=True)
    elif orden == "desc":
        resultado = resultado.sort_values("precio", ascending=False)

    total_encontrados = len(resultado)

    # 5. Límite de resultados a mostrar
    cantidad_pedida = detectar_cantidad(pregunta_lower)
    quiere_todos = any(p in pregunta_lower for p in ["todos", "todas", "lista completa"])

    if cantidad_pedida:
        limite = cantidad_pedida
    elif quiere_todos:
        limite = 50
    elif orden:
        limite = 10  # si pide "el más caro" sin número, mostramos top 10 por defecto
    else:
        limite = 10

    resultados_mostrados = resultado.head(limite)

    return resultados_mostrados, total_encontrados


# --- Prueba ---
if __name__ == "__main__":
    df = cargar_precios()
    print(f"Excel cargado: {len(df)} productos\n")

    casos_prueba = [
        "dame las 20 lamparas mas baratas que hay en stock",
        "cual es el producto mas barato que hay en stock",
        "cual es el aplique mas caro que venden",
        "tienen algo economico para regalar menos de 15 dolares",
        "productos entre 20 y 30 dolares",
    ]

    for pregunta in casos_prueba:
        resultado, total = buscar_producto(pregunta, df)
        print(f"Pregunta: {pregunta}")
        print(f"Total encontrados: {total} (mostrando {len(resultado)})")
        print(resultado[["codigo", "descripcion", "precio"]].to_string(index=False))
        print("="*70)
        print()