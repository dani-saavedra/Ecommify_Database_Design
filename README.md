# Ecommify — Arquitectura Híbrida PostgreSQL + MongoDB

Plataforma marketplace implementada sobre arquitectura de bases de datos híbrida, integrando
**PostgreSQL (Supabase)** para transacciones y **MongoDB Atlas** para el catálogo flexible y analítica.

Dataset base: [Brazilian E-Commerce — Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

## Integrantes
- Valentina Rodríguez Romero
- Andrés Santiago Santafe Silva
- Daniel Orlando Saavedra Fonnegra

Universidad de La Sabana — Diseño y Optimización de Bases de Datos, 2026

---

## Estructura del repositorio

```
.
├── postgresql/
│   ├── schema/
│   │   ├── 01_extensions.sql       # uuid-ossp, pg_trgm, PostGIS
│   │   ├── 02_tables.sql           # Tablas relacionales + índices baseline
│   │   └── 03_partitions.sql       # Particiones de la tabla orders
│   ├── seed_data/
│   │   └── 01_seed.sql             # Datos mínimos de prueba
│   ├── queries/
│   │   └── 01_analytical_queries.sql
│   └── optimization/
│       ├── 00_setup_and_explain.sql # Setup completo + EXPLAIN ANALYZE
│       └── 04_indexes_and_explain.sql
├── mongodb/
│   ├── schema/
│   │   ├── products_catalog.js     # Colección con JSON Schema
│   │   └── order_reviews.js
│   └── optimization/
│       └── 02_indexes_and_pipeline.js
├── notebooks/
│   ├── Data_Exploration_Analysis.ipynb
│   └── Optimization_Analysis.ipynb # Benchmark antes/después
├── scripts/
│   ├── setup_full.py               # Carga dataset Kaggle en Supabase + crea índices
│   ├── load_kaggle_to_supabase.py  # Descarga y transforma dataset Olist desde Kaggle
│   ├── capture_explain_metrics.py  # Captura métricas EXPLAIN ANALYZE automatizada
│   └── patch_q4_q5.py              # Métricas EXPLAIN ANALYZE (Q4 GIN trigram, Q5 GiST)
├── evidencias/
│   ├── postgresql/
│   │   ├── metrics_raw.json
│   │   └── comparison_table.md
│   └── mongodb/
│       ├── metrics_raw.json
│       └── comparison_table.md
└── docs/
    ├── Documento_Tecnico_Diseno.pdf
    └── Presentacion_Ejecutiva.pdf
```

---

## Setup — PostgreSQL (Supabase)

### Prerequisitos
```bash
pip install supabase pandas kagglehub requests reportlab matplotlib numpy
```

### Paso 1: Crear esquema en Supabase
1. Abre [Supabase SQL Editor](https://supabase.com/dashboard/project/litdnoxzcbdecgrjjewt/sql)
2. Pega y ejecuta el contenido de `postgresql/optimization/00_setup_and_explain.sql`
   - Crea extensiones, tablas, particiones e índices
   - Genera datos sintéticos de prueba para validar EXPLAIN ANALYZE

### Paso 2: Cargar dataset real de Kaggle
```bash
# El script descarga el dataset de Kaggle y lo carga en Supabase automáticamente
SUPABASE_PAT=sbp_xxxx python3 scripts/setup_full.py
```
Carga: ~32,000 productos, ~99,000 órdenes, ~103,000 pagos

### Paso 3: Capturar métricas EXPLAIN ANALYZE (Q4 y Q5)
```bash
SUPABASE_PAT=sbp_xxxx python3 scripts/patch_q4_q5.py
```
Genera `evidencias/postgresql/metrics_raw.json` y `comparison_table.md`.

---

## Setup — MongoDB Atlas

### Prerequisitos
```bash
pip install pymongo
```

### Paso 1: Crear colecciones
```bash
mongosh "mongodb+srv://olist.02nueqj.mongodb.net/" \
  --username santoles5_db_user \
  --file mongodb/schema/products_catalog.js
mongosh "mongodb+srv://olist.02nueqj.mongodb.net/" \
  --username santoles5_db_user \
  --file mongodb/schema/order_reviews.js
```

### Paso 2: Cargar datos e índices
```bash
mongosh "mongodb+srv://olist.02nueqj.mongodb.net/" \
  --username santoles5_db_user \
  --file mongodb/optimization/02_indexes_and_pipeline.js
```

---

## Notebooks de análisis

| Notebook | Contenido |
|---|---|
| [`notebooks/Data_Exploration_Analysis.ipynb`](notebooks/Data_Exploration_Analysis.ipynb) | Exploración del dataset Olist (distribuciones, categorías, volumen) |
| [`notebooks/Optimization_Analysis.ipynb`](notebooks/Optimization_Analysis.ipynb) | Benchmark antes/después: EXPLAIN ANALYZE PostgreSQL + executionStats MongoDB |

Ábrelos en Google Colab subiendo el archivo o clonando el repositorio en Drive.

---

## Resultados de optimización

### MongoDB (datos reales — 32,951 productos, 99,224 reseñas)

| Query | Tipo índice | Docs antes | Docs después | Tiempo antes | Tiempo después | Mejora |
|---|---|---|---|---|---|---|
| Q1: ESR (categoría + peso + sort) | Compuesto | 32,951 | 583 | 28 ms | 4 ms | 85.7% |
| Q2: Reseñas positivas (score ≥ 4) | Parcial | 99,224 | 76,470 | 68 ms | 100 ms | −47%* |
| Q3: Full-text en comentarios | Text | — | 8,652 | — | 60 ms | Nueva capacidad |

> *Q2: El índice parcial es más lento porque retorna el 77% de la colección. Lección aprendida: índices parciales son efectivos solo cuando el subconjunto es < 30%.

### PostgreSQL (datos reales — 32,951 productos, 99,441 órdenes, 103,886 pagos)

| Query | Tipo índice | Tiempo antes | Tiempo después | Scan antes | Scan después | Mejora |
|---|---|---|---|---|---|---|
| Q1: Historial por cliente | B-Tree | 9.19 ms | 5.74 ms | Append | Append | 37.5% |
| Q2: Productos por categoría | B-Tree | 336.95 ms | 4.95 ms | Seq Scan | Bitmap Heap | 98.5% |
| Q3: Atributos JSONB | GIN | 4.98 ms | 0.19 ms | Seq Scan | Bitmap Heap | 96.2% |
| Q4: Búsqueda difusa (trigram) | GIN trigram | 150.37 ms | 0.95 ms | Seq Scan | Bitmap Heap | 99.4% |
| Q5: Geoespacial PostGIS | GiST | 83.13 ms | 11.53 ms | Seq Scan | Seq Scan | 86.1% |

> Medido con `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` en Supabase (PostgreSQL 15). Detalle completo en `evidencias/postgresql/comparison_table.md`.

---

## Arquitectura de escalabilidad

### MongoDB — Replica Set (teórico)
- 1 Primary (escritura)
- 1 Secondary (lectura, `secondaryPreferred`)
- 1 Arbiter (elección en failover)

### MongoDB — Sharding (teórico)
- Shard key compuesta: `{ category: 1, seller_id: "hashed" }`
- Afinidad funcional por categoría + distribución uniforme vía hash

---

## Variables de entorno
```bash
SUPABASE_URL=https://litdnoxzcbdecgrjjewt.supabase.co
SUPABASE_KEY=<anon_key>
MONGO_URI=mongodb+srv://santoles5_db_user:<password>@olist.02nueqj.mongodb.net/
```
