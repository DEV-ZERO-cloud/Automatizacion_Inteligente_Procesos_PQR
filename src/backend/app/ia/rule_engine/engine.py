import re
import logging
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

RULES_PATH = Path(__file__).parent / "rules.yaml"


@dataclass
class RuleResult:
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: str | None = None
    rules_matched: list[str] = field(default_factory=list)


@dataclass
class _CompiledCondition:
    """Condición pre-procesada para evaluación rápida."""
    keywords: frozenset[str] | None  # None si es regex
    pattern: re.Pattern | None       # None si es contains


@dataclass
class _CompiledRule:
    id: str
    operator: str                          # "AND" | "OR"
    conditions: list[_CompiledCondition]
    set_category: str | None
    set_priority: str | None
    add_tags: list[str]


class RuleEngine:
    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules_path = rules_path
        self._compiled: list[_CompiledRule] = []
        self.load_rules()

    # ──────────────────────────────────────────────
    # Carga y compilación
    # ──────────────────────────────────────────────

    def load_rules(self) -> None:
        """Carga reglas desde YAML y las compila (keywords→frozenset, regex→re.Pattern)."""
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_rules: list[dict[str, Any]] = sorted(
            data["rules"], key=lambda r: r.get("priority", 99)
        )
        self._compiled = [self._compile_rule(r) for r in raw_rules]
        logger.info("[RuleEngine] %d reglas compiladas.", len(self._compiled))

    def reload(self) -> None:
        """Recarga reglas en caliente sin reiniciar el servicio."""
        self.load_rules()

    @staticmethod
    def _compile_rule(raw: dict[str, Any]) -> _CompiledRule:
        conditions_block = raw.get("conditions", {})
        operator = conditions_block.get("operator", "OR").upper()
        compiled_conditions: list[_CompiledCondition] = []

        for item in conditions_block.get("items", []):
            if "contains" in item:
                # Convertir lista a frozenset de strings en minúsculas para O(1) lookup
                compiled_conditions.append(
                    _CompiledCondition(
                        keywords=frozenset(kw.lower() for kw in item["contains"]),
                        pattern=None,
                    )
                )
            elif "regex" in item:
                compiled_conditions.append(
                    _CompiledCondition(
                        keywords=None,
                        pattern=re.compile(item["regex"], re.IGNORECASE),
                    )
                )

        actions = raw.get("actions", {})
        return _CompiledRule(
            id=raw["id"],
            operator=operator,
            conditions=compiled_conditions,
            set_category=actions.get("set_category"),
            set_priority=actions.get("set_priority"),
            add_tags=actions.get("add_tags", []),
        )

    # ──────────────────────────────────────────────
    # Evaluación
    # ──────────────────────────────────────────────

    @staticmethod
    def _eval_condition(cond: _CompiledCondition, text: str) -> bool:
        if cond.keywords is not None:
            # Búsqueda de subcadena: cualquier keyword presente en el texto
            return any(kw in text for kw in cond.keywords)
        # Regex pre-compilado
        return bool(cond.pattern.search(text))  # type: ignore[union-attr]

    def evaluate(self, text: str) -> RuleResult:
        """
        Evalúa todas las reglas sobre el texto (ya debe venir en minúsculas).
        Devuelve un RuleResult con las acciones acumuladas.
        """
        text_lower = text.lower()
        result = RuleResult()
        tags_seen: set[str] = set()

        for rule in self._compiled:
            # Cortocircuito AND/OR sin construir lista completa de resultados
            if rule.operator == "AND":
                matched = all(self._eval_condition(c, text_lower) for c in rule.conditions)
            else:  # OR
                matched = any(self._eval_condition(c, text_lower) for c in rule.conditions)

            if not matched:
                continue

            result.rules_matched.append(rule.id)

            if rule.set_category and result.category is None:
                result.category = rule.set_category

            if rule.set_priority and result.priority is None:
                result.priority = rule.set_priority

            for tag in rule.add_tags:
                if tag not in tags_seen:
                    tags_seen.add(tag)
                    result.tags.append(tag)

        return result