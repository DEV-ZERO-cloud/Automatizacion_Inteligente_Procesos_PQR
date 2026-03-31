import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field

RULES_PATH = Path(__file__).parent / "rules.yaml"


@dataclass
class RuleResult:
    category: str | None = None
    tags: list[str] = field(default_factory=list)
    priority: str | None = None
    rules_matched: list[str] = field(default_factory=list)


class RuleEngine:
    def __init__(self, rules_path: Path = RULES_PATH):
        self.rules_path = rules_path
        self.rules = []
        self.load_rules()

    def load_rules(self):
        """Carga y ordena reglas por prioridad (menor número = mayor precedencia)."""
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.rules = sorted(data["rules"], key=lambda r: r.get("priority", 99))
        print(f"[RuleEngine] {len(self.rules)} reglas cargadas.")

    def reload(self):
        """Recarga reglas en caliente sin reiniciar el servicio."""
        self.load_rules()

    def _evaluate_condition(self, condition: dict, text: str) -> bool:
        """Evalúa una condición individual sobre el texto."""
        text_lower = text.lower()
        if "contains" in condition:
            return any(kw.lower() in text_lower for kw in condition["contains"])
        if "regex" in condition:
            return bool(re.search(condition["regex"], text_lower))
        return False

    def _evaluate_conditions(self, conditions: dict, text: str) -> bool:
        """Evalúa un bloque de condiciones con operador AND/OR."""
        operator = conditions.get("operator", "OR").upper()
        items = conditions.get("items", [])

        results = [self._evaluate_condition(item, text) for item in items]

        if operator == "AND":
            return all(results)
        return any(results)

    def evaluate(self, text: str) -> RuleResult:
        """
        Evalúa todas las reglas sobre el texto.
        Devuelve un RuleResult con las acciones acumuladas.
        """
        result = RuleResult()

        for rule in self.rules:
            conditions = rule.get("conditions", {})
            if not self._evaluate_conditions(conditions, text):
                continue

            # Regla coincide — aplicar acciones
            result.rules_matched.append(rule["id"])
            actions = rule.get("actions", {})

            if "set_category" in actions and result.category is None:
                result.category = actions["set_category"]

            if "set_priority" in actions and result.priority is None:
                result.priority = actions["set_priority"]

            if "add_tags" in actions:
                for tag in actions["add_tags"]:
                    if tag not in result.tags:
                        result.tags.append(tag)

        return result