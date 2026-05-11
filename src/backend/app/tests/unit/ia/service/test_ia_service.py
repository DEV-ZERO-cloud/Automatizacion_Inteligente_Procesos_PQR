"""
test_ia_service.py

Pruebas unitarias para el pipeline de clasificación de PQR.
Adaptadas al nuevo flujo donde classify:
  1. Ejecuta el pipeline IA (reglas + ML)
  2. Hace POST a /classifications/create con el resultado
  3. Retorna ok_response(data="Clasificado Correctamente")

La clasificación se dispara como BackgroundTask desde POST /pqrs.

Cubre:
  - _resolve_source
  - _get_pqr  (helper HTTP)
  - classify  (flujo completo, errores y casos de falla del modelo IA)
  - health
  - reload_rules / reload_models
  - trigger_training
  - Instancias lazy (singletons)

Ejecutar:
    pytest test_ia_service.py -v
"""

import pytest
import numpy as np
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# ── Importaciones del módulo bajo prueba ──────────────────────────────────────
from app.api.routes.ai_service.ai_service import (
    router,
    _resolve_source,
    get_rule_engine,
    get_embedding_generator,
    get_category_classifier,
    get_priority_classifier,
)

app = FastAPI()
app.include_router(router, prefix="/ai")


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
    r.tags = ["cobro duplicado", "facturación"]
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


def _build_mocks(
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
    mock_rule_engine = MagicMock()
    mock_rule_engine.evaluate.return_value = rule_result

    mock_generator = MagicMock()
    mock_generator.generate_one.return_value = embedding

    mock_cat_clf = MagicMock()
    mock_cat_clf.predict.return_value = (categoria, cat_conf)
    mock_cat_clf.is_ready.return_value = cat_ready

    mock_pri_clf = MagicMock()
    mock_pri_clf.predict.return_value = (prioridad, pri_conf)
    mock_pri_clf.is_ready.return_value = pri_ready

    return mock_rule_engine, mock_generator, mock_cat_clf, mock_pri_clf


# ── Helper: patches comunes para flujos completos ─────────────────────────────

def _base_classify_patches(mock_pqr, mock_re, mock_gen, mock_cat, mock_pri,
                            categoria_id=10, prioridad_id=3):
    """
    Retorna el context manager de patches necesarios para que classify()
    complete su flujo sin llamadas HTTP reales.
    Mockea _get_category, _get_priority y _post_classification.
    """
    return (
        patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
        patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
        patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
        patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
        patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
        patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
        patch("app.api.routes.ai_service.ai_service._get_category",
              new=AsyncMock(return_value=categoria_id)),
        patch("app.api.routes.ai_service.ai_service._get_priority",
              new=AsyncMock(return_value=prioridad_id)),
        patch("app.api.routes.ai_service.ai_service._post_classification",
              new=AsyncMock(return_value=True)),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 1. _resolve_source
# ══════════════════════════════════════════════════════════════════════════════

class TestResolveSource:

    def test_hybrid_reglas_y_ambos_clasificadores(self):
        assert _resolve_source(True, True, True) == "hybrid"

    def test_hybrid_reglas_y_solo_categoria(self):
        assert _resolve_source(True, True, False) == "hybrid"

    def test_hybrid_reglas_y_solo_prioridad(self):
        assert _resolve_source(True, False, True) == "hybrid"

    def test_rules_solo_reglas(self):
        assert _resolve_source(True, False, False) == "rules"

    def test_ml_solo_clasificadores(self):
        assert _resolve_source(False, True, True) == "ml"

    def test_ml_solo_categoria(self):
        assert _resolve_source(False, True, False) == "ml"

    def test_ml_solo_prioridad(self):
        assert _resolve_source(False, False, True) == "ml"

    def test_unavailable_nada_disponible(self):
        assert _resolve_source(False, False, False) == "unavailable"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Cálculo de confianza (lógica pura, sin HTTP)
# ══════════════════════════════════════════════════════════════════════════════

class TestConfianzaCalculo:

    def _calc(self, cat_conf, pri_conf):
        confidences = [c for c in [cat_conf, pri_conf] if c is not None]
        return round(sum(confidences) / len(confidences), 4) if confidences else None

    def test_promedio_ambas(self):
        assert self._calc(0.8, 0.6) == 0.7

    def test_solo_categoria(self):
        assert self._calc(0.9, None) == 0.9

    def test_solo_prioridad(self):
        assert self._calc(None, 0.7) == 0.7

    def test_ambas_none_retorna_none(self):
        assert self._calc(None, None) is None

    def test_confianza_baja_bajo_umbral(self):
        assert self._calc(0.4, 0.3) < 0.60

    def test_confianza_alta_sobre_umbral(self):
        assert self._calc(0.85, 0.75) >= 0.60

    def test_confianza_exactamente_en_umbral(self):
        assert self._calc(0.60, 0.60) == 0.60


# ══════════════════════════════════════════════════════════════════════════════
# 3. _get_pqr — helper HTTP
# ══════════════════════════════════════════════════════════════════════════════

class TestGetPqr:

    @pytest.mark.asyncio
    async def test_exitoso(self, mock_pqr):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": {"id": 1, "descripcion": "test"}}

        with patch("httpx.AsyncClient") as MockClient:
            client_inst = AsyncMock()
            client_inst.__aenter__ = AsyncMock(return_value=client_inst)
            client_inst.__aexit__ = AsyncMock(return_value=False)
            client_inst.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value = client_inst

            with patch("app.models.pqr.PQRCreate.from_dict", return_value=mock_pqr):
                from app.api.routes.ai_service.ai_service import _get_pqr
                result = await _get_pqr(pqr_id=1, token="tok")
                assert result.ID == 1

    @pytest.mark.asyncio
    async def test_pqr_no_existe_lanza_http_error(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock(status_code=404)
        )

        with patch("httpx.AsyncClient") as MockClient:
            client_inst = AsyncMock()
            client_inst.__aenter__ = AsyncMock(return_value=client_inst)
            client_inst.__aexit__ = AsyncMock(return_value=False)
            client_inst.get = AsyncMock(return_value=mock_resp)
            MockClient.return_value = client_inst

            from app.api.routes.ai_service.ai_service import _get_pqr
            with pytest.raises(httpx.HTTPStatusError):
                await _get_pqr(pqr_id=9999, token="tok")

    @pytest.mark.asyncio
    async def test_timeout_lanza_excepcion(self):
        with patch("httpx.AsyncClient") as MockClient:
            client_inst = AsyncMock()
            client_inst.__aenter__ = AsyncMock(return_value=client_inst)
            client_inst.__aexit__ = AsyncMock(return_value=False)
            client_inst.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            MockClient.return_value = client_inst

            from app.api.routes.ai_service.ai_service import _get_pqr
            with pytest.raises(httpx.TimeoutException):
                await _get_pqr(pqr_id=1, token="tok")

    @pytest.mark.asyncio
    async def test_servidor_caido_lanza_connect_error(self):
        with patch("httpx.AsyncClient") as MockClient:
            client_inst = AsyncMock()
            client_inst.__aenter__ = AsyncMock(return_value=client_inst)
            client_inst.__aexit__ = AsyncMock(return_value=False)
            client_inst.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
            MockClient.return_value = client_inst

            from app.api.routes.ai_service.ai_service import _get_pqr
            with pytest.raises(httpx.ConnectError):
                await _get_pqr(pqr_id=1, token="tok")


# ══════════════════════════════════════════════════════════════════════════════
# 4. classify — flujo exitoso
# Ahora classify termina guardando en BD y retorna ok_response.
# Verificamos que la respuesta sea exitosa y que los helpers HTTP se llamen.
# ══════════════════════════════════════════════════════════════════════════════

class TestClassifyFlujoExitoso:

    @pytest.mark.asyncio
    async def test_source_hybrid_con_area_y_ml(
        self, mock_pqr, mock_rule_result_con_area, embedding_fake
    ):
        """
        Flujo hybrid: reglas + ML. classify debe completar y retornar ok_response.
        """
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_con_area, embedding_fake
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            # El endpoint exitoso retorna ok_response con data="Clasificado Correctamente"
            assert result is not None
            # _post_classification debe haber sido llamado con los IDs correctos
            mock_post_clf.assert_called_once()
            call_kwargs = mock_post_clf.call_args
            assert call_kwargs.kwargs.get("category_id") == 10 or \
                   (call_kwargs.args and 10 in call_kwargs.args)

    @pytest.mark.asyncio
    async def test_source_ml_sin_reglas(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        Flujo ML puro (sin reglas). classify debe completar y llamar _post_classification.
        """
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result is not None
            mock_post_clf.assert_called_once()

    @pytest.mark.asyncio
    async def test_id_pqr_se_propaga_al_response(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        El pqr_id debe ser propagado a _post_classification como parte de classify_response.
        """
        mock_pqr.ID = 42
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake
        )
        mock_post_clf = AsyncMock(return_value=True)
        mock_get_cat = AsyncMock(return_value=10)
        mock_get_pri = AsyncMock(return_value=3)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=mock_get_cat),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=mock_get_pri),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=42, token="tok", current_user={"id": 1})

            assert result is not None
            # Verificar que classify_response.id == 42 se pasó a _post_classification
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg is not None
            assert classify_response_arg.id == 42


# ══════════════════════════════════════════════════════════════════════════════
# 5. classify — Análisis de Errores y Casos de Falla del Modelo IA
# En el nuevo flujo, cuando el pipeline IA falla o produce baja confianza,
# classify aún intenta guardar la clasificación (incluyendo requiere_revision=True).
# Los tests verifican que el flujo completa (con _post_classification mockeado)
# o que lanza HTTPException en casos de error real.
# ══════════════════════════════════════════════════════════════════════════════

class TestCasosFallaModeloIA:

    # ── 5.1 Confianza baja ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_confianza_baja_activa_requiere_revision(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """
        conf=0.35 < umbral=0.60 → requiere_revision=True en classify_response.
        classify debe completar igual (guardando con requiere_revision=True).
        """
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.35, pri_conf=0.35,
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            # El flujo completa — la revisión se registra en classify_response
            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.requiere_revision is True
            assert classify_response_arg.confianza < 0.60

    # ── 5.2 Confianza exactamente en el umbral ────────────────────────────────

    @pytest.mark.asyncio
    async def test_confianza_igual_al_umbral_no_requiere_revision(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """conf=0.60 == umbral → requiere_revision=False (no estrictamente menor)."""
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.60, pri_conf=0.60,
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.confianza == 0.60
            assert classify_response_arg.requiere_revision is False

    # ── 5.3 Modelos no entrenados ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_modelos_no_entrenados_source_rules_requiere_revision(
        self, mock_pqr, mock_rule_result_con_area, embedding_fake
    ):
        """Clasificadores no listos → source='rules', confianza=None, requiere_revision=True."""
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_con_area, embedding_fake,
            cat_ready=False, pri_ready=False,
            cat_conf=None, pri_conf=None,
            categoria=None, prioridad=None,
        )
        mock_cat.predict.return_value = (None, None)
        mock_pri.predict.return_value = (None, None)
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=None)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=None)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.source == "rules"
            assert classify_response_arg.confianza is None
            assert classify_response_arg.requiere_revision is True

    # ── 5.4 Solo un clasificador disponible ───────────────────────────────────

    @pytest.mark.asyncio
    async def test_solo_priority_classifier_no_listo(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """PriorityClassifier no listo → confianza solo de cat, requiere_revision=True."""
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.78, pri_conf=None, pri_ready=False,
        )
        mock_pri.predict.return_value = (None, None)
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=None)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.confianza == 0.78
            assert classify_response_arg.requiere_revision is True  # pri_clf no listo

    # ── 5.5 Texto vacío tras limpieza ─────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_texto_vacio_tras_limpieza_confianza_baja(
        self, mock_rule_result_sin_area, embedding_fake
    ):
        """clean_text devuelve '' → embedding pobre → confianza baja → requiere_revision=True."""
        pqr = MagicMock()
        pqr.ID = 5
        pqr.descripcion = "!!!???..."

        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.30, pri_conf=0.28,
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", return_value=""),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=5, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.requiere_revision is True
            assert classify_response_arg.confianza < 0.60

    # ── 5.6 Descripción muy corta (≤5 palabras) ───────────────────────────────

    @pytest.mark.asyncio
    async def test_descripcion_muy_corta_genera_confianza_baja(
        self, mock_rule_result_sin_area, embedding_fake
    ):
        """'Cobro no corresponde' → 3 palabras → confianza esperada baja."""
        pqr = MagicMock()
        pqr.ID = 6
        pqr.descripcion = "Cobro no corresponde"

        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            pqr, mock_rule_result_sin_area, embedding_fake,
            cat_conf=0.41, pri_conf=0.38,
        )
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=10)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=3)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=6, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.confianza < 0.60
            assert classify_response_arg.requiere_revision is True

    # ── 5.7 Fallo del generador de embeddings ─────────────────────────────────

    @pytest.mark.asyncio
    async def test_fallo_generador_embeddings_retorna_500(
        self, mock_pqr, mock_rule_result_sin_area
    ):
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

    # ── 5.8 Clasificador no ajustado (predict lanza ValueError) ───────────────

    @pytest.mark.asyncio
    async def test_category_classifier_no_ajustado_retorna_500(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        mock_re = MagicMock()
        mock_re.evaluate.return_value = mock_rule_result_sin_area
        mock_gen = MagicMock()
        mock_gen.generate_one.return_value = embedding_fake
        mock_cat = MagicMock()
        mock_cat.predict.side_effect = ValueError("Model not fitted yet")
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

    # ── 5.9 PQR no encontrada (HTTP 404) ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_pqr_no_encontrada_retorna_500(self):
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.HTTPStatusError(
                    "404", request=MagicMock(), response=MagicMock(status_code=404)
                ))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=9999, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    # ── 5.10 Timeout al obtener la PQR ────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_timeout_get_pqr_retorna_500(self):
        with (
            patch(
                "app.api.routes.ai_service.ai_service._get_pqr",
                new=AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            ),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
        ):
            from app.api.routes.ai_service.ai_service import classify
            with pytest.raises(HTTPException) as exc:
                await classify(pqr_id=1, token="tok", current_user={"id": 1})
            assert exc.value.status_code == 500

    # ── 5.11 Motor de reglas lanza excepción ──────────────────────────────────

    @pytest.mark.asyncio
    async def test_rule_engine_falla_retorna_500(
        self, mock_pqr, embedding_fake
    ):
        mock_re = MagicMock()
        mock_re.evaluate.side_effect = Exception("YAML corrupto")

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

    # ── 5.12 source=unavailable cuando nada está listo ────────────────────────

    @pytest.mark.asyncio
    async def test_source_unavailable_sin_reglas_ni_ml(
        self, mock_pqr, mock_rule_result_sin_area, embedding_fake
    ):
        """Sin reglas ni ML listo → source='unavailable', requiere_revision=True."""
        mock_re, mock_gen, mock_cat, mock_pri = _build_mocks(
            mock_pqr, mock_rule_result_sin_area, embedding_fake,
            cat_ready=False, pri_ready=False,
            cat_conf=None, pri_conf=None,
            categoria=None, prioridad=None,
        )
        mock_cat.predict.return_value = (None, None)
        mock_pri.predict.return_value = (None, None)
        mock_post_clf = AsyncMock(return_value=True)

        with (
            patch("app.api.routes.ai_service.ai_service._get_pqr", new=AsyncMock(return_value=mock_pqr)),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
            patch("app.api.routes.ai_service.ai_service.get_current_user", return_value={"id": 1}),
            patch("app.ia.preprocessing.cleaner.clean_text", side_effect=lambda x: x),
            patch("app.api.routes.ai_service.ai_service._get_category", new=AsyncMock(return_value=None)),
            patch("app.api.routes.ai_service.ai_service._get_priority", new=AsyncMock(return_value=None)),
            patch("app.api.routes.ai_service.ai_service._post_classification", new=mock_post_clf),
        ):
            from app.api.routes.ai_service.ai_service import classify
            result = await classify(pqr_id=1, token="tok", current_user={"id": 1})

            assert result is not None
            call_kwargs = mock_post_clf.call_args
            classify_response_arg = call_kwargs.kwargs.get("classify_response") or \
                                    (call_kwargs.args[0] if call_kwargs.args else None)
            assert classify_response_arg.source == "unavailable"
            assert classify_response_arg.requiere_revision is True


# ══════════════════════════════════════════════════════════════════════════════
# 6. /health
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthEndpoint:

    @pytest.mark.asyncio
    async def test_todos_los_componentes_ok(self):
        mock_gen = MagicMock()
        mock_gen._model = MagicMock()
        mock_re = MagicMock()
        mock_re.rules = [1, 2, 3]
        mock_cat = MagicMock()
        mock_cat.is_ready.return_value = True
        mock_pri = MagicMock()
        mock_pri.is_ready.return_value = True

        with (
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
        ):
            from app.api.routes.ai_service.ai_service import health
            result = await health()
            assert result.status == "ok"
            assert result.model_loaded is True
            assert result.rules_count == 3
            assert result.ml_status["category_ready"] is True
            assert result.ml_status["priority_ready"] is True

    @pytest.mark.asyncio
    async def test_modelo_no_cargado(self):
        mock_gen = MagicMock()
        mock_gen._model = None
        mock_re = MagicMock()
        mock_re.rules = []
        mock_cat = MagicMock()
        mock_cat.is_ready.return_value = False
        mock_pri = MagicMock()
        mock_pri.is_ready.return_value = False

        with (
            patch("app.api.routes.ai_service.ai_service.get_embedding_generator", return_value=mock_gen),
            patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
        ):
            from app.api.routes.ai_service.ai_service import health
            result = await health()
            assert result.model_loaded is False
            assert result.ml_status["category_ready"] is False
            assert result.ml_status["priority_ready"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 7. /reload_rules  y  /reload_models
# ══════════════════════════════════════════════════════════════════════════════

class TestReloadEndpoints:

    @pytest.mark.asyncio
    async def test_reload_rules_exitoso(self):
        mock_re = MagicMock()
        mock_re.rules = [1, 2, 3, 4, 5]
        mock_re.reload = MagicMock()

        with patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re):
            from app.api.routes.ai_service.ai_service import reload_rules
            result = await reload_rules()
            assert result.success is True
            assert result.rules_count == 5
            mock_re.reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_rules_yaml_no_encontrado_retorna_500(self):
        mock_re = MagicMock()
        mock_re.reload.side_effect = FileNotFoundError("rules.yaml no encontrado")

        with patch("app.api.routes.ai_service.ai_service.get_rule_engine", return_value=mock_re):
            from app.api.routes.ai_service.ai_service import reload_rules
            with pytest.raises(HTTPException) as exc:
                await reload_rules()
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_reload_models_exitoso(self):
        mock_cat = MagicMock()
        mock_cat.is_ready.return_value = True
        mock_pri = MagicMock()
        mock_pri.is_ready.return_value = True

        with (
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
        ):
            from app.api.routes.ai_service.ai_service import reload_models
            result = await reload_models()
            assert result["success"] is True
            assert result["models_ready"]["category"] is True
            assert result["models_ready"]["priority"] is True

    @pytest.mark.asyncio
    async def test_reload_models_reinicia_instancias_globales(self):
        """Después de reload_models las instancias globales deben ser None antes de recargar."""
        import app.api.routes.ai_service.ai_service as svc
        svc._category_clf = MagicMock()
        svc._priority_clf = MagicMock()

        mock_cat = MagicMock()
        mock_cat.is_ready.return_value = True
        mock_pri = MagicMock()
        mock_pri.is_ready.return_value = True

        def get_cat_side_effect():
            svc._category_clf = mock_cat
            return mock_cat

        def get_pri_side_effect():
            svc._priority_clf = mock_pri
            return mock_pri

        with (
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", side_effect=get_cat_side_effect),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", side_effect=get_pri_side_effect),
        ):
            from app.api.routes.ai_service.ai_service import reload_models
            await reload_models()
            assert svc._category_clf is not None
            assert svc._priority_clf is not None


# ══════════════════════════════════════════════════════════════════════════════
# 8. /train
# ══════════════════════════════════════════════════════════════════════════════

class TestTrainEndpoint:

    @pytest.mark.asyncio
    async def test_entrenamiento_exitoso(self):
        mock_result = {
            "status": "done",
            "categoria": {"accuracy": 0.91},
            "prioridad": {"accuracy": 0.87},
        }
        mock_cat = MagicMock()
        mock_pri = MagicMock()

        with (
            patch("app.ia.scripts.train_classifiers.run_training", return_value=mock_result),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat),
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri),
        ):
            from app.api.routes.ai_service.ai_service import trigger_training
            result = await trigger_training(csv_path="/data/pqr.csv", target="all", min_per_class=5)
            assert result["status"] == "done"

    @pytest.mark.asyncio
    async def test_csv_no_encontrado_retorna_404(self):
        with patch("app.ia.scripts.train_classifiers.run_training", side_effect=FileNotFoundError("CSV no encontrado")):
            from app.api.routes.ai_service.ai_service import trigger_training
            with pytest.raises(HTTPException) as exc:
                await trigger_training(csv_path="/no/existe.csv")
            assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_clases_insuficientes_retorna_422(self):
        with patch("app.ia.scripts.train_classifiers.run_training", side_effect=ValueError("min_per_class no alcanzado")):
            from app.api.routes.ai_service.ai_service import trigger_training
            with pytest.raises(HTTPException) as exc:
                await trigger_training(csv_path="/data/pqr.csv", min_per_class=100)
            assert exc.value.status_code == 422

    @pytest.mark.asyncio
    async def test_error_generico_retorna_500(self):
        with patch("app.ia.scripts.train_classifiers.run_training", side_effect=RuntimeError("Error inesperado")):
            from app.api.routes.ai_service.ai_service import trigger_training
            with pytest.raises(HTTPException) as exc:
                await trigger_training(csv_path="/data/pqr.csv")
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_entrenamiento_exitoso_recarga_modelos(self):
        """Si status=done los modelos deben ser recargados automáticamente."""
        mock_result = {"status": "done"}
        mock_cat = MagicMock()
        mock_pri = MagicMock()

        with (
            patch("app.ia.scripts.train_classifiers.run_training", return_value=mock_result),
            patch("app.api.routes.ai_service.ai_service.get_category_classifier", return_value=mock_cat) as p_cat,
            patch("app.api.routes.ai_service.ai_service.get_priority_classifier", return_value=mock_pri) as p_pri,
        ):
            from app.api.routes.ai_service.ai_service import trigger_training
            await trigger_training(csv_path="/data/pqr.csv")
            p_cat.assert_called()
            p_pri.assert_called()


# ══════════════════════════════════════════════════════════════════════════════
# 9. Instancias lazy (singletons)
# ══════════════════════════════════════════════════════════════════════════════

class TestInstanciasLazy:

    def test_rule_engine_es_singleton(self):
        import app.api.routes.ai_service.ai_service as svc
        svc._rule_engine = None
        with patch("app.api.routes.ai_service.ai_service.RuleEngine") as MockRE:
            MockRE.return_value = MagicMock()
            r1 = get_rule_engine()
            r2 = get_rule_engine()
            assert r1 is r2
            MockRE.assert_called_once()

    def test_embedding_generator_es_singleton(self):
        import app.api.routes.ai_service.ai_service as svc
        svc._embedding_generator = None
        with patch("app.api.routes.ai_service.ai_service.EmbeddingGenerator") as MockEG:
            MockEG.return_value = MagicMock()
            g1 = get_embedding_generator()
            g2 = get_embedding_generator()
            assert g1 is g2
            MockEG.assert_called_once()

    def test_category_classifier_llama_load(self):
        import app.api.routes.ai_service.ai_service as svc
        svc._category_clf = None
        mock_clf = MagicMock()
        with patch("app.api.routes.ai_service.ai_service.CategoryClassifier", return_value=mock_clf):
            get_category_classifier()
            mock_clf.load.assert_called_once()

    def test_priority_classifier_llama_load(self):
        import app.api.routes.ai_service.ai_service as svc
        svc._priority_clf = None
        mock_clf = MagicMock()
        with patch("app.api.routes.ai_service.ai_service.PriorityClassifier", return_value=mock_clf):
            get_priority_classifier()
            mock_clf.load.assert_called_once()