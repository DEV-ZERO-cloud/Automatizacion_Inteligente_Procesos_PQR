import joblib
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

class CategoryClassifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        
        self.model_path = base_dir / "data" / "models" / "category_classifier.pkl"
        self.label_path = base_dir / "data" / "models" / "category_labels.pkl"
        self.model = None
        self.labels = None
    
    def load(self) -> bool:
        """Carga el modelo y las etiquetas desde disco."""
        try:
            if self.model_path.exists() and self.label_path.exists():
                self.model = joblib.load(self.model_path)
                self.labels = joblib.load(self.label_path)
                return True
            else:
                print(f"Modelo no encontrado en: {self.model_path}")
                print(f"Labels no encontrado en: {self.label_path}")
                return False
        except Exception as e:
            print(f"Error cargando clasificador de categoría: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Indica si el modelo está cargado y listo para predecir."""
        return self.model is not None and self.labels is not None
    
    def predict(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Predice la categoría dado un embedding."""
        if not self.is_ready():
            return None, None
        
        try:
            import numpy as np
            
            # === NORMALIZAR EMBEDDING ===
            # Convertir a numpy array si no lo es
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            
            # Aplanar a 2D (n_samples, n_features)
            if embedding.ndim == 3:
                # (1, 1, 384) -> (1, 384)
                embedding = embedding.reshape(embedding.shape[0], -1)
            elif embedding.ndim == 1:
                # (384,) -> (1, 384)
                embedding = embedding.reshape(1, -1)
            elif embedding.ndim == 2:
                # (1, 384) o (n, 384) - ya está bien
                pass
            else:
                raise ValueError(f"Embedding con dimensión {embedding.ndim} no soportada")
            
            # Verificar que la forma es correcta
            if embedding.shape[1] != 384:  # MiniLM-L12-v2 tiene 384 dimensiones
                print.warning(f"Dimensión inesperada: {embedding.shape[1]}, esperaba 384")
            
            # Predicción
            proba = self.model.predict_proba(embedding)[0]
            idx = proba.argmax()
            category = self.labels[idx]
            confidence = float(proba[idx])
            
            return category, confidence
            
        except Exception as e:
            print(f"Error en predicción de categoría: {e}")
            return None, None
    
    def save(self) -> None:
        """Guarda el modelo entrenado."""
        if self.model is not None and self.labels is not None:
            # Asegurar que el directorio existe
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.labels, self.label_path)
            print(f"Modelo guardado en: {self.model_path}")
        else:
            print("No hay modelo para guardar")
    
    def train(self, embeddings: np.ndarray, labels: list) -> None:
        """
        Entrena el clasificador con embeddings y etiquetas.
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder
        
        # Codificar etiquetas
        self.labels_encoder = LabelEncoder()
        y = self.labels_encoder.fit_transform(labels)
        self.labels = list(self.labels_encoder.classes_)
        
        # Entrenar modelo
        self.model = LogisticRegression(
            max_iter=1000, 
            C=1.0, 
            class_weight="balanced"
        )
        self.model.fit(embeddings, y)
        
        print(f"Modelo de categorías entrenado con {len(self.labels)} clases")