# Usa una imagen base oficial de Python
# Usa la imagen base de Python 3.12
FROM python:3.12

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de dependencias al contenedor
COPY requirements.txt .
# Copiar el código fuente
COPY . .
# Instala las dependencias usando pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia los archivos de la aplicación al contenedor
COPY app /app
# Copia los archivos de joblib al contenedor
COPY joblib /app/joblib
# Expone el puerto 8000 en el contenedor
EXPOSE 8000

# Comando para ejecutar la aplicación usando Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]





