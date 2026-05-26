// Script de inicialización y esquema de validación estructural de la colección NoSQL
db.createCollection("products_catalog", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "product_id", "product_name", "category", "specifications" ],
         properties: {
            product_id: { bsonType: "string", description: "UUID de mapeo relacional" },
            product_name: { bsonType: "string" },
            category: {
               bsonType: "object",
               required: [ "category_id", "name" ],
               properties: {
                  category_id: { bsonType: "string" },
                  name: { bsonType: "string" }
               }
            },
            specifications: {
               bsonType: "array",
               description: "Patrón de Atributo para variantes dinámicas",
               items: {
                  bsonType: "object",
                  required: [ "attribute", "value" ],
                  properties: {
                     attribute: { bsonType: "string" },
                     value: { bsonType: "string" }
                  }
               }
            },
            photos: { bsonType: "array", items: { bsonType: "string" } }
         }
      }
   }
});