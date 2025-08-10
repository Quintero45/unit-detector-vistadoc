# Imagen base ligera
FROM python:3.11-slim

# Dependencias nativas para OpenCV (headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Ajustes Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Directorio de trabajo
WORKDIR /app

# Instala dependencias primero (mejor caché)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copia el código
COPY . .

# Crea carpetas de trabajo (por si el proceso arranca sin escribir antes)
RUN mkdir -p uploads outputs

# (Opcional) Exponer puerto informativo
EXPOSE 8000

# IMPORTANTE: Render inyecta $PORT.
# Cargamos la app Flask desde main:app y escuchamos en 0.0.0.0:$PORT
# -w 2 workers, gthread para I/O; ajusta si lo necesitas
CMD ["/bin/sh", "-c", "gunicorn -w 2 -k gthread -t 120 -b 0.0.0.0:$PORT main:app"]
