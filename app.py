import streamlit as st
import sys
import os
from datetime import datetime
import re

def escapar_asteriscos_sueltos(texto):
    # Escapa un "*" individual (no seguido/precedido de otro "*"),
    # para que Markdown no lo interprete como cursiva y se muestre tal cual.
    # Los "**" dobles (negritas reales) se dejan intactos.
    return re.sub(r'(?<!\*)\*(?!\*)', r'\\*', texto)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# --- Generar la base vectorial automáticamente si está vacía ---
RUTA_CHROMA = os.path.join(os.path.dirname(__file__), "chroma_db")

import chromadb
_cliente_check = chromadb.PersistentClient(path=RUTA_CHROMA)
_coleccion_check = _cliente_check.get_or_create_collection(
    name="megalamparas_documentos",
    metadata={"hnsw:space": "cosine"}
)

if _coleccion_check.count() == 0:
    with st.spinner("Preparando el agente por primera vez, esto puede tardar un par de minutos..."):
        from leer_documento import leer_todos_los_documentos
        from procesar_texto import crear_chunks
        from generar_embeddings import generar_embeddings
        from guardar_vectores import guardar_en_chroma

        _ruta_politicas = os.path.join(os.path.dirname(__file__), "Politicas-Negocio")
        textos, _tablas = leer_todos_los_documentos(_ruta_politicas)
        chunks = crear_chunks(textos)
        chunks_con_embeddings = generar_embeddings(chunks)
        guardar_en_chroma(chunks_con_embeddings)

from router import responder

st.set_page_config(
    page_title="Agente MEGALÁMPARAS",
    page_icon="💡",
    layout="wide"
)

st.info("🤖 Estás conversando con un agente de inteligencia artificial, no con una persona. Las respuestas se basan en los documentos internos de la empresa.")

# --- Ícono de lámpara en SVG, elegante y sin depender de archivos externos ---
ICONO_LAMPARA = """
<svg width="42" height="42" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="vertical-align: middle;">
  <path d="M12 2C8.5 2 6 4.5 6 8c0 2.5 1.5 4 2.5 5.2.6.7 1 1.3 1 2.3v1h5v-1c0-1 .4-1.6 1-2.3C16.5 12 18 10.5 18 8c0-3.5-2.5-6-6-6z"
        stroke="#d4af6a" stroke-width="1.3" fill="#3a3226"/>
  <line x1="9.5" y1="19" x2="14.5" y2="19" stroke="#d4af6a" stroke-width="1.3"/>
  <line x1="10" y1="21" x2="14" y2="21" stroke="#d4af6a" stroke-width="1.3"/>
  <line x1="12" y1="9" x2="12" y2="12" stroke="#f2e3c6" stroke-width="1"/>
</svg>
"""

# --- Estilo personalizado, inspirado en la identidad de Megalámparas ---
st.markdown("""
<style>
    .stApp {
        background-color: #14120f;
    }
    [data-testid="stSidebar"] {
        background-color: #1c1a15;
        border-right: 1px solid #3a3226;
        min-width: 260px !important;
        max-width: 260px !important;
    }
    h1 {
        color: #f2e3c6 !important;
        font-weight: 700 !important;
    }
    .subtitulo {
        color: #b8a888;
        font-size: 0.95rem;
        margin-top: -10px;
        margin-bottom: 25px;
    }
    [data-testid="stChatMessage"] {
        background-color: #201d17;
        border: 1px solid #34301fdd;
        border-radius: 10px;
    }
    .stChatInput textarea {
        background-color: #201d17 !important;
        color: #f2e3c6 !important;
    }
    .stChatInput textarea:focus {
        outline: none !important;
        box-shadow: 0 0 0 1px #3a3226 !important;
        border-color: #3a3226 !important;
    }
    [data-testid="stChatInput"] {
        background-color: #14120f !important;
    }
    [data-testid="stBottomBlockContainer"] {
        background-color: #14120f !important;
    }
    [data-testid="stChatInputContainer"] {
        background-color: #14120f !important;
    }
    footer {
        visibility: hidden;
    }
    div[data-testid="stMarkdownContainer"] p {
        color: #e8ddc7;
    }
    .badge-categoria {
        display: inline-block;
        background-color: #3a3226;
        color: #d4af6a;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        margin-bottom: 8px;
    }
    .footer-copyright {
        color: #6b6250;
        font-size: 0.75rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Barra lateral: información y preguntas guía ---
with st.sidebar:
    st.markdown(f"### {ICONO_LAMPARA} MEGALÁMPARAS", unsafe_allow_html=True)
    st.markdown("**Agente interno de consulta**")
    st.caption("Herramienta de uso exclusivo para el equipo de Megalámparas.")

    st.divider()

    st.markdown("**Ejemplos de preguntas**")
    st.caption("Haz clic para probar el agente")

    ejemplos = [
        "¿Cuál es la misión de la empresa?",
        "¿Cuánto cuesta el producto APL-30066?",
        "¿Tienen apliques de pared color negro?",
        "¿Cuáles son los valores de la empresa?",
        "¿Cómo es el proceso de contratación?",
        "Dame los 10 productos más baratos",
        "Productos entre 20 y 30 dólares",
    ]

    for ejemplo in ejemplos:
        if st.button(ejemplo, use_container_width=True):
            st.session_state.pregunta_sugerida = ejemplo

    st.divider()
    anio_actual = datetime.now().year
    st.markdown(
        f'<p class="footer-copyright">© {anio_actual} Megalámparas — Grupo AP&P.<br>Todos los derechos reservados.</p>',
        unsafe_allow_html=True
    )

# --- Encabezado principal ---
st.markdown(f"# {ICONO_LAMPARA} Agente Virtual MEGALÁMPARAS", unsafe_allow_html=True)
st.markdown('<p class="subtitulo">Consulta productos, precios y políticas internas de la empresa.</p>', unsafe_allow_html=True)

# --- Historial de conversación ---
if "historial" not in st.session_state:
    st.session_state.historial = []

for mensaje in st.session_state.historial:
    with st.chat_message(mensaje["rol"]):
        if mensaje["rol"] == "assistant" and "categoria" in mensaje:
            st.markdown(f'<span class="badge-categoria">{mensaje["categoria"]}</span>', unsafe_allow_html=True)
        st.write(mensaje["contenido"])

# --- Entrada de texto: por click en sidebar o escribiendo directo ---
pregunta_sugerida = st.session_state.pop("pregunta_sugerida", None)
pregunta = st.chat_input("Escribe tu pregunta aquí...")

if pregunta_sugerida:
    pregunta = pregunta_sugerida

if pregunta:
    st.session_state.historial.append({"rol": "user", "contenido": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Buscando información..."):
            respuesta, categoria = responder(pregunta)
        st.markdown(f'<span class="badge-categoria">{categoria}</span>', unsafe_allow_html=True)
        st.write(escapar_asteriscos_sueltos(respuesta))
        feedback = st.feedback("thumbs", key=f"feedback_{len(st.session_state.historial)}")
    st.session_state.historial.append({"rol": "assistant", "contenido": respuesta, "categoria": categoria})