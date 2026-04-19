import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _infer_dim(model) -> Optional[int]:
    if hasattr(model, "n_features_in_"):
        return int(model.n_features_in_)
    if hasattr(model, "steps"):
        return _infer_dim(model.steps[-1][1])
    return None


class PriorityClassifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.model_path = base_dir / "data" / "models" / "priority_classifier.pkl"
        self.label_path = base_dir / "data" / "models" / "priority_labels.pkl"
        self.model = None
        self.labels: Optional[list] = None
        self._expected_dim: Optional[int] = None

    def load(self) -> bool:
        """Carga el modelo y las etiquetas desde disco."""
        try:
            if self.model_path.exists() and self.label_path.exists():
                self.model = joblib.load(self.model_path)
                self.labels = joblib.load(self.label_path)
                self._expected_dim = _infer_dim(self.model)
                logger.info(
                    "PriorityClassifier cargado — %d clases, dim=%s",
                    len(self.labels),
                    self._expected_dim or "desconocida",
                )
                return True
            logger.error("Modelo no encontrado en: %s", self.model_path)
            logger.error("Labels no encontrado en: %s", self.label_path)
            return False
        except Exception:
            logger.exception("Error cargando clasificador de prioridad")
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

    def predict(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Predice la prioridad dado un embedding. Retorna (prioridad, confianza)."""
        if not self.is_ready():
            return None, None
        try:
            emb = self._normalize(embedding)
            proba: np.ndarray = self.model.predict_proba(emb)[0]
            idx: int = int(proba.argmax())
            return self.labels[idx], float(proba[idx])
        except Exception:
            logger.exception("Error en predicción de prioridad")
            return None, None