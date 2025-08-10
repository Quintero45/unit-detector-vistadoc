FROM python:3.11-slim

# Dependencias nativas para OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar deps primero para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar código
COPY . .

# Carpetas de trabajo
RUN mkdir -p uploads outputs

# (informativo) Render usa $PORT propio
EXPOSE 8000

# 🔑 OJO: nos movemos a la carpeta app/ antes de cargar main:app
CMD ["/bin/sh", "-c", "gunicorn -w 2 -k gthread -t 120 --chdir app -b 0.0.0.0:$PORT main:app"]
