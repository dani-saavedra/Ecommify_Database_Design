-- Creación de tablas independientes y maestras
CREATE TABLE geolocations (
    geolocation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zip_code_prefix VARCHAR(20) NOT NULL,
    latitude NUMERIC(10,8) NOT NULL,
    longitude NUMERIC(11,8) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state CHAR(2) NOT NULL,
    geom GEOMETRY(Point, 4326) -- Campo espacial optimizado para PostGIS
);

CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(150) UNIQUE NOT NULL,
    category_name_english VARCHAR(150) UNIQUE
);

CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_unique_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state CHAR(2) NOT NULL,
    geolocation_id UUID REFERENCES geolocations(geolocation_id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sellers (
    seller_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_name VARCHAR(150) NOT NULL,
    seller_city VARCHAR(100) NOT NULL,
    seller_state CHAR(2) NOT NULL,
    geolocation_id UUID REFERENCES geolocations(geolocation_id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES categories(category_id),
    product_name VARCHAR(200) NOT NULL,
    product_description TEXT,
    specifications JSONB DEFAULT '{}'::jsonb, -- Soporte polimórfico local
    photos TEXT[],
    promotion_period TSTZRANGE,
    weight_g INTEGER CHECK (weight_g >= 0),
    length_cm NUMERIC(10,2) CHECK (length_cm >= 0),
    height_cm NUMERIC(10,2) CHECK (height_cm >= 0),
    width_cm NUMERIC(10,2) CHECK (width_cm >= 0),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Tabla Core con estrategia de Range Partitioning por fechas
CREATE TABLE orders (
    order_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    order_status VARCHAR(30) NOT NULL CHECK (order_status IN ('created', 'approved', 'shipped', 'delivered', 'canceled')),
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    order_approved_at TIMESTAMPTZ,
    order_delivered_carrier_date TIMESTAMPTZ,
    order_delivered_customer_date TIMESTAMPTZ,
    order_estimated_delivery_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (order_id, order_purchase_timestamp) -- Llave compuesta obligatoria para partición
) PARTITION BY RANGE (order_purchase_timestamp);

-- Tablas dependientes unidas mediante llaves compuestas a la tabla padre particionada
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    product_id UUID NOT NULL REFERENCES products(product_id),
    seller_id UUID NOT NULL REFERENCES sellers(seller_id),
    quantity INTEGER CHECK (quantity > 0),
    price NUMERIC(12,2) CHECK (price >= 0),
    freight_value NUMERIC(12,2) CHECK (freight_value >= 0),
    shipping_limit_date TIMESTAMPTZ,
    FOREIGN KEY (order_id, order_purchase_timestamp) REFERENCES orders(order_id, order_purchase_timestamp)
);

CREATE TABLE payments (
    payment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    order_purchase_timestamp TIMESTAMPTZ NOT NULL,
    payment_sequential INTEGER CHECK (payment_sequential > 0),
    payment_type VARCHAR(50) NOT NULL,
    payment_installments INTEGER CHECK (payment_installments >= 0),
    payment_value NUMERIC(12,2) CHECK (payment_value >= 0),
    FOREIGN KEY (order_id, order_purchase_timestamp) REFERENCES orders(order_id, order_purchase_timestamp)
);

CREATE TABLE inventory (
    inventory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(product_id),
    seller_id UUID NOT NULL REFERENCES sellers(seller_id),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0),
    last_update TIMESTAMPTZ DEFAULT now()
);

-- Indexación avanzada para optimización de consultas masivas
CREATE INDEX idx_products_name_trgm ON products USING gin (product_name gin_trgm_ops);
CREATE INDEX idx_geolocations_spatial ON geolocations USING gist (geom);