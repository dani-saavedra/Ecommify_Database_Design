# PostgreSQL — Comparativa antes/después de índices

_Generado: 2026-06-16 21:47_

| Query | Tipo índice | Columna | Descripción | Tiempo ANTES (ms) | Scan ANTES | Tiempo DESPUÉS (ms) | Scan DESPUÉS | Mejora |
|---|---|---|---|---:|---|---:|---|---:|
| Q1 | B-Tree | `orders(customer_id)` | Historial por cliente | 9.19 | Append | 5.74 | Append | +37.5% |
| Q2 | B-Tree | `products(category_id)` | Productos por categoría | 336.95 | Seq Scan | 4.95 | Bitmap Heap Scan | +98.5% |
| Q3 | GIN | `products(specifications)` | Atributos JSONB | 4.98 | Seq Scan | 0.19 | Bitmap Heap Scan | +96.2% |
| Q4 | GIN trigram | `products(product_name)` | Búsqueda difusa | 150.37 | Seq Scan | 0.95 | Bitmap Heap Scan | +99.4% |
| Q5 | GiST | `geolocations(geom)` | Geoespacial PostGIS | 83.13 | Seq Scan | 11.53 | Seq Scan | +86.1% |

## Notas
- Dataset: Olist Brazilian E-Commerce — 32,951 productos, 99,441 órdenes.
- Tiempos medidos con `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` en Supabase (PostgreSQL 15).
- Tabla `orders` particionada por RANGE en `order_purchase_timestamp` (particiones 2016–2019).
