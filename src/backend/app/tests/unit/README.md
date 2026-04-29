# 🧪 Pruebas Unitarias – Sistema PQR

## Estructura

```
unit_tests/
├── conftest.py                  # Fixtures globales (mock DB, mock settings)
├── requirements-test.txt        # Dependencias
├── test_user_auth.py            # Tests de Autenticación y Usuarios
└── test_reports_dashboard.py    # Tests de Reportes y Dashboard
```

## Módulos cubiertos

### `test_user_auth.py` (40 tests)
| Clase | Qué prueba |
|---|---|
| `TestSecurity` | hash, verify, is_hashed de contraseñas |
| `TestAuth` | encode_token, get_current_user, scopes, cookies |
| `TestLogin` | login exitoso, inactivo, no existe, pass incorrecta, roles |
| `TestRegister` | registro OK, correo dup, id dup, rol asignado |
| `TestCreateUser` | creación admin, correo dup |
| `TestGetUsers` | lista, por id, no existe, solo supervisores |
| `TestUpdateDeleteUser` | update OK, 404, delete OK, 404 |

### `test_reports_dashboard.py` (27 tests)
| Clase | Qué prueba |
|---|---|
| `TestDashboard` | resumen, estructura, suma correcta, 500, sin datos |
| `TestByCategory` | petición/queja/reclamo, vacío, 500 |
| `TestByPriority` | alta/media/baja, totales positivos, 500 |
| `TestByArea` | áreas, vacío, 500 |
| `TestReportAccessControl` | admin/supervisor OK, agente/usuario 403, sin token 401 |

## Instalación y ejecución

```bash
# 1. Instalar dependencias (desde la raíz del proyecto)
pip install -r tests/unit_tests/requirements-test.txt

# 2. Ejecutar todos los tests
pytest tests/unit_tests/ -v

# 3. Con reporte de cobertura
pip install pytest-cov
pytest tests/unit_tests/ -v --cov=app --cov-report=html

# 4. Solo un módulo
pytest tests/unit_tests/test_user_auth.py -v
pytest tests/unit_tests/test_reports_dashboard.py -v
```

## Notas importantes

- Los tests usan `unittest.mock` para evitar conexiones reales a PostgreSQL.
- El `conftest.py` parchea automáticamente `psycopg2.connect` y `settings`.
- Los tests de funciones `async` usan `pytest-asyncio` con decorador `@pytest.mark.asyncio`.
- Coloca esta carpeta dentro de `proyecto/tests/unit/` para mantener la estructura existente.

## Variables de entorno (no requeridas para unit tests)

Los mocks en `conftest.py` sobreescriben `SECRET_KEY` con un valor de prueba.
Para integración, sí necesitas un `.env` con las variables reales.
