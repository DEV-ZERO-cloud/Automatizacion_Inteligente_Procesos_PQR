"""
UniversalControllerJSON
=======================
Controlador universal que usa archivos .json como base de datos local.
Tiene la MISMA interfaz pública que UniversalController (SQL Server),
por lo que es un reemplazo transparente para pruebas en local.

Estructura de archivos en disco
--------------------------------
db/
├── Usuario.json
├── PQR.json
├── Area.json
└── ...

Cada archivo JSON es una lista de objetos:
[
  {"ID": 1, "nombre": "Ana", "correo": "ana@pqr.com", ...},
  {"ID": 2, "nombre": "Luis", ...}
]

Cómo activarlo
--------------
En universal_controller_instance.py, cambia la línea de importación:

    # Para SQL Server (producción)
    from app.logic.universal_controller_sql import UniversalController

    # Para JSON local (desarrollo / pruebas)
    from app.logic.universal_controller_json import UniversalControllerJSON as UniversalController

O bien, usa la variable de entorno DB_MODE=json (ver abajo).
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carpeta donde se guardan los archivos JSON.
# Puede sobreescribirse con la variable de entorno DB_JSON_PATH.
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent.parent / "db"


class UniversalControllerJSON:
    """
    Controlador universal con persistencia en archivos JSON.

    Misma interfaz pública que UniversalController (SQL Server):
        get_all, get_by_id, get_by_column, add, update, delete
        + métodos de reportes de PQR
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(os.getenv("DB_JSON_PATH", db_path or DEFAULT_DB_PATH))
        self.db_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()          # seguridad en entornos con hilos
        logger.info("UniversalControllerJSON inicializado. DB_PATH=%s", self.db_path)

    # ══════════════════════════════════════════════════════════════════════════
    #  Utilidades internas
    # ══════════════════════════════════════════════════════════════════════════

    def _file(self, table: str) -> Path:
        """Retorna la ruta del archivo JSON para la tabla dada."""
        return self.db_path / f"{table}.json"

    def _load(self, table: str) -> List[dict]:
        """Lee todos los registros de una tabla (archivo JSON)."""
        f = self._file(table)
        if not f.exists():
            return []
        with open(f, "r", encoding="utf-8") as fp:
            try:
                data = json.load(fp)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                logger.warning("Archivo JSON corrupto: %s. Se devuelve lista vacía.", f)
                return []

    def _save(self, table: str, records: List[dict]) -> None:
        """Persiste la lista de registros en el archivo JSON correspondiente."""
        f = self._file(table)
        with open(f, "w", encoding="utf-8") as fp:
            json.dump(records, fp, ensure_ascii=False, indent=2)

    def _get_table_name(self, obj: Any) -> str:
        """Obtiene __entity_name__ del objeto o su clase."""
        if hasattr(obj, "__entity_name__"):
            return obj.__entity_name__
        if hasattr(obj.__class__, "__entity_name__"):
            return obj.__class__.__entity_name__
        raise ValueError(
            f"El objeto {type(obj).__name__} no tiene definido '__entity_name__'."
        )

    def _next_id(self, records: List[dict]) -> int:
        """Genera el próximo ID autoincremental."""
        if not records:
            return 1
        return max((r.get("ID", 0) for r in records), default=0) + 1

    # ══════════════════════════════════════════════════════════════════════════
    #  CRUD genérico  (idéntico al de SQL Server)
    # ══════════════════════════════════════════════════════════════════════════

    def get_all(self, cls: Any) -> List[Any]:
        """Retorna todos los registros de la tabla asociada a cls."""
        table = cls.__entity_name__
        with self._lock:
            records = self._load(table)
        logger.info("[JSON] get_all(%s) → %d registros", table, len(records))
        return [cls.from_dict(r) for r in records]

    def get_by_id(self, cls: Any, record_id: int) -> Optional[Any]:
        """Retorna el registro cuyo ID coincida, o None."""
        table = cls.__entity_name__
        with self._lock:
            records = self._load(table)
        match = next((r for r in records if r.get("ID") == record_id), None)
        if match is None:
            logger.info("[JSON] get_by_id(%s, %s) → no encontrado", table, record_id)
            return None
        logger.info("[JSON] get_by_id(%s, %s) → encontrado", table, record_id)
        return cls.from_dict(match)

    def get_by_column(self, cls: Any, column: str, value: Any) -> Optional[Any]:
        """Retorna el primer registro donde column == value, o None."""
        table = cls.__entity_name__
        with self._lock:
            records = self._load(table)
        match = next((r for r in records if r.get(column) == value), None)
        if match is None:
            logger.info("[JSON] get_by_column(%s.%s=%s) → no encontrado", table, column, value)
            return None
        logger.info("[JSON] get_by_column(%s.%s=%s) → encontrado", table, column, value)
        return cls.from_dict(match)

    def add(self, obj: Any) -> Any:
        """
        Inserta un nuevo registro.
        Si ID es None o 0, se asigna automáticamente (autoincremental).
        """
        table = self._get_table_name(obj)
        data = obj.to_dict()

        with self._lock:
            records = self._load(table)

            # Autoincremental si no viene ID
            if not data.get("ID"):
                data["ID"] = self._next_id(records)
                # Sincronizar con el objeto si tiene atributo ID
                if hasattr(obj, "ID"):
                    object.__setattr__(obj, "ID", data["ID"]) if hasattr(obj, "__fields__") else setattr(obj, "ID", data["ID"])

            # Verificar duplicado de ID
            if any(r.get("ID") == data["ID"] for r in records):
                raise ValueError(
                    f"Ya existe un registro con ID={data['ID']} en {table}."
                )

            records.append(data)
            self._save(table, records)

        logger.info("[JSON] add(%s) → ID=%s insertado", table, data["ID"])
        return obj

    def update(self, obj: Any) -> Any:
        """Actualiza el registro cuyo ID coincida con el del objeto."""
        table = self._get_table_name(obj)
        data = obj.to_dict()

        if not data.get("ID"):
            raise ValueError("El objeto debe tener un campo 'ID' válido para actualizar.")

        with self._lock:
            records = self._load(table)
            idx = next((i for i, r in enumerate(records) if r.get("ID") == data["ID"]), None)

            if idx is None:
                raise ValueError(
                    f"No existe registro con ID={data['ID']} en {table}."
                )

            records[idx] = data
            self._save(table, records)

        logger.info("[JSON] update(%s) → ID=%s actualizado", table, data["ID"])
        return obj

    def delete(self, obj: Any) -> bool:
        """Elimina el registro cuyo ID coincida con el del objeto."""
        table = self._get_table_name(obj)
        data = obj.to_dict()

        if not data.get("ID"):
            raise ValueError("El objeto debe tener un campo 'ID' válido para eliminar.")

        with self._lock:
            records = self._load(table)
            original_len = len(records)
            records = [r for r in records if r.get("ID") != data["ID"]]

            if len(records) == original_len:
                raise ValueError(
                    f"No existe registro con ID={data['ID']} en {table}."
                )

            self._save(table, records)

        logger.info("[JSON] delete(%s) → ID=%s eliminado", table, data["ID"])
        return True

    # ══════════════════════════════════════════════════════════════════════════
    #  Reportes de PQR  (misma interfaz que el controlador SQL)
    # ══════════════════════════════════════════════════════════════════════════

    def get_dashboard_summary(self) -> dict:
        """
        Retorna totales de PQR: total, pendientes y resueltas.
        Lee directamente del archivo PQR.json.
        """
        with self._lock:
            pqrs = self._load("PQR")

        total = len(pqrs)
        pendientes = sum(1 for p in pqrs if p.get("estado") == "pendiente")
        resueltas = sum(1 for p in pqrs if p.get("estado") == "resuelta")

        logger.info("[JSON] dashboard → total=%d pendientes=%d resueltas=%d", total, pendientes, resueltas)
        return {"total_pqrs": total, "pendientes": pendientes, "resueltas": resueltas}

    def get_pqrs_by_category(self) -> List[dict]:
        """Agrupa PQR por el campo 'categoria' y retorna conteos."""
        with self._lock:
            pqrs = self._load("PQR")

        counts: dict = {}
        for p in pqrs:
            cat = p.get("categoria", "Sin categoría")
            counts[cat] = counts.get(cat, 0) + 1

        result = [{"categoria": k, "cantidad": v} for k, v in counts.items()]
        result.sort(key=lambda x: x["cantidad"], reverse=True)
        logger.info("[JSON] by-category → %d categorías", len(result))
        return result

    def get_pqrs_by_priority(self) -> List[dict]:
        """Agrupa PQR por el campo 'prioridad' y retorna conteos."""
        with self._lock:
            pqrs = self._load("PQR")

        counts: dict = {}
        for p in pqrs:
            pri = p.get("prioridad", "sin prioridad")
            counts[pri] = counts.get(pri, 0) + 1

        result = [{"prioridad": k, "cantidad": v} for k, v in counts.items()]
        result.sort(key=lambda x: x["cantidad"], reverse=True)
        logger.info("[JSON] by-priority → %d prioridades", len(result))
        return result

    def get_pqrs_by_area(self) -> List[dict]:
        """
        Agrupa PQR por área, cruzando con Area.json para obtener el nombre.
        Si no existe Area.json usa el ID como nombre.
        """
        with self._lock:
            pqrs = self._load("PQR")
            areas_raw = self._load("Area")

        area_map = {a["ID"]: a.get("nombre", str(a["ID"])) for a in areas_raw}

        counts: dict = {}
        for p in pqrs:
            area_id = p.get("area_id")
            area_name = area_map.get(area_id, f"Área {area_id}")
            counts[area_name] = counts.get(area_name, 0) + 1

        result = [{"area": k, "cantidad": v} for k, v in counts.items()]
        result.sort(key=lambda x: x["cantidad"], reverse=True)
        logger.info("[JSON] by-area → %d áreas", len(result))
        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  Utilidades de desarrollo
    # ══════════════════════════════════════════════════════════════════════════

    def seed(self, table: str, records: List[dict], overwrite: bool = False) -> None:
        """
        Precarga datos de prueba en una tabla JSON.

        Args:
            table: Nombre de la tabla (ej. "Usuario", "PQR").
            records: Lista de dicts a insertar.
            overwrite: Si True, reemplaza todos los datos existentes.
                       Si False, solo inserta si la tabla está vacía.
        """
        with self._lock:
            existing = self._load(table)
            if existing and not overwrite:
                logger.info("[JSON] seed(%s) → omitido, ya tiene %d registros", table, len(existing))
                return
            self._save(table, records)
        logger.info("[JSON] seed(%s) → %d registros cargados", table, len(records))

    def drop_table(self, table: str) -> None:
        """Elimina el archivo JSON de la tabla (equivale a DROP TABLE)."""
        f = self._file(table)
        if f.exists():
            f.unlink()
            logger.info("[JSON] drop_table(%s) → eliminado", table)

    def clear_tables(self) -> None:
        """Elimina todos los datos de todas las tablas existentes sin borrar los archivos."""
        with self._lock:
            tables = self.list_tables()
            for table in tables:
                self._save(table, [])
                logger.info("[JSON] clear_tables() → tabla %s limpiada", table)

    def list_tables(self) -> List[str]:
        """Lista todas las tablas (archivos .json) existentes en la carpeta db."""
        return [f.stem for f in self.db_path.glob("*.json")]

    def dump(self, table: str) -> List[dict]:
        """Retorna todos los registros crudos de una tabla (para depuración)."""
        with self._lock:
            return self._load(table)
