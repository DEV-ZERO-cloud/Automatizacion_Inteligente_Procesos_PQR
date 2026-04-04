import time
import structlog
from fastapi import APIRouter, HTTPException
from src.embeddings.generator import EmbeddingGenerator
from src.rule_engine.engine import RuleEngine
from src.api.models.classify_request import ClassifyRequestIn, ClassifyRequestOut
from src.api.models.classify_response import ClassifyResponseIn, ClassifyResponseOut
from src.api.models.health_response import HealthResponseIn
from src.api.models.reload_response import ReloadResponseIn

logger = structlog.get_logger()
router = APIRouter()

# Instancias compartidas (se inicializan al importar el módulo)
rule_engine = RuleEngine()
embedding_generator = EmbeddingGenerator()


@router.post("/classify")
async def classify(request: ClassifyRequestIn):
    """
    Clasifica una PQR y devuelve categoría, tags y prioridad.
    Por ahora usa solo el motor de reglas.
    Cuando los clasificadores ML estén entrenados, se integran aquí.
    """
    start = time.time()

    try:
        # Fase 4: motor de reglas
        rule_result = rule_engine.evaluate(request.text)

        # Fase 2: generamos el embedding (listo para cuando llegue el ML)
        embedding = embedding_generator.generate_one(request.text)

        elapsed = round(time.time() - start, 3)

        classify_response = ClassifyResponseIn(
            category=rule_result.category,
            tags=rule_result.tags,
            priority=rule_result.priority,
            rules_matched=rule_result.rules_matched,
            source="rules",
            confidence=None
        )

        logger.info(
            "classify_request",
            classify_response.to_dict()
        )

        return classify_response

    except Exception as e:
        logger.error("classify_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al clasificar: {str(e)}")


@router.get("/health")
async def health():
    """Verifica que el servicio y sus componentes estén operativos."""

    return     HealthResponseIn(
        status="ok",
        model_loaded=embedding_generator.model is not None,
        rules_count=len(rule_engine.rules),
    
    )


@router.post("/reload_rules")
async def reload_rules():
    """Recarga las reglas desde el YAML sin reiniciar el servicio."""
    try:
        rule_engine.reload()
        return ReloadResponseIn(
            success=True,
            rules_count=len(rule_engine.rules),
            message="Reglas recargadas correctamente.",
        )
    except Exception as e:
        logger.error("reload_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al recargar: {str(e)}")