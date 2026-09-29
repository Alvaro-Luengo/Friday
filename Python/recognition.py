from deepface import DeepFace
import os
import pickle

IMAGES_DIR = r"C:\DOWLOADED IMAGES\imagenes_ucjc"
SEARCH_DIR = r"C:\DOWLOADED IMAGES\busqueda"

ENCODINGS_FILE = "reference_embeddings.pkl"

# Crear embeddings precomputados
if os.path.exists(ENCODINGS_FILE):
    print("Cargando embeddings precomputados...")
    with open(ENCODINGS_FILE, "rb") as f:
        reference_embeddings = pickle.load(f)
else:
    print("Generando embeddings de las imágenes de referencia...")
    reference_embeddings = []
    for filename in os.listdir(IMAGES_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            path = os.path.join(IMAGES_DIR, filename)
            try:
                embedding = DeepFace.represent(img_path=path, model_name="VGG-Face", enforce_detection=False)[0]["embedding"]
                reference_embeddings.append((filename, embedding))
            except Exception as e:
                print(f"Error procesando {filename}: {e}")
    # Guardar para uso futuro
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(reference_embeddings, f)

print(f"Total embeddings cargados: {len(reference_embeddings)}")

# Comparar los embdings
from scipy.spatial.distance import cosine

def find_matches(search_embedding, reference_embeddings, top_n=5):
    results = []
    for filename, ref_embedding in reference_embeddings:
        distance = cosine(search_embedding, ref_embedding)
        results.append((filename, distance))
    # Ordenar por menor distancia (más parecido)
    results.sort(key=lambda x: x[1])
    return results[:top_n]

# Procesar imágenes de búsqueda
for search_file in os.listdir(SEARCH_DIR):
    if search_file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        search_path = os.path.join(SEARCH_DIR, search_file)
        print(f"\nBuscando coincidencias para: {search_file}")
        try:
            search_embedding = DeepFace.represent(img_path=search_path, model_name="VGG-Face", enforce_detection=False)[0]["embedding"]
            matches = find_matches(search_embedding, reference_embeddings)
            if matches:
                print("Coincidencias encontradas:")
                for filename, distance in matches:
                    print(f"{filename} (distancia: {distance:.4f})")
            else:
                print("No se encontraron coincidencias.")
        except Exception as e:
            print(f"Error procesando {search_file}: {e}")
