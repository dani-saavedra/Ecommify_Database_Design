#!/usr/bin/env python3
"""
patch_q4_q5.py — Completa Q4 y Q5 en evidencias sin recargar datos.
Uso: SUPABASE_PAT=sbp_xxxx python3 scripts/patch_q4_q5.py
"""
import os, sys, json, requests
from pathlib import Path
from datetime import datetime

PROJECT_REF = "litdnoxzcbdecgrjjewt"
MGMT_URL    = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
EVIDENCIAS  = Path(__file__).resolve().parent.parent / "evidencias" / "postgresql"

pat = os.environ.get("SUPABASE_PAT", "").strip()
if not pat:
    sys.exit("Falta SUPABASE_PAT")

def sql_exec(sql):
    r = requests.post(MGMT_URL,
        headers={"Authorization": f"Bearer {pat}", "Content-Type": "application/json"},
        json={"query": sql}, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(r.text[:300])
    return r.json() if r.text else []

def explain_stats(sql):
    rows = sql_exec(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}")
    if not rows:
        return {"execution_time_ms": 0, "planning_time_ms": 0, "scan_type": "?", "rows_returned": 0}
    raw = rows[0].get("QUERY PLAN", rows[0])
    plan_list = json.loads(raw) if isinstance(raw, str) else (raw if isinstance(raw, list) else [raw])
    plan = plan_list[0]
    return {
        "planning_time_ms":  round(plan.get("Planning Time", 0), 2),
        "execution_time_ms": round(plan.get("Execution Time", 0), 2),
        "rows_returned":     plan["Plan"].get("Actual Rows", 0),
        "scan_type":         plan["Plan"].get("Node Type", "?"),
    }

print("Midiendo Q4 — GIN trigram products(product_name)...")
sql_exec("DROP INDEX IF EXISTS idx_products_name_trgm")
q4_before = explain_stats("SELECT product_id, product_name FROM products WHERE product_name % 'Smartphone'")
sql_exec("CREATE INDEX idx_products_name_trgm ON products USING gin (product_name gin_trgm_ops)")
q4_after  = explain_stats("SELECT product_id, product_name FROM products WHERE product_name % 'Smartphone'")
print(f"  ANTES:  {q4_before['execution_time_ms']}ms  scan={q4_before['scan_type']}")
print(f"  DESPUÉS:{q4_after['execution_time_ms']}ms  scan={q4_after['scan_type']}")

print("Midiendo Q5 — GiST geolocations(geom)...")
sql_exec("DROP INDEX IF EXISTS idx_geolocations_spatial")
q5_sql = "SELECT city FROM geolocations WHERE ST_DWithin(geom::geography, ST_MakePoint(-46.6333,-23.5505)::geography, 500000)"
q5_before = explain_stats(q5_sql)
sql_exec("CREATE INDEX idx_geolocations_spatial ON geolocations USING gist (geom)")
q5_after  = explain_stats(q5_sql)
print(f"  ANTES:  {q5_before['execution_time_ms']}ms  scan={q5_before['scan_type']}")
print(f"  DESPUÉS:{q5_after['execution_time_ms']}ms  scan={q5_after['scan_type']}")

# Actualizar JSON existente
json_path = EVIDENCIAS / "metrics_raw.json"
data = json.loads(json_path.read_text())
data["queries"]["Q4_gin_trigram_product_name"] = {
    "before": q4_before, "after": q4_after,
    "improvement_pct": round((q4_before["execution_time_ms"] - q4_after["execution_time_ms"])
                              / max(q4_before["execution_time_ms"], 0.001) * 100, 1)
}
data["queries"]["Q5_gist_geospatial"] = {
    "before": q5_before, "after": q5_after,
    "improvement_pct": round((q5_before["execution_time_ms"] - q5_after["execution_time_ms"])
                              / max(q5_before["execution_time_ms"], 0.001) * 100, 1)
}
json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

# Regenerar comparison_table.md
queries_meta = [
    ("Q1","B-Tree","orders(customer_id)","Historial por cliente","Q1_btree_orders_customer"),
    ("Q2","B-Tree","products(category_id)","Productos por categoría","Q2_btree_products_category"),
    ("Q3","GIN","products(specifications)","Atributos JSONB","Q3_gin_jsonb_specifications"),
    ("Q4","GIN trigram","products(product_name)","Búsqueda difusa","Q4_gin_trigram_product_name"),
    ("Q5","GiST","geolocations(geom)","Geoespacial PostGIS","Q5_gist_geospatial"),
]
counts = data["table_counts"]
md = [
    "# PostgreSQL — Comparativa antes/después de índices\n",
    f"_Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n",
    "| Query | Tipo índice | Columna | Descripción | Tiempo ANTES (ms) | Scan ANTES | Tiempo DESPUÉS (ms) | Scan DESPUÉS | Mejora |",
    "|---|---|---|---|---:|---|---:|---|---:|",
]
for q, tipo, col, desc, key in queries_meta:
    if key not in data["queries"]:
        continue
    b   = data["queries"][key]["before"]
    a   = data["queries"][key]["after"]
    imp = data["queries"][key]["improvement_pct"]
    sign = "+" if imp >= 0 else ""
    md.append(f"| {q} | {tipo} | `{col}` | {desc} | {b['execution_time_ms']} | {b['scan_type']} | {a['execution_time_ms']} | {a['scan_type']} | {sign}{imp}% |")
md += [
    "\n## Notas",
    f"- Dataset: Olist Brazilian E-Commerce — {counts['products']:,} productos, {counts['orders']:,} órdenes.",
    "- Tiempos medidos con `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` en Supabase (PostgreSQL 15).",
    "- Tabla `orders` particionada por RANGE en `order_purchase_timestamp` (particiones 2016–2019).",
]
(EVIDENCIAS / "comparison_table.md").write_text("\n".join(md) + "\n")
print(f"\n✅ Evidencias actualizadas en {EVIDENCIAS}")
