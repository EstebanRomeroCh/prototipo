create database banco_alimentos CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci; 
USE banco_alimentos; 

CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,       -- Identificador único del rol
    nombre VARCHAR(50) NOT NULL UNIQUE,          -- Nombre del rol (ej: Administrador, Asistente, Voluntario)
    descripcion VARCHAR(150)                     -- Breve descripción de sus funciones
);
select * FROM usuarios;
INSERT INTO roles (nombre, descripcion) VALUES 
('Administrador', 'Control total del sistema, usuarios, donaciones y reportes.'),
('Asistente', 'Gestiona donaciones, inventarios y generación de certificados.'),
('Auxiliar de Bodega', 'Apoya en el registro y clasificación de productos donados.');

-- =====================================================
-- TABLA: usuarios
-- =====================================================
-- Guarda la información básica y de seguridad de cada usuario.
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,   -- Identificador único
    nombre_completo VARCHAR(150) NOT NULL,       -- Nombre y apellido
    correo VARCHAR(100) NOT NULL UNIQUE,         -- Correo electrónico (login)
    contrasena VARCHAR(255) NOT NULL,           -- Contraseña cifrada (hash con Flask)
    telefono VARCHAR(20),                        -- Teléfono (opcional)
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo', -- Controla acceso
    rol_id INT NOT NULL,                         -- Tipo de usuario (rol)
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Fecha automática
    intentos_fallidos INT DEFAULT 0,
    bloqueado_hasta datetime null,
    FOREIGN KEY (rol_id) REFERENCES roles(id_rol) ON DELETE CASCADE
);

-- Tabla de bitácora de acciones de usuario
CREATE TABLE bitacora_acciones (
    id_bitacora INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    modulo VARCHAR(50) NOT NULL,        -- 'DONACIONES', 'GASTOS', 'PRODUCTOS', etc.
    accion VARCHAR(50) NOT NULL,        -- 'CREAR', 'EDITAR', 'ANULAR', 'ELIMINAR', etc.
    descripcion VARCHAR(255) NOT NULL,  -- Texto entendible de lo que hizo
    tabla_afectada VARCHAR(50) NULL,    -- 'entradas', 'gastos', 'productos', etc.
    id_registro INT NULL,               -- ID del registro en esa tabla
    ip_origen VARCHAR(45) NULL,         -- IP del cliente
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
);
SELECT * 
FROM bitacora_acciones
ORDER BY fecha DESC
LIMIT 10;


-- =====================================================
-- TABLA: logs_acceso
-- =====================================================
-- Registra las sesiones e intentos de inicio/cierre de sesión.
CREATE TABLE logs_acceso (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accion ENUM('LOGIN', 'LOGOUT') NOT NULL,
    ip_origen VARCHAR(45),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- =====================================================
-- TABLA: tipo donante
-- =====================================================
CREATE TABLE tipo_donante (
    id_tipo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tipo_documento (
    id_tipo_doc INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado ENUM('activo','inactivo') DEFAULT 'activo'
);
ALTER TABLE tipo_documento ADD COLUMN estado ENUM('activo','inactivo') DEFAULT 'activo';
select * from tipo_documento;



-- =====================================================
-- TABLA: donante
-- =====================================================
CREATE TABLE donantes (
    id_donante INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    tipo_doc_id INT,
    numero_documento VARCHAR(50),
    tipo_id INT NOT NULL,
    correo VARCHAR(100),
    telefono VARCHAR(20),
    direccion VARCHAR(255),
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tipo_id) REFERENCES tipo_donante(id_tipo) ON DELETE RESTRICT,
    FOREIGN KEY (tipo_doc_id) REFERENCES tipo_documento(id_tipo_doc)
);

CREATE TABLE tipos_organizacion (
    id_tipo_organizacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre               VARCHAR(100)  NOT NULL,
    descripcion          VARCHAR(255)  NULL,
    -- Ej: "Parroquia", "Fundación", "Empresa privada", "Colegio", etc.

    estado               ENUM('Activo','Inactivo') NOT NULL DEFAULT 'Activo',
    fecha_creacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  DATETIME NULL ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE parroquias (
    id_parroquia INT AUTO_INCREMENT PRIMARY KEY,
    -- FK al tipo de organización (Parroquia, Fundación, Colegio, etc.)
    id_tipo_organizacion INT NOT NULL,
    -- FK al tipo de documento (CC, NIT, TI, etc. desde tipo_documento)
    tipo_doc_id INT NOT NULL,
    -- Datos básicos
    nombre            VARCHAR(150) NOT NULL,   -- Nombre de la parroquia
    nombre_encargado  VARCHAR(150) NOT NULL,   -- Nombre del párroco / encargado
    numero_documento  VARCHAR(50)  NOT NULL,   -- NIT/CC del encargado o de la parroquia según definas
    telefono          VARCHAR(20),
    direccion         VARCHAR(255),
    correo            VARCHAR(100),
    familias_atendidas INT NOT NULL DEFAULT 0,
    -- Ubicación
    departamento VARCHAR(100),
    municipio    VARCHAR(100),
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_parroquia_tipo_org
        FOREIGN KEY (id_tipo_organizacion)
        REFERENCES tipos_organizacion(id_tipo_organizacion)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_parroquia_tipo_doc
        FOREIGN KEY (tipo_doc_id)
        REFERENCES tipo_documento(id_tipo_doc)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE fundacioines (
    id_fundaciones INT AUTO_INCREMENT PRIMARY KEY,
    -- FK al tipo de organización (Parroquia, Fundación, Colegio, etc.)
    id_tipo_organizacion INT NOT NULL,
    -- FK al tipo de documento (CC, NIT, TI, etc. desde tipo_documento)
    tipo_doc_id INT NOT NULL,
    -- Datos básicos
    nombre            VARCHAR(150) NOT NULL,   -- Nombre de la parroquia
    nombre_encargado  VARCHAR(150) NOT NULL,   -- Nombre del párroco / encargado
    numero_documento  VARCHAR(50)  NOT NULL,   -- NIT/CC del encargado o de la parroquia según definas
    telefono          VARCHAR(20),
    direccion         VARCHAR(255),
    correo            VARCHAR(100),
    familias_atendidas INT NOT NULL DEFAULT 0,
    -- Ubicación
    departamento VARCHAR(100),
    municipio    VARCHAR(100),
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fundaciones_tipo_org
        FOREIGN KEY (id_tipo_organizacion)
        REFERENCES tipos_organizacion(id_tipo_organizacion)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fundaciones_tipo_doc
        FOREIGN KEY (tipo_doc_id)
        REFERENCES tipo_documento(id_tipo_doc)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =====================================================
-- TABLA: categorias
-- =====================================================
CREATE TABLE categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- TABLA: subcategorias
-- =====================================================
CREATE TABLE subcategorias (
    id_subcategoria INT AUTO_INCREMENT PRIMARY KEY,
    id_categoria INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255),
    estado ENUM('Activo', 'Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =====================================================
-- TABLA: productos
-- =====================================================

CREATE TABLE productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    id_categoria INT NOT NULL,
    id_subcategoria INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    stock_minimo DECIMAL(10,3) NOT NULL DEFAULT 0,
    id_unidad INT NOT NULL,
    -- peso_unitario: cantidad en la unidad elegida (ej: 500 si son 500 g, 2 si son 2 lb)
    peso_unitario DECIMAL(10,3) NOT NULL,
    -- peso_kg: peso neto del producto convertido a kilogramos (lo llenará el backend)
    peso_kg DECIMAL(10,3) NOT NULL,
    descripcion TEXT,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo',
    CONSTRAINT fk_prod_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_subcategoria
        FOREIGN KEY (id_subcategoria) REFERENCES subcategorias(id_subcategoria)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_prod_unidad
        FOREIGN KEY (id_unidad) REFERENCES unidades_medida(id_unidad)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE unidades_medida (
    id_unidad INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,      -- Nombre visible: Kilogramo, Gramo, Libra...
    abreviatura VARCHAR(10) NOT NULL, -- kg, g, lb...
    factor_kg DECIMAL(10,6) NOT NULL, -- Conversión a kg (1 kg = 1, 1 g = 0.001)
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bodegas (
    id_bodega INT AUTO_INCREMENT PRIMARY KEY,
    nombre_bodega VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(150),
    descripcion TEXT
);


INSERT INTO unidades_medida (nombre, abreviatura, factor_kg, estado) VALUES
('Kilogramo', 'kg', 1, 'Activo'),
('Gramo', 'g', 0.001, 'Activo'),
('Libra', 'lb', 0.453592, 'Activo'),
('Litro', 'L', 1, 'Activo'),
('Mililitro', 'ml', 0.001, 'Activo'),
('Unidad', 'ud', 1, 'Activo');

CREATE TABLE tipo_entrada (
    id_tipo_entrada INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,      -- Donación, Compra, Intercambio…
    descripcion VARCHAR(255),
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tipo_entrada (nombre, descripcion) VALUES
('Reagro', 'Producto del Campo');

CREATE TABLE entradas (
    id_entrada INT AUTO_INCREMENT PRIMARY KEY,
    id_tipo_entrada INT NOT NULL,            -- Donación / Compra / Intercambio
    id_donante INT NULL,                     -- Solo si es donación
    fecha_entrada DATETIME DEFAULT CURRENT_TIMESTAMP,
    observacion TEXT,
    total_peso_kg DECIMAL(10,3),
    total_valor DECIMAL(12,2),
    FOREIGN KEY (id_tipo_entrada) REFERENCES tipo_entrada(id_tipo_entrada),
    FOREIGN KEY (id_donante) REFERENCES donantes(id_donante)
);

ALTER TABLE entradas
DROP COLUMN responsable;

ALTER TABLE entradas ADD estado ENUM('Activo','Anulado') DEFAULT 'Activo';
ALTER TABLE entradas
ADD COLUMN total_peso_kg DECIMAL(10,3) NOT NULL DEFAULT 0
AFTER observacion;

ALTER TABLE entradas
ADD COLUMN total_valor DECIMAL(12,2) NOT NULL DEFAULT 0
AFTER total_peso_kg;

CREATE TABLE entrada_archivos (
    id_archivo INT AUTO_INCREMENT PRIMARY KEY,
    id_entrada INT NOT NULL,                 -- Donación a la que pertenece
    nombre_original VARCHAR(255) NOT NULL,   -- Nombre que subió el usuario
    nombre_guardado VARCHAR(255) NOT NULL,   -- Nombre físico en el servidor
    ruta_relativa VARCHAR(255) NOT NULL,     -- Ej: 'uploads/entradas/abc123.pdf'
    tipo_mime VARCHAR(100),                  -- image/jpeg, application/pdf, etc.
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_entrada) REFERENCES entradas(id_entrada)
        ON DELETE CASCADE
);

SELECT * FROM entrada_archivos;


CREATE TABLE entrada_detalles (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_entrada INT NOT NULL,
    id_producto INT NOT NULL,
    id_categoria INT NOT NULL,
    cantidad DECIMAL(10,3) NOT NULL,
    peso_unitario DECIMAL(10,3) NOT NULL,   -- copia del peso_unitario del producto en esa entrada
    peso_total_kg DECIMAL(10,3),
    id_unidad INT NOT NULL,
    id_bodega INT NOT NULL,
    bodega_texto VARCHAR(150),
    valor_producto DECIMAL(12,2) NULL,
    fecha_vencimiento DATE NULL,
    codigo_barras VARCHAR(100) NULL,
    CONSTRAINT fk_ed_entrada
        FOREIGN KEY (id_entrada) REFERENCES entradas(id_entrada),
    CONSTRAINT fk_ed_producto
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
    CONSTRAINT fk_ed_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria),
    CONSTRAINT fk_ed_unidad
        FOREIGN KEY (id_unidad) REFERENCES unidades_medida(id_unidad),
    CONSTRAINT fk_ed_bodega
        FOREIGN KEY (id_bodega) REFERENCES bodegas(id_bodega)
);
ALTER TABLE entrada_detalles
ADD id_categoria INT NOT NULL AFTER id_producto,
ADD FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria);

ALTER TABLE entrada_detalles
ADD id_categoria INT NULL AFTER id_producto;
ALTER TABLE entrada_detalles
ADD COLUMN bodega_texto VARCHAR(150) NULL AFTER id_bodega;
ALTER TABLE entrada_detalles
ADD COLUMN peso_total_kg DECIMAL(10,3) NOT NULL DEFAULT 0
AFTER peso_unitario;

ALTER TABLE entrada_detalles
ADD COLUMN valor_total DECIMAL(12,2) NULL
AFTER valor_producto;

-- 4) Crear tabla inventario_productos desde cero
CREATE TABLE inventario_productos (
    id_producto INT PRIMARY KEY,
    cantidad_total DECIMAL(10,3) NOT NULL DEFAULT 0,  -- siempre en kg
    reservado DECIMAL(10,3) NOT NULL DEFAULT 0,
    estado ENUM('OK','BAJO','AGOTADO') DEFAULT 'OK',
    ultima_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inv_producto
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        ON DELETE CASCADE ON UPDATE CASCADE
);
-- 5) Crear trigger que suma peso_total_kg al inventario
DELIMITER $$
CREATE TRIGGER trg_inventario_insert
AFTER INSERT ON entrada_detalles
FOR EACH ROW
BEGIN
    INSERT INTO inventario_productos (id_producto, cantidad_total)
    VALUES (NEW.id_producto, NEW.peso_total_kg)
    ON DUPLICATE KEY UPDATE 
        cantidad_total = cantidad_total + NEW.peso_total_kg,
        ultima_actualizacion = NOW();
END $$
DELIMITER ;

CREATE TABLE metodos_donacion (
    id_metodo INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    estado ENUM('Activo','Inactivo') DEFAULT 'Activo'
);
INSERT INTO metodos_donacion (nombre) VALUES
('Efectivo'),
('Transferencia'),
('Cheque');
CREATE TABLE donaciones_monetarias (
    id_donacion INT AUTO_INCREMENT PRIMARY KEY,
    id_donante INT NOT NULL,
    id_metodo INT NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    descripcion TEXT,
    fecha_donacion DATE NOT NULL DEFAULT (CURRENT_DATE),
    FOREIGN KEY (id_donante) REFERENCES donantes(id_donante)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (id_metodo) REFERENCES metodos_donacion(id_metodo)
        ON DELETE RESTRICT ON UPDATE CASCADE
);
ALTER TABLE donaciones_monetarias ADD estado ENUM('Activo','Anulado') DEFAULT 'Activo';
CREATE TABLE donacion_monetaria_archivos (
    id_archivo INT AUTO_INCREMENT PRIMARY KEY,
    id_donacion INT NOT NULL,               -- 👉 FK a donaciones_monetarias.id_donacion
    nombre_original VARCHAR(255) NOT NULL,  -- Nombre que subió el usuario
    nombre_guardado VARCHAR(255) NOT NULL,  -- Nombre físico en el servidor
    ruta_relativa VARCHAR(255) NOT NULL,    -- Ej: 'uploads/monetarias/abc123.pdf'
    tipo_mime VARCHAR(100),                 -- image/jpeg, application/pdf, etc.
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dm_archivo_donacion
        FOREIGN KEY (id_donacion) REFERENCES donaciones_monetarias(id_donacion)
        ON DELETE CASCADE
);

CREATE TABLE tipo_salida (
    id_tipo_salida INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(50) NOT NULL UNIQUE,      -- Donación, Baja por vencimiento, Consumo interno, etc.
    descripcion    VARCHAR(255),
    estado         ENUM('Activo','Inactivo') DEFAULT 'Activo',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tipo_salida (nombre, descripcion) VALUES
('Intercambio', 'Intercambio con Bancos de alimentos');

SELECT * FROM salidas;
SELECT DISTINCT estado FROM tipo_salida;


CREATE TABLE salidas (
    id_salida INT AUTO_INCREMENT PRIMARY KEY,
    -- Tipo de salida: Donación, Baja por vencimiento, Consumo interno, etc.
    id_tipo_salida INT NOT NULL,
    -- Parroquia beneficiaria (por ahora solo parroquias)
    id_parroquia INT NULL,
    fecha_salida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacion TEXT,
    -- Totales de la salida
    total_peso_kg DECIMAL(10,3) NOT NULL DEFAULT 0,
    total_valor   DECIMAL(12,2) NOT NULL DEFAULT 0,
    estado ENUM('Activo','Anulado') DEFAULT 'Activo',
    CONSTRAINT fk_sal_tipo_salida
        FOREIGN KEY (id_tipo_salida) REFERENCES tipo_salida(id_tipo_salida),
    CONSTRAINT fk_sal_parroquia
        FOREIGN KEY (id_parroquia) REFERENCES parroquias(id_parroquia)
);

ALTER TABLE salidas
  ADD COLUMN id_fundaciones INT NULL AFTER id_parroquia;

ALTER TABLE salidas
  ADD CONSTRAINT fk_salidas_fundaciones
  FOREIGN KEY (id_fundaciones)
  REFERENCES fundacioines(id_fundaciones)
  ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE salidas
ADD COLUMN id_acta_vencimiento INT NULL AFTER id_fundaciones;

ALTER TABLE salidas
ADD CONSTRAINT fk_salidas_acta_vencimiento
FOREIGN KEY (id_acta_vencimiento)
REFERENCES actas_vencimiento(id_acta)
ON DELETE SET NULL;

CREATE TABLE salida_detalles (
    id_detalle_salida INT AUTO_INCREMENT PRIMARY KEY,
    id_salida         INT NOT NULL,
    id_producto       INT NOT NULL,
    id_categoria      INT NOT NULL,
    id_bodega         INT NOT NULL,
    bodega_texto      VARCHAR(150) NULL,
    -- Lote que estamos entregando
    fecha_vencimiento DATE NULL,
    -- Cantidad que sale (siempre en kg, igual que el inventario_productos)
    cantidad_kg       DECIMAL(10,3) NOT NULL,
    -- Valores opcionales
    valor_unitario    DECIMAL(12,2) NULL,
    valor_total       DECIMAL(12,2) NULL,
    -- referencia al detalle de entrada del que sale
    id_entrada_detalle INT NULL,
    CONSTRAINT fk_sd_salida
        FOREIGN KEY (id_salida) REFERENCES salidas(id_salida),
    CONSTRAINT fk_sd_producto
        FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
    CONSTRAINT fk_sd_categoria
        FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria),
    CONSTRAINT fk_sd_bodega
        FOREIGN KEY (id_bodega) REFERENCES bodegas(id_bodega),
    CONSTRAINT fk_sd_entrada_detalle
        FOREIGN KEY (id_entrada_detalle) REFERENCES entrada_detalles(id_detalle)
);

DELIMITER $$

CREATE TRIGGER trg_inventario_salida_insert
AFTER INSERT ON salida_detalles
FOR EACH ROW
BEGIN
    -- Restar del inventario la cantidad que salió
    UPDATE inventario_productos inv
    JOIN productos p ON p.id_producto = inv.id_producto
    SET 
        inv.cantidad_total = GREATEST(inv.cantidad_total - NEW.cantidad_kg, 0),
        inv.estado = CASE
            WHEN inv.cantidad_total - NEW.cantidad_kg <= 0 THEN 'AGOTADO'
            WHEN inv.cantidad_total - NEW.cantidad_kg <= p.stock_minimo THEN 'BAJO'
            ELSE 'OK'
        END,
        inv.ultima_actualizacion = NOW()
    WHERE inv.id_producto = NEW.id_producto;
END$$

DELIMITER ;






CREATE TABLE parametros_certificados (
    id_parametro INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Datos de la organización
    nombre_organizacion VARCHAR(150) NOT NULL,
    nit_organizacion VARCHAR(50) NULL,
    ciudad VARCHAR(100) NOT NULL,
    direccion_organizacion VARCHAR(150) NULL,
    telefono_organizacion VARCHAR(50) NULL,
    
    -- Textos base del certificado
    texto_encabezado TEXT NOT NULL,       -- Ej: "El Banco de Alimentos Diocesano de Valledupar certifica que:"
    texto_cuerpo_base TEXT NOT NULL,      -- Ej: "Ha realizado una donación en especie a esta organización..."
    texto_despedida TEXT NOT NULL,        -- Ej: "Agradecemos profundamente su generosidad..."
    
    -- Lugar y firma
    lugar_emision VARCHAR(100) NOT NULL,  -- Ej: "Valledupar (Cesar)"
    firma_responsable VARCHAR(150) NOT NULL,  -- Nombre de quien firma
    cargo_responsable VARCHAR(150) NOT NULL,  -- Cargo del responsable
    
    -- Logo y configuración visual
    ruta_logo VARCHAR(255) NULL,          -- Ej: "static/images/imagen.png"
    
    -- Mostrar o no el valor monetario estimado de la donación
    mostrar_valor_monetario ENUM('Si','No') DEFAULT 'No'
);
-- Salidas con su acta (si existe)
SELECT s.id_salida, s.fecha_salida, av.id_acta, av.fecha_acta, av.estado
FROM salidas s
LEFT JOIN actas_vencimiento av ON av.id_salida = s.id_salida
ORDER BY s.id_salida DESC;
SHOW COLUMNS FROM salidas LIKE 'id_acta_vencimiento';
DESCRIBE actas_vencimiento;



CREATE TABLE actas_vencimiento (
  id_acta INT AUTO_INCREMENT PRIMARY KEY,
  
  -- 1 a 1 con salidas
  id_salida INT NOT NULL UNIQUE,

  fecha_acta DATE NOT NULL,

  -- texto libre: “por qué / descripción del acta”
  motivo TEXT NOT NULL,

  -- usuario que creó el acta (guardas nombre o puedes guardar id_usuario)
  creado_por VARCHAR(150) NOT NULL,

  estado ENUM('Activo','Anulado') DEFAULT 'Activo',
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_acta_salida
    FOREIGN KEY (id_salida) REFERENCES salidas(id_salida)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE actas_vencimiento
  ADD COLUMN id_usuario_creador INT NOT NULL,
  ADD CONSTRAINT fk_acta_usuario
    FOREIGN KEY (id_usuario_creador) REFERENCES usuarios(id_usuario)
    ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE actas_vencimiento
  DROP COLUMN creado_por;

CREATE TABLE acta_vencimiento_detalles (
  id_detalle_acta INT AUTO_INCREMENT PRIMARY KEY,
  id_acta INT NOT NULL,

  -- referencia al detalle real de la salida
  id_detalle_salida INT NOT NULL,

  -- snapshot (copiado al crear el acta)
  id_producto INT NOT NULL,
  nombre_producto VARCHAR(150) NOT NULL,
  fecha_vencimiento DATE NULL,
  cantidad_kg DECIMAL(10,3) NOT NULL,

  id_bodega INT NULL,
  nombre_bodega VARCHAR(100) NULL,
  bodega_texto VARCHAR(150) NULL,

  CONSTRAINT fk_avd_acta
    FOREIGN KEY (id_acta) REFERENCES actas_vencimiento(id_acta)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_avd_detalle_salida
    FOREIGN KEY (id_detalle_salida) REFERENCES salida_detalles(id_detalle_salida)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_acta_estado_fecha ON actas_vencimiento (estado, fecha_acta);
CREATE INDEX idx_acta_detalles_acta ON acta_vencimiento_detalles (id_acta);


-- 1. Desactivar validación de llaves foráneas
SET FOREIGN_KEY_CHECKS = 0;
-- 2. TRUNCATE en tablas hijas primero (por orden lógico)

TRUNCATE TABLE usuarios;
TRUNCATE TABLE parametros_certificados;
TRUNCATE TABLE logs_acceso;




-- 3. Reactivar validación de llaves foráneas
SET FOREIGN_KEY_CHECKS = 1;


