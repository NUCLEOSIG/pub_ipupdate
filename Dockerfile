# Usa una imagen base oficial de Python.
# python:3.9-slim es una buena opción por ser ligera.
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor.
WORKDIR /app

# Copia el archivo de dependencias al directorio de trabajo.
COPY requirements.txt .

# Instala las dependencias definidas en requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script de Python al directorio de trabajo.
COPY update.py .
COPY urls.txt .
COPY ip.txt .

# El comando para ejecutar la aplicación cuando el contenedor se inicie.
CMD [ "python", "update.py" ]