"""
capture_explain_metrics.py
Captura métricas EXPLAIN ANALYZE de PostgreSQL vía Supabase REST API.
Requiere que las tablas existan y tengan datos.
"""
import os, json, re, requests, warnings
warnings.filterwarnings('ignore')

SUPABASE_URL = "https://litdnoxzcbdecgrjjewt.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_TDWPbmPplOFc4kREL-_XAw_9aO1ymm2")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def parse_explain(text):
    """Extrae métricas clave del output de EXPLAIN ANALYZE."""
    exec_time   = re.search(r"Execution Time:\s*([\d.]+) ms", text)
    plan_time   = re.search(r"Planning Time:\s*([\d.]+) ms", text)
    rows_removed= re.search(r"Rows Removed by Filter:\s*(\d+)", text)
    scan_type   = "Seq Scan" if "Seq Scan" in text else \
                  "Index Scan" if "Index Scan" in text else \
                  "Bitmap" if "Bitmap" in text else "Other"
    return {
        "execution_ms":     float(exec_time.group(1)) if exec_time else None,
        "planning_ms":      float(plan_time.group(1)) if plan_time else None,
        "scan_type":        scan_type,
        "rows_removed":     int(rows_removed.group(1)) if rows_removed else None,
        "raw":              text[:500]
    }

def run_explain_via_rpc(sql):
    """
    Intenta ejecutar EXPLAIN via RPC.
    Requiere que exista la función explain_query en Supabase.
    """
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/explain_query",
        headers=headers,
        json={"query_text": sql},
        timeout=30
    )
    if r.status_code == 200:
        return r.json()
    return {"error": r.text[:200], "status": r.status_code}

# Queries a medir
QUERIES = {
    "Q1_before_btree_orders": """
        EXPLAIN ANALYZE SELECT * FROM orders
        WHERE customer_id = (SELECT customer_id FROM customers LIMIT 1);
    """,
    "Q2_before_btree_products": """
        EXPLAIN ANALYZE SELECT * FROM products
        WHERE category_id = (SELECT category_id FROM categories LIMIT 1);
    """,
    "Q3_before_gin_jsonb": """
        EXPLAIN ANALYZE SELECT * FROM products
        WHERE specifications @> '{"weight_g": "220"}';
    """,
    "Q4_trigram": """
        EXPLAIN ANALYZE SELECT product_id, product_name,
            similarity(product_name, 'Smartphone Pro') AS score
        FROM products
        WHERE product_name % 'Smartphone Pro'
        ORDER BY score DESC;
    """,
    "Q5_geospatial": """
        EXPLAIN ANALYZE
        SELECT o.order_id, c.customer_city, s.seller_name,
            ST_DistanceSphere(g_sel.geom, g_cust.geom) / 1000 AS distancia_km
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN geolocations g_cust ON c.geolocation_id = g_cust.geolocation_id
        JOIN order_items oi ON o.order_id = oi.order_id
            AND o.order_purchase_timestamp = oi.order_purchase_timestamp
        JOIN sellers s ON oi.seller_id = s.seller_id
        JOIN geolocations g_sel ON s.geolocation_id = g_sel.geolocation_id
        WHERE o.customer_id = (SELECT customer_id FROM customers LIMIT 1);
    """
}

if __name__ == "__main__":
    print("Capturando métricas EXPLAIN ANALYZE via Supabase RPC...")
    results = {}
    for name, sql in QUERIES.items():
        print(f"  {name}...")
        result = run_explain_via_rpc(sql.strip())
        results[name] = result

    output_path = os.path.join(os.path.dirname(__file__),
                               "../evidencias/postgresql/metrics_raw.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Guardado en {output_path}")
