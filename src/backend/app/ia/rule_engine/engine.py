"""
engine.py

Motor de reglas responsable ÚNICAMENTE de:
  - add_tags:  extraer palabras clave del texto
  - set_area:  asignar el área de dependencia responsable

La categoría y la prioridad son responsabilidad del modelo ML (classifier.py).

Diseño:
  - Las reglas se cargan desde rules.yaml y se compilan al iniciar.
  - Keywords → frozenset para búsqueda O(1).
  - Regex → re.Pattern precompilado.
  - Recarga en caliente vía reload() sin reiniciar el servicio.
"""

import re
import logging
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).parent / "rules.yaml"


# ── Resultado del motor de reglas ──────────────────────────────────────────────

@dataclass
class RuleResult:
    area: str | None = None                        # área de dependencia
    tags: list[str] = field(default_factory=list)  # palabras clave acumuladas
    rules_matched: list[str] = field(default_factory=list)


# ── Estructuras internas compiladas ───────────────────────────────────────────

@dataclass
class _CompiledCondition:
    keywords: frozenset[str] | None   # None si es regex
    pattern: re.Pattern | None        # None si es contains


@dataclass
class _CompiledRule:
    id: str
    operator: str                          # "AND" | "OR"
    conditions: list[_CompiledCondition]
    set_area: str | None
    add_tags: list[str]


# ── Motor principal ────────────────────────────────────────────────────────────

class RuleEngine:
    """
    Motor de reglas para extracción de tags y área de dependencia.

    Uso:
        engine = RuleEngine()
        result = engine.evaluate(texto_limpio)
        # result.area  → "Logística"
        # result.tags  → ["pedido no entregado", "entrega"]
    """

    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules_path = rules_path
        self._compiled: list[_CompiledRule] = []
        self.load_rules()

    # ── Propiedad pública ──────────────────────────────────────────────────────

    @property
    def rules(self) -> list[_CompiledRule]:
        return self._compiled

    # ── Carga y compilación ────────────────────────────────────────────────────

    def load_rules(self) -> None:
        """Carga el YAML y compila todas las reglas."""
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_rules: list[dict[str, Any]] = sorted(
            data.get("rules", []),
            key=lambda r: r.get("priority", 99),
        )
        self._compiled = [self._compile(r) for r in raw_rules]
        logger.info("[RuleEngine] %d reglas compiladas desde %s.", len(self._compiled), self.rules_path.name)

    def reload(self) -> None:
        """Recarga reglas en caliente sin reiniciar el servicio."""
        self.load_rules()
        logger.info("[RuleEngine] Reglas recargadas.")

    @staticmethod
    def _compile(raw: dict[str, Any]) -> _CompiledRule:
        block    = raw.get("conditions", {})
        operator = block.get("operator", "OR").upper()

        conditions: list[_CompiledCondition] = []
        for item in block.get("items", []):
            if "contains" in item:
                conditions.append(_CompiledCondition(
                    keywords=frozenset(kw.lower() for kw in item["contains"]),
                    pattern=None,
                ))
            elif "regex" in item:
                conditions.append(_CompiledCondition(
                    keywords=None,
                    pattern=re.compile(item["regex"], re.IGNORECASE),
                ))

        actions = raw.get("actions", {})
        return _CompiledRule(
            id=raw["id"],
            operator=operator,
            conditions=conditions,
            set_area=actions.get("set_area"),       # ← solo área
            add_tags=actions.get("add_tags", []),   # ← solo tags
        )

    # ── Evaluación ─────────────────────────────────────────────────────────────

    @staticmethod
    def _match_condition(cond: _CompiledCondition, text: str) -> bool:
        if cond.keywords is not None:
            return any(kw in text for kw in cond.keywords)
        return bool(cond.pattern.search(text))  # type: ignore[union-attr]

    def evaluate(self, text: str) -> RuleResult:
        """
        Evalúa todas las reglas sobre el texto (debe venir ya limpio/minúsculas).

        Returns:
            RuleResult con area, tags y rules_matched.
        """
        text_lower = text.lower()
        result     = RuleResult()
        tags_seen: set[str] = set()

        for rule in self._compiled:
            if rule.operator == "AND":
                matched = all(self._match_condition(c, text_lower) for c in rule.conditions)
            else:
                matched = any(self._match_condition(c, text_lower) for c in rule.conditions)

            if not matched:
                continue

            result.rules_matched.append(rule.id)

            # Área: primera regla que hace match gana
            if rule.set_area and result.area is None:
                result.area = rule.set_area

            # Tags: acumulan sin duplicados
            for tag in rule.add_tags:
                if tag not in tags_seen:
                    tags_seen.add(tag)
                    result.tags.append(tag)

        return result