CREATE TABLE cars (
    id                  SERIAL PRIMARY KEY,

    -- Jerarquía como strings directamente
    marca               VARCHAR(100) NOT NULL,
    modelo              VARCHAR(100) NOT NULL,
    submodelo           VARCHAR(200) NOT NULL,
    nombre              VARCHAR(300) NOT NULL,

    url                 TEXT UNIQUE NOT NULL,
    foto_url            TEXT,
    fecha_inicio        DATE,
    fecha_fin           DATE,
    precio              NUMERIC(10, 2),
    carroceria          VARCHAR(100),
    puertas             SMALLINT,
    plazas              SMALLINT,
    longitud            NUMERIC(7, 1),
    anchura             NUMERIC(7, 1),
    altura              NUMERIC(7, 1),
    capacidad_maletero  NUMERIC(7, 1),
    combustible         VARCHAR(50),
    potencia            NUMERIC(7, 2),
    aceleracion         NUMERIC(5, 2),
    velocidad_maxima    NUMERIC(6, 1),
    peso                NUMERIC(8, 1),
    consumo_medio       NUMERIC(6, 2),
    traccion            VARCHAR(50),
    transmision         VARCHAR(50),
    numero_marchas      SMALLINT,
    capacidad_deposito  NUMERIC(7, 2)
);

-- Índices para las consultas más frecuentes
CREATE INDEX idx_cars_marca        ON cars(marca);
CREATE INDEX idx_cars_modelo       ON cars(modelo);
CREATE INDEX idx_cars_precio       ON cars(precio);
CREATE INDEX idx_cars_combustible  ON cars(combustible);
CREATE INDEX idx_cars_carroceria   ON cars(carroceria);
CREATE INDEX idx_cars_potencia     ON cars(potencia);
CREATE INDEX idx_cars_plazas       ON cars(plazas);
-- Soporte para el orden por defecto (fecha_inicio DESC) y el filtro solo_vigentes.
CREATE INDEX idx_cars_fecha_inicio ON cars(fecha_inicio);
CREATE INDEX idx_cars_vigentes     ON cars(id) WHERE fecha_fin IS NULL;