from app.ia.preprocessing.cleaner import clean_text


def tokenize(text: str) -> list[str]:
    """
    Tokenización simple por espacios después de limpiar el texto.
    No se usa para embeddings (el modelo lo hace internamente),
    sino para el motor de reglas y análisis de keywords.
    """
    cleaned = clean_text(text)
    return cleaned.split()


def preprocess(text: str) -> str:
    """
    Pipeline completo de preprocesamiento.
    Devuelve texto limpio listo para embeddings o reglas.
    """
    return clean_text(text)