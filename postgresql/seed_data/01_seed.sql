-- Población inicial de datos de prueba coherentes para el año 2026
INSERT INTO geolocations (geolocation_id, zip_code_prefix, latitude, longitude, city, state, geom) VALUES 
('110111aa-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '110221', 4.64828370, -74.06027410, 'Bogota', 'DC', ST_SetSRID(ST_MakePoint(-74.06027410, 4.64828370), 4326)),
('220222aa-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '050012', 6.24420300, -75.58121100, 'Medellin', 'ANT', ST_SetSRID(ST_MakePoint(-75.58121100, 6.24420300), 4326));

INSERT INTO categories (category_id, category_name, category_name_english) VALUES 
('440111dd-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'Tecnologia', 'Technology'),
('440222dd-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'Muebles', 'Furniture');

INSERT INTO customers (customer_id, customer_unique_id, email, customer_city, customer_state, geolocation_id) VALUES 
('220111bb-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'USR-99440', 'val.rodriguez@unisabana.edu.co', 'Bogota', 'DC', '110111aa-b2c3-4e5f-a6b7-c8d9e0f1a2b3');

INSERT INTO sellers (seller_id, seller_name, seller_city, seller_state, geolocation_id) VALUES 
('330111cc-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'Ecommify Tech Store', 'Medellin', 'ANT', '220222aa-b2c3-4e5f-a6b7-c8d9e0f1a2b3');

INSERT INTO products (product_id, category_id, product_name, product_description, specifications, photos, weight_g) VALUES 
('550111ee-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '440111dd-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'Smartphone X Pro Max', 'Telefono de alta gama', '{"RAM": "12GB", "Storage": "256GB"}'::jsonb, ARRAY['front.png'], 220);

INSERT INTO inventory (product_id, seller_id, stock_quantity) VALUES 
('550111ee-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '330111cc-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 150);

INSERT INTO orders (order_id, customer_id, order_status, order_purchase_timestamp) VALUES 
('660111ff-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '220111bb-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 'approved', '2026-05-25 14:30:00-05');

INSERT INTO order_items (order_id, order_purchase_timestamp, product_id, seller_id, quantity, price, freight_value) VALUES 
('660111ff-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '2026-05-25 14:30:00-05', '550111ee-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '330111cc-b2c3-4e5f-a6b7-c8d9e0f1a2b3', 1, 899.99, 25.00);

INSERT INTO payments (order_id, order_purchase_timestamp, payment_sequential, payment_type, payment_installments, payment_value) VALUES 
('660111ff-b2c3-4e5f-a6b7-c8d9e0f1a2b3', '2026-05-25 14:30:00-05', 1, 'credit_card', 3, 924.99);