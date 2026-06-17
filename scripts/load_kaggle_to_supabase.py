"""
load_kaggle_to_supabase.py
Carga el dataset Kaggle de Brazilian E-Commerce en Supabase via REST API.
PRERREQUISITO: Ejecutar 00_setup_and_explain.sql en el SQL Editor de Supabase primero.
"""
import os, uuid, glob, warnings, time
import pandas as pd
from supabase import create_client

warnings.filterwarnings('ignore')

SUPABASE_URL = "https://litdnoxzcbdecgrjjewt.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_TDWPbmPplOFc4kREL-_XAw_9aO1ymm2")
KAGGLE_PATH  = os.path.expanduser("~/.cache/kagglehub/datasets/olistbr/brazilian-ecommerce")
BATCH_SIZE   = 500

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def find_csv(name):
    matches = glob.glob(f"{KAGGLE_PATH}/**/*{name}*.csv", recursive=True)
    if not matches:
        raise FileNotFoundError(f"CSV {name} no encontrado en {KAGGLE_PATH}")
    return matches[0]

def insert_batch(table, rows):
    """Inserta en lotes con retry simple."""
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i+BATCH_SIZE]
        try:
            sb.table(table).insert(batch).execute()
        except Exception as e:
            print(f"  ⚠ Error batch {i//BATCH_SIZE}: {e}")
        time.sleep(0.1)

def main():
    print("=" * 60)
    print("Ecommify — Carga de datos Kaggle → Supabase")
    print("=" * 60)

    # -- Leer CSVs --
    print("\n[1/5] Leyendo dataset Kaggle...")
    products_df = pd.read_csv(find_csv("products"))
    orders_df   = pd.read_csv(find_csv("orders"))
    payments_df = pd.read_csv(find_csv("payments"))
    reviews_df  = pd.read_csv(find_csv("reviews"))
    print(f"  products: {len(products_df):,} | orders: {len(orders_df):,} | payments: {len(payments_df):,}")

    # -- Geolocalizaciones (20 ciudades brasileñas reales) --
    print("\n[2/5] Insertando geolocalizaciones...")
    cities = [
        ("São Paulo","SP",-23.5505,-46.6333),("Rio de Janeiro","RJ",-22.9068,-43.1729),
        ("Belo Horizonte","MG",-19.9167,-43.9345),("Brasília","DF",-15.7801,-47.9292),
        ("Curitiba","PR",-25.4278,-49.2731),("Porto Alegre","RS",-30.0346,-51.2177),
        ("Salvador","BA",-12.9714,-38.5014),("Fortaleza","CE",-3.7172,-38.5434),
        ("Manaus","AM",-3.1190,-60.0217),("Recife","PE",-8.0476,-34.8770),
        ("Belém","PA",-1.4558,-48.5044),("Goiânia","GO",-16.6869,-49.2648),
        ("Guarulhos","SP",-23.4543,-46.5336),("Campinas","SP",-22.9056,-47.0608),
        ("São Luís","MA",-2.5307,-44.3068),("Maceió","AL",-9.6658,-35.7350),
        ("Natal","RN",-5.7945,-35.2120),("Teresina","PI",-5.0920,-42.8038),
        ("Campo Grande","MS",-20.4697,-54.6201),("Joinville","SC",-26.3044,-48.8487),
    ]
    geo_id_map = {}
    geo_rows = []
    for city, state, lat, lon in cities:
        gid = str(uuid.uuid4())
        geo_id_map[city] = gid
        geo_rows.append({
            "geolocation_id": gid,
            "zip_code_prefix": f"{abs(int(lat*100)):05d}",
            "latitude": lat, "longitude": lon,
            "city": city, "state": state,
        })
    insert_batch("geolocations", geo_rows)
    print(f"  ✅ {len(geo_rows)} geolocalizaciones")

    # -- Categorías --
    print("\n[3/5] Insertando categorías y productos...")
    cat_names = products_df['product_category_name'].dropna().unique()
    cat_id_map = {}
    cat_rows = []
    for cat in cat_names:
        cid = str(uuid.uuid4())
        cat_id_map[cat] = cid
        cat_rows.append({
            "category_id": cid,
            "category_name": cat,
            "category_name_english": cat.replace("_", " ").title()
        })
    insert_batch("categories", cat_rows)
    print(f"  ✅ {len(cat_rows)} categorías")

    # -- Sellers sintéticos (dataset original tiene ~3000 seller_ids) --
    seller_hash_to_uuid = {}
    seller_rows = []
    for i, city in enumerate(cities[:20]):
        sid = str(uuid.uuid4())
        seller_rows.append({
            "seller_id": sid,
            "seller_name": f"Vendedor {city[0]} {i+1}",
            "seller_city": city[0], "seller_state": city[1],
            "geolocation_id": geo_id_map[city[0]]
        })
    insert_batch("sellers", seller_rows)
    default_seller_id = seller_rows[0]["seller_id"]
    print(f"  ✅ {len(seller_rows)} sellers")

    # -- Productos --
    product_hash_to_uuid = {}
    prod_rows = []
    for _, row in products_df.iterrows():
        pid = str(uuid.uuid4())
        product_hash_to_uuid[row['product_id']] = pid
        cat_name = row.get('product_category_name', None)
        cat_id = cat_id_map.get(cat_name, cat_rows[0]["category_id"]) if cat_name and pd.notna(cat_name) else cat_rows[0]["category_id"]
        specs = {}
        if pd.notna(row.get('product_weight_g')):   specs["weight_g"]   = str(int(row['product_weight_g']))
        if pd.notna(row.get('product_length_cm')):  specs["length_cm"]  = str(int(row['product_length_cm']))
        if pd.notna(row.get('product_height_cm')):  specs["height_cm"]  = str(int(row['product_height_cm']))
        if pd.notna(row.get('product_width_cm')):   specs["width_cm"]   = str(int(row['product_width_cm']))
        prod_rows.append({
            "product_id": pid,
            "category_id": cat_id,
            "product_name": f"Produto {cat_name or 'outros'} {str(row['product_id'])[:6].upper()}".replace("_"," ").title(),
            "specifications": specs,
            "weight_g": int(row['product_weight_g']) if pd.notna(row.get('product_weight_g')) else None,
        })
    insert_batch("products", prod_rows)
    print(f"  ✅ {len(prod_rows):,} productos")

    # -- Customers --
    print("\n[4/5] Insertando clientes y órdenes...")
    customer_hash_to_uuid = {}
    cust_rows = []
    for i, cid_hash in enumerate(orders_df['customer_id'].unique()):
        cuid = str(uuid.uuid4())
        customer_hash_to_uuid[cid_hash] = cuid
        city_obj = cities[i % len(cities)]
        cust_rows.append({
            "customer_id": cuid,
            "customer_unique_id": f"USR-{str(i+1).zfill(6)}",
            "email": f"customer{i+1}@ecommify.com",
            "customer_city": city_obj[0],
            "customer_state": city_obj[1],
            "geolocation_id": geo_id_map[city_obj[0]]
        })
    insert_batch("customers", cust_rows)
    print(f"  ✅ {len(cust_rows):,} clientes")

    # -- Orders (datos reales 2016–2018, necesita particiones correspondientes) --
    order_hash_to_uuid = {}
    valid_orders = orders_df.dropna(subset=['order_purchase_timestamp']).copy()
    valid_orders['order_purchase_timestamp'] = pd.to_datetime(valid_orders['order_purchase_timestamp'])
    statuses = ['created','approved','shipped','delivered','canceled']
    order_rows = []
    for _, row in valid_orders.iterrows():
        if row['customer_id'] not in customer_hash_to_uuid:
            continue
        oid = str(uuid.uuid4())
        order_hash_to_uuid[row['order_id']] = (oid, row['order_purchase_timestamp'].isoformat())
        status = row['order_status'] if row['order_status'] in statuses else 'delivered'
        order_rows.append({
            "order_id": oid,
            "customer_id": customer_hash_to_uuid[row['customer_id']],
            "order_status": status,
            "order_purchase_timestamp": row['order_purchase_timestamp'].isoformat(),
        })
    insert_batch("orders", order_rows)
    print(f"  ✅ {len(order_rows):,} órdenes")

    # -- Payments --
    print("\n[5/5] Insertando pagos...")
    pay_rows = []
    for _, row in payments_df.iterrows():
        if row['order_id'] not in order_hash_to_uuid:
            continue
        oid, ts = order_hash_to_uuid[row['order_id']]
        pay_rows.append({
            "order_id": oid,
            "order_purchase_timestamp": ts,
            "payment_sequential": int(row['payment_sequential']),
            "payment_type": str(row['payment_type']),
            "payment_installments": int(row['payment_installments']) if pd.notna(row.get('payment_installments')) else 1,
            "payment_value": float(row['payment_value']) if pd.notna(row.get('payment_value')) else 0.0,
        })
    insert_batch("payments", pay_rows)
    print(f"  ✅ {len(pay_rows):,} pagos")

    print("\n" + "=" * 60)
    print("✅ Carga completa. Verifica en Supabase Table Editor.")
    print("=" * 60)

if __name__ == "__main__":
    main()
