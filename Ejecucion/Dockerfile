# syntax=docker/dockerfile:1
# Construir desde la RAIZ del repo:  docker build -f Ejecucion/Dockerfile -t reconocedor-billetes .
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1) Dependencias primero: aprovecha la cache de capas de Docker
COPY Ejecucion/requirements.txt .
RUN pip install -r requirements.txt

# 2) Codigo de la aplicacion
COPY Back ./Back
COPY Front ./Front

# Streamlit lee Front/.streamlit/config.toml (viene dentro de Front); se ejecuta desde Front
WORKDIR /app/Front

# 3) Usuario sin privilegios (no se ejecuta como root)
RUN useradd --create-home --uid 10001 appuser && chown -R appuser /app
USER 10001

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3).status == 200 else 1)"]

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
