import os
import re

# Ruta de la carpeta con las fotos
carpeta = "C:\DOWLOADED IMAGES\imagenes_ucjc"

# Expresión regular para los nombres válidos
# Debe tener dos palabras separadas por guion o guion bajo, y extensión jpg o png
patron = re.compile(r'^[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+[-_][A-Za-zÁÉÍÓÚÑÜáéíóúñü]+.*\.(jpg|png|jpeg|webp)$', re.IGNORECASE)

# Lista para guardar los archivos que no cumplen el formato
no_cumplen = []

# Recorremos todos los archivos de la carpeta
for archivo in os.listdir(carpeta):
    if os.path.isfile(os.path.join(carpeta, archivo)):
        # Condición 1: no cumple patrón OR Condición 2: empieza con "foto"
        if not patron.match(archivo) or archivo.lower().startswith("foto"):
            no_cumplen.append(archivo)

# Resultado
if no_cumplen:
    print("Archivos que NO cumplen el formato:")
    for nombre in no_cumplen:
        print(" -", nombre)
else:
    print("✅ Todos los archivos cumplen el formato correctamente.")
