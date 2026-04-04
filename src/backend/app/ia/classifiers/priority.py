import joblib
import numpy as np
from pathlib import Path
from typing import Optional, Tuple


class PriorityClassifier:
    def __init__(self):
        base_dir = Path(__file__).parent.parent.parent.parent.parent.parent
        self.model_path = base_dir / "data" / "models" / "priority_classifier.pkl"
        self.label_path = base_dir / "data" / "models" / "priority_labels.pkl"
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
            print(f"Error cargando prioridades: {e}")
            return False
        
    def predict(self, embedding: np.ndarray) -> Tuple[Optional[str], Optional[float]]:
        """Predice la prioridad dado un embedding."""
        if not self.is_ready():
            return None, None
        
        try:
            import numpy as np
            
            # === NORMALIZAR EMBEDDING ===
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)
            
            if embedding.ndim == 3:
                embedding = embedding.reshape(embedding.shape[0], -1)
            elif embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)
            elif embedding.ndim == 2:
                pass
            
            # Predicción
            proba = self.model.predict_proba(embedding)[0]
            idx = proba.argmax()
            priority = self.labels[idx]
            confidence = float(proba[idx])
            
            return priority, confidence
            
        except Exception as e:
            print(f"Error en predicción de prioridad: {e}")
            return None, None

    def is_ready(self) -> bool:
        return self.model is not None