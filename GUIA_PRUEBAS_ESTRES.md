# Guía de Pruebas de Estrés - PQR & Historial

> Solo necesitas **Postman para Windows** y los **2 archivos** incluidos en este repositorio.

---

## Archivos necesarios

| Archivo | Ruta |
|---|---|
| Colección | `postman/collections/PQR_Stress_Tests.postman_collection.json` |
| Environment | `postman/environments/PQR_Stress_Env.postman_environment.json` |

---

## Paso 1 - Importar en Postman

1. Abre Postman para Windows
2. `File` → `Import` → `Files`
3. Selecciona ambos archivos (collection + environment)
4. En la esquina superior derecha, selecciona el environment **"PQR Stress Env"**

---

## Paso 2 - Verificar credenciales

Los usuarios de prueba vienen pre-cargados en la BD:

| Correo | Contraseña | Rol |
|---|---|---|
| admin@pqr.com | 123456 | admin |
| laura@pqr.com | 123456 | supervisor |
| operador@pqr.com | 123456 | operador |
| maria@pqr.com | 123456 | usuario (cliente) |

> Si cambiaste las contraseñas, edítalas en el environment (`admin_pass`, `supervisor_pass`, etc.)

---

## Paso 3 - Obtener tokens de acceso

1. En la colección, expande la carpeta **"🔐 00 - Auth"**
2. Ejecuta los 4 requests uno por uno (click `Send`)
3. Cada uno guarda automáticamente su token en las variables de entorno
4. Verifica que las variables `admin_token`, `supervisor_token`, `operador_token` y `usuario_token` tengan valor

---

## Paso 4 - Seed (pre-cargar PQRs)

Para las pruebas de estrés necesitas PQRs existentes en BD:

1. Ve a la carpeta **"📋 01 - PQR Service"**
2. Click derecho → `Run Folder`
3. Configura: **100 iteraciones**, **delay 0ms**
4. Click `Run`
5. Esto crea 100 PQRs con datos únicos. Si necesitas más, ejecuta de nuevo.

> Opcional: haz esto con la carpeta **"🔄 03 - Workflows"** para tener PQRs en distintos estados (pendiente, en_proceso, resuelta, cerrada).

---

## Paso 5 - Ejecutar pruebas de estrés

### Fase 1 - Baseline (carga mínima)

| Configuración | Valor |
|---|---|
| Carpeta | **"🟢 Baseline"** (dentro de Stress Suites) |
| Iteraciones | **10** |
| Delay | **1000ms** (1 segundo) |
| Data | No usar archivo |

**Objetivo:** Medir tiempos de respuesta base del sistema sin carga.

---

### Fase 2 - Carga media

| Configuración | Valor |
|---|---|
| Carpeta | **"🟡 Carga Media"** (dentro de Stress Suites) |
| Iteraciones | **100** |
| Delay | **200ms** |
| Data | No usar archivo |

**Objetivo:** Medir degradación bajo carga moderada sostenida.

---

### Fase 3 - Pico (carga máxima)

| Configuración | Valor |
|---|---|
| Carpeta | **"🔴 Pico"** (dentro de Stress Suites) |
| Iteraciones | **1000** |
| Delay | **0ms** |
| Data | No usar archivo |

**Objetivo:** Encontrar el punto de quiebre del sistema.

---

### Fase 4 - Workflows (flujo completo)

| Configuración | Valor |
|---|---|
| Carpeta | **"🔄 03 - Workflows"** |
| Iteraciones | **50** |
| Delay | **100ms** |
| Data | No usar archivo |

**Objetivo:** Medir latencia extremo a extremo (Crear → Clasificar → Resolver → Cerrar).

---

### Fase 5 - Spike (concurrencia real)

1. Abre **3 ventanas de Postman**
2. En cada una, selecciona la carpeta **"🔴 Pico"**
3. En cada ventana, configura el Runner: **200 iteraciones**, **delay 0ms**
4. Las 3 personas/ventanas hacen click en **"Run"** al mismo tiempo

**Objetivo:** Simular múltiples usuarios concurrentes golpeando el sistema.

---

## Paso 6 - Leer métricas desde el Runner

Cuando el Runner termina, Postman muestra automáticamente:

| Métrica | Dónde verla |
|---|---|
| **Tiempo promedio de respuesta** | `Avg` en la tabla de resultados |
| **Tiempo mínimo / máximo** | `Min` / `Max` en la tabla |
| **Requests por segundo** | `Requests/sec` |
| **Total de requests** | `Total` |
| **Errores (failed)** | `Failed` |
| **Tasa de error** | Failed / Total × 100 |
| **Distribución de tiempos** | Gráfico de líneas `Response Time` |

---

## Paso 7 - Generar gráficos de métricas

### Método 1: Capturas del Runner (sin instalar nada)

El Runner de Postman ya genera gráficos en tiempo real:

1. **Gráfico de Response Time:** Se dibuja automáticamente mientras corre la prueba (eje X = tiempo, eje Y = ms)
2. **Pie chart de resultados:** Muestra proporción de passed vs failed
3. **Tabla de requests:** Muestra tiempo individual por cada request

Para guardarlos:
- `Print Screen` + pegar en Paint/Word
- O usa la herramienta `Recortes` de Windows

### Método 2: Exportar resultados a JSON

1. En el Runner, click en el nombre del resultado
2. Click `Export Results` → guardar como `.json`
3. Puedes abrirlo en Excel o parsearlo con Python para gráficos personalizados

### Método 3: Exportar a CSV (para Excel)

1. En el Runner, click `Export Results`
2. Selecciona formato CSV
3. Abre el CSV en Excel
4. En Excel: inserta gráficos de línea para Response Time, columnas para errores, etc.

---

## Interpretación de resultados

| Resultado | Significa |
|---|---|
| Avg < 500ms en baseline | Sistema responde bien sin carga |
| Avg < 1000ms en carga media | Degradación aceptable |
| Avg > 3000ms en pico | Sistema está al límite |
| Errores 4xx | Problema de datos o autenticación |
| Errores 5xx | Servidor no soporta la carga |
| Timeouts | Servidor saturado, revisar conexiones BD |

---

## Troubleshooting

| Problema | Solución |
|---|---|
| `401 Unauthorized` | Los tokens expiraron (60 min). Re-ejecuta la carpeta Auth |
| `404 Not Found` | El `pqr_id` o `history_id` no existe. Corre el Seed primero |
| `400 Categoría no válida` | Cambia la variable `categoria` por una existente (Facturacion, Tecnica, Servicio, etc.) |
| Runner lento | Reduce el delay entre requests |
| Se acabaron los IDs | Las tablas usan SERIAL, no debería pasar. Si ocurre, resetea la BD |

---

## Resumen de fases

| Fase | Carpeta | Iteraciones | Delay | Objetivo |
|---|---|---|---|---|
| 🟢 Baseline | Stress Suites → 🟢 | 10 | 1000ms | Línea base |
| 🟡 Carga media | Stress Suites → 🟡 | 100 | 200ms | Degradación |
| 🔴 Pico | Stress Suites → 🔴 | 1000 | 0ms | Punto de quiebre |
| 🔄 Workflow | Workflows | 50 | 100ms | Latencia E2E |
| ⚡ Spike | 🔴 Pico (3 ventanas) | 200 c/u | 0ms | Concurrencia |
