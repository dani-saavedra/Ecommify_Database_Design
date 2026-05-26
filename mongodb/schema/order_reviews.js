db.createCollection("order_reviews", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "review_id", "order_id", "review_score" ],
         properties: {
            review_id: { bsonType: "string" },
            order_id: { bsonType: "string" },
            review_score: { 
               bsonType: "int", 
               minimum: 1, 
               maximum: 5, 
               description: "Calificación entera obligatoria entre 1 y 5" 
            },
            review_comment_title: { bsonType: "string" },
            review_comment_message: { bsonType: "string" },
            customer_summary: {
               bsonType: "object",
               properties: {
                  customer_id: { bsonType: "string" },
                  username: { bsonType: "string" }
               }
            }
         }
      }
   }
});