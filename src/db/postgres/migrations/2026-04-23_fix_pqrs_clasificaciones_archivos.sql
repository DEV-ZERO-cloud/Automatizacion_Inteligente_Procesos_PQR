BEGIN;

-- 1) Asegura columna de clasificación vigente en pqrs.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'pqrs'
          AND column_name = 'clasificacion_id'
    ) THEN
        ALTER TABLE pqrs ADD COLUMN clasificacion_id INTEGER;
    END IF;
END $$;

-- 2) Inserta categorías faltantes basadas en datos legacy de pqrs.categoria.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'pqrs'
          AND column_name = 'categoria'
    ) THEN
        WITH source_values AS (
            SELECT DISTINCT BTRIM(categoria) AS nombre
            FROM pqrs
            WHERE categoria IS NOT NULL
              AND BTRIM(categoria) <> ''
        ), missing AS (
            SELECT s.nombre
            FROM source_values s
            LEFT JOIN categorias c ON LOWER(c.nombre) = LOWER(s.nombre)
            WHERE c.id IS NULL
        ), numbered AS (
            SELECT nombre, ROW_NUMBER() OVER (ORDER BY nombre) AS rn
            FROM missing
        ), base AS (
            SELECT COALESCE(MAX(id), 0) AS max_id
            FROM categorias
        )
        INSERT INTO categorias (id, nombre)
        SELECT base.max_id + numbered.rn, numbered.nombre
        FROM numbered
        CROSS JOIN base;
    END IF;
END $$;

-- 3) Inserta prioridades faltantes basadas en datos legacy de pqrs.prioridad.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'pqrs'
          AND column_name = 'prioridad'
    ) THEN
        WITH source_values AS (
            SELECT DISTINCT LOWER(BTRIM(prioridad)) AS nombre
            FROM pqrs
            WHERE prioridad IS NOT NULL
              AND BTRIM(prioridad) <> ''
        ), missing AS (
            SELECT s.nombre
            FROM source_values s
            LEFT JOIN prioridades p ON LOWER(p.nombre) = LOWER(s.nombre)
            WHERE p.id IS NULL
        ), numbered AS (
            SELECT nombre, ROW_NUMBER() OVER (ORDER BY nombre) AS rn
            FROM missing
        ), base AS (
            SELECT COALESCE(MAX(id), 0) AS max_id
            FROM prioridades
        )
        INSERT INTO prioridades (id, nombre)
        SELECT base.max_id + numbered.rn, numbered.nombre
        FROM numbered
        CROSS JOIN base;
    END IF;
END $$;

-- 4) Migra clasificación desde columnas legacy si no existe en clasificaciones.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'pqrs'
          AND column_name = 'categoria'
    ) AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'pqrs'
          AND column_name = 'prioridad'
    ) THEN
        INSERT INTO clasificaciones (
            pqr_id,
            modelo_version,
            categoria_id,
            prioridad_id,
            confianza,
            origen,
            fue_corregida,
            validado_por
        )
        SELECT
            p.id,
            'legacy-migration',
            c.id,
            pr.id,
            0.5000,
            'MANUAL',
            TRUE,
            NULL
        FROM pqrs p
        JOIN categorias c
          ON LOWER(c.nombre) = LOWER(BTRIM(p.categoria))
        JOIN prioridades pr
          ON LOWER(pr.nombre) = LOWER(BTRIM(p.prioridad))
        LEFT JOIN clasificaciones existing
          ON existing.pqr_id = p.id
        WHERE existing.id IS NULL
          AND p.categoria IS NOT NULL
          AND p.prioridad IS NOT NULL
          AND BTRIM(p.categoria) <> ''
          AND BTRIM(p.prioridad) <> '';
    END IF;
END $$;

-- 5) Sincroniza pqrs.clasificacion_id con la clasificación más reciente de cada PQR.
WITH latest_classification AS (
    SELECT DISTINCT ON (pqr_id)
        pqr_id,
        id
    FROM clasificaciones
    ORDER BY pqr_id, created_at DESC, id DESC
)
UPDATE pqrs p
SET clasificacion_id = lc.id
FROM latest_classification lc
WHERE p.id = lc.pqr_id
  AND (p.clasificacion_id IS DISTINCT FROM lc.id);

-- 6) Asegura FK e índice para clasificación vigente.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'pqrs_clasificacion_id_fkey'
    ) THEN
        ALTER TABLE pqrs
        ADD CONSTRAINT pqrs_clasificacion_id_fkey
        FOREIGN KEY (clasificacion_id)
        REFERENCES clasificaciones(id)
        ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_pqrs_clasificacion_id ON pqrs (clasificacion_id);

-- 7) Elimina columnas legacy de pqrs.
ALTER TABLE pqrs DROP COLUMN IF EXISTS categoria;
ALTER TABLE pqrs DROP COLUMN IF EXISTS prioridad;

COMMIT;
