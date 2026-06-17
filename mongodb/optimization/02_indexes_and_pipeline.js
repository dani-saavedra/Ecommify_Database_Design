// Unidad 5 - Optimización MongoDB
// Dataset: Olist Brazilian E-Commerce — 32,951 productos, 99,224 reseñas
// Cluster: olist.02nueqj.mongodb.net | DB: ecommify

// ============================================================
// 1. Índice compuesto siguiendo regla ESR
//    E: category.name (Equality)
//    S: product_name  (Sort)
//    R: dimensions.weight_g (Range)
// ============================================================

// ANTES — sin índice (COLLSCAN, 32,951 docs examinados, 28ms)
db.products_catalog.find({
  "category.name": "Celulares y Smartphones",
  "dimensions.weight_g": { $gte: 200 }
}).sort({ product_name: 1 }).explain("executionStats");
// executionStats: { totalDocsExamined: 32951, nReturned: 583, executionTimeMillis: 28, stage: "SORT" }

db.products_catalog.createIndex(
  { "category.name": 1, product_name: 1, "dimensions.weight_g": 1 },
  { name: "idx_esr_category_name_weight" }
);

// DESPUÉS — con índice ESR (IXSCAN, 583 docs examinados, 4ms → 85.7% más rápido)
db.products_catalog.find({
  "category.name": "Celulares y Smartphones",
  "dimensions.weight_g": { $gte: 200 }
}).sort({ product_name: 1 }).explain("executionStats");
// executionStats: { totalDocsExamined: 583, nReturned: 583, executionTimeMillis: 4, stage: "FETCH" }
// Mejora: 98.2% reducción de docs examinados, 85.7% reducción de tiempo


// ============================================================
// 2. Índice parcial — reseñas positivas (score >= 4)
// NOTA: Con 76,470/99,224 docs (77%), el overhead supera al beneficio.
//       Más lento: 68ms → 100ms. Ver Lecciones Aprendidas.
// ============================================================

// ANTES — sin índice (COLLSCAN, 99,224 docs, 68ms)
db.order_reviews.find({
  review_score: { $gte: 4 }
}).explain("executionStats");
// executionStats: { totalDocsExamined: 99224, nReturned: 76470, executionTimeMillis: 68, stage: "COLLSCAN" }

db.order_reviews.createIndex(
  { review_score: 1 },
  { partialFilterExpression: { review_score: { $gte: 4 } }, name: "idx_partial_positive_reviews" }
);

// DESPUÉS — con índice parcial (76,470 docs, 100ms — selectividad insuficiente)
db.order_reviews.find({
  review_score: { $gte: 4 }
}).explain("executionStats");
// executionStats: { totalDocsExamined: 76470, nReturned: 76470, executionTimeMillis: 100, stage: "FETCH" }


// ============================================================
// 3. Índice de texto — full-text search en comentarios
// ============================================================

db.order_reviews.createIndex(
  { review_comment_title: "text", review_comment_message: "text" },
  { name: "idx_text_reviews" }
);

// DESPUÉS — con índice (TEXT_MATCH, 8,652 docs de 99,224 total, 60ms)
db.order_reviews.find({
  $text: { $search: "excelente entrega" }
}).explain("executionStats");
// executionStats: { totalDocsExamined: 8652, nReturned: 8652, executionTimeMillis: 60, stage: "TEXT_MATCH" }
// Solo el 8.7% de la colección fue examinado


// ============================================================
// 4. Aggregation Pipeline optimizado (5 stages)
// Resultado real: 4,536 productos en 114ms
// NOTA: $lookup sobre 99K docs causa MaxTimeMSExpired en free tier.
//       Workaround: $limit antes del $lookup o pipeline sin $lookup.
// ============================================================

db.products_catalog.aggregate([
  {
    $match: { "category.name": "Celulares y Smartphones" }
    // Filtra 4,536 de 32,951 docs (86.2% reducción antes de etapas siguientes)
  },
  {
    $unwind: "$specifications"
  },
  {
    $group: {
      _id: "$category.name",
      total_products:      { $sum: 1 },
      attributes_detected: { $addToSet: "$specifications.attribute" },
      avg_weight_g:        { $avg: { $toDouble: "$specifications.value" } }
    }
  },
  {
    $project: {
      category:            "$_id",
      total_products:      1,
      attributes_detected: 1,
      avg_weight_g:        { $round: ["$avg_weight_g", 1] },
      _id: 0
    }
  },
  {
    $sort: { total_products: -1 }
  }
], { allowDiskUse: true });
// Resultado: [{ category: "Celulares y Smartphones", total_products: 4536,
//              attributes_detected: ["weight_g","width_cm","height_cm","length_cm"],
//              avg_weight_g: 68.8 }]
// Tiempo: 114ms