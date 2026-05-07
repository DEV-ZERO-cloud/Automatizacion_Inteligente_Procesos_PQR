"""
Herramienta de Evaluación del Agente IA – Sistema PQR
======================================================
Evalúa el componente de clasificación automática contra validación humana experta.

Flujo de evaluación:
  1. POST /pqrs          → Crea cada PQR en el sistema
  2. POST /classify/{id} → Clasifica cada PQR y obtiene predicción
  3. Compara predicción vs ground truth del JSON

Métricas evaluadas:
  1. Precisión de clasificación     → Meta: ≥ 70%
  2. Tiempo de procesamiento        → Meta: ≤ 30 segundos por solicitud
  3. Tiempo de validación humana    → Meta: < 10 segundos por caso
  4. Capacidad de carga             → Meta: ≥ 3.000 solicitudes/mes sin degradación
  5. Métricas ML por campo          → Accuracy, Precision, Recall (TPR), F1-Score
                                       (macro y weighted) + Matriz de Confusión

Uso:
  python ai_evaluator.py --host http://localhost:8000 --mode interactive
  python ai_evaluator.py --host http://localhost:8000 --mode batch --file casos_muestra.json
  python ai_evaluator.py --host http://localhost:8000 --mode load_test
  python ai_evaluator.py --host http://localhost:8000 --mode report
  python ai_evaluator.py --host http://localhost:8000 --mode validate
"""

import argparse
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# ── Configuración ──────────────────────────────────────────────────────────────
BASE_URL           = "http://localhost:8000"
CREATE_PQR_ENDPOINT = "/pqrs"
CLASSIFY_ENDPOINT  = "/classifications/pqr/{pqr_id}"
CATEGORY_ENDPOINT  = "/categories/"
PRIORITY_ENDPOINT = "/priorities/"
HEALTH_ENDPOINT    = "/health"

# Valores fijos requeridos por la API al crear PQRs
DEFAULT_AREA_ID       = 1
DEFAULT_USUARIO_ID    = 1
DEFAULT_OPERADOR_ID   = 1
DEFAULT_SUPERVISOR_ID = 1
DEFAULT_ESTADO           = "pendiente"
DEFAULT_CLASIFICACION_ID = None  # None = omitido del payload (FK nullable). Usa --clasificacion_id si la columna es NOT NULL.

# Metas de desempeño (SLAs)
SLA_PRECISION_PCT   = 70.0    # % mínimo de aciertos
SLA_PROCESS_MS      = 30_000  # ms máximo por solicitud
SLA_VALIDATION_S    = 10.0    # segundos máximos de validación humana
SLA_MONTHLY_VOLUME  = 3_000   # solicitudes/mes mínimas sin degradación

RESULTS_FILE = Path("eval_results.json")

# Paleta de colores para terminal
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
CHECK  = "✓"
CROSS  = "✗"
ARROW  = "→"

# Valores aceptados por los CHECK constraints de la base de datos:
#   tipo  → ARRAY['peticion', 'queja', 'reclamo']
#   estado → ARRAY['pendiente', 'en_proceso', 'resuelta', 'cerrada']

# Mapeo de categorías JSON → tipo aceptado por la API
# 'sugerencia' NO existe en el CHECK de la BD → se envía como 'peticion'
CATEGORY_TO_TIPO = {
    "Facturacion":            "peticion",
    "Tecnica":                "queja",
    "Técnica":                "queja",
    "Servicio":               "queja",
    "Atención al cliente":    "queja",
    "Cambio de datos":        "peticion",
    "Cancelación de pedido":  "reclamo",
    "Devolución y reembolso": "reclamo",
    "Entrega tardía":         "queja",
    "Estado de pedido":       "peticion",
    "Experiencia de compra":  "peticion",
    "Factura y documentos":   "peticion",
    "Facturación incorrecta": "reclamo",
    "Fraude / seguridad":     "reclamo",
    "Garantía":               "peticion",
    "Información de producto":"peticion",
    "Logística y entrega":    "queja",
    "Pedido no entregado":    "reclamo",
    "Producto defectuoso":    "reclamo",
    "Producto incorrecto":    "reclamo",
    "Programa de fidelización":"peticion",
    "Publicidad engañosa":    "reclamo",
}
# Normalización de categorías: nombre en casos_muestra.json → nombre canónico en minúscula
# que coincide con lo que devuelve la API en predicted_categoria.
# Regla: simplemente lower() del nombre de la tabla `categorias`.
CATEGORY_NORMALIZATION = {
    "Facturacion":            "facturacion",
    "Tecnica":                "tecnica",
    "Técnica":                "tecnica",
    "Servicio":               "servicio",
    "Atención al cliente":    "atención al cliente",
    "Cambio de datos":        "cambio de datos",
    "Cancelación de pedido":  "cancelación de pedido",
    "Devolución y reembolso": "devolución y reembolso",
    "Entrega tardía":         "entrega tardía",
    "Estado de pedido":       "estado de pedido",
    "Experiencia de compra":  "experiencia de compra",
    "Factura y documentos":   "factura y documentos",
    "Facturación incorrecta": "facturación incorrecta",
    "Fraude / seguridad":     "fraude / seguridad",
    "Garantía":               "garantía",
    "Información de producto":"información de producto",
    "Logística y entrega":    "logística y entrega",
    "Pedido no entregado":    "pedido no entregado",
    "Producto defectuoso":    "producto defectuoso",
    "Producto incorrecto":    "producto incorrecto",
    "Programa de fidelización":"programa de fidelización",
    "Publicidad engañosa":    "publicidad engañosa",
}
VALID_API_TIPOS   = {"peticion", "queja", "reclamo"}
VALID_API_ESTADOS = {"pendiente", "en_proceso", "resuelta", "cerrada"}

# Campos de comparación que devuelve /classify
CLASSIFY_FIELDS = {
    "categoria":   "categoria",
    "prioridad":   "prioridad",
    "tags":        "tags",
    "area":        "area",
    "source":      "source",
    "confianza":   "confianza",
    "rules_matched": "rules_matched",
    "requiere_revision": "requiere_revision",
}


# ──────────────────────────────────────────────────────────────────────────────
# Validación del archivo de casos
# ──────────────────────────────────────────────────────────────────────────────
VALID_CATEGORIES = {
    "Facturacion",
    "Tecnica",
    "Técnica",
    "Servicio",
    "Atención al cliente",
    "Cambio de datos",
    "Cancelación de pedido",
    "Devolución y reembolso",
    "Entrega tardía",
    "Estado de pedido",
    "Experiencia de compra",
    "Factura y documentos",
    "Facturación incorrecta",
    "Fraude / seguridad",
    "Garantía",
    "Información de producto",
    "Logística y entrega",
    "Pedido no entregado",
    "Producto defectuoso",
    "Producto incorrecto",
    "Programa de fidelización",
    "Publicidad engañosa",
}
VALID_PRIORITIES = {"alta", "media", "baja", "urgente", "crítico", "critico"}

# Normalización de prioridades: unifica variantes que devuelve la API al nivel
# canónico de la tabla `prioridades`. La API puede devolver "crítica" (femenino)
# o "critica" (sin tilde) que deben mapearse a "crítico".
PRIORITY_NORMALIZATION = {
    "critica":  "crítico",
    "crítica":  "crítico",
    "critico":  "crítico",
    "crítico":  "crítico",
    "urgente":  "urgente",
    "alta":     "alta",
    "media":    "media",
    "baja":     "baja",
}
def validate_cases(cases: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Valida los casos del JSON de entrada.
    Retorna (casos_válidos, lista_de_errores).
    """
    valid   = []
    errors  = []
    seen_ids = set()

    for idx, case in enumerate(cases):
        loc = f"Caso índice {idx}"
        ok  = True

        # pqr_id
        pqr_id = case.get("pqr_id")
        if pqr_id is None:
            errors.append(f"{loc}: falta 'pqr_id'")
            ok = False
        elif not isinstance(pqr_id, int) or pqr_id <= 0:
            errors.append(f"{loc}: 'pqr_id' debe ser entero positivo (valor: {pqr_id!r})")
            ok = False
        elif pqr_id in seen_ids:
            errors.append(f"{loc}: 'pqr_id' duplicado ({pqr_id})")
            ok = False
        else:
            seen_ids.add(pqr_id)
            loc = f"PQR #{pqr_id}"

        # text
        text = case.get("text", "")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{loc}: 'text' vacío o no es cadena")
            ok = False
        elif len(text.strip()) < 10:
            errors.append(f"{loc}: 'text' demasiado corto (mínimo 10 caracteres)")
            ok = False

        # category
        cat = case.get("category", "")
        if cat not in VALID_CATEGORIES:
            errors.append(
                f"{loc}: 'category' inválida ({cat!r}). "
                f"Válidas: {sorted(VALID_CATEGORIES)}"
            )
            ok = False

        # priority
        pri = case.get("priority", "")
        if pri not in VALID_PRIORITIES:
            errors.append(
                f"{loc}: 'priority' inválida ({pri!r}). "
                f"Válidas: {sorted(VALID_PRIORITIES)}"
            )
            ok = False

        if ok:
            valid.append(case)

    return valid, errors


# ──────────────────────────────────────────────────────────────────────────────
# Estructuras de datos
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CaseResult:
    """Resultado de un caso evaluado."""
    pqr_id: int
    text: str

    # ID asignado por el sistema tras crear el PQR
    system_pqr_id:      Optional[int]   = None
    pqr_created:        bool            = False
    pqr_creation_ms:    Optional[float] = None

    # Predicción del agente (/classify)
    predicted_categoria:  Optional[str]   = None
    predicted_prioridad:  Optional[str]   = None
    predicted_prioridad_id: Optional[int] = None
    predicted_categoria_id: Optional[int] = None
    predicted_tags:       list            = field(default_factory=list)
    predicted_area:       Optional[str]   = None
    confianza:            Optional[float] = None
    source:               Optional[str]   = None
    rules_matched:        list            = field(default_factory=list)
    requiere_revision:    Optional[bool]  = None
    processing_ms:        Optional[float] = None

    # Ground truth del JSON
    expert_category:    Optional[str] = None
    expert_priority:    Optional[str] = None
    validation_seconds: Optional[float] = None

    # Veredicto
    category_correct:   Optional[bool] = None
    priority_correct:   Optional[bool] = None
    both_correct:       Optional[bool] = None
    timestamp:          str  = field(default_factory=lambda: datetime.now().isoformat())
    error:              Optional[str] = None


@dataclass
class LoadTestResult:
    """Resultado de prueba de carga."""
    n_requests:         int   = 0
    total_ms:           float = 0.0
    avg_ms:             float = 0.0
    p50_ms:             float = 0.0
    p95_ms:             float = 0.0
    p99_ms:             float = 0.0
    max_ms:             float = 0.0
    min_ms:             float = 0.0
    errors:             int   = 0
    projected_monthly:  int   = 0
    timestamp:          str   = field(default_factory=lambda: datetime.now().isoformat())


# ──────────────────────────────────────────────────────────────────────────────
# Funciones auxiliares
# ──────────────────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗
║        EVALUADOR DE AGENTE IA – SISTEMA PQR              ║
║        Validación con Experto Humano                     ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")


def sla_badge(value, threshold, higher_is_better=True) -> str:
    ok = (value >= threshold) if higher_is_better else (value <= threshold)
    icon  = CHECK if ok else CROSS
    color = GREEN if ok else RED
    return f"{color}{BOLD}[{icon} SLA]{RESET}"


def fmt_ms(ms: float) -> str:
    return f"{ms:,.1f} ms" if ms < 1000 else f"{ms/1000:,.2f} s"


# ── Creación de PQR ────────────────────────────────────────────────────────────

def build_pqr_payload(case: dict, clasificacion_id=None) -> dict:
    """
    Construye el payload para POST /pqrs.
    clasificacion_id se omite del payload cuando es None (columna nullable).
    Si la columna es NOT NULL, pasa un ID válido via --clasificacion_id.
    """
    tipo = CATEGORY_TO_TIPO.get(case.get("category"), "reclamo")
    now  = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "titulo":        case["text"][:120].strip(),
        "descripcion":   case["text"].strip(),
        "tipo":          tipo,
        "estado":        DEFAULT_ESTADO,
        "area_id":       DEFAULT_AREA_ID,
        "usuario_id":    DEFAULT_USUARIO_ID,
        "operador_id":   DEFAULT_OPERADOR_ID,
        "supervisor_id": DEFAULT_SUPERVISOR_ID,
        "created_at":    now,
        "updated_at":    now,
    }
    # Solo incluir clasificacion_id si se provee un valor válido
    # (evita FK violation cuando clasificacion_id=0 no existe en tabla clasificaciones)
    effective = clasificacion_id if clasificacion_id is not None else DEFAULT_CLASIFICACION_ID
    if effective is not None:
        payload["clasificacion_id"] = effective
    return payload


def create_pqr(host: str, case: dict, token: Optional[str] = None, clasificacion_id=None) -> tuple[dict, float]:
    """
    POST /pqrs → crea el PQR y retorna (respuesta_json, tiempo_ms).
    clasificacion_id: ID válido en tabla clasificaciones, o None para omitir el campo.
    """
    url     = host.rstrip("/") + CREATE_PQR_ENDPOINT
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = build_pqr_payload(case, clasificacion_id=clasificacion_id)
    t0      = time.perf_counter()
    resp    = requests.post(url, json=payload, headers=headers, timeout=60)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    return resp.json(), elapsed_ms


def extract_system_id(pqr_resp: dict, fallback: int) -> int:
    """
    Extrae el ID asignado por la BD desde la respuesta de POST /pqrs.
    Estructura del backend: ok_response → {"success": true, "data": {"id": N, ...}}
    El campo en PQROut es `ID` (mayúscula) pero _serialize_pqr_response lo expone como `id`.
    """
    # Estructura estándar del backend: {"data": {"id": N}}
    data = pqr_resp.get("data")
    if isinstance(data, dict):
        sid = data.get("id") or data.get("ID") or data.get("pqr_id")
        if sid:
            return int(sid)
    # Estructura plana por si ok_response cambia: {"id": N}
    sid = pqr_resp.get("id") or pqr_resp.get("ID") or pqr_resp.get("pqr_id")
    if sid:
        return int(sid)
    logger.warning("extract_system_id: no se encontró 'id' en la respuesta %s — usando fallback %d", pqr_resp, fallback)
    return fallback


def call_classify(host: str, pqr_id: int, token: Optional[str] = None) -> tuple[dict, float]:
    """
    #get /classify/{pqr_id} → clasifica el PQR y retorna (respuesta_json, tiempo_ms).
    #El endpoint solo necesita el pqr_id en la URL; no se envía body.
    """
    url     = host.rstrip("/") + CLASSIFY_ENDPOINT.format(pqr_id=pqr_id)
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    t0   = time.perf_counter()
    resp = requests.get(url, headers=headers, timeout=60)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    resp.raise_for_status()
    return resp.json(), elapsed_ms

def get_catalog(host: str, endpoint: str, token: Optional[str] = None) -> dict:
    """Obtiene un catálogo genérico (categorías, prioridades, etc.)"""
    url     = host.rstrip("/") + endpoint
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_categorias(host: str, token: Optional[str] = None) -> dict:
    return get_catalog(host, CATEGORY_ENDPOINT, token)


def get_prioridades(host: str, token: Optional[str] = None) -> dict:
    return get_catalog(host, PRIORITY_ENDPOINT, token)

def build_catalog_dict(host: str, endpoint: str, token: Optional[str] = None) -> dict:
    """Retorna {id: nombre} desde un endpoint de catálogo."""
    data = get_catalog(host, endpoint, token)
    return {item['id']: item['nombre'] for item in data['data']}


# ── Autenticación ──────────────────────────────────────────────────────────────

def get_access_token(host: str, username: str, password: str) -> str:
    """Obtiene un token de acceso desde /auth/login."""
    url     = host.rstrip("/") + "/auth/login"
    payload = {"username": username, "password": password}
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}

    last_exc: Exception | None = None
    for attempt in range(1, 3):
        try:
            resp = requests.post(url, data=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            break
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt == 2:
                raise RuntimeError(f"Error de conexión con {url}: {exc}") from exc
            time.sleep(1)

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Respuesta inválida desde {url}: {resp.text}") from exc

    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"No se obtuvo access_token desde {url}: {data}")
    return token


# ── Persistencia ───────────────────────────────────────────────────────────────

def load_existing_results() -> list[dict]:
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_results(results: list[dict]):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# ── Métricas ───────────────────────────────────────────────────────────────────

def compute_ml_metrics(results: list[dict], field_pred: str, field_true: str) -> dict:
    """
    Calcula métricas ML clásicas (multiclase) para un campo de predicción.

    Retorna un dict con:
      - accuracy            : fracción de predicciones correctas
      - macro_precision     : promedio no ponderado de precisión por clase
      - macro_recall        : promedio no ponderado de recall por clase
      - macro_f1            : promedio no ponderado de F1 por clase
      - weighted_precision  : promedio ponderado (por soporte) de precisión
      - weighted_recall     : promedio ponderado (por soporte) de recall
      - weighted_f1         : promedio ponderado (por soporte) de F1
      - per_class           : dict clase → {precision, recall, f1, support}
      - confusion_matrix    : dict (true_label, pred_label) → count
      - labels              : lista ordenada de etiquetas únicas
    """
    validated = [
        r for r in results
        if r.get(field_pred) is not None and r.get(field_true) is not None
        and r.get("both_correct") is not None
    ]
    if not validated:
        return {}

    y_true = [r[field_true] for r in validated]
    y_pred = [r[field_pred] for r in validated]
    labels = sorted(set(y_true) | set(y_pred))
    n      = len(validated)

    # Matriz de confusión: cm[true][pred]
    cm: dict[str, dict[str, int]] = {lbl: {l: 0 for l in labels} for lbl in labels}
    for yt, yp in zip(y_true, y_pred):
        if yt not in cm:
            cm[yt] = {l: 0 for l in labels}
        if yp not in cm[yt]:
            cm[yt][yp] = 0
        cm[yt][yp] += 1

    # Métricas por clase
    per_class: dict[str, dict] = {}
    for lbl in labels:
        tp = cm.get(lbl, {}).get(lbl, 0)
        fp = sum(cm.get(other, {}).get(lbl, 0) for other in labels if other != lbl)
        fn = sum(cm.get(lbl, {}).get(other, 0) for other in labels if other != lbl)
        support = tp + fn

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)
        per_class[lbl] = {
            "precision": round(precision, 4),
            "recall":    round(recall,    4),
            "f1":        round(f1,        4),
            "support":   support,
        }

    accuracy          = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp) / n
    supports          = [per_class[lbl]["support"] for lbl in labels]
    total_support     = sum(supports) or 1
    macro_precision   = sum(per_class[l]["precision"] for l in labels) / len(labels)
    macro_recall      = sum(per_class[l]["recall"]    for l in labels) / len(labels)
    macro_f1          = sum(per_class[l]["f1"]        for l in labels) / len(labels)
    weighted_precision= sum(per_class[l]["precision"] * per_class[l]["support"] for l in labels) / total_support
    weighted_recall   = sum(per_class[l]["recall"]    * per_class[l]["support"] for l in labels) / total_support
    weighted_f1       = sum(per_class[l]["f1"]        * per_class[l]["support"] for l in labels) / total_support

    # Serializar confusion_matrix como lista de dicts para JSON
    confusion_matrix_list = [
        {"true": yt, "predicted": yp, "count": cm[yt][yp]}
        for yt in labels for yp in labels
        if cm.get(yt, {}).get(yp, 0) > 0
    ]

    return {
        "accuracy":           round(accuracy,           4),
        "macro_precision":    round(macro_precision,    4),
        "macro_recall":       round(macro_recall,       4),
        "macro_f1":           round(macro_f1,           4),
        "weighted_precision": round(weighted_precision, 4),
        "weighted_recall":    round(weighted_recall,    4),
        "weighted_f1":        round(weighted_f1,        4),
        "per_class":          per_class,
        "confusion_matrix":   confusion_matrix_list,
        "labels":             labels,
        "n_samples":          n,
        "_cm_raw":            cm,   # solo para uso interno
    }


def compute_metrics(results: list[dict]) -> dict:
    """Calcula métricas agregadas a partir de resultados guardados."""
    validated = [r for r in results if r.get("both_correct") is not None]
    total = len(validated)
    if total == 0:
        return {}

    correct_cat  = sum(1 for r in validated if r.get("category_correct"))
    correct_pri  = sum(1 for r in validated if r.get("priority_correct"))
    correct_both = sum(1 for r in validated if r.get("both_correct"))

    proc_times = [r["processing_ms"] for r in validated if r.get("processing_ms") is not None]
    val_times  = [r["validation_seconds"] for r in validated if r.get("validation_seconds") is not None]
    errors     = [r for r in results if r.get("error")]

    sources = {}
    for r in validated:
        s = r.get("source", "unknown")
        sources[s] = sources.get(s, 0) + 1

    # ── Métricas ML ─────────────────────────────────────────────────────────
    ml_category = compute_ml_metrics(validated, "predicted_categoria", "expert_category")
    ml_priority = compute_ml_metrics(validated, "predicted_prioridad",  "expert_priority")

    return {
        "total_evaluated":        total,
        "precision_category_pct": round(correct_cat  / total * 100, 1),
        "precision_priority_pct": round(correct_pri  / total * 100, 1),
        "precision_both_pct":     round(correct_both / total * 100, 1),
        "avg_processing_ms":      round(statistics.mean(proc_times), 1) if proc_times else None,
        "p95_processing_ms":      round(sorted(proc_times)[int(len(proc_times) * 0.95)] if len(proc_times) > 1 else proc_times[0], 1) if proc_times else None,
        "max_processing_ms":      round(max(proc_times), 1) if proc_times else None,
        "avg_validation_s":       round(statistics.mean(val_times), 1) if val_times else None,
        "max_validation_s":       round(max(val_times), 1) if val_times else None,
        "error_count":            len(errors),
        "sources_distribution":   sources,
        "sla_precision_ok":       (correct_both / total * 100) >= SLA_PRECISION_PCT if total else False,
        "sla_processing_ok":      (max(proc_times) <= SLA_PROCESS_MS) if proc_times else None,
        "sla_validation_ok":      (max(val_times) <= SLA_VALIDATION_S) if val_times else None,
        # Nuevas métricas ML
        "ml_category":            ml_category,
        "ml_priority":            ml_priority,
    }


# ──────────────────────────────────────────────────────────────────────────────
# MODO 0: Validación del archivo JSON
# ──────────────────────────────────────────────────────────────────────────────

def run_validate(filepath: str):
    """Valida el archivo JSON de casos sin llamar a la API."""
    banner()
    print(f"{BOLD}Modo: Validación de archivo – {filepath}{RESET}\n")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except FileNotFoundError:
        print(f"{RED}ERROR: Archivo no encontrado: {filepath}{RESET}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{RED}ERROR: JSON inválido – {e}{RESET}")
        sys.exit(1)

    if not isinstance(cases, list):
        print(f"{RED}ERROR: El JSON debe ser una lista de objetos.{RESET}")
        sys.exit(1)

    valid, errors = validate_cases(cases)

    print(f"  Total de casos en archivo : {len(cases)}")
    print(f"  {GREEN}Válidos  : {len(valid)}{RESET}")
    print(f"  {RED if errors else GREEN}Con errores: {len(errors)}{RESET}\n")

    if errors:
        print(f"{BOLD}{RED}Errores encontrados:{RESET}")
        for e in errors:
            print(f"  {RED}✗{RESET} {e}")
        print()
    else:
        print(f"{GREEN}{BOLD}✓ Todos los casos son válidos para pruebas.{RESET}\n")

    # Advertir sobre remapeos por CHECK constraints de la BD
    remapped = [c for c in valid if c.get("category") not in VALID_API_TIPOS]
    if remapped:
        print(f"{YELLOW}\u26a0  Aviso CHECK constraint – campo 'tipo':{RESET}")
        print(f"   La BD solo acepta: {sorted(VALID_API_TIPOS)}")
        print(f"   Los siguientes casos se enviarán con tipo remapeado al crear el PQR:\n")
        for c in remapped:
            orig   = c.get("category", "?")
            mapped = CATEGORY_TO_TIPO.get(orig, "peticion")
            print(f"   PQR #{c['pqr_id']:>3}  category={orig!r}  →  tipo={mapped!r}")
        print()

    # Distribución
    from collections import Counter
    cats = Counter(c.get("category", "?") for c in valid)
    pris = Counter(c.get("priority", "?") for c in valid)
    print(f"{BOLD}Distribución de categorías (ground truth JSON):{RESET}")
    for k, v in sorted(cats.items()):
        api_tipo   = CATEGORY_TO_TIPO.get(k, k)
        remap_note = f"  {YELLOW}→ tipo=\'{api_tipo}\' en API{RESET}" if api_tipo != k else ""
        print(f"  {k:>12} : {v}{remap_note}")
    print(f"\n{BOLD}Distribución de prioridades:{RESET}")
    for k, v in sorted(pris.items()):
        print(f"  {k:>12} : {v}")
    print()


# ──────────────────────────────────────────────────────────────────────────────
# MODO 1: Evaluación interactiva (caso a caso con experto humano)
# ──────────────────────────────────────────────────────────────────────────────

def run_interactive(host: str, token: Optional[str] = None, clasificacion_id=None):
    """Modo interactivo: el evaluador ingresa casos uno a uno."""
    banner()
    print(f"{BOLD}Modo: Evaluación Interactiva con Experto Humano{RESET}")
    print(f"{DIM}Escribe 'fin' para terminar. Los resultados se acumulan en {RESULTS_FILE}{RESET}\n")

    results         = load_existing_results()
    session_results = []
    case_num        = len([r for r in results if r.get("both_correct") is not None]) + 1
    
    categorias  = build_catalog_dict(host, CATEGORY_ENDPOINT, token=token)
    prioridades = build_catalog_dict(host, PRIORITY_ENDPOINT, token=token)

    while True:
        print(f"{CYAN}{'─'*60}{RESET}")
        print(f"{BOLD}Caso #{case_num}{RESET}")

        print(f"\n{BOLD}Texto de la solicitud PQR{RESET} (o 'fin'):")
        text = input("  > ").strip()
        if text.lower() in ("fin", "exit", "q"):
            break
        if not text:
            print(f"{YELLOW}Texto vacío, intente de nuevo.{RESET}")
            continue

        # Construir un caso temporal para crear el PQR
        tmp_case = {
            "pqr_id":   case_num,
            "text":     text,
            "category": "reclamo",   # default para modo interactivo
            "priority": "media",
        }

        result = CaseResult(pqr_id=case_num, text=text)
        print(f"\n{DIM}Creando PQR en el sistema...{RESET}", end="", flush=True)

        # ── PASO 1: Crear PQR ──────────────────────────────────────────────
        try:
            pqr_resp, creation_ms = create_pqr(host, tmp_case, token, clasificacion_id=clasificacion_id)
            system_id = extract_system_id(pqr_resp, fallback=case_num)
            result.system_pqr_id   = system_id
            result.pqr_created     = True
            result.pqr_creation_ms = round(creation_ms, 1)
            print(f" {GREEN}✓{RESET} ID={system_id} ({fmt_ms(creation_ms)})")
        except Exception as e:
            result.error = f"Creación PQR: {e}"
            print(f"\n{RED}Error al crear PQR: {e}{RESET}")
            results.append(asdict(result))
            save_results(results)
            case_num += 1
            continue

        # ── PASO 2: Clasificar ─────────────────────────────────────────────
        print(f"{DIM}Clasificando con agente IA...{RESET}", end="", flush=True)
        try:
            time.sleep(10)
            response_request, elapsed_ms = call_classify(host, system_id, token)

            response = response_request["data"]
            
            # Normalizar campos de la respuesta
            result.processing_ms       = round(elapsed_ms, 1)
            result.predicted_categoria_id = (response.get("categoria_id") or "")
            result.predicted_prioridad_id        = (response.get("prioridad_id") or "")
            result.predicted_tags      = response.get("tags", [])
            result.predicted_area      = response.get("area")
            result.confianza           = response.get("confianza")
            result.source              = response.get("source")
            result.rules_matched       = response.get("rules_matched", [])
            result.requiere_revision   = response.get("requiere_revision")

            result.predicted_categoria = categorias[result.predicted_categoria_id].lower()
            result.predicted_prioridad = prioridades[result.predicted_prioridad_id]
            

            print(f" {fmt_ms(elapsed_ms)}")
        except Exception as e:
            result.error = str(e)
            print(f"\n{RED}Error al clasificar: {e}{RESET}")
            results.append(asdict(result))
            save_results(results)
            case_num += 1
            continue

        # ── Mostrar predicción ─────────────────────────────────────────────
        proc_badge = sla_badge(elapsed_ms, SLA_PROCESS_MS, higher_is_better=False)
        conf_str   = f"{result.confianza*100:.1f}%" if result.confianza else "N/A"
        rev_str    = f"{RED}Sí{RESET}" if result.requiere_revision else f"{GREEN}No{RESET}"
        print(f"""
{BOLD}┌─ Predicción del Agente IA ─────────────────────────────┐{RESET}
│  Categoría  : {CYAN}{BOLD}{result.predicted_categoria or 'Sin determinar'}{RESET}
│  Prioridad  : {CYAN}{BOLD}{result.predicted_prioridad or 'Sin determinar'}{RESET}
│  Área       : {result.predicted_area or 'N/A'}
│  Confianza  : {conf_str}
│  Rev. manual: {rev_str}
│  Fuente     : {result.source}
│  Reglas     : {', '.join(result.rules_matched) if result.rules_matched else 'ninguna'}
│  Tiempo     : {fmt_ms(elapsed_ms)} {proc_badge}
{BOLD}└────────────────────────────────────────────────────────┘{RESET}""")

        # ── Validación del experto humano ──────────────────────────────────
        print(f"\n{BOLD}⏱  Validación del Experto Humano{RESET}")
        print(f"{DIM}(El tiempo se mide desde ahora hasta que confirmes){RESET}")
        input(f"  Presiona {BOLD}ENTER{RESET} cuando estés listo para validar...")
        t_val_start = time.perf_counter()

        cats = [
            "Facturación incorrecta", "Información de producto", "Tecnica",
            "Producto defectuoso", "Atención al cliente", "Servicio",
            "Cancelación de pedido", "Devolución y reembolso", "Factura y documentos",
            "Cambio de datos", "Logística y entrega", "Garantía",
            "Fraude / seguridad", "Entrega tardía", "Pedido no entregado",
            "Estado de pedido", "Experiencia de compra", "Producto incorrecto",
            "Programa de fidelización", "Publicidad engañosa",
        ]
        # Normalizar para comparación
        cats_lower = [c.lower() for c in cats]
        print(f"\n  Categoría correcta para este caso:")
        for i, c in enumerate(cats, 1):
            marker = f"{GREEN}←{RESET}" if c.lower() == (result.predicted_categoria or "").lower() else ""
            print(f"    {i:>2}. {c} {marker}")
        print(f"    0. Otra (escribir)")
        cat_input = input(f"  Selección [1-{len(cats)} / 0 / ENTER=acepto agente]: ").strip()

        if cat_input == "":
            result.expert_category = result.predicted_categoria
        elif cat_input == "0":
            result.expert_category = input("  Escribe la categoría correcta: ").strip().lower()
        elif cat_input.isdigit() and 1 <= int(cat_input) <= len(cats):
            result.expert_category = cats_lower[int(cat_input) - 1]
        else:
            result.expert_category = result.predicted_categoria

        pris = ["baja", "media", "alta", "urgente", "crítico"]
        print(f"\n  Prioridad correcta para este caso:")
        for i, p in enumerate(pris, 1):
            marker = f"{GREEN}←{RESET}" if p == result.predicted_prioridad else ""
            print(f"    {i}. {p} {marker}")
        pri_input = input(f"  Selección [1-{len(pris)} / ENTER=acepto agente]: ").strip()

        if pri_input == "":
            result.expert_priority = result.predicted_prioridad
        elif pri_input.isdigit() and 1 <= int(pri_input) <= len(pris):
            raw_exp_pri = pris[int(pri_input) - 1]
            result.expert_priority = PRIORITY_NORMALIZATION.get(raw_exp_pri, raw_exp_pri)
        else:
            result.expert_priority = result.predicted_prioridad

        val_elapsed             = time.perf_counter() - t_val_start
        result.validation_seconds = round(val_elapsed, 1)

        # ── Veredicto ──────────────────────────────────────────────────────
        result.category_correct = (result.predicted_categoria == result.expert_category)
        result.priority_correct  = (result.predicted_prioridad  == result.expert_priority)
        result.both_correct      = result.category_correct and result.priority_correct

        val_badge     = sla_badge(val_elapsed, SLA_VALIDATION_S, higher_is_better=False)
        verdict_color = GREEN if result.both_correct else (YELLOW if (result.category_correct or result.priority_correct) else RED)

        print(f"""
{BOLD}┌─ Veredicto ────────────────────────────────────────────┐{RESET}
│  Categoría  : {GREEN+'✓ Correcta'+RESET if result.category_correct else RED+'✗ Incorrecta'+RESET}   ({result.predicted_categoria} {ARROW} {result.expert_category})
│  Prioridad  : {GREEN+'✓ Correcta'+RESET if result.priority_correct else RED+'✗ Incorrecta'+RESET}   ({result.predicted_prioridad} {ARROW} {result.expert_priority})
│  Veredicto  : {verdict_color}{BOLD}{'ACIERTO TOTAL' if result.both_correct else 'PARCIAL' if (result.category_correct or result.priority_correct) else 'FALLO'}{RESET}
│  Val. humana: {fmt_ms(val_elapsed*1000)} {val_badge}
{BOLD}└────────────────────────────────────────────────────────┘{RESET}""")

        session_results.append(result)
        results.append(asdict(result))
        save_results(results)

        validated = [r for r in session_results if r.both_correct is not None]
        if validated:
            correct = sum(1 for r in validated if r.both_correct)
            pct     = correct / len(validated) * 100
            badge   = sla_badge(pct, SLA_PRECISION_PCT)
            print(f"\n{DIM}  Sesión actual: {correct}/{len(validated)} ({pct:.0f}% precisión) {badge}{RESET}")

        case_num += 1

    if session_results:
        print(f"\n{BOLD}{CYAN}{'═'*60}")
        print(f"  RESUMEN DE SESIÓN ({len(session_results)} casos evaluados)")
        print(f"{'═'*60}{RESET}")
        _print_summary(compute_metrics([asdict(r) for r in session_results]))

    print(f"\n{DIM}Resultados guardados en: {RESULTS_FILE.absolute()}{RESET}\n")


# ──────────────────────────────────────────────────────────────────────────────
# MODO 2: Evaluación en lote (batch) desde archivo JSON
# ──────────────────────────────────────────────────────────────────────────────

def run_batch(host: str, filepath: str, token: Optional[str] = None, clasificacion_id=None):
    """
    Modo batch:
      1. Valida todos los casos del JSON.
      2. POST /pqrs           → crea cada PQR en el sistema.
      3. get /classify/{id}  → clasifica y obtiene predicción.
      4. Compara predicción vs ground truth y calcula métricas.
    """
    banner()
    print(f"{BOLD}Modo: Evaluación Batch – {filepath}{RESET}\n")

    # ── Cargar y validar JSON ──────────────────────────────────────────────
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            cases = json.load(f)
    except FileNotFoundError:
        print(f"{RED}ERROR: Archivo no encontrado: {filepath}{RESET}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{RED}ERROR: JSON inválido – {e}{RESET}")
        sys.exit(1)

    valid_cases, val_errors = validate_cases(cases)

    if val_errors:
        print(f"{YELLOW}⚠  Se encontraron {len(val_errors)} problema(s) en el JSON:{RESET}")
        for err in val_errors:
            print(f"   {RED}✗{RESET} {err}")
        print()

    if not valid_cases:
        print(f"{RED}No hay casos válidos para procesar.{RESET}")
        sys.exit(1)

    skipped = len(cases) - len(valid_cases)
    if skipped:
        print(f"{YELLOW}  Se omitirán {skipped} caso(s) inválido(s).{RESET}\n")

    print(f"  Procesando {len(valid_cases)} caso(s)...\n")
    print(f"  {'#':>5}  {'PQR ID':>8}  {'Sys ID':>8}  {'Crear':>8}  {'Clasif.':>8}  {'Cat IA':>18}  {'Pri IA':>7}  {'Conf':>6}  Veredicto")
    print(f"  {'─'*5}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*18}  {'─'*7}  {'─'*6}  {'─'*10}")

    results     = load_existing_results()
    new_results = []
    total       = len(valid_cases)
    
    # -- PASO 0: Obtener Dict de Categorias y Prioridades
    categorias  = build_catalog_dict(host, CATEGORY_ENDPOINT, token=token)
    prioridades = build_catalog_dict(host, PRIORITY_ENDPOINT, token=token)

    for i, case in enumerate(valid_cases, 1):
        pqr_id    = case["pqr_id"]
        text      = case["text"]
        raw_cat   = case.get("category", "")
        truth_cat = CATEGORY_NORMALIZATION.get(raw_cat, raw_cat.lower()).strip()
        raw_pri   = case.get("priority", "").lower().strip()
        truth_pri = PRIORITY_NORMALIZATION.get(raw_pri, raw_pri)

        result = CaseResult(
            pqr_id=pqr_id,
            text=text,
            expert_category=truth_cat,
            expert_priority=truth_pri,
        )

        system_id = pqr_id  # fallback
        

        # ── PASO 1: Crear PQR ──────────────────────────────────────────────
        try:
            pqr_resp, creation_ms = create_pqr(host, case, token, clasificacion_id=clasificacion_id)
            system_id = extract_system_id(pqr_resp, fallback=pqr_id)
            result.system_pqr_id   = system_id
            result.pqr_created     = True
            result.pqr_creation_ms = round(creation_ms, 1)

        except Exception as e:
            result.error = f"Creación PQR: {e}"
            print(f"  {i:>5}  {pqr_id:>8}  {'–':>8}  {RED}ERROR{RESET}: {e}")
            new_results.append(asdict(result))
            continue

        # ── PASO 2: Clasificar (con retry — el backend clasifica en background task) ──
        # El POST /pqrs dispara _post_classification como BackgroundTask,
        # así que /classifications/pqr/{id} puede tardar varios segundos en estar listo.
        MAX_RETRIES   = 5
        RETRY_DELAYS  = [3, 6, 12, 20, 30]   # backoff progresivo en segundos
        classify_resp = None
        elapsed_ms    = None

        for attempt, delay in enumerate(RETRY_DELAYS[:MAX_RETRIES], 1):
            try:
                time.sleep(delay)
                classify_resp, elapsed_ms = call_classify(host, system_id, token)
                break   # éxito — salir del loop
            except requests.exceptions.HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code == 404:
                    if attempt < MAX_RETRIES:
                        next_delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                        print(f"  {i:>5}  {pqr_id:>8}  {system_id:>8}  {YELLOW}404 – reintento {attempt}/{MAX_RETRIES-1} en {next_delay}s…{RESET}")
                        continue
                    # Agotados los reintentos
                    result.error = f"classify: {http_err}"
                    print(f"  {i:>5}  {pqr_id:>8}  {system_id:>8}  {'–':>8}  {RED}ERROR classify: {http_err}{RESET}")
                    new_results.append(asdict(result))
                    break
                else:
                    raise   # otro error HTTP — propagar
            except Exception as exc:
                result.error = f"classify: {exc}"
                print(f"  {i:>5}  {pqr_id:>8}  {system_id:>8}  {'–':>8}  {RED}ERROR classify: {exc}{RESET}")
                new_results.append(asdict(result))
                break

        if result.error or classify_resp is None:
            continue

        try:
            response = classify_resp["data"]
            
            # Normalizar campos de la respuesta
            result.processing_ms          = round(elapsed_ms, 1)
            result.predicted_categoria_id = (response.get("categoria_id") or "")
            result.predicted_prioridad_id = (response.get("prioridad_id") or "")
            result.predicted_tags         = response.get("tags", [])
            result.predicted_area         = response.get("area")
            result.confianza              = response.get("confianza")
            result.source                 = response.get("source")
            result.rules_matched          = response.get("rules_matched", [])
            result.requiere_revision      = response.get("requiere_revision")

            result.predicted_categoria = categorias[result.predicted_categoria_id]
            result.predicted_prioridad = prioridades[result.predicted_prioridad_id]

            # Veredicto: comparar en minúscula normalizada
            result.category_correct = (result.predicted_categoria == truth_cat)
            result.priority_correct  = (result.predicted_prioridad  == truth_pri)
            result.both_correct      = result.category_correct and result.priority_correct

            verdict = f"{GREEN}✓{RESET}" if result.both_correct else (
                f"{YELLOW}~{RESET}" if (result.category_correct or result.priority_correct) else f"{RED}✗{RESET}"
            )
            conf_str = f"{result.confianza:.2f}" if result.confianza is not None else "  N/A"
            cat_str  = (result.predicted_categoria or "?")[:18]
            pri_str  = (result.predicted_prioridad  or "?")[:7]

            print(
                f"  {i:>5}  {pqr_id:>8}  {system_id:>8}  "
                f"{fmt_ms(result.pqr_creation_ms):>8}  "
                f"{fmt_ms(elapsed_ms):>8}  "
                f"{cat_str:>18}  {pri_str:>7}  {conf_str:>6}  {verdict}"
            )

        except Exception as e:
            result.error = str(e)
            print(f"  {i:>5}  {pqr_id:>8}  {system_id:>8}  –  {RED}ERROR classify parse: {e}{RESET}")

        new_results.append(asdict(result))

    results.extend(new_results)
    save_results(results)

    print(f"\n{BOLD}{CYAN}{'═'*60}")
    print(f"  RESULTADOS BATCH ({total} casos)")
    print(f"{'═'*60}{RESET}")
    _print_summary(compute_metrics(new_results))
    print(f"\n{DIM}Guardado en: {RESULTS_FILE.absolute()}{RESET}\n")


# ──────────────────────────────────────────────────────────────────────────────
# MODO 3: Prueba de carga (load test)
# ──────────────────────────────────────────────────────────────────────────────

LOAD_TEST_TEXTS = [
    "Mi factura tiene un cobro adicional que no corresponde a los servicios contratados.",
    "Solicito información sobre los planes de mantenimiento disponibles para este año.",
    "El técnico no apareció en la fecha acordada y nadie me avisó del cambio.",
    "Quiero dar de baja el servicio de internet porque el precio aumentó sin previo aviso.",
    "El producto llegó con el empaque dañado y algunos componentes faltantes.",
    "Necesito que me expliquen cómo funciona el proceso de devolución de mercancía.",
    "Llevo tres semanas esperando la resolución de mi caso y no he recibido respuesta.",
    "Felicitaciones al equipo de atención, resolvieron mi problema en tiempo récord.",
    "El agua caliente no funciona correctamente desde que hicieron el mantenimiento.",
    "Requiero copia certificada de mi contrato de servicio para trámites legales.",
]

LOAD_TEST_CATEGORIES = [
    "Facturación incorrecta",
    "Información de producto",
    "Técnica",
    "Cancelación de pedido",
    "Producto defectuoso",
    "Información de producto",
    "Atención al cliente",
    "Atención al cliente",
    "Técnica",
    "Factura y documentos",
]


def run_load_test(host: str, n: int = 100, token: Optional[str] = None, clasificacion_id=None):
    """
    Prueba de carga:
      1. Crea N PQRs vía POST /pqrs.
      2. Clasifica cada uno vía POST /classify/{id}.
    Mide el tiempo total del ciclo completo (creación + clasificación).
    """
    banner()
    print(f"{BOLD}Modo: Prueba de Carga – {n} solicitudes (crear + clasificar){RESET}\n")

    times_ms = []
    errors   = 0

    for i in range(n):
        text     = LOAD_TEST_TEXTS[i % len(LOAD_TEST_TEXTS)]
        category = LOAD_TEST_CATEGORIES[i % len(LOAD_TEST_CATEGORIES)]
        tmp_case = {
            "pqr_id":   i + 1,
            "text":     text,
            "category": category,
            "priority": "media",
        }

        t0 = time.perf_counter()
        try:
            # Crear PQR
            pqr_resp, _ = create_pqr(host, tmp_case, token, clasificacion_id=clasificacion_id)
            system_id   = extract_system_id(pqr_resp, fallback=i + 1)
            # Clasificar
            _, _ = call_classify(host, system_id, token)

            total_ms = (time.perf_counter() - t0) * 1000
            times_ms.append(total_ms)
            pct = (i + 1) / n * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            print(f"\r  [{bar}] {pct:5.1f}%  {fmt_ms(total_ms)}", end="", flush=True)
        except Exception as e:
            errors += 1
            print(f"\r  {RED}Error #{i+1}: {e}{RESET}")

    print("\n")

    if not times_ms:
        print(f"{RED}Todas las solicitudes fallaron.{RESET}")
        return

    sorted_times = sorted(times_ms)
    lr = LoadTestResult(
        n_requests  = n,
        total_ms    = sum(times_ms),
        avg_ms      = round(statistics.mean(times_ms), 1),
        p50_ms      = round(sorted_times[int(n * 0.50)], 1),
        p95_ms      = round(sorted_times[min(int(n * 0.95), n - 1)], 1),
        p99_ms      = round(sorted_times[min(int(n * 0.99), n - 1)], 1),
        max_ms      = round(max(times_ms), 1),
        min_ms      = round(min(times_ms), 1),
        errors      = errors,
    )

    requests_per_sec     = n / (lr.total_ms / 1000)
    lr.projected_monthly = int(requests_per_sec * 86_400 * 30)

    sla_p95 = sla_badge(lr.p95_ms, SLA_PROCESS_MS, higher_is_better=False)
    sla_max = sla_badge(lr.max_ms, SLA_PROCESS_MS, higher_is_better=False)
    sla_vol = sla_badge(lr.projected_monthly, SLA_MONTHLY_VOLUME)

    print(f"""{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║              RESULTADOS PRUEBA DE CARGA                  ║
╚══════════════════════════════════════════════════════════╝{RESET}

  {BOLD}Solicitudes totales : {n}{RESET}   (Errores: {RED+str(errors)+RESET if errors else GREEN+'0'+RESET})
  {DIM}Nota: cada solicitud incluye POST /pqrs + POST /classify/{'{id}'}{RESET}

  {BOLD}Tiempos de Respuesta (ciclo completo):{RESET}
    Mínimo  : {fmt_ms(lr.min_ms)}
    Promedio: {fmt_ms(lr.avg_ms)}
    P50     : {fmt_ms(lr.p50_ms)}
    P95     : {fmt_ms(lr.p95_ms)} {sla_p95}
    P99     : {fmt_ms(lr.p99_ms)}
    Máximo  : {fmt_ms(lr.max_ms)} {sla_max}

  {BOLD}Capacidad:{RESET}
    Throughput      : {requests_per_sec:.2f} req/seg
    Proyección/mes  : {lr.projected_monthly:,} solicitudes {sla_vol}
    Meta mensual    : {SLA_MONTHLY_VOLUME:,} solicitudes
""")

    load_results = load_existing_results()
    load_results.append({"_type": "load_test", **asdict(lr)})
    save_results(load_results)
    print(f"{DIM}Guardado en: {RESULTS_FILE.absolute()}{RESET}\n")


# ──────────────────────────────────────────────────────────────────────────────
# MODO 4: Reporte consolidado
# ──────────────────────────────────────────────────────────────────────────────

def run_report():
    """Muestra reporte consolidado de todos los resultados guardados."""
    banner()
    print(f"{BOLD}Modo: Reporte Consolidado – {RESULTS_FILE}{RESET}\n")

    all_results  = load_existing_results()
    case_results = [r for r in all_results if r.get("_type") != "load_test" and r.get("both_correct") is not None]
    load_results = [r for r in all_results if r.get("_type") == "load_test"]

    if not case_results and not load_results:
        print(f"{YELLOW}No hay resultados guardados aún. Ejecuta primero el modo 'interactive' o 'batch'.{RESET}\n")
        return

    if case_results:
        metrics = compute_metrics(case_results)
        print(f"{BOLD}{CYAN}{'═'*60}")
        print(f"  MÉTRICAS DE PRECISIÓN ({metrics['total_evaluated']} casos validados)")
        print(f"{'═'*60}{RESET}")
        _print_summary(metrics)

        recent = case_results[-10:]
        print(f"\n{BOLD}Últimos {len(recent)} casos evaluados:{RESET}")
        print(f"  {'ID':>4}  {'SysID':>6}  {'Categoría IA':>18}  {'Prio IA':>7}  {'Cat GT':>12}  {'Pri GT':>7}  {'Conf':>6}  {'ms':>8}  Veredicto")
        print(f"  {'─'*4}  {'─'*6}  {'─'*18}  {'─'*7}  {'─'*12}  {'─'*7}  {'─'*6}  {'─'*8}  {'─'*10}")
        for r in recent:
            ok      = r.get("both_correct")
            verdict = f"{GREEN}ACIERTO{RESET}" if ok else f"{RED}FALLO{RESET}"
            cat_ai  = (r.get("predicted_categoria") or "?")[:18]
            pri_ai  = (r.get("predicted_prioridad")  or "?")[:7]
            cat_gt  = (r.get("expert_category")       or "?")[:12]
            pri_gt  = (r.get("expert_priority")        or "?")[:7]
            conf    = f"{r['confianza']:.2f}" if r.get("confianza") is not None else " N/A"
            ms_s    = f"{r.get('processing_ms', 0):,.0f}"
            sid     = str(r.get("system_pqr_id") or "?")[:6]
            print(f"  {r.get('pqr_id','?'):>4}  {sid:>6}  {cat_ai:>18}  {pri_ai:>7}  {cat_gt:>12}  {pri_gt:>7}  {conf:>6}  {ms_s:>8}  {verdict}")

    if load_results:
        print(f"\n{BOLD}{CYAN}{'═'*60}")
        print(f"  HISTORIAL DE PRUEBAS DE CARGA ({len(load_results)} ejecuciones)")
        print(f"{'═'*60}{RESET}")
        print(f"  {'Fecha':>22}  {'N':>6}  {'Avg ms':>8}  {'P95 ms':>8}  {'Max ms':>8}  {'Proy/mes':>10}")
        print(f"  {'─'*22}  {'─'*6}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*10}")
        for lr in load_results:
            ts  = lr.get("timestamp", "?")[:19]
            n   = lr.get("n_requests", 0)
            avg = lr.get("avg_ms", 0)
            p95 = lr.get("p95_ms", 0)
            mx  = lr.get("max_ms", 0)
            vol = lr.get("projected_monthly", 0)
            vol_ok = GREEN if vol >= SLA_MONTHLY_VOLUME else RED
            print(f"  {ts:>22}  {n:>6}  {avg:>8.0f}  {p95:>8.0f}  {mx:>8.0f}  {vol_ok}{vol:>10,}{RESET}")

    print()


def _print_ml_metrics(m: dict):
    """Imprime sección 6 con métricas ML: Accuracy, Precision, Recall, F1 y Confusion Matrix."""

    def _render_block(title: str, ml: dict):
        if not ml:
            return
        acc  = ml.get("accuracy", 0)
        mp   = ml.get("macro_precision", 0)
        mr   = ml.get("macro_recall", 0)
        mf1  = ml.get("macro_f1", 0)
        wp   = ml.get("weighted_precision", 0)
        wr   = ml.get("weighted_recall", 0)
        wf1  = ml.get("weighted_f1", 0)
        n    = ml.get("n_samples", 0)

        print(f"""
  {BOLD}6.{title}{RESET}
  ┌────────────────────────────────────────────────────────────────────┐
  │  Muestras evaluadas : {n}
  │
  │  {BOLD}Métricas globales:{RESET}
  │    Accuracy (exactitud)           : {GREEN if acc >= 0.7 else RED}{acc*100:>6.1f}%{RESET}
  │
  │    {DIM}── Macro (promedio no ponderado) ──────────────────────{RESET}
  │    Precision  (macro)             : {mp*100:>6.1f}%
  │    Recall     (macro / TPR)       : {mr*100:>6.1f}%
  │    F1-Score   (macro)             : {mf1*100:>6.1f}%
  │
  │    {DIM}── Weighted (ponderado por soporte) ─────────────────{RESET}
  │    Precision  (weighted)          : {wp*100:>6.1f}%
  │    Recall     (weighted / TPR)    : {wr*100:>6.1f}%
  │    F1-Score   (weighted)          : {wf1*100:>6.1f}%
  └────────────────────────────────────────────────────────────────────┘""")

        # ── Tabla por clase ──────────────────────────────────────────────
        per_class = ml.get("per_class", {})
        if per_class:
            col_w = max((len(lbl) for lbl in per_class), default=12)
            col_w = max(col_w, 12)
            header = f"  {'Clase':>{col_w}}  {'Precision':>10}  {'Recall':>8}  {'F1':>8}  {'Soporte':>8}"
            sep    = f"  {'─'*col_w}  {'─'*10}  {'─'*8}  {'─'*8}  {'─'*8}"
            print(f"\n  {BOLD}  Detalle por clase:{RESET}")
            print(header)
            print(sep)
            for lbl, stats in sorted(per_class.items()):
                p   = stats["precision"]
                r   = stats["recall"]
                f1  = stats["f1"]
                sup = stats["support"]
                p_c = GREEN if p  >= 0.7 else (YELLOW if p  >= 0.5 else RED)
                r_c = GREEN if r  >= 0.7 else (YELLOW if r  >= 0.5 else RED)
                f_c = GREEN if f1 >= 0.7 else (YELLOW if f1 >= 0.5 else RED)
                print(
                    f"  {lbl:>{col_w}}  "
                    f"{p_c}{p*100:>9.1f}%{RESET}  "
                    f"{r_c}{r*100:>7.1f}%{RESET}  "
                    f"{f_c}{f1*100:>7.1f}%{RESET}  "
                    f"{sup:>8}"
                )

        # ── Matriz de confusión ─────────────────────────────────────────
        cm_raw = ml.get("_cm_raw", {})
        labels = ml.get("labels", [])
        if cm_raw and labels:
            col_w2 = max((len(lbl) for lbl in labels), default=8)
            col_w2 = max(col_w2, 8)
            print(f"\n  {BOLD}  Matriz de Confusión (filas=real, columnas=predicho):{RESET}")
            # Cabecera
            header_cm = f"  {' '*col_w2}  " + "  ".join(f"{lbl[:col_w2]:>{col_w2}}" for lbl in labels)
            print(header_cm)
            print(f"  {'─'*(col_w2 + (col_w2+2)*len(labels))}")
            for true_lbl in labels:
                row_vals = []
                for pred_lbl in labels:
                    cnt = cm_raw.get(true_lbl, {}).get(pred_lbl, 0)
                    if true_lbl == pred_lbl:
                        cell = f"{GREEN}{cnt:>{col_w2}}{RESET}"
                    elif cnt > 0:
                        cell = f"{RED}{cnt:>{col_w2}}{RESET}"
                    else:
                        cell = f"{' '*col_w2}"
                    row_vals.append(cell)
                print(f"  {true_lbl:>{col_w2}}  " + "  ".join(row_vals))
            print()

    _render_block(" MÉTRICAS ML – CATEGORÍA", m.get("ml_category", {}))
    _render_block(" MÉTRICAS ML – PRIORIDAD", m.get("ml_priority", {}))


def _print_summary(m: dict):
    """Imprime resumen de métricas con badges SLA."""
    if not m:
        print(f"{YELLOW}  Sin datos suficientes.{RESET}\n")
        return

    prec_pct = m.get("precision_both_pct", 0)
    badge_p  = sla_badge(prec_pct, SLA_PRECISION_PCT)
    bar_len  = int(prec_pct / 2)
    bar      = f"{GREEN}{'█'*bar_len}{RESET}{'░'*(50-bar_len)}"

    print(f"""
  {BOLD}1. PRECISIÓN DE CLASIFICACIÓN{RESET}  {badge_p}
  ┌────────────────────────────────────────────────────────┐
  │  [{bar}]
  │  Categoría + Prioridad correctas : {prec_pct:>5.1f}%  (meta ≥ {SLA_PRECISION_PCT}%)
  │  Solo categoría correcta         : {m.get('precision_category_pct', 0):>5.1f}%
  │  Solo prioridad correcta         : {m.get('precision_priority_pct', 0):>5.1f}%
  │  Casos evaluados                 : {m.get('total_evaluated', 0)}
  └────────────────────────────────────────────────────────┘""")

    avg_ms  = m.get("avg_processing_ms")
    p95_ms  = m.get("p95_processing_ms")
    max_ms  = m.get("max_processing_ms")
    badge_t = sla_badge(max_ms, SLA_PROCESS_MS, higher_is_better=False) if max_ms else ""
    print(f"""
  {BOLD}2. TIEMPO DE PROCESAMIENTO{RESET}  {badge_t}
  ┌────────────────────────────────────────────────────────┐
  │  Promedio : {fmt_ms(avg_ms) if avg_ms else 'N/A':>12}   (meta ≤ {SLA_PROCESS_MS//1000} s)
  │  P95      : {fmt_ms(p95_ms) if p95_ms else 'N/A':>12}
  │  Máximo   : {fmt_ms(max_ms) if max_ms else 'N/A':>12}
  └────────────────────────────────────────────────────────┘""")

    avg_v  = m.get("avg_validation_s")
    max_v  = m.get("max_validation_s")
    badge_v = sla_badge(max_v, SLA_VALIDATION_S, higher_is_better=False) if max_v else ""
    print(f"""
  {BOLD}3. VALIDACIÓN HUMANA{RESET}  {badge_v}
  ┌────────────────────────────────────────────────────────┐
  │  Promedio : {f'{avg_v:.1f} s' if avg_v else 'N/A':>12}   (meta < {SLA_VALIDATION_S} s)
  │  Máximo   : {f'{max_v:.1f} s' if max_v else 'N/A':>12}
  └────────────────────────────────────────────────────────┘""")

    sources = m.get("sources_distribution", {})
    total_s = sum(sources.values()) or 1
    print(f"""
  {BOLD}4. DISTRIBUCIÓN DE FUENTES{RESET}
  ┌────────────────────────────────────────────────────────┐""")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        pct_s = cnt / total_s * 100
        print(f"  │  {src:>10}: {cnt:>4} casos ({pct_s:>5.1f}%)")
    print("  └────────────────────────────────────────────────────────┘")

    err = m.get("error_count", 0)
    print(f"""
  {BOLD}5. ERRORES{RESET}
  ┌────────────────────────────────────────────────────────┐
  │  Total errores del agente : {RED+str(err)+RESET if err else GREEN+'0'+RESET}
  └────────────────────────────────────────────────────────┘""")

    # ── Sección 6: Métricas ML ─────────────────────────────────────────────
    _print_ml_metrics(m)

    all_ok = m.get("sla_precision_ok") and (m.get("sla_processing_ok") is not False) and (m.get("sla_validation_ok") is not False)
    status_color = GREEN if all_ok else RED
    print(f"""
  {BOLD}ESTADO GENERAL : {status_color}{'✓ AGENTE CUMPLE METAS SLA' if all_ok else '✗ REVISAR – ALGÚN SLA INCUMPLIDO'}{RESET}
""")


# ──────────────────────────────────────────────────────────────────────────────
# MODO 5: Generar archivo de casos de ejemplo
# ──────────────────────────────────────────────────────────────────────────────

SAMPLE_CASES = [
    {"pqr_id": 1,  "text": "Mi factura llegó con un cobro adicional que no reconozco, exijo que me devuelvan el dinero de inmediato.",           "category": "Facturación incorrecta", "priority": "alta"},
    {"pqr_id": 2,  "text": "Solicito información detallada sobre los nuevos planes de servicios disponibles para empresas medianas.",            "category": "Información de producto","priority": "baja"},
    {"pqr_id": 3,  "text": "El técnico no llegó a la cita programada para el día de ayer y nadie me avisó del cambio.",                         "category": "Tecnica",               "priority": "media"},
    {"pqr_id": 4,  "text": "El producto llegó completamente dañado. El empaque estaba roto y faltaban piezas. Quiero solución inmediata.",       "category": "Producto defectuoso",    "priority": "alta"},
    {"pqr_id": 5,  "text": "¿Cuáles son los requisitos para acceder al programa de mantenimiento preventivo trimestral?",                        "category": "Información de producto","priority": "baja"},
    {"pqr_id": 6,  "text": "Llevo dos semanas sin resolver mi caso y ya voy para la tercera llamada sin ninguna respuesta concreta.",            "category": "Atención al cliente",    "priority": "alta"},
    {"pqr_id": 7,  "text": "Sugiero que implementen notificaciones automáticas por WhatsApp para el seguimiento de solicitudes.",                "category": "Atención al cliente",    "priority": "baja"},
    {"pqr_id": 8,  "text": "Me cobraron el doble en el último ciclo de facturación. Necesito que corrijan este error urgente.",                 "category": "Facturación incorrecta", "priority": "alta"},
    {"pqr_id": 9,  "text": "Necesito el certificado de garantía y las actas de entrega de los equipos instalados el mes pasado.",               "category": "Factura y documentos",   "priority": "media"},
    {"pqr_id": 10, "text": "El servicio de internet lleva tres días fallando en horario laboral, afectando gravemente nuestras operaciones.",    "category": "Servicio",               "priority": "alta"},
    {"pqr_id": 11, "text": "Quiero cancelar el contrato de servicio porque no estoy satisfecho con la calidad de la atención.",                 "category": "Cancelación de pedido",  "priority": "media"},
    {"pqr_id": 12, "text": "Por favor envíen el manual de usuario del equipo modelo XR-200 que adquirimos la semana pasada.",                   "category": "Información de producto","priority": "baja"},
    {"pqr_id": 13, "text": "El servicio prometido en el contrato no corresponde a lo que realmente están prestando. Exijo cumplimiento.",        "category": "Servicio",               "priority": "alta"},
    {"pqr_id": 14, "text": "El tiempo de espera en la línea de atención supera los 45 minutos. Esto afecta la experiencia del cliente.",         "category": "Atención al cliente",    "priority": "media"},
    {"pqr_id": 15, "text": "Propongo que habiliten un canal de autogestión en línea para cambios de dirección de facturación.",                  "category": "Cambio de datos",        "priority": "baja"},
    {"pqr_id": 16, "text": "Solicito copia de todos los contratos vigentes entre mi empresa y la suya para auditoría interna.",                  "category": "Factura y documentos",   "priority": "media"},
    {"pqr_id": 17, "text": "La aplicación móvil sigue crasheando cuando intento ver el historial de pagos. Ya lo reporté hace un mes.",          "category": "Servicio",               "priority": "media"},
    {"pqr_id": 18, "text": "Me están cobrando por un servicio que di de baja hace tres meses. Exijo la devolución total.",                       "category": "Devolución y reembolso", "priority": "alta"},
    {"pqr_id": 19, "text": "¿Tienen planes especiales para instituciones educativas? Somos una universidad pública.",                            "category": "Información de producto","priority": "baja"},
    {"pqr_id": 20, "text": "El personal de soporte fue muy amable y resolvió mi problema en menos de una hora. Muchas gracias.",                 "category": "Atención al cliente",    "priority": "baja"},
]


def generate_sample_file():
    """Genera un archivo JSON de casos de prueba de ejemplo."""
    path = Path("casos_muestra.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_CASES, f, ensure_ascii=False, indent=2)
    print(f"{GREEN}✓{RESET} Archivo de muestra generado: {BOLD}{path.absolute()}{RESET}")
    print(f"{DIM}  Úsalo con: python ai_evaluator.py --mode batch --file casos_muestra.json{RESET}\n")


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Evaluador del Agente IA – Sistema PQR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de uso:
  validate      Valida el JSON de casos sin llamar a la API (recomendado primero)
  interactive   Evalúa casos uno a uno con validación humana en tiempo real
  batch         Crea PQRs via POST /pqrs, clasifica via POST /classify/{id} y evalúa
  load_test     Prueba de carga (ciclo completo: crear + clasificar)
  report        Muestra reporte consolidado de todos los resultados
  sample        Genera un archivo JSON de casos de ejemplo para batch

Flujo recomendado:
  1. python ai_evaluator.py --mode validate  --file casos_muestra.json
  2. python ai_evaluator.py --mode batch     --file casos_muestra.json --user admin --password secret
  3. python ai_evaluator.py --mode report

Ejemplos:
  python ai_evaluator.py --mode validate  --file casos_muestra.json
  python ai_evaluator.py --mode batch     --file casos_muestra.json --token MY_TOKEN
  python ai_evaluator.py --mode load_test --n 200 --token MY_TOKEN
  python ai_evaluator.py --mode report
  python ai_evaluator.py --mode sample
        """
    )
    parser.add_argument("--host",     default=BASE_URL,           help=f"URL del backend (default: {BASE_URL})")
    parser.add_argument("--mode",     default="interactive",
                        choices=["validate", "interactive", "batch", "load_test", "report", "sample"],
                        help="Modo de ejecución")
    parser.add_argument("--file",     default="casos_muestra.json", help="Archivo JSON para modo batch/validate")
    parser.add_argument("--n",        type=int, default=100,       help="Número de requests para load_test")
    parser.add_argument("--token",    default=os.getenv("AUTH_TOKEN"),    help="Bearer token. También se lee AUTH_TOKEN.")
    parser.add_argument("--user",     default=os.getenv("AUTH_USER"),     help="Usuario para /auth/login.")
    parser.add_argument("--password", default=os.getenv("AUTH_PASSWORD"), help="Contraseña para /auth/login.")
    parser.add_argument("--clasificacion_id", type=int, default=None,
                        help="ID válido en tabla clasificaciones para POST /pqrs. "
                             "Si se omite, el campo no se envía (solo funciona si la columna es nullable).")

    args = parser.parse_args()

    # Modo validate y report no requieren API
    if args.mode in ("validate", "report", "sample"):
        if args.mode == "validate":
            run_validate(args.file)
        elif args.mode == "report":
            run_report()
        elif args.mode == "sample":
            generate_sample_file()
        return

    # Obtener token si no se proveyó
    token = args.token
    if not token and args.user and args.password:
        try:
            token = get_access_token(args.host, args.user, args.password)
            print(f"{GREEN}✓{RESET} Token obtenido automáticamente de /auth/login")
        except Exception as exc:
            print(f"{RED}Error al obtener token desde /auth/login: {exc}{RESET}")
            sys.exit(1)

    if not token:
        print(f"{RED}ERROR: Los endpoints requieren autenticación.{RESET}")
        print("Indica --token o define AUTH_TOKEN, o usa --user/--password para obtenerlo desde /auth/login.")
        sys.exit(1)

    clasificacion_id = args.clasificacion_id

    if args.mode == "interactive":
        run_interactive(args.host, token, clasificacion_id=clasificacion_id)
    elif args.mode == "batch":
        run_batch(args.host, args.file, token, clasificacion_id=clasificacion_id)
    elif args.mode == "load_test":
        run_load_test(args.host, args.n, token, clasificacion_id=clasificacion_id)


if __name__ == "__main__":
    main()