import time
import structlog
from fastapi import APIRouter, HTTPException

from app.ia.embeddings.generator import EmbeddingGenerator
from app.ia.rule_engine.engine import RuleEngine
from app.ia.classifiers.category import CategoryClassifier
from app.ia.classifiers.tags import TagsClassifier
from app.ia.classifiers.priority import PriorityClassifier
from app.ia.preprocessing.cleaner import clean_text
from app.models.classify_request import ClassifyRequestIn
from app.models.classify_response import ClassifyResponseIn
from app.models.health_response import HealthResponseIn
from app.models.reload_response import ReloadResponseIn

logger = structlog.get_logger()
router = APIRouter()

# ── Instancias lazy ────────────────────────────────────────────────────────────
_rule_engine = None
_embedding_generator = None
_category_clf = None
_tags_clf = None
_priority_clf = None


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


def get_classifiers() -> tuple:
    """
    Intenta cargar los clasificadores ML.
    Si no están entrenados aún, los devuelve como None sin romper el servicio.
    """
    global _category_clf, _tags_clf, _priority_clf

    if _category_clf is None:
        try:
            _category_clf = CategoryClassifier()
            _category_clf.load()
        except FileNotFoundError:
            _category_clf = CategoryClassifier()  # instancia vacía, is_ready() = False

    if _tags_clf is None:
        try:
            _tags_clf = TagsClassifier()
            _tags_clf.load()
        except FileNotFoundError:
            _tags_clf = TagsClassifier()

    if _priority_clf is None:
        try:
            _priority_clf = PriorityClassifier()
            _priority_clf.load()
        except FileNotFoundError:
            _priority_clf = PriorityClassifier()
    return _category_clf, _tags_clf, _priority_clf


def _determine_source(rule_matched: bool, ml_ready: bool) -> str:
    """Determina la fuente de clasificación según qué componentes aportaron."""
    if rule_matched and ml_ready:
        return "hybrid"
    if ml_ready:
        return "ml"
    return "rules"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/classify", tags=["IA"])
async def classify(request: ClassifyRequestIn):
    start = time.time()

    try:
        text = clean_text(request.text)

        # Motor de reglas
        re = get_rule_engine()
        rule_result = re.evaluate(text)

        # Embedding - sin normalizar aquí
        eg = get_embedding_generator()
        embedding = eg.generate_one(text)

        # Clasificadores ML (ellos mismos normalizarán)
        cat_clf, tags_clf, pri_clf = get_classifiers()

        # ── Categoría ──────────────────────────────────────────────────────
        category = rule_result.category
        confidence = None

        if cat_clf.is_ready() and embedding is not None:
            ml_category, ml_confidence = cat_clf.predict(embedding)  # Ya normaliza internamente
            if category is None:
                category = ml_category
                confidence = ml_confidence

        # ── Tags ───────────────────────────────────────────────────────────
        tags = list(rule_result.tags)
        if tags_clf.is_ready() and embedding is not None:
            ml_tags = tags_clf.predict(embedding)  # Ya normaliza internamente
            for tag in ml_tags:
                if tag not in tags:
                    tags.append(tag)

        # ── Prioridad ──────────────────────────────────────────────────────
        priority = rule_result.priority
        if pri_clf.is_ready() and priority is None and embedding is not None:
            priority, _ = pri_clf.predict(embedding)  # Ya normaliza internamente

        # ── Fuente ─────────────────────────────────────────────────────────
        ml_ready = cat_clf.is_ready() or tags_clf.is_ready() or pri_clf.is_ready()
        source = _determine_source(
            rule_matched=len(rule_result.rules_matched) > 0,
            ml_ready=ml_ready
        )

        elapsed = round((time.time() - start) * 1000, 1)
        logger.info(
            "classify_request",
            pqr_id=request.pqr_id,
            category=category,
            priority=priority,
            source=source,
            elapsed_ms=elapsed,
        )

        return ClassifyResponseIn(
            category=category,
            tags=tags,
            priority=priority,
            rules_matched=rule_result.rules_matched,
            source=source,
            confidence=confidence,
        )

    except Exception as e:
        logger.error("classify_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al clasificar: {str(e)}")

@router.get("/health", tags=["IA"])
async def health():
    """Estado del servicio IA y sus componentes."""
    eg = get_embedding_generator()
    re = get_rule_engine()
    cat_clf, tags_clf, pri_clf = get_classifiers()
    logger.info(
        "ml_models_status",
        category_ready=cat_clf.is_ready(),
        tags_ready=tags_clf.is_ready(),
        priority_ready=pri_clf.is_ready()
    )
    return HealthResponseIn(
        status="ok",
        model_loaded=eg.model is not None,
        rules_count=len(re.rules),
    )


@router.post("/reload_rules", tags=["IA"])
async def reload_rules():
    """Recarga reglas desde YAML sin reiniciar el servicio."""
    try:
        re = get_rule_engine()
        re.reload()
        return ReloadResponseIn(
            success=True,
            rules_count=len(re.rules),
            message="Reglas recargadas correctamente.",
        )
    except Exception as e:
        logger.error("reload_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al recargar: {str(e)}")


@router.post("/reload_models", tags=["IA"])
async def reload_models():
    """
    Recarga los clasificadores ML desde disco.
    Útil después de un reentrenamiento sin reiniciar el servicio.
    """
    global _category_clf, _tags_clf, _priority_clf
    _category_clf = None
    _tags_clf = None
    _priority_clf = None

    cat_clf, tags_clf, pri_clf = get_classifiers()

    return {
        "success": True,
        "models_ready": {
            "category": cat_clf.is_ready(),
            "tags": tags_clf.is_ready(),
            "priority": pri_clf.is_ready(),
        },
        "message": "Modelos recargados correctamente."
    }

@router.get("/debug/ml_status", tags=["IA"])
async def debug_ml_status():
    """Debug: Ver estado actual de los modelos ML"""
    cat_clf, tags_clf, pri_clf = get_classifiers()
    
    return {
        "category_classifier": {
            "is_ready": cat_clf.is_ready(),
            "has_model": hasattr(cat_clf, 'model') and cat_clf.model is not None,
            "classifier_type": str(type(cat_clf))
        },
        "tags_classifier": {
            "is_ready": tags_clf.is_ready(),
            "has_model": hasattr(tags_clf, 'model') and tags_clf.model is not None,
        },
        "priority_classifier": {
            "is_ready": pri_clf.is_ready(),
            "has_model": hasattr(pri_clf, 'model') and pri_clf.model is not None,
        },
        "embedding_ready": get_embedding_generator().model is not None,
        "rules_count": len(get_rule_engine().rules)
    }