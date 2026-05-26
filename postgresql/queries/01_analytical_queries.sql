-- 1. Búsqueda difusa de productos tolerante a errores ortográficos (RF02)
SELECT product_id, product_name, similarity(product_name, 'Smarfone Pro') AS score
FROM products
WHERE product_name % 'Smarfone Pro'
ORDER BY score DESC;

-- 2. Cálculo espacial de distancias lineales reales entre cliente y vendedor (RF07)
SELECT 
    o.order_id,
    c.customer_city,
    s.seller_name,
    ST_DistanceSphere(g_sel.geom, g_cust.geom) / 1000 AS distancia_kilometros
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN geolocations g_cust ON c.geolocation_id = g_cust.geolocation_id
JOIN order_items oi ON o.order_id = oi.order_id AND o.order_purchase_timestamp = oi.order_purchase_timestamp
JOIN sellers s ON oi.seller_id = s.seller_id
JOIN geolocations g_sel ON s.geolocation_id = g_sel.geolocation_id
WHERE o.order_id = '660111ff-b2c3-4e5f-a6b7-c8d9e0f1a2b3';