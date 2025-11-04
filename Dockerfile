# --- Fase 1: La Base ---
# Usamos una imagen oficial de Python ligera.
# python:3.11-slim es una base excelente y moderna.
FROM python:3.11-slim

# --- Fase 2: Configuración del Entorno ---
# Establecemos el directorio de trabajo DENTRO del contenedor
# A partir de aquí, todos los comandos se ejecutan en /app
WORKDIR /app

# Copia SÓLO el archivo de requisitos primero.
# Esto aprovecha la caché de Docker: si no cambias las librerías,
# no se volverán a instalar cada vez, haciendo builds más rápidos.
COPY backend/requirements.txt .

# Instala las librerías de Python
# --no-cache-dir crea una imagen un poco más ligera
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
# --- Fase 4: Copiar tu Aplicación ---
# Ahora copia el resto de tu proyecto (tu código, la carpeta models)
# al directorio /app dentro del contenedor
# El primer '.' es tu PC, el segundo '.' es /app en el contenedor
COPY . .

# --- Fase 5: Exponer el Puerto ---
# Informa a Docker que tu app escuchará en el puerto 8000
# (Uvicorn/Gunicorn usan 8000 por defecto)
EXPOSE 8000

# --- Fase 6: Comando de Ejecución ---
# El comando que se ejecutará cuando el contenedor se inicie.
# Usamos Gunicorn como "gestor" de producción y Uvicorn como "trabajador".
# -w 4: Inicia 4 procesos "worker" (un buen punto de partida)
# -k uvicorn.workers.UvicornWorker: El tipo de trabajador
# main_completo:app: El archivo (main_completo.py) y el objeto (app)
# -b 0.0.0.0:8000: Escucha en todas las IPs en el puerto 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
