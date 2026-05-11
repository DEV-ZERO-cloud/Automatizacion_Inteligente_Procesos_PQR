"""
scripts.train_classifiers.py  (versión optimizada)

Cambios vs versión original:
  - Reemplaza SVC (O(n²~³)) por LogisticRegression (O(n)) → 10-50x más rápido
  - GridSearchCV reducido: cv=3, param_grid pequeño, n_jobs=2
  - Submuestreo para GridSearch (max 200/clase) → búsqueda rápida, fit final con todos
  - Cross-validation final separada del GridSearch → no duplica trabajo
  - Memoria controlada: sin n_jobs=-1 que multiplica copias de la matriz

Entrena CategoryClassifier y PriorityClassifier sobre embeddings generados
por paraphrase-multilingual-MiniLM-L12-v2 (transformer congelado).

Columnas requeridas en el CSV:
  - texto      → descripción de la PQR (texto libre)
  - categoria  → etiqueta de categoría (ej: "Pedido no entregado")
  - prioridad  → etiqueta de prioridad ("Crítica" | "Alta" | "Media" | "Baja")

Uso:
  python -m app.ia.scripts.train_classifiers --csv data/training/pqr_etiquetadas.csv
  python -m app.ia.scripts.train_classifiers --csv data/training/pqr_etiquetadas.csv --target prioridad
  python -m app.ia.scripts.train_classifiers --csv data/training/pqr_etiquetadas.csv --min-per-class 10
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
from sklearn.model_selection import cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.utils import shuffle

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── Configuración ──────────────────────────────────────────────────────────────

CSV_REQUIRED_COLS     = {"texto", "categoria", "prioridad"}


# ── Features de reglas ─────────────────────────────────────────────────────────
#
# Cada feature es una señal OBJETIVA de prioridad extraída por el RuleEngine.
# Se concatenan al embedding del transformer para que el clasificador de prioridad
# tenga señales explícitas más allá del espacio semántico del texto.
#
# CRÍTICO: este orden y estas tags deben ser IDÉNTICOS en train y en inferencia.
# Si cambias aquí, cambia también PRIORITY_RULE_TAGS en classifiers.py.

PRIORITY_RULE_TAGS = [
    # Señales que implican CRÍTICA
    "cuenta hackeada",       # fraude_cuenta_comprometida
    "acceso no autorizado",  # fraude_cuenta_comprometida
    "fraude",                # fraude_estafa_robo
    "cargo no reconocido",   # fraude_cargo_no_reconocido
    "phishing",              # fraude_phishing
    "acción legal",          # legal_acciones_formales
    "SIC",                   # legal_acciones_formales
    # Señales que implican ALTA
    "pedido extraviado",     # logistica_pedido_perdido
    "entrega fallida",       # logistica_entrega_fallida
    "cobro duplicado",       # cartera_cobro_duplicado
    "reembolso",             # cartera_reembolso
    "falla técnica",         # garantias_falla_tecnica
    "falla plataforma",      # tech_falla_plataforma
    "pago fallido",          # tech_pago_fallido
    # Señales que implican MEDIA / contexto
    "escalamiento",          # atencion_sugerencia_supervisor
    "caso sin resolver",     # atencion_caso_sin_resolver
    "producto defectuoso",   # garantias_producto_defectuoso
    "valor incorrecto",      # cartera_valor_incorrecto
]


def build_rule_features(texts: list[str]) -> np.ndarray:
    """
    Genera un vector binario de features objetivas para cada texto usando el RuleEngine.

    Retorna np.ndarray de shape (N, len(PRIORITY_RULE_TAGS)) con valores 0.0 / 1.0.
    Se concatena al embedding del transformer antes de entrenar.
    """
    from app.ia.rule_engine.engine import RuleEngine  # import aquí para no romper el módulo si no está disponible

    engine = RuleEngine()
    tag_index = {tag: i for i, tag in enumerate(PRIORITY_RULE_TAGS)}
    n_features = len(PRIORITY_RULE_TAGS)

    features = np.zeros((len(texts), n_features), dtype=np.float32)
    for row_idx, text in enumerate(texts):
        result = engine.evaluate(text)
        for tag in result.tags:
            if tag in tag_index:
                features[row_idx, tag_index[tag]] = 1.0

    logger.info(
        "Rule features generadas: shape=%s | tags con al menos 1 hit: %d/%d",
        features.shape,
        int((features.sum(axis=0) > 0).sum()),
        n_features,
    )
    return features
MODELS_DIR            = Path(__file__).parent.parent.parent.parent.parent / "data" / "models"
MIN_PER_CLASS_DEFAULT = 5
CV_MIN_SAMPLES        = 30    # mínimo de ejemplos para hacer cross-validation
GRIDSEARCH_MAX_PER_CLASS = 200  # submuestreo para búsqueda de hiperparámetros


# ── Carga del CSV ──────────────────────────────────────────────────────────────

def load_csv(csv_path: str | Path) -> list[dict]:
    """
    Carga el CSV de entrenamiento y valida columnas requeridas.
    Acepta separador coma o punto y coma automáticamente.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")

    with open(path, encoding="utf-8-sig") as f:
        sample = f.read(2048)
        sep = ";" if sample.count(";") > sample.count(",") else ","

    rows: list[dict] = []
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
            if not texto or not categoria or not prioridad:
                continue
            rows.append({"texto": texto, "categoria": categoria, "prioridad": prioridad})

    if not rows:
        raise ValueError("El CSV no tiene filas válidas después del filtrado.")

    logger.info("CSV cargado: %d filas válidas desde %s", len(rows), path.name)
    return rows


# ── Generación de embeddings ───────────────────────────────────────────────────

def generate_embeddings(texts: list[str]) -> np.ndarray:
    """
    Genera embeddings usando EmbeddingGenerator (transformer congelado).
    El modelo se mantiene en memoria vía Singleton.
    """
    from app.ia.embeddings.generator import EmbeddingGenerator
    generator = EmbeddingGenerator()
    logger.info("Generando embeddings para %d textos...", len(texts))
    embeddings = generator.generate(texts)
    logger.info("Embeddings generados: shape=%s", embeddings.shape)
    return embeddings


def generate_priority_embeddings(texts: list[str]) -> np.ndarray:
    """
    Embedding extendido exclusivo para el clasificador de PRIORIDAD.

    Concatena al embedding semántico del transformer un vector binario de
    features objetivas extraídas por el RuleEngine (señales de fraude, acción
    legal, entrega fallida, etc.).

    Shape resultante: (N, 384 + len(PRIORITY_RULE_TAGS))

    CRÍTICO: classifiers.py debe aplicar la misma transformación en inferencia
    usando el mismo PRIORITY_RULE_TAGS en el mismo orden.
    """
    base = generate_embeddings(texts)
    rule_feats = build_rule_features(texts)
    extended = np.concatenate([base, rule_feats], axis=1)
    logger.info(
        "Priority embeddings: %d base + %d rule_features = %d dims totales",
        base.shape[1], rule_feats.shape[1], extended.shape[1],
    )
    return extended


# ── Submuestreo estratificado para GridSearch ──────────────────────────────────

def subsample_for_gridsearch(
    embeddings: np.ndarray,
    labels: list,
    max_per_class: int,
    random_state: int = 42,
) -> tuple[np.ndarray, list]:
    """
    Toma hasta max_per_class ejemplos por clase para hacer GridSearch rápido.
    El fit final siempre usa todos los datos.
    """
    rng = np.random.RandomState(random_state)
    indices = []
    label_array = np.array(labels)

    for cls in np.unique(label_array):
        cls_idx = np.where(label_array == cls)[0]
        if len(cls_idx) > max_per_class:
            cls_idx = rng.choice(cls_idx, size=max_per_class, replace=False)
        indices.extend(cls_idx.tolist())

    indices = sorted(indices)
    return embeddings[indices], [labels[i] for i in indices]


# ── Entrenamiento de un clasificador ──────────────────────────────────────────

def train_single(
    embeddings: np.ndarray,
    labels_raw: list[str],
    name: str,
    min_per_class: int = MIN_PER_CLASS_DEFAULT,
) -> tuple | None:
    """
    Entrena un LogisticRegression para un campo (categoria o prioridad).

    Estrategia de velocidad:
      1. GridSearchCV con submuestreo (max 200/clase) y cv=3  → rápido
      2. Fit final con TODOS los datos y los mejores parámetros → preciso
      3. Cross-validation final para reportar métricas reales

    Returns:
        (modelo, lista_de_clases) o None si no hay suficientes datos.
    """
    counts = Counter(labels_raw)
    logger.info("[%s] Distribución de clases: %s", name, dict(counts))

    valid_classes = {cls for cls, n in counts.items() if n >= min_per_class}
    if len(valid_classes) < 2:
        logger.warning(
            "[%s] Solo %d clase(s) con >= %d ejemplos. Se necesitan al menos 2. Saltando.",
            name, len(valid_classes), min_per_class,
        )
        return None

    # Filtrar clases con pocos ejemplos
    mask     = [l in valid_classes for l in labels_raw]
    emb_full = embeddings[mask]
    lab_full = [l for l, m in zip(labels_raw, mask) if m]
    dropped  = len(labels_raw) - len(lab_full)
    if dropped:
        logger.warning("[%s] %d filas descartadas (clases con < %d ejemplos).", name, dropped, min_per_class)

    emb_full, lab_full = shuffle(emb_full, lab_full, random_state=42)

    # Codificación de etiquetas
    encoder   = LabelEncoder()
    y_full    = encoder.fit_transform(lab_full)
    labels    = list(encoder.classes_)

    # ── Paso 1: GridSearch sobre submuestreo ───────────────────────────────────
    min_class_count = min(counts[c] for c in valid_classes)
    gs_max          = min(GRIDSEARCH_MAX_PER_CLASS, min_class_count)
    emb_gs, lab_gs  = subsample_for_gridsearch(emb_full, lab_full, max_per_class=gs_max)
    y_gs            = encoder.transform(lab_gs)

    logger.info(
        "[%s] GridSearch sobre %d muestras (max %d/clase, %d clases)...",
        name, len(lab_gs), gs_max, len(labels),
    )

    # LogisticRegression: lineal, O(n), perfecto para embeddings densos de alta dimensión
    param_grid = {
        "C":        [0.01, 0.1, 1, 10],
        "solver":   ["lbfgs"],   # saga es más lento en datasets < 50k, lbfgs es suficiente
        "max_iter": [1000],
    }
    cv_gs = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    grid_search = GridSearchCV(
        LogisticRegression(class_weight="balanced", random_state=42),
        param_grid,
        cv=cv_gs,
        scoring="f1_macro",
        n_jobs=2,       # 2 workers: paralelismo controlado sin explotar RAM
        verbose=1,
        refit=False,    # no reentrenar aquí; lo hacemos con todos los datos abajo
    )
    grid_search.fit(emb_gs, y_gs)
    best_params = grid_search.best_params_
    logger.info("[%s] Mejores parámetros: %s", name, best_params)

    # ── Paso 2: Fit final con TODOS los datos ──────────────────────────────────
    logger.info("[%s] Entrenando modelo final con %d muestras...", name, len(lab_full))
    best_params_clean = {k: v for k, v in best_params.items() if k != "max_iter"}
    model = LogisticRegression(
        class_weight="balanced",
        random_state=42,
        max_iter=1000,
        **best_params_clean,
    )
    model.fit(emb_full, y_full)

    # ── Paso 3: Cross-validation de métricas ──────────────────────────────────
    if len(lab_full) >= CV_MIN_SAMPLES:
        n_splits_cv = max(2, min(5, min_class_count))
        cv_final    = StratifiedKFold(n_splits=n_splits_cv, shuffle=True, random_state=42)
        scores      = cross_val_score(model, emb_full, y_full, cv=cv_final, scoring="f1_macro", n_jobs=2)
        logger.info(
            "[%s] F1-macro CV (%d-fold): %.3f ± %.3f | clases: %d | ejemplos: %d",
            name, n_splits_cv, scores.mean(), scores.std(), len(labels), len(lab_full),
        )
    else:
        logger.info(
            "[%s] Entrenado con %d ejemplos (pocos para CV). Clases: %s",
            name, len(lab_full), labels,
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
    """
    logger.info("=== Iniciando entrenamiento ===")
    logger.info("CSV: %s | target: %s | min_per_class: %d", csv_path, target, min_per_class)

    rows  = load_csv(csv_path)
    texts = [r["texto"] for r in rows]
    results: dict[str, str] = {}

    if target in ("all", "categoria"):
        # Categoría usa embeddings base — ya tiene 99.5% accuracy, no necesita features extra
        embeddings_cat = generate_embeddings(texts)
        labels_cat = [r["categoria"] for r in rows]
        pair = train_single(embeddings_cat, labels_cat, "CategoryClassifier", min_per_class)
        if pair:
            save_model(pair[0], pair[1], "category_classifier.pkl", "category_labels.pkl")
            results["categoria"] = f"ok ({len(pair[1])} clases)"
        else:
            results["categoria"] = "skipped (datos insuficientes)"

    if target in ("all", "prioridad"):
        # Prioridad usa embeddings extendidos: base + rule_features objetivas
        embeddings_pri = generate_priority_embeddings(texts)
        labels_pri = [r["prioridad"] for r in rows]
        pair = train_single(embeddings_pri, labels_pri, "PriorityClassifier", min_per_class)
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