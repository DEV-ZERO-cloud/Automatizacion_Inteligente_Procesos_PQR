import os
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


class EmbeddingGenerator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(MODEL_NAME)
        return cls._instance

    def generate(self, texts: list[str]) -> np.ndarray:
        """Recibe una lista de textos, devuelve matriz de embeddings."""
        return self.model.encode(texts, show_progress_bar=False)

    def generate_one(self, text: str) -> np.ndarray:
        """Recibe un solo texto, devuelve vector 1D."""
        return self.model.encode([text])[0]