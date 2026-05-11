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


# ── Features de reglas para prioridad ─────────────────────────────────────────
#
# CRÍTICO: este orden debe ser IDÉNTICO al de train_classifiers.py.
# Cualquier cambio aquí requiere reentrenar el PriorityClassifier.

PRIORITY_RULE_TAGS = [
    # Señales que implican CRÍTICA
    "cuenta hackeada",
    "acceso no autorizado",
    "fraude",
    "cargo no reconocido",
    "phishing",
    "acción legal",
    "SIC",
    # Señales que implican ALTA
    "pedido extraviado",
    "entrega fallida",
    "cobro duplicado",
    "reembolso",
    "falla técnica",
    "falla plataforma",
    "pago fallido",
    # Señales de contexto / MEDIA
    "escalamiento",
    "caso sin resolver",
    "producto defectuoso",
    "valor incorrecto",
]

_TAG_INDEX: dict[str, int] = {tag: i for i, tag in enumerate(PRIORITY_RULE_TAGS)}


def _build_rule_features(text: str) -> np.ndarray:
    """
    Genera el vector binario de features objetivas para un texto en inferencia.
    Usa el RuleEngine (importado lazy para no romper el módulo si no está disponible).
    """
    from app.ia.rule_engine.engine import RuleEngine
    result = RuleEngine().evaluate(text)
    features = np.zeros(len(PRIORITY_RULE_TAGS), dtype=np.float32)
    for tag in result.tags:
        if tag in _TAG_INDEX:
            features[_TAG_INDEX[tag]] = 1.0
    return features


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

    En inferencia extiende el embedding base con features objetivas del RuleEngine
    (misma transformación que en train_classifiers.py → generate_priority_embeddings).
    """
    model_file  = "priority_classifier.pkl"
    labels_file = "priority_labels.pkl"
    name        = "PriorityClassifier"

    def predict(self, embedding: np.ndarray, text: str = "") -> tuple[Optional[str], Optional[float]]:
        """
        Predice la prioridad dado un embedding base y el texto original.

        Args:
            embedding: embedding base del transformer (shape 1-D o 2-D).
            text:      texto original — se usa para construir las rule_features.
                       Pasar siempre que se disponga de él.

        Returns:
            (label, confianza) o (None, None) si el modelo no está listo.
        """
        if not self.is_ready():
            return None, None
        try:
            emb = self._normalize(embedding)           # → (1, 384)

            if text:
                rule_feats = _build_rule_features(text)             # → (19,)
                rule_feats = rule_feats.reshape(1, -1)              # → (1, 19)
                emb = np.concatenate([emb, rule_feats], axis=1)     # → (1, 403)

            proba = self.model.predict_proba(emb)[0]
            idx   = int(proba.argmax())
            return self.labels[idx], float(proba[idx])
        except Exception:
            logger.exception("[%s] Error en predicción.", self.name)
            return None, None