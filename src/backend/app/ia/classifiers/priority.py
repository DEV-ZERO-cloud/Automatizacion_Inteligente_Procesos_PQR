import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# Agrega esto al tope de priority.py, después de los imports
from app.ia.classifier.engine import RuleEngine

PRIORITY_RULE_TAGS = [
    "cuenta hackeada", "acceso no autorizado", "fraude", "cargo no reconocido",
    "phishing", "acción legal", "SIC",
    "pedido extraviado", "entrega fallida", "cobro duplicado", "reembolso",
    "falla técnica", "falla plataforma", "pago fallido",
    "escalamiento", "caso sin resolver", "producto defectuoso", "valor incorrecto",
]
_TAG_INDEX = {tag: i for i, tag in enumerate(PRIORITY_RULE_TAGS)}

def _build_rule_features(text: str) -> np.ndarray:
    result = RuleEngine().evaluate(text)
    features = np.zeros(len(PRIORITY_RULE_TAGS), dtype=np.float32)
    for tag in result.tags:
        if tag in _TAG_INDEX:
            features[_TAG_INDEX[tag]] = 1.0
    return features

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

    def predict(self, embedding: np.ndarray, text: str = "") -> Tuple[Optional[str], Optional[float]]:
        if not self.is_ready():
            return None, None
        try:
            emb = self._normalize(embedding)          # → (1, 384)
            if text:
                rule_feats = _build_rule_features(text).reshape(1, -1)  # → (1, 18)
                emb = np.concatenate([emb, rule_feats], axis=1)         # → (1, 402)
            proba = self.model.predict_proba(emb)[0]
            idx = int(proba.argmax())
            return self.labels[idx], float(proba[idx])
        except Exception:
            logger.exception("Error en predicción de prioridad")
            return None, None