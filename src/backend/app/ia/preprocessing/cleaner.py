import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Limpieza básica de texto para PQRs en español.
    - Normaliza caracteres unicode
    - Elimina caracteres especiales
    - Colapsa espacios múltiples
    - Convierte a minúsculas
    """
    # Normalizar unicode (ej. á -> á en forma NFC)
    text = unicodedata.normalize("NFC", text)

    # Minúsculas
    text = text.lower()

    # Eliminar URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Eliminar caracteres especiales excepto letras, números, espacios y puntuación básica
    text = re.sub(r"[^a-záéíóúüñ0-9\s.,;:!?¿¡]", " ", text)

    # Colapsar espacios múltiples
    text = re.sub(r"\s+", " ", text).strip()

    return text