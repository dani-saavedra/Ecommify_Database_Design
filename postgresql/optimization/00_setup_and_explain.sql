-- ============================================================
-- ECOMMIFY - Setup completo + métricas EXPLAIN ANALYZE
-- Ejecutar en Supabase SQL Editor (paso único)
-- ============================================================

-- ============================================================
-- PASO 1: EXTENSIONES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS postgis;


-- ============================================================
-- PASO 2: TABLAS (drop y recrear limpio)
-- ============================================================
DROP TABLE IF EXISTS payments     CASCADE;
DROP TABLE IF EXISTS order_items  CASCADE;
DROP TABLE IF EXISTS orders       CASCADE;
DROP TABLE IF EXISTS inventory    CASCADE;
DROP TABLE IF EXISTS products     CASCADE;
DROP TABLE IF EXISTS sellers      CASCADE;
DROP TABLE IF EXISTS customers    CASCADE;
DROP TABLE IF EXISTS categories   CASCADE;
DROP TABLE IF EXISTS geolocations CASCADE;

CREATE TABLE geolocations (
    geolocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zip_code_prefix VARCHAR(20)  NOT NULL,
    latitude        NUMERIC(10,8) NOT NULL,
    longitude       NUMERIC(11,8) NOT NULL,
    city            VARCHAR(100)  NOT NULL,
    state           CHAR(2)       NOT NULL,
    geom            GEOMETRY(Point, 4326)
);

CREATE TABLE categories (
    category_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name          VARCHAR(150) UNIQUE NOT NULL,
    category_name_english  VARCHAR(150) UNIQUE
);

CREATE TABLE customers (
    customer_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_unique_id VARCHAR(50)  UNIQUE NOT NULL,
    email              VARCHAR(150) UNIQUE NOT NULL,
    customer_city      VARCHAR(100) NOT NULL,
    customer_state     CHAR(2)      NOT NULL,
    geolocation_id     UUID REFERENCES geolocations(geolocation_id),
    created_at         TIMESTAMPTZ DEFAULT now(),
    updated_at         TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sellers (
    seller_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_name    VARCHAR(150) NOT NULL,
    seller_city    VARCHAR(100) NOT NULL,
    seller_state   CHAR(2)     NOT NULL,
    geolocation_id UUID REFERENCES geolocations(geolocation_id),
    created_at     TIMESTAMPTZ DEFAULT now(),
    updated_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE products (
    product_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id         UUID NOT NULL REFERENCES categories(category_id),
    product_name        VARCHAR(200) NOT NULL,
    product_description TEXT,
    specifications      JSONB DEFAULT '{}'::jsonb,
    photos              TEXT[],
    weight_g            INTEGER     CHECK (weight_g >= 0),
    length_cm           NUMERIC(10,2) CHECK (length_cm >= 0),
    height_cm           NUMERIC(10,2) CHECK (height_cm >= 0),
    width_cm            NUMERIC(10,2) CHECK (width_cm >= 0),
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE orders (
    order_id                      UUID        NOT NULL,
    customer_id                   UUID        NOT NULL REFERENCES customers(customer_id),
    order_status                  VARCHAR(30) NOT NULL
        CHECK (order_status IN ('created','approved','shipped','delivered','canceled')),
    order_purchase_timestamp      TIMESTAMPTZ NOT NULL,
    order_approved_at             TIMESTAMPTZ,
    order_delivered_carrier_date  TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ,
    created_at                    TIMESTAMPTZ DEFAULT now(),
    updated_at                    TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (order_id, order_purchase_timestamp)
) PARTITION BY RANGE (order_purchase_timestamp);

CREATE TABLE order_items (
    order_item_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id                 UUID NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    product_id               UUID NOT NULL REFERENCES products(product_id),
    seller_id                UUID NOT NULL REFERENCES sellers(seller_id),
    quantity                 INTEGER     CHECK (quantity > 0),
    price                    NUMERIC(12,2) CHECK (price >= 0),
    freight_value            NUMERIC(12,2) CHECK (freight_value >= 0),
    shipping_limit_date      TIMESTAMPTZ,
    FOREIGN KEY (order_id, order_purchase_timestamp)
        REFERENCES orders(order_id, order_purchase_timestamp)
);

CREATE TABLE payments (
    payment_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id                 UUID NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    payment_sequential       INTEGER     CHECK (payment_sequential > 0),
    payment_type             VARCHAR(50) NOT NULL,
    payment_installments     INTEGER     CHECK (payment_installments >= 0),
    payment_value            NUMERIC(12,2) CHECK (payment_value >= 0),
    FOREIGN KEY (order_id, order_purchase_timestamp)
        REFERENCES orders(order_id, order_purchase_timestamp)
);

CREATE TABLE inventory (
    inventory_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id     UUID NOT NULL REFERENCES products(product_id),
    seller_id      UUID NOT NULL REFERENCES sellers(seller_id),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    last_update    TIMESTAMPTZ DEFAULT now()
);

-- Índices siempre presentes (trigram y espacial)
CREATE INDEX idx_products_name_trgm   ON products USING gin (product_name gin_trgm_ops);
CREATE INDEX idx_geolocations_spatial ON geolocations USING gist (geom);


-- ============================================================
-- PASO 3: PARTICIONES (2024–2026)
-- ============================================================
CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
CREATE TABLE orders_2024_q3 PARTITION OF orders
    FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');
CREATE TABLE orders_2024_q4 PARTITION OF orders
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
CREATE TABLE orders_2025_h1 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-07-01');
CREATE TABLE orders_2025_h2 PARTITION OF orders
    FOR VALUES FROM ('2025-07-01') TO ('2026-01-01');
CREATE TABLE orders_2026_m05 PARTITION OF orders
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
CREATE TABLE orders_2026_m06 PARTITION OF orders
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');


-- ============================================================
-- PASO 4: DATOS SINTÉTICOS (volumen suficiente para benchmarks)
-- ============================================================

-- Geolocalizaciones (20 ciudades)
INSERT INTO geolocations (geolocation_id, zip_code_prefix, latitude, longitude, city, state, geom)
SELECT
    uuid_generate_v4(),
    lpad(i::text, 6, '0'),
    4.0 + (random() * 8),
    -76.0 - (random() * 6),
    (ARRAY['Bogota','Medellin','Cali','Barranquilla','Cartagena',
           'Cucuta','Bucaramanga','Pereira','Manizales','Ibague',
           'Villavicencio','Pasto','Monteria','Valledupar','Sincelejo',
           'Popayan','Tunja','Armenia','Neiva','Riohacha'])[i],
    (ARRAY['DC','ANT','VAC','ATL','BOL','NSA','SAN','RIS','CAL','TOL',
           'MET','NAR','COR','CES','SUC','CAU','BOY','QUI','HUI','LAG'])[i],
    ST_SetSRID(ST_MakePoint(-76.0 - random()*6, 4.0 + random()*8), 4326)
FROM generate_series(1, 20) AS i;

-- Categorías (10)
INSERT INTO categories (category_id, category_name, category_name_english)
VALUES
    ('440111dd-0001-4e5f-a6b7-c8d9e0f1a2b3','Tecnologia','Technology'),
    ('440111dd-0002-4e5f-a6b7-c8d9e0f1a2b3','Muebles','Furniture'),
    ('440111dd-0003-4e5f-a6b7-c8d9e0f1a2b3','Deportes','Sports'),
    ('440111dd-0004-4e5f-a6b7-c8d9e0f1a2b3','Ropa','Clothing'),
    ('440111dd-0005-4e5f-a6b7-c8d9e0f1a2b3','Hogar','Home'),
    ('440111dd-0006-4e5f-a6b7-c8d9e0f1a2b3','Alimentos','Food'),
    ('440111dd-0007-4e5f-a6b7-c8d9e0f1a2b3','Juguetes','Toys'),
    ('440111dd-0008-4e5f-a6b7-c8d9e0f1a2b3','Libros','Books'),
    ('440111dd-0009-4e5f-a6b7-c8d9e0f1a2b3','Belleza','Beauty'),
    ('440111dd-0010-4e5f-a6b7-c8d9e0f1a2b3','Electrodomesticos','Appliances');

-- Clientes (500)
INSERT INTO customers (customer_id, customer_unique_id, email, customer_city, customer_state, geolocation_id)
SELECT
    uuid_generate_v4(),
    'USR-' || lpad(i::text, 5, '0'),
    'user' || i || '@ecommify.com',
    (SELECT city FROM geolocations ORDER BY random() LIMIT 1),
    (SELECT state FROM geolocations ORDER BY random() LIMIT 1),
    (SELECT geolocation_id FROM geolocations ORDER BY random() LIMIT 1)
FROM generate_series(1, 500) AS i;

-- Sellers (50)
INSERT INTO sellers (seller_id, seller_name, seller_city, seller_state, geolocation_id)
SELECT
    uuid_generate_v4(),
    'Tienda ' || i || ' Store',
    (SELECT city FROM geolocations ORDER BY random() LIMIT 1),
    (SELECT state FROM geolocations ORDER BY random() LIMIT 1),
    (SELECT geolocation_id FROM geolocations ORDER BY random() LIMIT 1)
FROM generate_series(1, 50) AS i;

-- Productos (1000) con JSONB variado
INSERT INTO products (product_id, category_id, product_name, product_description, specifications, weight_g)
SELECT
    uuid_generate_v4(),
    (SELECT category_id FROM categories ORDER BY random() LIMIT 1),
    (ARRAY['Smartphone','Laptop','Tablet','Monitor','Teclado','Mouse','Audifonos',
           'Camara','Impresora','Router','Smart TV','Consola','Silla','Escritorio',
           'Lampara','Zapatillas','Camiseta','Pantalon','Reloj','Mochila'])[1 + (i % 20)]
        || ' ' || (ARRAY['Pro','Max','Ultra','Lite','Plus','Elite','Basic','Premium',
                          'Sport','Air','Neo','Flex','Boost','Core','Edge'])[1 + (i % 15)]
        || ' ' || i,
    'Descripcion del producto numero ' || i,
    jsonb_build_object(
        'RAM',    (ARRAY['4GB','8GB','12GB','16GB','32GB'])[1 + (i % 5)],
        'Storage',(ARRAY['64GB','128GB','256GB','512GB','1TB'])[1 + (i % 5)],
        'Color',  (ARRAY['Negro','Blanco','Gris','Azul','Rojo'])[1 + (i % 5)]
    ),
    100 + (i * 7 % 2000)
FROM generate_series(1, 1000) AS i;

-- Inventario (1 por producto)
INSERT INTO inventory (product_id, seller_id, stock_quantity)
SELECT
    p.product_id,
    (SELECT seller_id FROM sellers ORDER BY random() LIMIT 1),
    10 + (random() * 500)::int
FROM products p;

-- Órdenes (800 distribuidas entre 2024 y 2026)
INSERT INTO orders (order_id, customer_id, order_status, order_purchase_timestamp)
SELECT
    uuid_generate_v4(),
    (SELECT customer_id FROM customers ORDER BY random() LIMIT 1),
    (ARRAY['created','approved','shipped','delivered','canceled'])[1 + (i % 5)],
    TIMESTAMP '2024-01-01' + (random() * INTERVAL '900 days')
FROM generate_series(1, 800) AS i;

-- Order items (1 por orden)
INSERT INTO order_items (order_id, order_purchase_timestamp, product_id, seller_id, quantity, price, freight_value)
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    (SELECT product_id FROM products ORDER BY random() LIMIT 1),
    (SELECT seller_id FROM sellers ORDER BY random() LIMIT 1),
    1 + (random() * 5)::int,
    50 + (random() * 2000)::numeric(12,2),
    10 + (random() * 50)::numeric(12,2)
FROM orders o;

-- Payments
INSERT INTO payments (order_id, order_purchase_timestamp, payment_sequential, payment_type, payment_installments, payment_value)
SELECT
    o.order_id,
    o.order_purchase_timestamp,
    1,
    (ARRAY['credit_card','debit_card','voucher','boleto'])[1 + (random()*3)::int],
    1 + (random()*11)::int,
    oi.price + oi.freight_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
    AND oi.order_purchase_timestamp = o.order_purchase_timestamp;

-- Confirmar volumen
SELECT 'geolocations' AS tabla, COUNT(*) FROM geolocations UNION ALL
SELECT 'categories',            COUNT(*) FROM categories   UNION ALL
SELECT 'customers',             COUNT(*) FROM customers    UNION ALL
SELECT 'sellers',               COUNT(*) FROM sellers      UNION ALL
SELECT 'products',              COUNT(*) FROM products     UNION ALL
SELECT 'orders',                COUNT(*) FROM orders       UNION ALL
SELECT 'order_items',           COUNT(*) FROM order_items  UNION ALL
SELECT 'payments',              COUNT(*) FROM payments
ORDER BY tabla;


-- ============================================================
-- PASO 5: EXPLAIN ANALYZE — ANTES de índices de optimización
-- ============================================================

-- Asegurarse de que los índices de optimización NO existan aún
DROP INDEX IF EXISTS idx_orders_customer;
DROP INDEX IF EXISTS idx_products_category;
DROP INDEX IF EXISTS idx_products_specifications_gin;

-- Q1: Historial de pedidos por cliente (B-Tree)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders
WHERE customer_id = (SELECT customer_id FROM customers LIMIT 1);

-- Q2: Productos por categoría (B-Tree)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM products
WHERE category_id = '440111dd-0001-4e5f-a6b7-c8d9e0f1a2b3';

-- Q3: Búsqueda JSONB con operador @> (GIN)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM products
WHERE specifications @> '{"RAM": "12GB"}';

-- Q4: Búsqueda difusa trigram (índice ya existe desde DDL)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT product_id, product_name,
       similarity(product_name, 'Smarfone Pro') AS score
FROM products
WHERE product_name % 'Smarfone Pro'
ORDER BY score DESC;

-- Q5: Consulta geoespacial (índice GiST ya existe desde DDL)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    o.order_id,
    c.customer_city,
    s.seller_name,
    ST_DistanceSphere(g_sel.geom, g_cust.geom) / 1000 AS distancia_km
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN geolocations g_cust ON c.geolocation_id = g_cust.geolocation_id
JOIN order_items oi ON o.order_id = oi.order_id
    AND o.order_purchase_timestamp = oi.order_purchase_timestamp
JOIN sellers s     ON oi.seller_id = s.seller_id
JOIN geolocations g_sel ON s.geolocation_id = g_sel.geolocation_id
WHERE o.customer_id = (SELECT customer_id FROM customers LIMIT 1);


-- ============================================================
-- PASO 6: CREAR ÍNDICES DE OPTIMIZACIÓN
-- ============================================================
CREATE INDEX idx_orders_customer
    ON orders(customer_id);

CREATE INDEX idx_products_category
    ON products(category_id);

CREATE INDEX idx_products_specifications_gin
    ON products USING GIN(specifications);


-- ============================================================
-- PASO 7: EXPLAIN ANALYZE — DESPUÉS de índices
-- ============================================================

-- Q1 después
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders
WHERE customer_id = (SELECT customer_id FROM customers LIMIT 1);

-- Q2 después
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM products
WHERE category_id = '440111dd-0001-4e5f-a6b7-c8d9e0f1a2b3';

-- Q3 después
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM products
WHERE specifications @> '{"RAM": "12GB"}';

-- Q4 después (sin cambio, índice ya estaba)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT product_id, product_name,
       similarity(product_name, 'Smarfone Pro') AS score
FROM products
WHERE product_name % 'Smarfone Pro'
ORDER BY score DESC;

-- Q5 después (sin cambio, índice ya estaba)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    o.order_id,
    c.customer_city,
    s.seller_name,
    ST_DistanceSphere(g_sel.geom, g_cust.geom) / 1000 AS distancia_km
FROM orders o
JOIN customers c   ON o.customer_id = c.customer_id
JOIN geolocations g_cust ON c.geolocation_id = g_cust.geolocation_id
JOIN order_items oi ON o.order_id = oi.order_id
    AND o.order_purchase_timestamp = oi.order_purchase_timestamp
JOIN sellers s     ON oi.seller_id = s.seller_id
JOIN geolocations g_sel ON s.geolocation_id = g_sel.geolocation_id
WHERE o.customer_id = (SELECT customer_id FROM customers LIMIT 1);
