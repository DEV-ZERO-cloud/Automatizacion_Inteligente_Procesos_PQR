import logging
import joblib
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


def _infer_dim(model) -> "int | None":
    if hasattr(model, "n_features_in_"):
        return int(model.n_features_in_)
    if hasattr(model, "steps"):
        return _infer_dim(model.steps[-1][1])
    return None


class TagsClassifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.model_path = base_dir / "data" / "models" / "tags_classifier.pkl"
        self.label_path = base_dir / "data" / "models" / "tags_labels.pkl"
        self.model = None
        self.labels: list | None = None
        self._expected_dim: int | None = None

    def load(self) -> bool:
        """Carga el modelo y las etiquetas desde disco."""
        try:
            if self.model_path.exists() and self.label_path.exists():
                self.model = joblib.load(self.model_path)
                self.labels = joblib.load(self.label_path)
                self._expected_dim = _infer_dim(self.model)
                logger.info(
                    "TagsClassifier cargado — %d etiquetas, dim=%s",
                    len(self.labels),
                    self._expected_dim or "desconocida",
                )
                return True
            logger.error("Modelo no encontrado en: %s", self.model_path)
            logger.error("Labels no encontrado en: %s", self.label_path)
            return False
        except Exception:
            logger.exception("Error cargando clasificador de tags")
            return False

    def is_ready(self) -> bool:
        return self.model is not None and self.labels is not None

    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        if not isinstance(embedding, np.ndarray):
            embedding = np.asarray(embedding, dtype=np.float32)
        if embedding.ndim == 3:
            embedding = embedding.reshape(embedding.shape[0], -1)
        elif embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        if self._expected_dim and embedding.shape[1] != self._expected_dim:
            logger.error(
                "Dimensión del embedding (%d) no coincide con la del modelo (%d). "
                "Verifica que MODEL_NAME en .env corresponde al modelo entrenado.",
                embedding.shape[1],
                self._expected_dim,
            )
        return embedding

    def predict(self, embedding: np.ndarray) -> list[str]:
        """Predice los tags dado un embedding."""
        if not self.is_ready():
            return []
        try:
            emb = self._normalize(embedding)
            predictions: np.ndarray = self.model.predict(emb)[0]
            # Usar compresión de lista con zip para evitar enumerate + indexación
            return [label for label, active in zip(self.labels, predictions) if active == 1]
        except Exception:
            logger.exception("Error en predicción de tags")
            return []