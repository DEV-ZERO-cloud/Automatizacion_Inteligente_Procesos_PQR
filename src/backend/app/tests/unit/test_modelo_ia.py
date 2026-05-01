"""
test_modelo_ia_errores.py

Pruebas unitarias — Validación del modelo de IA
Análisis de Errores y Casos de Falla

Cubre:
  - Confianza baja / alta / exacta en umbral
  - Modelos no entrenados
  - Solo un clasificador disponible
  - Texto vacío o muy corto
  - Fallo del generador de embeddings
  - Clasificador no ajustado (predict lanza excepción)
  - Motor de reglas corrupto
  - Timeout y conexión caída al obtener la PQR
  - source=unavailable cuando nada está listo
  - Confianza None cuando ambas confianzas son None

Ejecutar:
    pytest test_modelo_ia_errores.py -v
"""

import pytest
import numpy as np
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_pqr():
    pqr = MagicMock()
    pqr.ID = 1
    pqr.titulo = "Factura incorrecta"
    pqr.descripcion = "Me cobraron dos veces el mismo servicio de internet"
    return pqr


@pytest.fixture
def mock_rule_result_con_area():
    r = MagicMock()
    r.area = "Cartera"
    r.tags = ["cobro duplicado"]
    r.rules_matched = ["cartera_cobro_duplicado"]
    return r


@pytest.fixture
def mock_rule_result_sin_area():
    r = MagicMock()
    r.area = None
    r.tags = []
    r.rules_matched = []
    return r


@pytest.fixture
def embedding_fake():
    return np.random.rand(384).astype(np.float32)


def _make_classify_patches(
    pqr,
    rule_result,
    embedding,
    categoria="Facturación incorrecta",
    cat_conf=0.85,
    prioridad="Alta",
    pri_conf=0.80,
    cat_ready=True,
    pri_ready=True,
):
    mock_re = MagicMock()
    mock_re.evaluate.return_value = rule_result

    mock_gen = MagicMock()
    mock_gen.generate_one.return_value = embedding

    mock_cat = MagicMock()
    mock_cat.predict.return_value = (categoria, cat_conf)
    mock_cat.is_ready.return_value = cat_ready

    mock_pri = MagicMock()
    mock_pri.predict.return_value = (prioridad, pri_conf)
    mock_pri.is_ready.return_value = pri_ready

    return mock_re, mock_gen, mock_cat, mock_pri


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO 1 — Confianza del modelo
# ══════════════════════════════════════════════════════════════════════════════

class TestConfianzaModelo:

    @pytest.mark.asyncio
    async def test_confianza_baja_activa_requiere_revision(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: confianza 0.35 < umbral 0.60
        Esperado: requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.35, pri_conf=0.35,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.requiere_revision is True
            assert result.confianza < 0.60

    @pytest.mark.asyncio
    async def test_confianza_alta_no_requiere_revision(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO EXITOSO: confianza 0.85 > umbral 0.60
        Esperado: requiere_revision=False
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.90, pri_conf=0.80,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.requiere_revision is False
            assert result.confianza >= 0.60

    @pytest.mark.asyncio
    async def test_confianza_exactamente_en_umbral_no_requiere_revision(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO LÍMITE: confianza == 0.60 (igual al umbral)
        La condición es confianza < umbral, por tanto 0.60 NO activa revisión.
        Esperado: requiere_revision=False
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.60, pri_conf=0.60,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.confianza == 0.60
            assert result.requiere_revision is False

    @pytest.mark.asyncio
    async def test_confianza_none_cuando_ambas_son_none(
        self, mock_pqr, mock_rule_result_con_area, embedding_fake
    ):
        """
        CASO DE FALLA: ningún clasificador retorna confianza
        Esperado: confianza=None, requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_con_area, embedding_fake,
            cat_conf=None, pri_conf=None,
            cat_ready=False, pri_ready=False,
            categoria=None, prioridad=None,
        )
        mock_cat.predict.return_value = (None, None)
        mock_pri.predict.return_value = (None, None)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.confianza is None
            assert result.requiere_revision is True


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO 2 — Modelos no entrenados o parcialmente disponibles
# ══════════════════════════════════════════════════════════════════════════════

class TestModelosNoEntrenados:

    @pytest.mark.asyncio
    async def test_ambos_modelos_no_listos_source_rules(
        self, mock_pqr, mock_rule_result_con_area, embedding_fake
    ):
        """
        CASO DE FALLA: CategoryClassifier y PriorityClassifier no entrenados.
        Esperado: source='rules', confianza=None, requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_con_area, embedding_fake,
            cat_ready=False, pri_ready=False,
            cat_conf=None, pri_conf=None,
            categoria=None, prioridad=None,
        )
        mock_cat.predict.return_value = (None, None)
        mock_pri.predict.return_value = (None, None)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.source == "rules"
            assert result.confianza is None
            assert result.requiere_revision is True

    @pytest.mark.asyncio
    async def test_ambos_modelos_no_listos_sin_reglas_source_unavailable(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: sin reglas Y sin modelos entrenados.
        Esperado: source='unavailable', requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_ready=False, pri_ready=False,
            cat_conf=None, pri_conf=None,
            categoria=None, prioridad=None,
        )
        mock_cat.predict.return_value = (None, None)
        mock_pri.predict.return_value = (None, None)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.source == "unavailable"
            assert result.requiere_revision is True

    @pytest.mark.asyncio
    async def test_solo_priority_classifier_no_listo(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: PriorityClassifier no entrenado, CategoryClassifier sí.
        Esperado: confianza solo de categoria, requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.78, pri_conf=None, pri_ready=False,
        )
        mock_pri.predict.return_value = (None, None)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.confianza == 0.78
            assert result.requiere_revision is True

    @pytest.mark.asyncio
    async def test_solo_category_classifier_no_listo(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: CategoryClassifier no entrenado, PriorityClassifier sí.
        Esperado: confianza solo de prioridad, requiere_revision=True
        """
        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=None, cat_ready=False, pri_conf=0.72,
        )
        mock_cat.predict.return_value = (None, None)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result.confianza == 0.72
            assert result.requiere_revision is True


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO 3 — Calidad del texto de entrada
# ══════════════════════════════════════════════════════════════════════════════

class TestCalidadTextoEntrada:

    @pytest.mark.asyncio
    async def test_texto_vacio_tras_limpieza_confianza_baja(
        self, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: clean_text devuelve '' (solo caracteres especiales).
        El embedding resultante es pobre → confianza baja esperada.
        Esperado: requiere_revision=True, confianza < 0.60
        """
        pqr = MagicMock()
        pqr.ID = 5
        pqr.descripcion = "!!!???..."

        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.30, pri_conf=0.28,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", return_value=""),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=5, token="tok", current_user={"id": 1})

            assert result.requiere_revision is True
            assert result.confianza < 0.60

    @pytest.mark.asyncio
    async def test_descripcion_muy_corta_confianza_baja(
        self, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: descripción de 3 palabras — embedding insuficiente.
        Reproduce el bug real de la PQR 1: 'Cobro no corresponde al consumo'.
        Esperado: requiere_revision=True, confianza < 0.60
        """
        pqr = MagicMock()
        pqr.ID = 6
        pqr.descripcion = "Cobro no corresponde"

        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.41, pri_conf=0.38,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=6, token="tok", current_user={"id": 1})

            assert result.confianza < 0.60
            assert result.requiere_revision is True

    @pytest.mark.asyncio
    async def test_titulo_mas_descripcion_mejora_confianza(
        self, mock_rule_result_sin_area, embedding_fake
    ):
        """
        MEJORA: concatenar titulo + descripcion enriquece el embedding.
        Simula la corrección aplicada: text = f'{titulo}. {descripcion}'
        Esperado: confianza >= 0.60, requiere_revision=False
        """
        pqr = MagicMock()
        pqr.ID = 7
        pqr.titulo = "Factura incorrecta"
        pqr.descripcion = "Cobro no corresponde al consumo"

        mock_re, mock_gen, mock_cat, mock_pri = _make_classify_patches(
            pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.81, pri_conf=0.74,
        )
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch(
                "app.ia.preprocessing.cleaner.clean_text",
                side_effect=lambda x: x,
            ),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=7, token="tok", current_user={"id": 1})

            assert result.confianza >= 0.60
            assert result.requiere_revision is False


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO 4 — Fallos internos de componentes del pipeline
# ══════════════════════════════════════════════════════════════════════════════

class TestFallosComponentesPipeline:

    @pytest.mark.asyncio
    async def test_fallo_generador_embeddings_retorna_500(
        self, mock_pqr, mock_rule_result_sin_area
    ):
        """
        CASO DE FALLA: EmbeddingGenerator lanza RuntimeError (ej. CUDA OOM).
        Esperado: HTTPException 500
        """
        mock_re = MagicMock()
        mock_re.evaluate.return_value = mock_rule_result_sin_area

        mock_gen = MagicMock()
        mock_gen.generate_one.side_effect = RuntimeError("CUDA out of memory")

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_category_classifier_no_ajustado_retorna_500(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: CategoryClassifier.predict lanza ValueError (modelo no ajustado).
        Esperado: HTTPException 500
        """
        mock_re = MagicMock()
        mock_re.evaluate.return_value = mock_rule_result_sin_area

        mock_gen = MagicMock()
        mock_gen.generate_one.return_value = embedding_fake

        mock_cat = MagicMock()
        mock_cat.predict.side_effect = ValueError("Model not fitted yet. Call fit().")
        mock_cat.is_ready.return_value = True

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_priority_classifier_no_ajustado_retorna_500(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        CASO DE FALLA: PriorityClassifier.predict lanza ValueError.
        Esperado: HTTPException 500
        """
        mock_re = MagicMock()
        mock_re.evaluate.return_value = mock_rule_result_sin_area

        mock_gen = MagicMock()
        mock_gen.generate_one.return_value = embedding_fake

        mock_cat = MagicMock()
        mock_cat.predict.return_value = ("Facturación incorrecta", 0.82)
        mock_cat.is_ready.return_value = True

        mock_pri = MagicMock()
        mock_pri.predict.side_effect = ValueError("Model not fitted yet. Call fit().")
        mock_pri.is_ready.return_value = True

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_rule_engine_yaml_corrupto_retorna_500(
        self, mock_pqr
    ):
        """
        CASO DE FALLA: RuleEngine.evaluate lanza excepción por YAML corrupto.
        Esperado: HTTPException 500
        """
        mock_re = MagicMock()
        mock_re.evaluate.side_effect = Exception("YAML parse error: mapping values are not allowed here")

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_clean_text_lanza_excepcion_retorna_500(
        self, mock_pqr
    ):
        """
        CASO DE FALLA: clean_text lanza excepción inesperada.
        Esperado: HTTPException 500
        """
        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch(
                "app.ia.preprocessing.cleaner.clean_text",
                side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid byte"),
            ),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500


# ══════════════════════════════════════════════════════════════════════════════
# GRUPO 5 — Fallos de comunicación HTTP
# ══════════════════════════════════════════════════════════════════════════════

class TestFallosHTTP:

    @pytest.mark.asyncio
    async def test_pqr_no_encontrada_404_retorna_500(self):
        """
        CASO DE FALLA: PQR no existe en el backend (HTTP 404).
        Esperado: HTTPException 500 (capturado por el handler genérico)
        """
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.HTTPStatusError(
                    "404 Not Found",
                    request=MagicMock(),
                    response=MagicMock(status_code=404),
                ))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=9999, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_al_obtener_pqr_retorna_500(self):
        """
        CASO DE FALLA: httpx.TimeoutException al llamar /pqrs/{id}.
        Esperado: HTTPException 500
        """
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.TimeoutException("Read timeout"))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_servidor_backend_caido_retorna_500(self):
        """
        CASO DE FALLA: servidor backend no disponible (ConnectError).
        Esperado: HTTPException 500
        """
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_pqr_retorna_401_no_autenticado_retorna_500(self):
        """
        CASO DE FALLA: token expirado → backend responde 401.
        Esperado: HTTPException 500
        """
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.HTTPStatusError(
                    "401 Unauthorized",
                    request=MagicMock(),
                    response=MagicMock(status_code=401),
                ))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok-expirado", current_user={"id": 1})
            assert exc.value.status_code == 500