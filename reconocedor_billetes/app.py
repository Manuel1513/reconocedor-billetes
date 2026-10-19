"""Interfaz web del reconocedor de billetes mexicanos (Streamlit + OpenCV).

Reutiliza el algoritmo de ``billetes.py``: segmenta el billete, lo clasifica y
muestra el resultado, los puntajes y la imagen rectificada.
"""
from pathlib import Path

import cv2
import numpy as np
import streamlit as st

import billetes

BASE_DIR = Path(__file__).resolve().parent
EJEMPLOS = sorted(p for p in (BASE_DIR / "ejemplos").glob("*")
                  if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
EQUIPO = ["Integrante 1", "Integrante 2", "Integrante 3"]   # <- escribe aquí los nombres del equipo
GRUPO = ""                                                   # <- y el grupo

st.set_page_config(page_title="Reconocedor de billetes mexicanos", page_icon="💵", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    html, body, [class*="st-"], .stMarkdown {font-family: 'Poppins', sans-serif;}
    .block-container {padding-top: 1.4rem; max-width: 1200px;}
    @keyframes flota {0%,100% {transform: translateY(0) rotate(-6deg);} 50% {transform: translateY(-10px) rotate(6deg);}}
    @keyframes brilla {0% {background-position: 0% 50%;} 100% {background-position: 200% 50%;}}
    .hero {position: relative; overflow: hidden; color: #fff; border-radius: 24px; padding: 2.4rem 2.6rem;
           background: linear-gradient(120deg, #2F3E14, #4F6228, #6B7F3A, #A3BF4A, #4F6228);
           background-size: 250% 100%; animation: brilla 9s linear infinite; box-shadow: 0 12px 34px rgba(79,98,40,.35);}
    .hero h1 {color: #fff; font-weight: 800; font-size: 2.7rem; line-height: 1.1; margin: 0; padding: 0;}
    .hero p {font-size: 1.1rem; opacity: .93; margin: .7rem 0 0 0; max-width: 680px;}
    .hero .bill {position: absolute; right: 2.5rem; top: 1.2rem; font-size: 5.5rem; animation: flota 4s ease-in-out infinite;}
    .chip {display: inline-block; background: rgba(255,255,255,.2); border: 1px solid rgba(255,255,255,.35);
           border-radius: 999px; padding: .2rem .9rem; margin: 1rem .45rem 0 0; font-size: .85rem;}
    .pill {display: inline-block; border-radius: 12px; padding: .5rem 1rem; margin: .3rem .4rem .3rem 0;
           font-weight: 800; font-size: 1.05rem;}
    .pill.on {background: #6B7F3A; color: #fff; box-shadow: 0 4px 12px rgba(107,127,58,.4);}
    .pill.off {background: #EEF3DC; color: #9AA87A; text-decoration: line-through;}
    .card {background: #fff; border: 1px solid #DDE6C0; border-radius: 18px; padding: 1.2rem 1.3rem; height: 100%;
           box-shadow: 0 4px 16px rgba(79,98,40,.08); transition: transform .2s, box-shadow .2s;}
    .card:hover {transform: translateY(-4px); box-shadow: 0 10px 24px rgba(79,98,40,.18);}
    .card .ico {font-size: 2rem;} .card h4 {margin: .4rem 0 .3rem 0; color: #4F6228;}
    .card p {margin: 0; font-size: .93rem; color: #3b4a22;}
    .res {border-radius: 20px; padding: 1.4rem 1.6rem; color: #fff; margin-bottom: .6rem;}
    .res.ok {background: linear-gradient(135deg, #4F6228, #7C9A2E); box-shadow: 0 10px 26px rgba(79,98,40,.35);}
    .res.no {background: linear-gradient(135deg, #B26A00, #E39A1B); box-shadow: 0 10px 26px rgba(178,106,0,.3);}
    .res .sub {font-size: .95rem; opacity: .9;} .res .big {font-size: 3rem; font-weight: 800; line-height: 1.1;}
    .res .conf {font-size: 1.05rem; margin-top: .2rem;}
    [data-testid="stMetric"] {background: #EEF3DC; border-radius: 14px; padding: .8rem 1rem;}
    .stTabs [data-baseweb="tab"] {font-weight: 600; font-size: 1rem;}
    .pie {text-align: center; color: #6B7F3A; font-size: .85rem; margin-top: 2rem;}
    </style>
    <div class="hero">
      <div class="bill">💵</div>
      <h1>Reconocedor de<br>billetes mexicanos</h1>
      <p>Sube una foto o usa tu cámara y descubre al instante la denominación del billete,
         con su nivel de confianza y el análisis completo.</p>
      <span class="chip">Visión por computadora</span><span class="chip">OpenCV</span>
      <span class="chip">Histograma HSV</span><span class="chip">ORB + RANSAC</span>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def obtener_plantillas():
    """Carga las plantillas una sola vez y las conserva en memoria."""
    return billetes.cargar_plantillas()


def leer_imagen(archivo):
    datos = np.frombuffer(archivo.getvalue(), dtype=np.uint8)
    return cv2.imdecode(datos, cv2.IMREAD_COLOR)


def bgr_a_rgb(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def mostrar_imagen(img, **kwargs):
    """st.image compatible con versiones nuevas (width) y anteriores (use_container_width)."""
    try:
        st.image(img, width="stretch", **kwargs)
    except TypeError:
        st.image(img, use_container_width=True, **kwargs)


plantillas = obtener_plantillas()
activas = sorted({p["den"] for p in plantillas}) if plantillas else []

st.write("")
tab_probar, tab_como, tab_acerca = st.tabs(["🔍 Probar", "⚙️ Cómo funciona", "ℹ️ Acerca del proyecto"])

# ------------------------------------------------------------------ PROBAR
with tab_probar:
    pills = "".join('<span class="pill %s">$%d</span>' % ("on" if d in activas else "off", d)
                    for d in billetes.DENOMINACIONES)
    st.markdown("**Denominaciones disponibles:** " + pills, unsafe_allow_html=True)

    if not plantillas:
        st.error("No hay plantillas disponibles. Agrega imágenes en plantillas/20, plantillas/50, etc.")
        st.stop()

    opciones = ["📁 Subir fotografía", "📷 Usar cámara"] + (["🖼️ Imagen de ejemplo"] if EJEMPLOS else [])
    fuente = st.radio("¿Cómo quieres probarlo?", opciones, horizontal=True)

    img = None
    if fuente.startswith("📁"):
        archivo = st.file_uploader("Selecciona la fotografía de un billete",
                                   type=["jpg", "jpeg", "png", "bmp", "webp"])
        if archivo is not None:
            img = leer_imagen(archivo)
    elif fuente.startswith("📷"):
        archivo = st.camera_input("Toma una fotografía del billete")
        if archivo is not None:
            img = leer_imagen(archivo)
    else:
        nombre = st.selectbox("Elige un ejemplo", [p.name for p in EJEMPLOS])
        img = cv2.imread(str(BASE_DIR / "ejemplos" / nombre))

    if img is None:
        st.markdown(
            '<div class="card"><div class="ico">💡</div><h4>Consejos para un buen resultado</h4>'
            "<p>Usa buena luz, muestra el billete completo, colócalo sobre un fondo liso "
            "y mantén la cámara enfocada.</p></div>", unsafe_allow_html=True)
    else:
        with st.spinner("Analizando billete..."):
            recorte, caja, valido = billetes.segmentar(img)
            denominacion, confianza, detalle = billetes.clasificar(recorte, plantillas)

        anotada = billetes.anotar(img, caja if valido else None, billetes.etiqueta(denominacion, confianza),
                                  (0, 200, 0) if denominacion is not None else (0, 0, 255))
        izq, der = st.columns([1.1, 1])
        with izq:
            st.subheader("Imagen analizada")
            mostrar_imagen(bgr_a_rgb(anotada))
        with der:
            if denominacion is not None:
                st.markdown('<div class="res ok"><div class="sub">✅ Billete identificado</div>'
                            '<div class="big">$%d MXN</div><div class="conf">Confianza %.1f%%</div></div>'
                            % (denominacion, confianza * 100), unsafe_allow_html=True)
            else:
                st.markdown('<div class="res no"><div class="sub">⚠️ No se pudo identificar con suficiente confianza</div>'
                            '<div class="big">No reconocido</div><div class="conf">Mejor puntaje %.1f%%</div></div>'
                            % (confianza * 100), unsafe_allow_html=True)
            st.progress(float(min(max(confianza, 0.0), 1.0)))
            c1, c2 = st.columns(2)
            c1.metric("Segmentación", "Detectado" if valido else "Imagen completa")
            c2.metric("Umbral de aceptación", "%d%%" % round(billetes.UMBRAL_ACEPTACION * 100))
            st.markdown("**Puntaje por denominación**")
            st.bar_chart({"$%d" % d: round(s, 3) for d, s in sorted(detalle.items())}, y_label="Puntaje")
        with st.expander("Ver imagen rectificada (600 × 280 px)"):
            mostrar_imagen(bgr_a_rgb(recorte), caption="Recorte normalizado que recibe el clasificador")

# ------------------------------------------------------------ COMO FUNCIONA
with tab_como:
    st.subheader("Del fotograma a la denominación en 5 pasos")
    pasos = [("✂️", "1. Segmentación", "Detecta los bordes y localiza el contorno principal del billete."),
             ("📐", "2. Perspectiva", "Endereza el billete y lo normaliza a 600 × 280 píxeles."),
             ("🎨", "3. Color", "Calcula un histograma HSV y lo compara con cada plantilla."),
             ("🔎", "4. Detalles", "Busca puntos ORB y valida las coincidencias con RANSAC."),
             ("🏆", "5. Decisión", "Combina 35 % color y 65 % ORB. Bajo 0.35 no lo acepta.")]
    for col, (ico, titulo, texto) in zip(st.columns(5), pasos):
        col.markdown('<div class="card"><div class="ico">%s</div><h4>%s</h4><p>%s</p></div>' % (ico, titulo, texto),
                     unsafe_allow_html=True)
    st.write("")
    st.info("Si el parecido con todas las plantillas es bajo, la aplicación responde *No reconocido* "
            "en lugar de adivinar.")

# ------------------------------------------------------------------- ACERCA
with tab_acerca:
    izq, der = st.columns(2)
    with izq:
        st.subheader("Proyecto")
        st.markdown("Aplicación de visión por computadora que identifica billetes mexicanos usando **Python, OpenCV "
                    "y Streamlit**.\n\n"
                    "**Universidad Autónoma del Estado de México**  \nCentro Universitario UAEM Nezahualcóyotl  \n"
                    "Ingeniería en Sistemas Inteligentes · Semestre noveno%s" % (" · Grupo %s" % GRUPO if GRUPO else ""))
    with der:
        st.subheader("Equipo")
        st.markdown("\n".join("- %s" % n for n in EQUIPO) + "\n\n**Profesor:** Víctor Antonio Flores Lezama")
    st.subheader("Limitaciones")
    st.markdown("- Solo reconoce las denominaciones con plantilla registrada (activas arriba).\n"
                "- Funciona mejor con buena luz y fondo liso.\n"
                "- No se ha medido la exactitud con un conjunto amplio de fotografías reales.")

st.markdown('<div class="pie">Hecho con OpenCV y Streamlit · UAEM CU Nezahualcóyotl</div>', unsafe_allow_html=True)
