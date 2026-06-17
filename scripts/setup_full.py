#!/usr/bin/env python3
"""
setup_full.py  –  Ecommify Unidad 5
====================================
Usa SOLO HTTPS — sin psycopg2, sin conexión directa a PostgreSQL.

  DDL  → Supabase Management API  (requiere SUPABASE_PAT)
  Data → supabase-py REST API     (anon key, funciona siempre)
  EXPLAIN → Management API

Uso:
    SUPABASE_PAT=sbp_xxxx python3 scripts/setup_full.py

Obtén tu PAT en: https://supabase.com/dashboard/account/tokens

Requisitos:
    pip install supabase pandas requests kagglehub
"""

import json, time, uuid, os, sys, glob
from pathlib import Path
from datetime import datetime

# ─────────────────────── CONFIG ─────────────────────────────────
PROJECT_REF  = "litdnoxzcbdecgrjjewt"
SUPABASE_URL = f"https://{PROJECT_REF}.supabase.co"
ANON_KEY     = "sb_publishable_TDWPbmPplOFc4kREL-_XAw_9aO1ymm2"
MGMT_BASE    = f"https://api.supabase.com/v1/projects/{PROJECT_REF}"

REPO_ROOT   = Path(__file__).resolve().parent.parent
EVIDENCIAS  = REPO_ROOT / "evidencias" / "postgresql"
BATCH_SIZE  = 500

CITIES = [
    ("São Paulo","SP",-23.5505,-46.6333),
    ("Rio de Janeiro","RJ",-22.9068,-43.1729),
    ("Belo Horizonte","MG",-19.9167,-43.9345),
    ("Brasília","DF",-15.7801,-47.9292),
    ("Curitiba","PR",-25.4278,-49.2731),
    ("Porto Alegre","RS",-30.0346,-51.2177),
    ("Salvador","BA",-12.9714,-38.5014),
    ("Fortaleza","CE",-3.7172,-38.5434),
    ("Manaus","AM",-3.1190,-60.0217),
    ("Recife","PE",-8.0476,-34.8770),
    ("Belém","PA",-1.4558,-48.5044),
    ("Goiânia","GO",-16.6869,-49.2648),
    ("Guarulhos","SP",-23.4543,-46.5336),
    ("Campinas","SP",-22.9056,-47.0608),
    ("São Luís","MA",-2.5307,-44.3068),
    ("Maceió","AL",-9.6658,-35.7350),
    ("Natal","RN",-5.7945,-35.2120),
    ("Teresina","PI",-5.0920,-42.8038),
    ("Campo Grande","MS",-20.4697,-54.6201),
    ("Joinville","SC",-26.3044,-48.8487),
]

# ─────────────────────── DEPENDENCIAS ───────────────────────────
try:
    import requests
    import pandas as pd
    from supabase import create_client
except ImportError:
    sys.exit("Instala: pip install supabase pandas requests")

# ─────────────────────── MANAGEMENT API ─────────────────────────

def get_pat():
    pat = os.environ.get("SUPABASE_PAT", "").strip()
    if not pat:
        sys.exit(
            "Falta el Personal Access Token.\n"
            "Ejecútalo así:\n"
            "  SUPABASE_PAT=sbp_xxxx python3 scripts/setup_full.py\n"
            "Obtén el token en: https://supabase.com/dashboard/account/tokens"
        )
    return pat

def sql_exec(pat, sql, label=""):
    """Ejecuta SQL via Management API y retorna las filas como lista de dicts."""
    r = requests.post(
        f"{MGMT_BASE}/database/query",
        headers={"Authorization": f"Bearer {pat}", "Content-Type": "application/json"},
        json={"query": sql},
        timeout=120,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"SQL error [{r.status_code}] {label}: {r.text[:300]}")
    if label:
        print(f"  ✅ {label}")
    return r.json() if r.text else []

def explain_stats(pat, sql):
    """Corre EXPLAIN ANALYZE y extrae métricas clave."""
    rows = sql_exec(pat, f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}")
    if not rows:
        return {"execution_time_ms": 0, "planning_time_ms": 0, "scan_type": "?", "rows_returned": 0}
    raw = rows[0].get("QUERY PLAN", rows[0])
    if isinstance(raw, str):
        plan_list = json.loads(raw)
    elif isinstance(raw, list):
        plan_list = raw
    else:
        plan_list = [raw]
    plan = plan_list[0]
    return {
        "planning_time_ms":  round(plan.get("Planning Time", 0), 2),
        "execution_time_ms": round(plan.get("Execution Time", 0), 2),
        "rows_returned":     plan["Plan"].get("Actual Rows", 0),
        "scan_type":         plan["Plan"].get("Node Type", "?"),
    }

# ─────────────────────── REST API (datos) ───────────────────────

def insert_batch(sb, table, rows):
    if not rows:
        return
    for i in range(0, len(rows), BATCH_SIZE):
        chunk = rows[i:i+BATCH_SIZE]
        try:
            sb.table(table).insert(chunk).execute()
        except Exception as e:
            print(f"  ⚠ {table} batch {i//BATCH_SIZE}: {e}")
        time.sleep(0.05)

# ─────────────────────── KAGGLE ─────────────────────────────────

def find_csv(name):
    patterns = [
        f"~/.cache/kagglehub/datasets/olistbr/brazilian-ecommerce/**/*{name}*.csv",
        f"~/Downloads/**/*{name}*.csv",
        f"./**/*{name}*.csv",
    ]
    for pat in patterns:
        m = glob.glob(os.path.expanduser(pat), recursive=True)
        if m:
            return m[0]
    return None

def load_kaggle():
    if not find_csv("orders_dataset"):
        print("  Descargando dataset vía kagglehub...")
        try:
            import kagglehub
            kagglehub.dataset_download("olistbr/brazilian-ecommerce")
        except Exception as e:
            sys.exit(f"No se pudo descargar: {e}\nInstala: pip install kagglehub")
    return (
        pd.read_csv(find_csv("products_dataset")),
        pd.read_csv(find_csv("orders_dataset")),
        pd.read_csv(find_csv("order_payments")),
    )

# ─────────────────────── DDL ────────────────────────────────────

DDL_STATEMENTS = [
    ('extensiones', "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""),
    ('extensiones', "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\""),
    ('extensiones', "CREATE EXTENSION IF NOT EXISTS \"postgis\""),

    # Drop en orden
    ('drop payments',    "DROP TABLE IF EXISTS payments CASCADE"),
    ('drop order_items', "DROP TABLE IF EXISTS order_items CASCADE"),
    ('drop inventory',   "DROP TABLE IF EXISTS inventory CASCADE"),
    ('drop orders',      "DROP TABLE IF EXISTS orders CASCADE"),
    ('drop products',    "DROP TABLE IF EXISTS products CASCADE"),
    ('drop sellers',     "DROP TABLE IF EXISTS sellers CASCADE"),
    ('drop customers',   "DROP TABLE IF EXISTS customers CASCADE"),
    ('drop categories',  "DROP TABLE IF EXISTS categories CASCADE"),
    ('drop geolocations',"DROP TABLE IF EXISTS geolocations CASCADE"),

    ('geolocations', """
        CREATE TABLE geolocations (
            geolocation_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            zip_code_prefix  VARCHAR(20) NOT NULL,
            latitude         NUMERIC(10,8) NOT NULL,
            longitude        NUMERIC(11,8) NOT NULL,
            city             VARCHAR(100) NOT NULL,
            state            CHAR(2) NOT NULL,
            geom             GEOMETRY(Point, 4326)
        )
    """),
    ('categories', """
        CREATE TABLE categories (
            category_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            category_name         VARCHAR(150) UNIQUE NOT NULL,
            category_name_english VARCHAR(150)
        )
    """),
    ('customers', """
        CREATE TABLE customers (
            customer_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            customer_unique_id VARCHAR(50) UNIQUE NOT NULL,
            email              VARCHAR(150) UNIQUE NOT NULL,
            customer_city      VARCHAR(100) NOT NULL,
            customer_state     CHAR(2) NOT NULL,
            geolocation_id     UUID REFERENCES geolocations(geolocation_id),
            created_at         TIMESTAMPTZ DEFAULT now(),
            updated_at         TIMESTAMPTZ DEFAULT now()
        )
    """),
    ('sellers', """
        CREATE TABLE sellers (
            seller_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            seller_name    VARCHAR(150) NOT NULL,
            seller_city    VARCHAR(100) NOT NULL,
            seller_state   CHAR(2) NOT NULL,
            geolocation_id UUID REFERENCES geolocations(geolocation_id),
            created_at     TIMESTAMPTZ DEFAULT now(),
            updated_at     TIMESTAMPTZ DEFAULT now()
        )
    """),
    ('products', """
        CREATE TABLE products (
            product_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            category_id         UUID NOT NULL REFERENCES categories(category_id),
            product_name        VARCHAR(200) NOT NULL,
            product_description TEXT,
            specifications      JSONB DEFAULT '{}'::jsonb,
            weight_g            INTEGER CHECK (weight_g >= 0),
            created_at          TIMESTAMPTZ DEFAULT now(),
            updated_at          TIMESTAMPTZ DEFAULT now()
        )
    """),
    ('orders (particionada)', """
        CREATE TABLE orders (
            order_id                      UUID NOT NULL,
            customer_id                   UUID NOT NULL REFERENCES customers(customer_id),
            order_status                  VARCHAR(30) NOT NULL CHECK (
                order_status IN ('created','approved','shipped','delivered','canceled')
            ),
            order_purchase_timestamp      TIMESTAMPTZ NOT NULL,
            order_approved_at             TIMESTAMPTZ,
            order_delivered_customer_date TIMESTAMPTZ,
            order_estimated_delivery_date TIMESTAMPTZ,
            created_at                    TIMESTAMPTZ DEFAULT now(),
            updated_at                    TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (order_id, order_purchase_timestamp)
        ) PARTITION BY RANGE (order_purchase_timestamp)
    """),
    ('particion 2016',  "CREATE TABLE orders_2016  PARTITION OF orders FOR VALUES FROM ('2016-01-01') TO ('2017-01-01')"),
    ('particion 2017',  "CREATE TABLE orders_2017  PARTITION OF orders FOR VALUES FROM ('2017-01-01') TO ('2018-01-01')"),
    ('particion 2018',  "CREATE TABLE orders_2018  PARTITION OF orders FOR VALUES FROM ('2018-01-01') TO ('2019-01-01')"),
    ('particion otros', "CREATE TABLE orders_otros PARTITION OF orders FOR VALUES FROM ('2019-01-01') TO ('2030-01-01')"),
    ('payments', """
        CREATE TABLE payments (
            payment_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            order_id                 UUID NOT NULL,
            order_purchase_timestamp TIMESTAMPTZ NOT NULL,
            payment_sequential       INTEGER CHECK (payment_sequential > 0),
            payment_type             VARCHAR(50) NOT NULL,
            payment_installments     INTEGER CHECK (payment_installments >= 0),
            payment_value            NUMERIC(12,2) CHECK (payment_value >= 0),
            FOREIGN KEY (order_id, order_purchase_timestamp)
                REFERENCES orders(order_id, order_purchase_timestamp)
        )
    """),
    ('order_items', """
        CREATE TABLE order_items (
            order_item_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            order_id                 UUID NOT NULL,
            order_purchase_timestamp TIMESTAMPTZ NOT NULL,
            product_id               UUID NOT NULL REFERENCES products(product_id),
            seller_id                UUID NOT NULL REFERENCES sellers(seller_id),
            price                    NUMERIC(12,2) CHECK (price >= 0),
            freight_value            NUMERIC(12,2) CHECK (freight_value >= 0),
            FOREIGN KEY (order_id, order_purchase_timestamp)
                REFERENCES orders(order_id, order_purchase_timestamp)
        )
    """),
    ('inventory', """
        CREATE TABLE inventory (
            inventory_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            product_id     UUID NOT NULL REFERENCES products(product_id),
            seller_id      UUID NOT NULL REFERENCES sellers(seller_id),
            stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
            last_update    TIMESTAMPTZ DEFAULT now()
        )
    """),
    ('idx trigram', "CREATE INDEX idx_products_name_trgm ON products USING gin (product_name gin_trgm_ops)"),
    ('idx gist',    "CREATE INDEX idx_geolocations_spatial ON geolocations USING gist (geom)"),
]

# ─────────────────────── MAIN ────────────────────────────────────

def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")

def main():
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    pat = get_pat()
    sb  = create_client(SUPABASE_URL, ANON_KEY)

    # ── Verificar PAT ──────────────────────────────────────────
    banner("1/7  Verificando conexión")
    try:
        sql_exec(pat, "SELECT 1 AS ok")
        print("  ✅ Management API OK")
    except Exception as e:
        sys.exit(f"  ❌ PAT inválido o sin acceso: {e}")

    # ── DDL ───────────────────────────────────────────────────
    banner("2/7  Creando schema (extensiones, tablas, particiones)")
    for label, stmt in DDL_STATEMENTS:
        sql_exec(pat, stmt.strip(), label)

    # ── Cargar dataset ────────────────────────────────────────
    banner("3/7  Cargando dataset Kaggle")
    products_df, orders_df, payments_df = load_kaggle()
    print(f"  products:{len(products_df):,}  orders:{len(orders_df):,}  payments:{len(payments_df):,}")

    # Geolocations
    geo_id_map = {}
    geo_rows = []
    for city, state, lat, lon in CITIES:
        gid = str(uuid.uuid4())
        geo_id_map[city] = gid
        geo_rows.append({
            "geolocation_id": gid,
            "zip_code_prefix": f"{abs(int(lat*100)):05d}",
            "latitude": lat, "longitude": lon,
            "city": city, "state": state,
        })
    insert_batch(sb, "geolocations", geo_rows)
    # Actualizar geom vía Management API
    sql_exec(pat, "UPDATE geolocations SET geom = ST_MakePoint(longitude::float, latitude::float)::geometry")
    print(f"  ✅ {len(geo_rows)} geolocalizaciones")

    # Categories
    cat_names  = products_df['product_category_name'].dropna().unique()
    cat_id_map = {}
    cat_rows   = []
    for cat in cat_names:
        cid = str(uuid.uuid4())
        cat_id_map[cat] = cid
        cat_rows.append({
            "category_id": cid,
            "category_name": cat,
            "category_name_english": cat.replace("_"," ").title()
        })
    insert_batch(sb, "categories", cat_rows)
    print(f"  ✅ {len(cat_rows)} categorías")

    # Sellers
    seller_ids = []
    seller_rows = []
    for i, (city, state, *_) in enumerate(CITIES):
        sid = str(uuid.uuid4())
        seller_ids.append(sid)
        seller_rows.append({
            "seller_id": sid, "seller_name": f"Seller {city}",
            "seller_city": city, "seller_state": state,
            "geolocation_id": geo_id_map[city]
        })
    insert_batch(sb, "sellers", seller_rows)
    default_seller = seller_ids[0]
    print(f"  ✅ {len(seller_rows)} sellers")

    # Products
    default_cat = cat_rows[0]["category_id"]
    prod_id_map = {}
    prod_rows   = []
    for _, row in products_df.iterrows():
        pid      = str(uuid.uuid4())
        prod_id_map[row['product_id']] = pid
        cat_name = row.get('product_category_name')
        cat_id   = cat_id_map.get(cat_name, default_cat) if pd.notna(cat_name) else default_cat
        specs    = {}
        for col, key in [('product_weight_g','weight_g'),('product_length_cm','length_cm'),
                         ('product_height_cm','height_cm'),('product_width_cm','width_cm')]:
            if pd.notna(row.get(col)): specs[key] = int(row[col])
        safe_cat = cat_name if (isinstance(cat_name, str) and cat_name) else 'outros'
        pname = f"Produto {safe_cat.replace('_',' ').title()} {str(row['product_id'])[:6].upper()}"
        wg    = int(row['product_weight_g']) if pd.notna(row.get('product_weight_g')) else None
        prod_rows.append({
            "product_id": pid, "category_id": cat_id,
            "product_name": pname, "specifications": json.dumps(specs), "weight_g": wg
        })
    insert_batch(sb, "products", prod_rows)
    print(f"  ✅ {len(prod_rows):,} productos")

    # Customers
    orders_df_v = orders_df.dropna(subset=['order_purchase_timestamp']).copy()
    orders_df_v['order_purchase_timestamp'] = pd.to_datetime(orders_df_v['order_purchase_timestamp'])
    cust_id_map = {}
    cust_rows   = []
    for i, chash in enumerate(orders_df_v['customer_id'].unique()):
        cuid = str(uuid.uuid4())
        cust_id_map[chash] = cuid
        city_obj = CITIES[i % len(CITIES)]
        cust_rows.append({
            "customer_id": cuid,
            "customer_unique_id": f"USR-{i+1:06d}",
            "email": f"customer{i+1}@ecommify.com",
            "customer_city": city_obj[0], "customer_state": city_obj[1],
            "geolocation_id": geo_id_map[city_obj[0]]
        })
    insert_batch(sb, "customers", cust_rows)
    print(f"  ✅ {len(cust_rows):,} clientes")

    # Orders
    valid_statuses = {'created','approved','shipped','delivered','canceled'}
    order_id_map   = {}
    order_rows     = []
    for _, row in orders_df_v.iterrows():
        if row['customer_id'] not in cust_id_map:
            continue
        oid  = str(uuid.uuid4())
        ts   = row['order_purchase_timestamp'].isoformat()
        order_id_map[row['order_id']] = (oid, ts)
        status = row['order_status'] if row['order_status'] in valid_statuses else 'delivered'
        approved  = row['order_approved_at'] if pd.notna(row.get('order_approved_at')) else None
        delivered = row['order_delivered_customer_date'] if pd.notna(row.get('order_delivered_customer_date')) else None
        estimated = row['order_estimated_delivery_date'] if pd.notna(row.get('order_estimated_delivery_date')) else None
        order_rows.append({
            "order_id": oid, "customer_id": cust_id_map[row['customer_id']],
            "order_status": status, "order_purchase_timestamp": ts,
            "order_approved_at": approved,
            "order_delivered_customer_date": delivered,
            "order_estimated_delivery_date": estimated,
        })
    insert_batch(sb, "orders", order_rows)
    print(f"  ✅ {len(order_rows):,} órdenes")

    # Payments
    pay_rows = []
    for _, row in payments_df.iterrows():
        if row['order_id'] not in order_id_map:
            continue
        oid, ts = order_id_map[row['order_id']]
        pay_rows.append({
            "order_id": oid, "order_purchase_timestamp": ts,
            "payment_sequential": int(row['payment_sequential']),
            "payment_type": str(row['payment_type']),
            "payment_installments": int(row['payment_installments']) if pd.notna(row.get('payment_installments')) else 1,
            "payment_value": float(row['payment_value']) if pd.notna(row.get('payment_value')) else 0.0,
        })
    insert_batch(sb, "payments", pay_rows)
    print(f"  ✅ {len(pay_rows):,} pagos")

    # ── IDs reales para EXPLAIN ───────────────────────────────
    banner("4/7  Obteniendo IDs reales para EXPLAIN")
    r_cust = sql_exec(pat, "SELECT customer_id FROM orders LIMIT 1")
    r_cat  = sql_exec(pat, "SELECT category_id FROM products LIMIT 1")
    sample_customer = r_cust[0]["customer_id"]
    sample_category = r_cat[0]["category_id"]
    print(f"  customer_id = {sample_customer}")
    print(f"  category_id = {sample_category}")

    # ── EXPLAIN ANALYZE ───────────────────────────────────────
    banner("5/7  EXPLAIN ANALYZE antes/después de índices")
    metrics = {}

    queries = [
        ("Q1_btree_orders_customer",
         "idx_orders_customer",
         f"CREATE INDEX idx_orders_customer ON orders(customer_id)",
         f"SELECT * FROM orders WHERE customer_id = '{sample_customer}'",
         "B-Tree orders(customer_id)"),
        ("Q2_btree_products_category",
         "idx_products_category",
         f"CREATE INDEX idx_products_category ON products(category_id)",
         f"SELECT * FROM products WHERE category_id = '{sample_category}'",
         "B-Tree products(category_id)"),
        ("Q3_gin_jsonb_specifications",
         "idx_products_specifications_gin",
         "CREATE INDEX idx_products_specifications_gin ON products USING GIN(specifications)",
         "SELECT * FROM products WHERE specifications @> '{\"weight_g\": 300}'",
         "GIN JSONB products(specifications)"),
        ("Q4_gin_trigram_product_name",
         "idx_products_name_trgm",
         "CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (product_name gin_trgm_ops)",
         "SELECT product_id, product_name FROM products WHERE product_name % 'Smartphone'",
         "GIN trigram products(product_name)"),
        ("Q5_gist_geospatial",
         "idx_geolocations_spatial",
         "CREATE INDEX IF NOT EXISTS idx_geolocations_spatial ON geolocations USING gist (geom)",
         "SELECT city FROM geolocations WHERE ST_DWithin(geom::geography, ST_MakePoint(-46.6333,-23.5505)::geography, 500000)",
         "GiST geolocations(geom)"),
    ]

    for key, idx_name, idx_sql, q_sql, label in queries:
        print(f"\n  {label}")
        try:
            sql_exec(pat, f"DROP INDEX IF EXISTS {idx_name}")
            b = explain_stats(pat, q_sql)
            sql_exec(pat, idx_sql)
            a = explain_stats(pat, q_sql)
            imp = round((b["execution_time_ms"] - a["execution_time_ms"])
                        / max(b["execution_time_ms"], 0.001) * 100, 1)
            metrics[key] = {"before": b, "after": a, "improvement_pct": imp}
            print(f"    ANTES:  {b['execution_time_ms']}ms  scan={b['scan_type']}")
            print(f"    DESPUÉS:{a['execution_time_ms']}ms  scan={a['scan_type']}")
        except Exception as e:
            print(f"    ⚠ Error en {label}: {e}")
            metrics[key] = {"before": {"execution_time_ms":0,"scan_type":"ERROR"},
                            "after":  {"execution_time_ms":0,"scan_type":"ERROR"},
                            "improvement_pct": 0}

    # ── Evidencias ────────────────────────────────────────────
    banner("6/7  Guardando evidencias")
    payload = {
        "generated_at": datetime.now().isoformat(),
        "database": "postgresql-supabase",
        "table_counts": {
            "products": len(prod_rows), "customers": len(cust_rows),
            "orders": len(order_rows), "payments": len(pay_rows),
            "geolocations": len(geo_rows), "categories": len(cat_rows),
        },
        "queries": metrics,
    }
    json_path = EVIDENCIAS / "metrics_raw.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"  ✅ {json_path}")

    query_labels = [
        ("Q1","B-Tree","orders(customer_id)","Historial por cliente","Q1_btree_orders_customer"),
        ("Q2","B-Tree","products(category_id)","Productos por categoría","Q2_btree_products_category"),
        ("Q3","GIN","products(specifications)","Atributos JSONB","Q3_gin_jsonb_specifications"),
        ("Q4","GIN trigram","products(product_name)","Búsqueda difusa","Q4_gin_trigram_product_name"),
        ("Q5","GiST","geolocations(geom)","Geoespacial PostGIS","Q5_gist_geospatial"),
    ]
    md = [
        "# PostgreSQL — Comparativa antes/después de índices\n",
        f"_Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
        "| Query | Tipo índice | Columna | Descripción | Tiempo ANTES (ms) | Scan ANTES | Tiempo DESPUÉS (ms) | Scan DESPUÉS | Mejora |",
        "|---|---|---|---|---:|---|---:|---|---:|",
    ]
    for q, tipo, col, desc, key in query_labels:
        if key not in metrics:
            continue
        b = metrics[key]["before"]
        a = metrics[key]["after"]
        imp = metrics[key]["improvement_pct"]
        sign = "+" if imp >= 0 else ""
        md.append(f"| {q} | {tipo} | `{col}` | {desc} | {b['execution_time_ms']} | {b['scan_type']} | {a['execution_time_ms']} | {a['scan_type']} | {sign}{imp}% |")
    md += [
        "\n## Notas",
        f"- Dataset: Olist Brazilian E-Commerce — {len(prod_rows):,} productos, {len(order_rows):,} órdenes.",
        "- Tiempos medidos con `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` en Supabase (PostgreSQL 15).",
        "- Tabla `orders` particionada por RANGE en `order_purchase_timestamp` (particiones 2016–2019).",
    ]
    md_path = EVIDENCIAS / "comparison_table.md"
    md_path.write_text("\n".join(md) + "\n")
    print(f"  ✅ {md_path}")

    banner("7/7  ¡Listo!")
    print(f"  productos  : {len(prod_rows):,}")
    print(f"  órdenes    : {len(order_rows):,}")
    print(f"  pagos      : {len(pay_rows):,}")
    print(f"\n  Evidencias → {EVIDENCIAS}")

if __name__ == "__main__":
    main()
