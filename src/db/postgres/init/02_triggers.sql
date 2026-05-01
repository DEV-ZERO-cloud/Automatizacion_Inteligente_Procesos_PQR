-- ============================================================================
-- TRIGGERS DE AUTOMATIZACIÓN PARA EL PROYECTO PQR
-- ============================================================================

-- 1) Mantener updated_at de pqrs
CREATE OR REPLACE FUNCTION fn_pqr_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_pqr_update_timestamp ON pqrs;
CREATE TRIGGER trg_pqr_update_timestamp
BEFORE UPDATE ON pqrs
FOR EACH ROW
EXECUTE FUNCTION fn_pqr_update_timestamp();


-- 2) Auditar creación/cambio de estado en historial
CREATE OR REPLACE FUNCTION fn_audit_pqr_history()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO historial (pqr_id, usuario_id, accion, detalle)
        VALUES (
            NEW.id,
            NEW.usuario_id,
            'CREACION PQR',
            'La solicitud fue radicada con estado inicial: ' || NEW.estado
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.estado IS DISTINCT FROM NEW.estado THEN
            INSERT INTO historial (pqr_id, usuario_id, accion, detalle)
            VALUES (
                NEW.id,
                COALESCE(NEW.operador_id, NEW.supervisor_id, NEW.usuario_id),
                'CAMBIO ESTADO',
                'El estado cambió de "' || OLD.estado || '" a "' || NEW.estado || '"'
            );
        END IF;
        RETURN NEW;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_pqr_history ON pqrs;
CREATE TRIGGER trg_audit_pqr_history
AFTER INSERT OR UPDATE ON pqrs
FOR EACH ROW
EXECUTE FUNCTION fn_audit_pqr_history();


-- 3) Sincronizar clasificación vigente en pqrs
CREATE OR REPLACE FUNCTION fn_update_pqr_on_classification()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pqrs
    SET
        clasificacion_id = NEW.id,
        estado = CASE WHEN estado = 'pendiente' THEN 'en_proceso' ELSE estado END
    WHERE id = NEW.pqr_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_pqr_on_classification ON clasificaciones;
CREATE TRIGGER trg_update_pqr_on_classification
AFTER INSERT ON clasificaciones
FOR EACH ROW
EXECUTE FUNCTION fn_update_pqr_on_classification();