"""
Script de entrenamiento de clasificadores PQR.

Uso:
    $env:PYTHONPATH = "src;src/backend"
    python src/backend/app/ia/scripts/train_classifiers.py --data src/data/labeled_data.csv

Formato esperado del CSV:
    text, category, tags, priority
    "No puedo acceder","Queja","account_access","alta"
"""
import argparse
import joblib
import numpy as np
import pandas as pd
import re
import unicodedata
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent
MODELS_PATH = BASE_DIR / "data" / "models"
MODELS_PATH.mkdir(parents=True, exist_ok=True)


# ── Preprocesamiento ───────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text))
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[^a-záéíóúüñ0-9\s.,;:!?¿¡]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Carga de datos ─────────────────────────────────────────────────────────────
def load_data(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required = {"text", "category", "tags", "priority"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes en el CSV: {missing}")

    df = df.dropna(subset=["text", "category", "priority"])
    df["text"] = df["text"].apply(clean_text)
    df = df[df["text"].str.len() > 10]

    # Tags: soporta múltiples etiquetas separadas por |
    df["tags_list"] = df["tags"].apply(
        lambda x: x.split("|") if isinstance(x, str) else []
    )

    print(f"Registros cargados: {len(df)}")
    print(f"\nDistribución categorías:\n{df['category'].value_counts()}")
    print(f"\nDistribución prioridad:\n{df['priority'].value_counts()}")
    return df


# ── Embeddings ─────────────────────────────────────────────────────────────────
def generate_embeddings(texts: list[str]) -> np.ndarray:
    from app.ia.embeddings.generator import EmbeddingGenerator
    print(f"\nGenerando embeddings para {len(texts)} textos...")
    generator = EmbeddingGenerator()
    embeddings = generator.generate(texts)
    print(f"Embeddings generados: {embeddings.shape}")
    return embeddings


# ── Entrenamiento: Categoría ───────────────────────────────────────────────────
def train_category(embeddings: np.ndarray, labels: list[str]):
    print("\n── Entrenando clasificador de categoría ──")
    le = LabelEncoder()
    y = le.fit_transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    joblib.dump(model, MODELS_PATH / "category_classifier.pkl")
    joblib.dump(list(le.classes_), MODELS_PATH / "category_labels.pkl")
    print(f"Guardado: {MODELS_PATH / 'category_classifier.pkl'}")


# ── Entrenamiento: Tags ────────────────────────────────────────────────────────
def train_tags(embeddings: np.ndarray, tags_list: list[list[str]]):
    print("\n── Entrenando clasificador de tags ──")
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(tags_list)

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, y, test_size=0.2, random_state=42
    )

    model = OneVsRestClassifier(LogisticRegression(max_iter=1000, C=1.0))
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(
        y_test, y_pred,
        target_names=mlb.classes_,
        zero_division=0
    ))

    joblib.dump(model, MODELS_PATH / "tags_classifier.pkl")
    joblib.dump(list(mlb.classes_), MODELS_PATH / "tags_labels.pkl")
    print(f"Guardado: {MODELS_PATH / 'tags_classifier.pkl'}")


# ── Entrenamiento: Prioridad ───────────────────────────────────────────────────
def train_priority(embeddings: np.ndarray, labels: list[str]):
    print("\n── Entrenando clasificador de prioridad ──")
    le = LabelEncoder()
    y = le.fit_transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    joblib.dump(model, MODELS_PATH / "priority_classifier.pkl")
    joblib.dump(list(le.classes_), MODELS_PATH / "priority_labels.pkl")
    print(f"Guardado: {MODELS_PATH / 'priority_classifier.pkl'}")


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Entrena los clasificadores PQR")
    parser.add_argument("--data", required=True, help="Ruta al CSV de datos etiquetados")
    parser.add_argument("--skip-embeddings", action="store_true",
                        help="Carga embeddings desde disco si ya fueron generados")
    args = parser.parse_args()

    df = load_data(args.data)

    embeddings_path = MODELS_PATH / "embeddings_cache.npy"

    if args.skip_embeddings and embeddings_path.exists():
        print(f"\nCargando embeddings desde caché: {embeddings_path}")
        embeddings = np.load(str(embeddings_path))
    else:
        embeddings = generate_embeddings(df["text"].tolist())
        np.save(str(embeddings_path), embeddings)
        print(f"Embeddings guardados en caché: {embeddings_path}")

    train_category(embeddings, df["category"].tolist())
    train_tags(embeddings, df["tags_list"].tolist())
    train_priority(embeddings, df["priority"].tolist())

    print("\n✓ Entrenamiento completo. Modelos guardados en:", MODELS_PATH)
    print("\nPara activar los modelos sin reiniciar la API, llama a:")
    print("  POST http://127.0.0.1:8000/reload_models")