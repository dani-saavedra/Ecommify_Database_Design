-- Creación manual de particiones mensuales operacionales para el año 2026
CREATE TABLE orders_2026_m05 PARTITION OF orders
    FOR VALUES FROM ('2026-05-01 00:00:00+00') TO ('2026-06-01 00:00:00+00');

CREATE TABLE orders_2026_m06 PARTITION OF orders
    FOR VALUES FROM ('2026-06-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');