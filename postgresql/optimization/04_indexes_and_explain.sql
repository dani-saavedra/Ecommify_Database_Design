-- ============================================================
-- Unidad 5 - Optimización PostgreSQL
-- Índices especializados y análisis con EXPLAIN ANALYZE
-- ============================================================

-- ------------------------------------------------------------
-- 1. Historial de pedidos por cliente
-- Índice B-Tree sobre orders(customer_id)
-- ------------------------------------------------------------

-- ANTES:
EXPLAIN ANALYZE
SELECT *
FROM orders
WHERE customer_id = '220111bb-b2c3-4e5f-a6b7-c8d9e0f1a2b3';

-- ÍNDICE:
CREATE INDEX IF NOT EXISTS idx_orders_customer
ON orders(customer_id);

-- DESPUÉS:
EXPLAIN ANALYZE
SELECT *
FROM orders
WHERE customer_id = '220111bb-b2c3-4e5f-a6b7-c8d9e0f1a2b3';


-- ------------------------------------------------------------
-- 2. Búsqueda de productos por categoría
-- Índice B-Tree sobre products(category_id)
-- ------------------------------------------------------------

-- ANTES:
EXPLAIN ANALYZE
SELECT *
FROM products
WHERE category_id = '440111dd-b2c3-4e5f-a6b7-c8d9e0f1a2b3';

-- ÍNDICE:
CREATE INDEX IF NOT EXISTS idx_products_category
ON products(category_id);

-- DESPUÉS:
EXPLAIN ANALYZE
SELECT *
FROM products
WHERE category_id = '440111dd-b2c3-4e5f-a6b7-c8d9e0f1a2b3';


-- ------------------------------------------------------------
-- 3. Búsqueda en atributos JSONB
-- Índice GIN sobre products(specifications)
-- ------------------------------------------------------------

-- ANTES:
EXPLAIN ANALYZE
SELECT *
FROM products
WHERE specifications @> '{"RAM":"12GB"}';

-- ÍNDICE:
CREATE INDEX IF NOT EXISTS idx_products_specifications_gin
ON products
USING GIN(specifications);

-- DESPUÉS:
EXPLAIN ANALYZE
SELECT *
FROM products
WHERE specifications @> '{"RAM":"12GB"}';


-- ------------------------------------------------------------
-- 4. Búsqueda difusa de productos
-- Índice GIN trigram sobre product_name
-- Este índice ya existe en postgresql/schema/02_tables.sql:
-- CREATE INDEX idx_products_name_trgm ON products USING gin (product_name gin_trgm_ops);
-- ------------------------------------------------------------

EXPLAIN ANALYZE
SELECT product_id, product_name, similarity(product_name, 'Smarfone Pro') AS score
FROM products
WHERE product_name % 'Smarfone Pro'
ORDER BY score DESC;


-- ------------------------------------------------------------
-- 5. Consulta geoespacial con PostGIS
-- Índice GiST sobre geolocations(geom)
-- Este índice ya existe en postgresql/schema/02_tables.sql:
-- CREATE INDEX idx_geolocations_spatial ON geolocations USING gist (geom);
-- ------------------------------------------------------------

EXPLAIN ANALYZE
SELECT 
    o.order_id,
    c.customer_city,
    s.seller_name,
    ST_DistanceSphere(g_sel.geom, g_cust.geom) / 1000 AS distancia_kilometros
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN geolocations g_cust ON c.geolocation_id = g_cust.geolocation_id
JOIN order_items oi ON o.order_id = oi.order_id 
    AND o.order_purchase_timestamp = oi.order_purchase_timestamp
JOIN sellers s ON oi.seller_id = s.seller_id
JOIN geolocations g_sel ON s.geolocation_id = g_sel.geolocation_id
WHERE o.order_id = '660111ff-b2c3-4e5f-a6b7-c8d9e0f1a2b3';