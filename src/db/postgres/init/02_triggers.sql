-- ==============================================================================
-- TRIGGERS DE AUTOMATIZACIÓN PARA EL PROYECTO PQR
-- Este archivo se ejecuta automáticamente al inicializar la BD en Docker
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. TRIGGER: Auto-actualizador de fecha (updated_at)
-- Propósito: Cada vez que una PQR es modificada, se actualiza automáticamente 
-- su campo 'updated_at' sin depender de que el backend envíe la fecha.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_pqr_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pqr_update_timestamp ON "PQRS";
CREATE TRIGGER trg_pqr_update_timestamp
BEFORE UPDATE ON "PQRS"
FOR EACH ROW
EXECUTE FUNCTION fn_pqr_update_timestamp();


-- ------------------------------------------------------------------------------
-- 2. TRIGGER: Automatización de Historial (Auditoría automática)
-- Propósito: Cuando se crea una PQR o cambia de estado, se genera 
-- automáticamente un registro en la tabla HISTORIAL, ahorrando múltiples 
-- llamados a la base de datos desde el backend (Pseudo-CQRS).
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_audit_pqr_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Caso 1: Creación de una PQR nueva
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO "HISTORIAL" (pqr_id, usuario_id, accion, comentario, created_at)
        VALUES (
            NEW.id, 
            NEW.usuario_id, 
            'CREACIÓN PQR', 
            'La solicitud PQR ha sido radicada exitosamente con estado inicial: ' || NEW.estado, 
            CURRENT_TIMESTAMP
        );
        RETURN NEW;
    
    -- Caso 2: Actualización de estado en una PQR existente
    ELSIF (TG_OP = 'UPDATE') THEN
        -- Solo se registra en el historial si el estado cambió
        IF (OLD.estado IS DISTINCT FROM NEW.estado) THEN
            INSERT INTO "HISTORIAL" (pqr_id, usuario_id, accion, comentario, created_at)
            VALUES (
                NEW.id, 
                NEW.operador_id, -- El operador que realizó el cambio (o el sistema)
                'CAMBIO ESTADO', 
                'El estado cambió de "' || OLD.estado || '" a "' || NEW.estado || '"', 
                CURRENT_TIMESTAMP
            );
        END IF;
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_pqr_history ON "PQRS";
CREATE TRIGGER trg_audit_pqr_history
AFTER INSERT OR UPDATE ON "PQRS"
FOR EACH ROW
EXECUTE FUNCTION fn_audit_pqr_history();


-- ------------------------------------------------------------------------------
-- 3. TRIGGER: Validar Clasificación y Notificar
-- Propósito: Cuando se inserta una Clasificación (por la IA), 
-- cambia el estado de la PQR a "Clasificada" o "Pendiente Validación" 
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_update_pqr_on_classification()
RETURNS TRIGGER AS $$
BEGIN
    -- Cuando la IA (o un humano) clasifica la PQR, actualizamos la tabla PQRS
    -- enlazando la id de esta clasificación al campo clasificacion_id de PQR.
    UPDATE "PQRS"
    SET clasificacion_id = NEW.id,
        estado = 'En Análisis' -- Estado después de clasificar
    WHERE id = NEW.pqr_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_pqr_on_classification ON "CLASIFICACIONES";
CREATE TRIGGER trg_update_pqr_on_classification
AFTER INSERT ON "CLASIFICACIONES"
FOR EACH ROW
EXECUTE FUNCTION fn_update_pqr_on_classification();