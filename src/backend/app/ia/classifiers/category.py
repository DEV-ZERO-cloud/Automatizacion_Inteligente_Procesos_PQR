import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def _infer_dim(model) -> Optional[int]:
    """
    Intenta leer la dimensión de entrada desde un modelo sklearn ya cargado.
    Funciona con LogisticRegression, SVC, RandomForest, etc.
    Retorna None si no puede determinarse.
    """
    # LogisticRegression, LinearSVC, SGDClassifier, etc.
    if hasattr(model, "n_features_in_"):
        return int(model.n_features_in_)
    # Pipeline de sklearn: revisar el último estimador
    if hasattr(model, "steps"):
        return _infer_dim(model.steps[-1][1])
    return None


class CategoryClassifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.model_path = base_dir / "data" / "models" / "category_classifier.pkl"
        self.label_path = base_dir / "data" / "models" / "category_labels.pkl"
        self.model = None
        self.labels: Optional[list] = None
        self._expected_dim: Optional[int] = None  # se infiere al cargar el modelo

    def load(self) -> bool:
        """Carga el modelo y las etiquetas desde disco."""
        try:
            if self.model_path.exists() and self.label_path.exists():
                self.model = joblib.load(self.model_path)
                self.labels = joblib.load(self.label_path)
                # Inferir dimensión esperada desde el modelo ya entrenado
                self._expected_dim = _infer_dim(self.model)
                logger.info(
                    "CategoryClassifier cargado — %d clases, dim=%s",
                    len(self.labels),
                    self._expected_dim or "desconocida",
                )
                return True
            logger.error("Modelo no encontrado en: %s", self.model_path)
            logger.error("Labels no encontrado en: %s", self.label_path)
            return False
        except Exception:
            logger.exception("Error cargando clasificador de categoría")
            return False

    def is_ready(self) -> bool:
        return self.model is not None and self.labels is not None

    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        """Convierte cualquier forma de embedding a (1, dim) y valida dimensión."""
        if not isinstance(embedding, np.ndarray):
            embedding = np.asarray(embedding, dtype=np.float32)
        if embedding.ndim == 3:
            embedding = embedding.reshape(embedding.shape[0], -1)
        elif embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        # ndim == 2 ya está bien
        if self._expected_dim and embedding.shape[1] != self._expected_dim:
            logger.error(
                "Dimensión del embedding (%d) no coincide con la del modelo (%d). "
                "Verifica que MODEL_NAME en .env corresponde al modelo entrenado.",
                embedding.shape[1],
                self._expected_dim,
            )
        return embedding

    def predict(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Predice la categoría dado un embedding. Retorna (categoría, confianza)."""
        if not self.is_ready():
            return None, None
        try:
            emb = self._normalize(embedding)
            proba: np.ndarray = self.model.predict_proba(emb)[0]
            idx: int = int(proba.argmax())
            return self.labels[idx], float(proba[idx])
        except Exception:
            logger.exception("Error en predicción de categoría")
            return None, None

    def save(self) -> None:
        """Guarda el modelo entrenado."""
        if not self.is_ready():
            logger.warning("No hay modelo para guardar")
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.labels, self.label_path)
        logger.info("Modelo guardado en: %s", self.model_path)

    def train(self, embeddings: np.ndarray, labels: list) -> None:
        """Entrena el clasificador con embeddings y etiquetas."""
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder

        encoder = LabelEncoder()
        y = encoder.fit_transform(labels)
        self.labels = list(encoder.classes_)
        self.model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
        self.model.fit(embeddings, y)
        logger.info("Modelo de categorías entrenado con %d clases", len(self.labels))