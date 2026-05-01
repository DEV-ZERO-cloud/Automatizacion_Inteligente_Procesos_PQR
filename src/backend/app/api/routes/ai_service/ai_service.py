import os
import logging
import httpx
from dotenv import load_dotenv
#------------------------------------------------------
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
#---------------------------------------------------------------------
from app.ia.embeddings.generator import EmbeddingGenerator
from app.ia.rule_engine.engine import RuleEngine
from app.ia.classifiers.classifiers import CategoryClassifier, PriorityClassifier
from app.ia.preprocessing.cleaner import clean_text
#--------------------------------------------------------------
from app.models.pqr import PQRCreate
from app.models.classify_response import ClassifyResponseIn
from app.models.classification import ClassificationCreate, PriorityCreate, CategoryCreate
from app.models.organization import AreaCreate
from app.models.health_response import HealthResponseIn
from app.models.reload_response import ReloadResponseIn
#--------------------------------------------------
from app.core.auth import get_current_user
#-------------------------------------------------------
import asyncio
from concurrent.futures import ThreadPoolExecutor
#-----------------------------------------------------
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

router        = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
BASE_URL      = os.getenv("BASE_URL", "")

# Umbral mínimo de confianza para no marcar como requiere_revision
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
_executor = ThreadPoolExecutor(max_workers=4)

# ── Instancias lazy ────────────────────────────────────────────────────────────

_rule_engine:        RuleEngine | None         = None
_embedding_generator: EmbeddingGenerator | None = None
_category_clf:       CategoryClassifier | None  = None
_priority_clf:       PriorityClassifier | None  = None
_http_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client

def get_rule_engine() -> RuleEngine:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine


def get_embedding_generator() -> EmbeddingGenerator:
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


def get_category_classifier() -> CategoryClassifier:
    global _category_clf
    if _category_clf is None:
        _category_clf = CategoryClassifier()
        _category_clf.load()
    return _category_clf


def get_priority_classifier() -> PriorityClassifier:
    global _priority_clf
    if _priority_clf is None:
        _priority_clf = PriorityClassifier()
        _priority_clf.load()
    return _priority_clf

def create_classification(classify_response: ClassifyResponseIn) ->ClassificationCreate:
    classification = ClassificationCreate(
        #id=,
        pqr_id=classify_response.id,
        modelo_version=classify_response.model,
        #categoria_id=,
        #prioridad_id=,
        confianza=classify_response.confianza,
        origen="IA",
        fue_corregida=False
    )
    return classification


# ── Helper HTTP ────────────────────────────────────────────────────────────────

async def _predict_parallel(embedding, cat_clf, pri_clf):
    loop = asyncio.get_event_loop()

    cat_future = loop.run_in_executor(_executor, cat_clf.predict, embedding)
    pri_future = loop.run_in_executor(_executor, pri_clf.predict, embedding)

    (categoria, cat_conf), (prioridad, pri_conf) = await asyncio.gather(
        cat_future, pri_future
    )
    return categoria, cat_conf, prioridad, pri_conf

async def _get_pqr(pqr_id: int, token: str) -> PQRCreate:
    client = get_http_client()
    response = await client.get(
            f"{BASE_URL}/pqrs/{pqr_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    response.raise_for_status()
    return PQRCreate.from_dict(response.json().get("data"))

async def _get_category(category_name: str, token: str) -> CategoryCreate:
    client = get_http_client()
    response = await client.get(
            f"{BASE_URL}/categories/name",
            headers={"Authorization": f"Bearer {token}"},
            params={"cat_name":category_name}
    )
    response.raise_for_status()
    
    data = response.json().get("data")
    return data["id"] 
    
async def _get_priority(priority_name: str, token: str) -> PriorityCreate:
    client = get_http_client()
    response = await client.get(
            f"{BASE_URL}/priorities/name",
            headers={"Authorization": f"Bearer {token}"},
            params={"prio_name":priority_name}
    )
    response.raise_for_status()
    
    data = response.json().get("data")
    return data["id"] 

async def _get_area(area_name: str, token: str) -> AreaCreate:
    client = get_http_client()
    response = await client.get(
            f"{BASE_URL}/areas/name",
            headers={"Authorization": f"Bearer {token}"},
             params={"nombre":area_name}
    )
    response.raise_for_status()
    return AreaCreate.from_dict(response.json().get("data"))
    

# ── Agregar Clasificacion hacia Tabla Classificacion
async def _post_classification(
        classify_response: ClassifyResponseIn, 
        category_id: int,
        priority_id: int,
        token: str
        ) -> ClassificationCreate:
    client = get_http_client()
    response = await client.post(
            f"{BASE_URL}/classifications/create",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pqr_id":            classify_response.id,
                "modelo_version":    classify_response.model,
                "categoria_id":         category_id,
                "prioridad_id":         priority_id,
                "confianza":         classify_response.confianza,
                "origen": "IA",
                "fue_corregida": False
            }
    )
    response.raise_for_status()
    return ClassificationCreate(
        pqr_id=classify_response.id,
        modelo_version=classify_response.model,
        categoria_id=category_id,
        prioridad_id=priority_id,
        confianza=classify_response.confianza,
        origen="IA",
        fue_corregida=False
    )
# ── Lógica de fuente ───────────────────────────────────────────────────────────

def _resolve_source(rules_matched: bool, cat_ready: bool, pri_ready: bool) -> str:
    if rules_matched and (cat_ready or pri_ready):
        return "hybrid"
    if rules_matched:
        return "rules"
    if cat_ready or pri_ready:
        return "ml"
    return "unavailable"


# ── Endpoints ──────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
#  POST /classify/{pqr_id}
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/classify/{pqr_id}", tags=["IA"])
async def classify(
    pqr_id: int,
    token: str = Depends(oauth2_scheme),
    current_user=Depends(get_current_user),
):
    """
    Clasifica una PQR por su ID.

    Retorna:
      - categoria   → modelo ML (CategoryClassifier)
      - prioridad   → modelo ML (PriorityClassifier)
      - area        → motor de reglas (rules.yaml)
      - tags        → motor de reglas (rules.yaml)
      - source      → "hybrid" | "rules" | "ml" | "unavailable"
      - confianza   → promedio de confianza de ambos modelos ML
      - requiere_revision → True si confianza < umbral o modelos no disponibles
    """
    try:
        pqr  = await _get_pqr(pqr_id, token)
        text = clean_text(f"{pqr.titulo}. {pqr.descripcion}")

        # ── 1. Motor de reglas → area + tags ──────────────────────────────────
        rule_eng    = get_rule_engine()
        rule_result = rule_eng.evaluate(text)

        # ── 2. Embedding ───────────────────────────────────────────────────────
        generator = get_embedding_generator()
        embedding = generator.generate_one(text)

        # ── 3. Clasificadores ML → categoria + prioridad ───────────────────────
        cat_clf = get_category_classifier()
        pri_clf = get_priority_classifier()

        categoria, cat_conf, prioridad, pri_conf = await _predict_parallel(
            embedding, cat_clf, pri_clf
        )
        # ── 4. Confianza global y flag de revisión ─────────────────────────────
        confidences = [c for c in [cat_conf, pri_conf] if c is not None]
        confianza   = round(sum(confidences) / len(confidences), 4) if confidences else None

        requiere_revision = (
            not cat_clf.is_ready()
            or not pri_clf.is_ready()
            or (confianza is not None and confianza < CONFIDENCE_THRESHOLD)
        )

        # ── 5. Fuente ──────────────────────────────────────────────────────────
        source = _resolve_source(
            rules_matched=bool(rule_result.rules_matched),
            cat_ready=cat_clf.is_ready(),
            pri_ready=pri_clf.is_ready(),
        )

        logger.info(
            "PQR %d clasificada — area=%s categoria=%s prioridad=%s conf=%.2f source=%s",
            pqr_id, rule_result.area, categoria, prioridad, confianza or 0, source,
        )

        classify_response = ClassifyResponseIn(
            id                = pqr.ID,
            categoria         = categoria,
            prioridad         = prioridad.lower() if prioridad else None,
            area              = rule_result.area,
            tags              = rule_result.tags,
            rules_matched     = rule_result.rules_matched,
            source            = source,
            confianza         = confianza,
            requiere_revision = requiere_revision,
            model             = os.getenv("MODEL_NAME"),
        )
        # ── 6. Post a tabla Classificacion ─────────────────────────────
        categoria_id, prioridad_id = await asyncio.gather(
            _get_category(category_name=classify_response.categoria, token=token),
             _get_priority(priority_name=classify_response.prioridad, token=token)
        )

        await _post_classification(
            classify_response=classify_response,
            category_id=categoria_id,
            priority_id=prioridad_id,
            token=token
            )
        return classify_response

    except Exception:
        logger.exception("Error al clasificar PQR %d", pqr_id)
        raise HTTPException(status_code=500, detail="Error al clasificar la PQR.")
# ══════════════════════════════════════════════════════════════════════════════
#  POST /reload_rules
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/reload_rules", tags=["IA"])
async def reload_rules():
    """Recarga rules.yaml en caliente sin reiniciar el servicio."""
    try:
        rule_eng = get_rule_engine()
        rule_eng.reload()
        return ReloadResponseIn(
            success     = True,
            rules_count = len(rule_eng.rules),
            message     = "Reglas recargadas correctamente.",
        )
    except Exception as exc:
        logger.error("Error recargando reglas: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    
# ══════════════════════════════════════════════════════════════════════════════
#  POST /reload_models
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/reload_models", tags=["IA"])
async def reload_models():
    """
    Recarga los modelos ML desde disco.
    Llamar después de ejecutar trainer.py para aplicar el reentrenamiento.
    """
    global _category_clf, _priority_clf
    _category_clf = None
    _priority_clf = None

    cat_clf = get_category_classifier()
    pri_clf = get_priority_classifier()

    return {
        "success": True,
        "models_ready": {
            "category": cat_clf.is_ready(),
            "priority": pri_clf.is_ready(),
        },
        "message": "Modelos recargados desde disco.",
    }

# ══════════════════════════════════════════════════════════════════════════════
#  POST /train
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/train", tags=["IA"])
async def trigger_training(
    csv_path: str,
    target: str = "all",
    min_per_class: int = 5,
):
    """
    Dispara el entrenamiento desde un CSV ya disponible en el servidor.

    Params:
      csv_path:      ruta absoluta al CSV en el servidor
      target:        "all" | "categoria" | "prioridad"
      min_per_class: mínimo de ejemplos por clase
    """
    try:
        from app.ia.scripts.train_classifiers import run_training
        result = run_training(csv_path=csv_path, target=target, min_per_class=min_per_class)

        # Recargar modelos automáticamente si el entrenamiento fue exitoso
        if result.get("status") == "done":
            global _category_clf, _priority_clf
            _category_clf = None
            _priority_clf = None
            get_category_classifier()
            get_priority_classifier()

        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception:
        logger.exception("Error en entrenamiento")
        raise HTTPException(status_code=500, detail="Error durante el entrenamiento.")

# ══════════════════════════════════════════════════════════════════════════════
#  GET /health
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/health", tags=["IA"])
async def health():
    """Estado del servicio IA y sus componentes."""
    generator = get_embedding_generator()
    rule_eng  = get_rule_engine()
    cat_clf   = get_category_classifier()
    pri_clf   = get_priority_classifier()

    return HealthResponseIn(
        status       = "ok",
        model_loaded = generator._model is not None,
        rules_count  = len(rule_eng.rules),
        ml_status    = {
            "category_ready": cat_clf.is_ready(),
            "priority_ready": pri_clf.is_ready(),
        },
    )

# ══════════════════════════════════════════════════════════════════════════════
#  GET /debug/status
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/debug/status", tags=["IA"])
async def debug_status():
    """Debug: estado completo del servicio IA."""
    rule_eng  = get_rule_engine()
    generator = get_embedding_generator()
    cat_clf   = get_category_classifier()
    pri_clf   = get_priority_classifier()

    return {
        "embedding_model":    os.getenv("MODEL_NAME"),
        "embedding_ready":    generator._model is not None,
        "rules_count":        len(rule_eng.rules),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "classifiers": {
            "category": {
                "ready":   cat_clf.is_ready(),
                "classes": cat_clf.labels if cat_clf.is_ready() else [],
            },
            "priority": {
                "ready":   pri_clf.is_ready(),
                "classes": pri_clf.labels if pri_clf.is_ready() else [],
            },
        },
        "active_mode": (
            "hybrid (rules + ml)"
            if cat_clf.is_ready() and pri_clf.is_ready()
            else "rules only (ML sin entrenar — ejecuta trainer.py)"
        ),
    }