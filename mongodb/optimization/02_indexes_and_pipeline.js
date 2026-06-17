// Unidad 5 - Optimización MongoDB

// 1. Índice compuesto siguiendo regla ESR
// Equality: category.name
// Sort: product_name
// Range: dimensions.weight_g

db.products_catalog.find({
  "category.name": "Celulares y Smartphones",
  "dimensions.weight_g": { $gte: 200 }
}).sort({ product_name: 1 }).explain("executionStats");

db.products_catalog.createIndex({
  "category.name": 1,
  product_name: 1,
  "dimensions.weight_g": 1
});

db.products_catalog.find({
  "category.name": "Celulares y Smartphones",
  "dimensions.weight_g": { $gte: 200 }
}).sort({ product_name: 1 }).explain("executionStats");


// 2. Índice parcial para reseñas positivas

db.order_reviews.find({
  review_score: { $gte: 4 }
}).explain("executionStats");

db.order_reviews.createIndex(
  { review_score: 1 },
  { partialFilterExpression: { review_score: { $gte: 4 } } }
);

db.order_reviews.find({
  review_score: { $gte: 4 }
}).explain("executionStats");


// 3. Índice de texto para búsqueda full-text

db.order_reviews.createIndex({
  review_comment_title: "text",
  review_comment_message: "text"
});

db.order_reviews.find({
  $text: { $search: "excelente entrega" }
}).explain("executionStats");


// 4. Aggregation Pipeline optimizado
// Incluye $match, $unwind, $lookup, $group, $project y $sort

db.products_catalog.aggregate([
  {
    $match: {
      "category.name": "Celulares y Smartphones"
    }
  },
  {
    $unwind: "$specifications"
  },
  {
    $lookup: {
      from: "order_reviews",
      localField: "product_id",
      foreignField: "product_id",
      as: "reviews"
    }
  },
  {
    $group: {
      _id: "$category.name",
      total_products: { $sum: 1 },
      attributes_detected: { $addToSet: "$specifications.attribute" },
      avg_review_score: { $avg: { $avg: "$reviews.review_score" } }
    }
  },
  {
    $project: {
      category: "$_id",
      total_products: 1,
      attributes_detected: 1,
      avg_review_score: 1,
      _id: 0
    }
  },
  {
    $sort: {
      total_products: -1
    }
  }
], { allowDiskUse: true });