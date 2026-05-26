-- Habilitación de extensiones para ID únicos, búsquedas difusas y datos geoespaciales
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm; -- Requerimiento RF02 (Búsquedas tolerantes a errores)
CREATE EXTENSION IF NOT EXISTS postgis; -- Requerimiento RF07 (Cálculo de costos por geolocalización)