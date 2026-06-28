-- ------------------------------------------------------------
-- Base de Datos para Sistema de Soporte Técnico 'BiteFixes'
-- Ejecuta este script en la consola de SQL de Supabase
-- ------------------------------------------------------------

-- Habilitar extensión para generar UUIDs de manera nativa si es necesario
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA DE CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(150) NOT NULL,
    whatsapp VARCHAR(20) UNIQUE NOT NULL, -- Almacena números limpios ej: '34612345678'
    direccion TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice para búsquedas ultra rápidas por número de whatsapp (indispensable para el webhook)
CREATE INDEX IF NOT EXISTS idx_clientes_whatsapp ON clientes(whatsapp);

-- 2. TABLA DE TICKETS DE SOPORTE
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY, -- Números secuenciales legibles e ideales para tickets de clientes (ej: Ticket #1003)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    categoria VARCHAR(30) NOT NULL CHECK (categoria IN ('Hardware', 'Software', 'Redes', 'Comercial', 'Otro')),
    cliente_id UUID REFERENCES clientes(id) ON DELETE CASCADE NOT NULL,
    descripcion TEXT NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'Abierto' CHECK (estatus IN ('Abierto', 'En Proceso', 'Resuelto'))
);

-- Insertar Datos Demo Iniciales para Pruebas
INSERT INTO clientes (nombre, whatsapp, direccion) 
VALUES 
('Carlos Mendoza', '34612345678', 'Calle Gran Vía 45, Piso 3, Madrid'),
('María Fernández', '34698765432', 'Avenida Diagonal 120, Barcelona')
ON CONFLICT (whatsapp) DO NOTHING;

INSERT INTO tickets (categoria, cliente_id, descripcion, estatus)
SELECT 
    'Hardware', 
    id, 
    'Mi computadora portátil enciende pero la pantalla se queda completamente en negro.', 
    'Abierto'
FROM clientes 
WHERE whatsapp = '34612345678'
LIMIT 1;

INSERT INTO tickets (categoria, cliente_id, descripcion, estatus)
SELECT 
    'Redes', 
    id, 
    'El enrutador de oficina pierde conexión intermitentemente cada tarde a las 3 PM.', 
    'En Proceso'
FROM clientes 
WHERE whatsapp = '34698765432'
LIMIT 1;
