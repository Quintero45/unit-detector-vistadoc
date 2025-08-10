FROM python:3.11-slim

# Libs necesarias para opencv-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar código
COPY . .

# Carpetas de trabajo (para tus endpoints /uploads y /outputs)
RUN mkdir -p uploads outputs

# Informativo (Render usa su propio $PORT)
EXPOSE 8000

# Iniciar Flask con gunicorn leyendo el puerto que inyecta Render
# Módulo: app.py  Objeto: app
CMD ["/bin/sh", "-c", "gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:$PORT app:app"]
