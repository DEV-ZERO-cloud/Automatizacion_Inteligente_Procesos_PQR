import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print(f"Descargando modelo: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

# Prueba rápida con texto en español
textos = [
    "Quiero reclamar un cobro incorrecto en mi factura",
    "No puedo acceder a mi cuenta desde hace tres días",
    "Solicito información sobre los planes disponibles",
]

embeddings = model.encode(textos)
print(f"Modelo cargado correctamente")
print(f"Dimensiones del embedding: {embeddings.shape}")
# Esperado: (3, 384)