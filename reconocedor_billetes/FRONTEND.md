# Documentación del Frontend — Reconocedor de billetes mexicanos

## 1. Objetivo

La interfaz web permite demostrar el funcionamiento del reconocedor de billetes sin utilizar directamente la terminal. El usuario puede subir una fotografía o tomar una fotografía desde la cámara del navegador.

La interfaz reutiliza el algoritmo implementado en `billetes.py`; no se creó un segundo clasificador para el frontend.

## 2. Tecnología utilizada

- **Python**: lenguaje principal.
- **Streamlit**: interfaz web y ejecución local.
- **OpenCV**: procesamiento de imágenes y reconocimiento.
- **NumPy**: manejo de matrices e imágenes.
- **Git/GitHub**: control de versiones y entrega del proyecto.

## 3. Flujo de la interfaz

1. El usuario abre la aplicación.
2. Selecciona **Subir fotografía** o **Usar cámara**.
3. Se recibe la imagen.
4. Se ejecuta la segmentación del billete.
5. Se normaliza la perspectiva a 600 × 280 px.
6. Se extraen características de color HSV y ORB.
7. Se comparan las características contra las plantillas disponibles.
8. Se muestra la denominación, el nivel de confianza y los puntajes.
9. Se permite revisar la imagen rectificada y una explicación del pipeline.

## 4. Componentes de la UI

### Encabezado

Muestra el nombre del sistema y el contexto académico del proyecto.

### Barra lateral

Contiene el selector de fuente de imagen y una descripción breve del pipeline.

### Entrada de imagen

- **Subir fotografía**: acepta JPG, JPEG, PNG, BMP y WEBP.
- **Usar cámara**: utiliza la cámara disponible en el navegador mediante `st.camera_input`.

### Resultado

Muestra:

- imagen original con anotación;
- denominación reconocida;
- confianza del resultado;
- estado de segmentación;
- gráfico de puntajes por denominación.

### Imagen rectificada

Permite visualizar el recorte que recibe el clasificador después de la corrección de perspectiva.

### Explicación del algoritmo

Incluye una explicación breve de segmentación, color, ORB, RANSAC y ponderación del clasificador.

## 5. UX (Experiencia del usuario)

Se busca que la prueba requiera pocos pasos y que el resultado sea visible inmediatamente.

Recomendaciones para obtener mejores resultados:

- usar buena iluminación;
- mostrar el billete completo;
- evitar objetos que oculten el billete;
- utilizar un fondo relativamente uniforme;
- mantener la cámara enfocada.

La interfaz comunica explícitamente cuando no existen plantillas o cuando la confianza es insuficiente.

## 6. Limitaciones actuales

El frontend depende de las plantillas existentes en `plantillas/`. Por lo tanto, si el repositorio contiene únicamente plantillas de algunas denominaciones, la aplicación solo podrá comparar contra esas denominaciones.

Las imágenes sintéticas de `generar_sinteticos.py` sirven para verificar el pipeline, pero no deben presentarse como medición de exactitud con billetes reales.

## 7. Ejecución local

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Después, Streamlit mostrará una dirección local en el navegador.

## 8. Estructura relevante

```text
reconocedor_billetes/
├── app.py                    # Frontend web
├── billetes.py               # Algoritmo de reconocimiento
├── generar_sinteticos.py     # Datos sintéticos para pruebas
├── requirements.txt           # Dependencias
├── README.md                  # Documentación general
├── FRONTEND.md                # Documentación de interfaz
└── plantillas/
    ├── 20/
    ├── 50/
    ├── 100/
    ├── 200/
    ├── 500/
    └── 1000/
```

## 9. Relación con la plantilla de documentación académica

La plantilla proporcionada solicita apartados de UI, herramientas, repositorio, estado del arte, desarrollo de software/App, capturas beta y UX.

Para esta entrega, `FRONTEND.md` cubre principalmente **UI, herramientas, desarrollo del software/app y UX**. Las capturas beta deberán realizarse después de ejecutar la aplicación para mostrar el funcionamiento real.
