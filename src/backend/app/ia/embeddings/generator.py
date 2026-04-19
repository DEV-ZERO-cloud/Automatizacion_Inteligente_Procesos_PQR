import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

# Tamaño de lote por defecto (ajustar según RAM/GPU disponible)
DEFAULT_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))


class EmbeddingGenerator:
    """Singleton que mantiene el modelo en memoria entre llamadas."""

    _instance: "EmbeddingGenerator | None" = None

    def __new__(cls) -> "EmbeddingGenerator":
        if cls._instance is None:
            instance = super().__new__(cls)
            logger.info("Cargando modelo de embeddings: %s", MODEL_NAME)
            instance._model = SentenceTransformer(MODEL_NAME)
            # Caché del vector de texto vacío para evitar recalcular
            instance._cache: dict[str, np.ndarray] = {}
            cls._instance = instance
        return cls._instance

    def generate(
        self,
        texts: list[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> np.ndarray:
        """
        Genera embeddings para una lista de textos.
        Usa batch_size para no saturar memoria en listas grandes.
        """
        return self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def generate_one(self, text: str, use_cache: bool = False) -> np.ndarray:
        """
        Genera embedding para un solo texto.
        Si use_cache=True, reutiliza resultados para el mismo texto (útil en demos/tests).
        """
        if use_cache:
            cached = self._cache.get(text)
            if cached is not None:
                return cached

        result: np.ndarray = self._model.encode(
            [text],
            show_progress_bar=False,
            convert_to_numpy=True,
        )[0]

        if use_cache:
            self._cache[text] = result

        return result

    def clear_cache(self) -> None:
        """Libera la caché de embeddings."""
        self._cache.clear()