"""
classifier.py

Dos clasificadores ML independientes entrenados sobre embeddings del transformer
paraphrase-multilingual-MiniLM-L12-v2 (congelado).

  - CategoryClassifier  → predice la categoría temática de la PQR
  - PriorityClassifier  → predice la prioridad (Crítica / Alta / Media / Baja)

Cada uno guarda/carga su propio .pkl en data/models/.
El transformer NUNCA se modifica — solo se usa para generar embeddings como features.

Flujo de aprendizaje:
  1. CSV con PQR etiquetadas → trainer.py genera embeddings → entrena LR → guarda .pkl
  2. Al arrancar el servicio, classifier.py carga los .pkl
  3. Para nuevas clasificaciones: generate_one(texto) → predict()
"""

import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent.parent.parent / "data" / "models"


def _infer_dim(model) -> Optional[int]:
    if hasattr(model, "n_features_in_"):
        return int(model.n_features_in_)
    if hasattr(model, "steps"):
        return _infer_dim(model.steps[-1][1])
    return None


# ── Base compartida ────────────────────────────────────────────────────────────

class _BaseClassifier:
    """
    Clase base con lógica común de carga, normalización y predicción.
    No instanciar directamente — usar CategoryClassifier o PriorityClassifier.
    """

    model_file:  str = ""   # sobreescribir en subclase
    labels_file: str = ""   # sobreescribir en subclase
    name:        str = ""   # para logs

    def __init__(self):
        self.model_path  = MODELS_DIR / self.model_file
        self.labels_path = MODELS_DIR / self.labels_file
        self.model       = None
        self.labels: Optional[list[str]] = None
        self._expected_dim: Optional[int] = None

    # ── Carga ──────────────────────────────────────────────────────────────────

    def load(self) -> bool:
        """Carga modelo y etiquetas desde disco. Retorna True si exitoso."""
        try:
            if self.model_path.exists() and self.labels_path.exists():
                self.model  = joblib.load(self.model_path)
                self.labels = joblib.load(self.labels_path)
                self._expected_dim = _infer_dim(self.model)
                logger.info(
                    "[%s] Cargado — %d clases, dim=%s",
                    self.name, len(self.labels), self._expected_dim or "?"
                )
                return True
            logger.warning("[%s] Modelo no encontrado en %s. Ejecuta trainer.py primero.", self.name, self.model_path)
            return False
        except Exception:
            logger.exception("[%s] Error al cargar modelo.", self.name)
            return False

    def is_ready(self) -> bool:
        return self.model is not None and self.labels is not None

    # ── Normalización ──────────────────────────────────────────────────────────

    def _normalize(self, embedding: np.ndarray) -> np.ndarray:
        """Convierte cualquier forma de embedding a (1, dim)."""
        if not isinstance(embedding, np.ndarray):
            embedding = np.asarray(embedding, dtype=np.float32)
        embedding = embedding.reshape(1, -1) if embedding.ndim == 1 else embedding.reshape(embedding.shape[0], -1)
        if self._expected_dim and embedding.shape[1] != self._expected_dim:
            logger.error(
                "[%s] Dimensión del embedding (%d) ≠ dimensión del modelo (%d). "
                "Verifica que MODEL_NAME en .env coincide con el modelo usado al entrenar.",
                self.name, embedding.shape[1], self._expected_dim,
            )
        return embedding

    # ── Predicción ─────────────────────────────────────────────────────────────

    def predict(self, embedding: np.ndarray) -> tuple[Optional[str], Optional[float]]:
        """
        Predice la clase dado un embedding.

        Args:
            embedding: np.ndarray de cualquier forma — se normaliza internamente.

        Returns:
            (label, confianza) o (None, None) si el modelo no está listo.
        """
        if not self.is_ready():
            return None, None
        try:
            emb   = self._normalize(embedding)
            proba = self.model.predict_proba(emb)[0]
            idx   = int(proba.argmax())
            return self.labels[idx], float(proba[idx])
        except Exception:
            logger.exception("[%s] Error en predicción.", self.name)
            return None, None

    # ── Guardado ───────────────────────────────────────────────────────────────

    def save(self) -> None:
        """Guarda modelo y etiquetas en disco."""
        if not self.is_ready():
            logger.warning("[%s] No hay modelo para guardar.", self.name)
            return
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model,  self.model_path)
        joblib.dump(self.labels, self.labels_path)
        logger.info("[%s] Guardado en %s", self.name, self.model_path)


# ── Clasificadores concretos ───────────────────────────────────────────────────

class CategoryClassifier(_BaseClassifier):
    """
    Clasifica la CATEGORÍA temática de la PQR.
    Ejemplo de salida: "Pedido no entregado", "Facturación incorrecta", etc.
    """
    model_file  = "category_classifier.pkl"
    labels_file = "category_labels.pkl"
    name        = "CategoryClassifier"


class PriorityClassifier(_BaseClassifier):
    """
    Clasifica la PRIORIDAD de la PQR.
    Salida: "Crítica" | "Alta" | "Media" | "Baja"
    """
    model_file  = "priority_classifier.pkl"
    labels_file = "priority_labels.pkl"
    name        = "PriorityClassifier"