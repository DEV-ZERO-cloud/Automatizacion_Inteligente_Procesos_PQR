CREATE TABLE IF NOT EXISTS rol (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS areas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    identificacion VARCHAR(30),
    nombre VARCHAR(120) NOT NULL,
    correo VARCHAR(120) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    rol_id INTEGER NOT NULL REFERENCES rol(id),
    area_id INTEGER REFERENCES areas(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    contrasena VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS pqrs (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN ('peticion', 'queja', 'reclamo')),
    categoria VARCHAR(80),
    prioridad VARCHAR(30) CHECK (prioridad IS NULL OR prioridad IN ('baja', 'media', 'alta', 'urgente')),
    estado VARCHAR(30) NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'en_proceso', 'resuelta', 'cerrada')),
    area_id INTEGER REFERENCES areas(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    operador_id INTEGER REFERENCES usuarios(id),
    supervisor_id INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS prioridades (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS clasificaciones (
    id SERIAL PRIMARY KEY,
    pqr_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    modelo_version VARCHAR(30) NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    prioridad_id INTEGER NOT NULL REFERENCES prioridades(id),
    confianza NUMERIC(5,4) NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
    origen VARCHAR(20) NOT NULL CHECK (origen IN ('IA', 'MANUAL')),
    fue_corregida BOOLEAN NOT NULL DEFAULT FALSE,
    validado_por INTEGER REFERENCES usuarios(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS archivos (
    id SERIAL PRIMARY KEY,
    pqr_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    ruta TEXT,
    tipo VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historial (
    id SERIAL PRIMARY KEY,
    pqr_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios(id),
    accion VARCHAR(120) NOT NULL,
    detalle TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pqrs_estado_created_at ON pqrs (estado, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pqrs_supervisor_estado ON pqrs (supervisor_id, estado);
CREATE INDEX IF NOT EXISTS idx_pqrs_usuario_created_at ON pqrs (usuario_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_clasificaciones_unique_pqr ON clasificaciones (pqr_id);
CREATE INDEX IF NOT EXISTS idx_historial_pqr_created_at ON historial (pqr_id, created_at DESC);

INSERT INTO rol (id, nombre) VALUES
(1, 'admin'),
(2, 'supervisor'),
(3, 'agente'),
(4, 'usuario'),
(5, 'operador'),
(6, 'gerente')
ON CONFLICT (id) DO NOTHING;

INSERT INTO areas (id, nombre, descripcion) VALUES
(1, 'Tecnologia', 'Incidentes y soporte tecnico'),
(2, 'Facturacion', 'Cobros y cartera'),
(3, 'Servicio al cliente', 'Atencion general')
ON CONFLICT (id) DO NOTHING;

SELECT setval('areas_id_seq', (SELECT MAX(id) FROM areas));

INSERT INTO usuarios (id, identificacion, nombre, correo, telefono, rol_id, area_id, activo, contrasena) VALUES
(1, '1001', 'Admin Sistema', 'admin@pqr.com', '3000000001', 1, 1, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak'),
(2, '1002', 'Laura Supervisora', 'laura@pqr.com', '3000000002', 2, 3, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak'),
(3, '1003', 'Carlos Agente', 'carlos@pqr.com', '3000000003', 3, 3, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak'),
(4, '1004', 'Maria Usuario', 'maria@pqr.com', '3000000004', 4, 2, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak'),
(5, '1005', 'Juan Operador', 'operador@pqr.com', '3000000005', 5, 3, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak'),
(6, '1006', 'Marta Gerente', 'gerente@pqr.com', '3000000006', 6, 3, TRUE, '$pbkdf2-sha256$29000$ifH.v1fq/Z9TCuF87z1nTA$OTJDj8HJuaxeQQMaDOwgBxx/Kdg6z5.CvLGX2amLDak')
ON CONFLICT (id) DO NOTHING;

SELECT setval('usuarios_id_seq', (SELECT MAX(id) FROM usuarios));

INSERT INTO categorias (id, nombre) VALUES
(1, 'Facturacion'),
(2, 'Tecnica'),
(3, 'Servicio')
ON CONFLICT (id) DO NOTHING;

INSERT INTO prioridades (id, nombre) VALUES
(1, 'baja'),
(2, 'media'),
(3, 'alta'),
(4, 'urgente')
ON CONFLICT (id) DO NOTHING;

INSERT INTO pqrs (id, titulo, descripcion, tipo, categoria, prioridad, estado, area_id, usuario_id, operador_id, supervisor_id) VALUES
(1, 'Factura incorrecta', 'Cobro no corresponde al consumo', 'reclamo', 'Facturacion', 'alta', 'pendiente', 2, 4, 3, 2),
(2, 'No funciona el portal', 'No permite autenticacion', 'queja', 'Tecnica', 'alta', 'pendiente', 1, 4, 3, 2),
(3, 'Solicitud de certificado', 'Certificado de paz y salvo', 'peticion', 'Servicio', 'media', 'resuelta', 3, 4, 3, 2)
ON CONFLICT (id) DO NOTHING;

SELECT setval('pqrs_id_seq', (SELECT MAX(id) FROM pqrs));

INSERT INTO clasificaciones (id, pqr_id, modelo_version, categoria_id, prioridad_id, confianza, origen, fue_corregida, validado_por) VALUES
(1, 1, 'v2.4.0', 1, 3, 0.9400, 'IA', FALSE, NULL),
(2, 2, 'v2.4.0', 2, 3, 0.9100, 'IA', FALSE, NULL),
(3, 3, 'v2.4.0', 3, 2, 0.8300, 'MANUAL', TRUE, 2)
ON CONFLICT (id) DO NOTHING;

SELECT setval('clasificaciones_id_seq', (SELECT MAX(id) FROM clasificaciones));

INSERT INTO historial (pqr_id, usuario_id, accion, detalle)
VALUES
(1, 4, 'CREACION', 'PQR creada por usuario'),
(2, 4, 'CREACION', 'PQR creada por usuario'),
(3, 2, 'CIERRE', 'PQR cerrada por supervisor')
ON CONFLICT DO NOTHING;
