# Reconocedor de billetes mexicanos

Sistema de reconocimiento de billetes mexicanos mediante Python + OpenCV. El proyecto incluye una interfaz web en Streamlit para demostrar el funcionamiento de forma visual.

## Funcionalidades

- Registro de plantillas mediante cámara o fotografías.
- Clasificación de fotografías.
- Reconocimiento en cámara mediante OpenCV.
- Evaluación con fotografías etiquetadas.
- Interfaz web para subir una imagen o tomar una captura.
- Visualización de confianza, puntajes e imagen rectificada.

## Arquitectura

```text
Usuario
  │
  ▼
Streamlit (app.py)
  │
  ▼
billetes.py
  ├── Segmentación
  ├── Corrección de perspectiva
  ├── Histograma HSV
  ├── ORB
  ├── RANSAC
  └── Clasificación
  │
  ▼
plantillas/<denominación>/
```

## Instalación

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecutar como aplicación (un clic)

Windows: doble clic en `iniciar.bat`. macOS/Linux: `./iniciar.sh`. Crea el entorno, instala dependencias y abre la app en el navegador.

## Ejecutar la página web

```bash
streamlit run app.py
```

La aplicación se abrirá en el navegador y permitirá subir una fotografía o utilizar la cámara.

## Publicar la página web (Streamlit Community Cloud)

1. Sube el repositorio a GitHub (ver sección siguiente).
2. Entra a <https://share.streamlit.io> e inicia sesión con GitHub.
3. **Create app** → *Deploy a public app from GitHub*.
4. Elige el repositorio, la rama `main` y el archivo principal `app.py`.
5. En *Advanced settings* selecciona Python 3.11 o 3.12 y pulsa **Deploy**.

Streamlit instala automáticamente `requirements.txt` (se usa `opencv-python-headless`, necesario en servidores sin pantalla). La URL pública `https://<nombre>.streamlit.app` es la que se entrega para la revisión del front. La cámara del navegador solo funciona sobre HTTPS, que ya viene incluido.

## Ejecutar por terminal

Registrar plantillas:

```bash
python billetes.py registrar --den 100
```

Clasificar una fotografía:

```bash
python billetes.py imagen foto.jpg --salida resultado.jpg
```

Reconocimiento en vivo:

```bash
python billetes.py camara
```

Evaluación:

```bash
python billetes.py evaluar pruebas --csv detalle.csv
```

## Cómo funciona

1. **Segmentación:** Canny + contorno principal + rectángulo rotado + corrección de perspectiva.
2. **Normalización:** el billete se transforma a 600 × 280 px.
3. **Características:** histograma HSV + puntos ORB.
4. **Validación:** RANSAC calcula coincidencias geométricamente consistentes.
5. **Clasificación:** `0.35 × color + 0.65 × ORB`.
6. **Umbral:** resultados menores a `0.35` se consideran no reconocidos.
7. **Cámara:** se utiliza votación de los últimos 7 cuadros.

## Documentación del frontend

Consulta `FRONTEND.md` para la documentación de UI, UX, flujo, componentes, limitaciones y relación con la plantilla académica.

## Git y GitHub

Desde la carpeta del proyecto:

```bash
git init
git add .
git commit -m "feat: agregar interfaz web del reconocedor de billetes"
git branch -M main
git remote add origin URL_DE_TU_REPOSITORIO
git push -u origin main
```

> Sustituye `URL_DE_TU_REPOSITORIO` por la URL real del repositorio de tu equipo.

## Imágenes de ejemplo

La carpeta `ejemplos/` contiene fotografías para probar la interfaz.

## Nota sobre las plantillas

El algoritmo solo puede reconocer correctamente las denominaciones para las que existan plantillas disponibles. Actualmente el repositorio incluye plantillas de **$20, $50 y $1000**; faltan $100, $200 y $500. Antes de la demostración conviene registrarlas con `python billetes.py registrar --den 100 --imagen foto.jpg` (y análogamente para 200 y 500).

Las imágenes generadas por `generar_sinteticos.py` son únicamente para comprobar que el pipeline funciona y no sustituyen una evaluación con fotografías reales.
