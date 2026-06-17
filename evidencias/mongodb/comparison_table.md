# Evidencias de Rendimiento — MongoDB Atlas
**Fecha:** 2026-06-16 | **Cluster:** olist.02nueqj.mongodb.net | **DB:** ecommify

## Volumen de datos
| Colección | Documentos |
|---|---|
| products_catalog | 32,951 |
| order_reviews | 99,224 |

---

## Tabla comparativa antes/después de índices

| # | Consulta | Índice | Stage ANTES | Docs examinados ANTES | Tiempo ANTES (ms) | Stage DESPUÉS | Docs examinados DESPUÉS | Tiempo DESPUÉS (ms) | Reducción docs | Reducción tiempo |
|---|---|---|---|---|---|---|---|---|---|---|
| Q1 | Búsqueda ESR: categoría + peso + orden | Compuesto (category.name, product_name, weight_g) | SORT (COLLSCAN) | 32,951 | 28 | FETCH (IXSCAN) | 583 | 4 | **98.2%** | **85.7%** |
| Q2 | Reseñas positivas (score ≥ 4) | Parcial (score ≥ 4) | COLLSCAN | 99,224 | 68 | FETCH | 76,470 | 100 | 22.9% | -47.1%* |
| Q3 | Búsqueda full-text en comentarios | Text (title + message) | N/A (requiere índice) | — | — | TEXT_MATCH | 8,652 | 60 | 91.3% vs total | N/A |

> *Q2: El índice parcial es **más lento** porque retorna 76,470 de 99,224 documentos (77%). Con selectividad tan alta, el overhead del índice supera al beneficio. Ver Lecciones Aprendidas.

---

## Aggregation Pipeline optimizado

| Etapa | Operación | Propósito |
|---|---|---|
| 1 | `$match` | Filtrar solo "Celulares y Smartphones" — reduce docs temprano |
| 2 | `$unwind` | Expandir array `specifications` para análisis por atributo |
| 3 | `$group` | Agrupar por categoría, contar productos, listar atributos |
| 4 | `$project` | Seleccionar campos finales |
| 5 | `$sort` | Ordenar por total de productos |

**Resultado:** 4,536 productos procesados en **114 ms**
```json
{
  "category": "Celulares y Smartphones",
  "total_products": 4536,
  "attributes_detected": ["weight_g", "width_cm", "height_cm", "length_cm"],
  "avg_weight_g": 68.8
}
```

---

## Resumen de índices implementados

| Índice | Colección | Tipo | Justificación (regla ESR) |
|---|---|---|---|
| idx_esr_category_name_weight | products_catalog | Compuesto | E: category.name, S: product_name, R: dimensions.weight_g |
| idx_partial_positive_reviews | order_reviews | Parcial | Solo score ≥ 4; reduce tamaño físico del índice |
| idx_text_reviews | order_reviews | Text | Habilita búsqueda semántica en comentarios |
