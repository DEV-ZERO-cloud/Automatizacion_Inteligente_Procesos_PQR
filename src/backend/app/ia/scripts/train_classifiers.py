"""
scripts.train_classifiers..py

Entrena CategoryClassifier y PriorityClassifier sobre embeddings generados
por paraphrase-multilingual-MiniLM-L12-v2 (transformer congelado).

Fuente de datos: CSV con PQR etiquetadas por humanos.

Columnas requeridas en el CSV:
  - texto      → descripción de la PQR (texto libre)
  - categoria  → etiqueta de categoría (ej: "Pedido no entregado")
  - prioridad  → etiqueta de prioridad ("Crítica" | "Alta" | "Media" | "Baja")

Columnas opcionales (se ignoran si no están):
  - id, tipo, area, tags, etc.

Uso:
  # Entrenamiento completo
  python -m app.ia.scripts.train_classifiers. --csv data/training/pqr_etiquetadas.csv

  # Solo reentrenar prioridad
  python -m app.ia.scripts.train_classifiers. --csv data/training/pqr_etiquetadas.csv --target prioridad

  # Con mínimo de ejemplos por clase
  python -m app.ia.scripts.train_classifiers. --csv data/training/pqr_etiquetadas.csv --min-per-class 10

Después de entrenar, llama a POST /ia/reload_models para que el servicio
cargue los nuevos .pkl sin reiniciar.
"""

import argparse
import logging
import csv
import numpy as np
import joblib
from pathlib import Path
from collections import Counter

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.utils import shuffle

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── Configuración ──────────────────────────────────────────────────────────────

CSV_REQUIRED_COLS = {"texto", "categoria", "prioridad"}
MODELS_DIR        = Path(__file__).parent.parent.parent.parent.parent / "data" / "models"
MIN_PER_CLASS_DEFAULT = 5
CV_MIN_SAMPLES        = 30   # mínimo de ejemplos para hacer cross-validation


# ── Carga del CSV ──────────────────────────────────────────────────────────────

def load_csv(csv_path: str | Path) -> list[dict]:
    """
    Carga el CSV de entrenamiento y valida columnas requeridas.

    Args:
        csv_path: ruta al CSV. Acepta separador coma o punto y coma.

    Returns:
        Lista de dicts con al menos las claves: texto, categoria, prioridad.

    Raises:
        ValueError: si faltan columnas requeridas o el archivo está vacío.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")

    rows: list[dict] = []

    # Detectar separador automáticamente
    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(2048)
        sep = ";" if sample.count(";") > sample.count(",") else ","

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=sep)
        headers = set(reader.fieldnames or [])
        missing = CSV_REQUIRED_COLS - headers
        if missing:
            raise ValueError(
                f"El CSV no tiene las columnas requeridas: {missing}. "
                f"Columnas encontradas: {headers}"
            )

        for row in reader:
            texto     = (row.get("texto") or "").strip()
            categoria = (row.get("categoria") or "").strip()
            prioridad = (row.get("prioridad") or "").strip()

            # Ignorar filas incompletas
            if not texto or not categoria or not prioridad:
                continue

            rows.append({
                "texto":     texto,
                "categoria": categoria,
                "prioridad": prioridad,
            })

    if not rows:
        raise ValueError("El CSV no tiene filas válidas después del filtrado.")

    logger.info("CSV cargado: %d filas válidas desde %s", len(rows), path.name)
    return rows


# ── Generación de embeddings ───────────────────────────────────────────────────

def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Genera embeddings usando EmbeddingGenerator (transformer congelado).
    El modelo se mantiene en memoria vía Singleton — no se recarga entre llamadas.
    """
    from app.ia.embeddings.generator import EmbeddingGenerator
    generator = EmbeddingGenerator()
    logger.info("Generando embeddings para %d textos...", len(texts))
    embeddings = generator.generate(texts)
    logger.info("Embeddings generados: shape=%s", embeddings.shape)
    return embeddings


# ── Entrenamiento de un clasificador ──────────────────────────────────────────

def train_single(
    embeddings: np.ndarray,
    labels_raw: list[str],
    name: str,
    min_per_class: int = MIN_PER_CLASS_DEFAULT,
) -> tuple[LogisticRegression, list[str]] | None:
    """
    Entrena una LogisticRegression para un campo (categoria o prioridad).

    Filtra clases con menos de min_per_class ejemplos para evitar overfitting.
    Ejecuta cross-validation si hay suficientes datos.

    Returns:
        (modelo, lista_de_clases) o None si no hay suficientes datos.
    """
    # Conteo por clase
    counts = Counter(labels_raw)
    logger.info("[%s] Distribución de clases: %s", name, dict(counts))

    valid_classes = {cls for cls, n in counts.items() if n >= min_per_class}
    if len(valid_classes) < 2:
        logger.warning(
            "[%s] Solo %d clase(s) con >= %d ejemplos. Se necesitan al menos 2. Saltando.",
            name, len(valid_classes), min_per_class,
        )
        return None

    # Filtrar filas de clases con pocos ejemplos
    mask       = [l in valid_classes for l in labels_raw]
    emb_filt   = embeddings[mask]
    lab_filt   = [l for l, m in zip(labels_raw, mask) if m]
    dropped    = len(labels_raw) - len(lab_filt)

    if dropped:
        logger.warning("[%s] %d filas descartadas por clases con < %d ejemplos.", name, dropped, min_per_class)

    emb_filt, lab_filt = shuffle(emb_filt, lab_filt, random_state=42)

    # Codificación de etiquetas
    encoder = LabelEncoder()
    y       = encoder.fit_transform(lab_filt)
    labels  = list(encoder.classes_)

    # Modelo
    model = LogisticRegression(
        max_iter=1000,
        C=1.0,
        class_weight="balanced",   # maneja desequilibrio de clases
        solver="lbfgs",            # lbfgs maneja multiclase nativamente desde sklearn 1.5
        random_state=42,
    )
    model.fit(emb_filt, y)

    # Cross-validation
    if len(lab_filt) >= CV_MIN_SAMPLES:
        n_splits = min(5, counts[min(counts, key=counts.get)])  # no más splits que ejemplos de la clase menor
        n_splits = max(2, n_splits)
        cv       = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores   = cross_val_score(model, emb_filt, y, cv=cv, scoring="f1_weighted")
        logger.info(
            "[%s] F1 CV (%d-fold): %.3f ± %.3f | clases: %d | ejemplos: %d",
            name, n_splits, scores.mean(), scores.std(), len(labels), len(lab_filt),
        )
    else:
        logger.info(
            "[%s] Entrenado con %d ejemplos (pocos para CV). Clases: %s",
            name, len(lab_filt), labels,
        )

    return model, labels


# ── Guardado ───────────────────────────────────────────────────────────────────

def save_model(model, labels: list[str], model_file: str, labels_file: str) -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model,  MODELS_DIR / model_file)
    joblib.dump(labels, MODELS_DIR / labels_file)
    logger.info("Guardado: %s (%d clases)", model_file, len(labels))


# ── Pipeline principal ─────────────────────────────────────────────────────────

def run_training(
    csv_path: str | Path,
    target: str = "all",
    min_per_class: int = MIN_PER_CLASS_DEFAULT,
) -> dict:
    """
    Pipeline completo:
      1. Carga CSV
      2. Genera embeddings (transformer congelado)
      3. Entrena CategoryClassifier y/o PriorityClassifier
      4. Guarda .pkl en data/models/

    Args:
        csv_path:      ruta al CSV de entrenamiento.
        target:        "all" | "categoria" | "prioridad"
        min_per_class: mínimo de ejemplos por clase para incluirla.

    Returns:
        dict con estado de cada clasificador entrenado.
    """
    logger.info("=== Iniciando entrenamiento ===")
    logger.info("CSV: %s | target: %s | min_per_class: %d", csv_path, target, min_per_class)

    rows  = load_csv(csv_path)
    texts = [r["texto"] for r in rows]

    embeddings = generate_embeddings(texts)

    results: dict[str, str] = {}

    # ── Categoría ──────────────────────────────────────────────────────────────
    if target in ("all", "categoria"):
        labels_cat = [r["categoria"] for r in rows]
        pair = train_single(embeddings, labels_cat, "CategoryClassifier", min_per_class)
        if pair:
            save_model(pair[0], pair[1], "category_classifier.pkl", "category_labels.pkl")
            results["categoria"] = f"ok ({len(pair[1])} clases)"
        else:
            results["categoria"] = "skipped (datos insuficientes)"

    # ── Prioridad ──────────────────────────────────────────────────────────────
    if target in ("all", "prioridad"):
        labels_pri = [r["prioridad"] for r in rows]
        pair = train_single(embeddings, labels_pri, "PriorityClassifier", min_per_class)
        if pair:
            save_model(pair[0], pair[1], "priority_classifier.pkl", "priority_labels.pkl")
            results["prioridad"] = f"ok ({len(pair[1])} clases)"
        else:
            results["prioridad"] = "skipped (datos insuficientes)"

    logger.info("=== Entrenamiento finalizado: %s ===", results)
    return {"status": "done", "samples": len(rows), "models": results}


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrenador de clasificadores PQR")
    parser.add_argument(
        "--csv", required=True,
        help="Ruta al CSV de entrenamiento (columnas: texto, categoria, prioridad)",
    )
    parser.add_argument(
        "--target", choices=["all", "categoria", "prioridad"], default="all",
        help="Qué clasificador entrenar (default: all)",
    )
    parser.add_argument(
        "--min-per-class", type=int, default=MIN_PER_CLASS_DEFAULT,
        help=f"Mínimo de ejemplos por clase (default: {MIN_PER_CLASS_DEFAULT})",
    )
    args = parser.parse_args()
    run_training(csv_path=args.csv, target=args.target, min_per_class=args.min_per_class)