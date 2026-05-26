# Ecommify Database Architecture

##  Descripción del Proyecto

Ecommify es una plataforma de comercio electrónico diseñada bajo una arquitectura híbrida de bases de datos, utilizando:

- PostgreSQL como motor transaccional principal.
- MongoDB para almacenamiento documental y consultas flexibles.

El proyecto toma como referencia el dataset público:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

La solución busca responder a necesidades reales de:
- procesamiento transaccional
- catálogo flexible
- alta disponibilidad
- búsquedas avanzadas
- analítica escalable
- sincronización entre motores SQL y NoSQL

# Objetivos

## Objetivo General

Diseñar una arquitectura de base de datos híbrida para una plataforma e-commerce, integrando PostgreSQL y MongoDB para soportar operaciones transaccionales y consultas flexibles de gran volumen.

## Objetivos Específicos

- Diseñar el modelo conceptual y lógico del sistema.
- Implementar un esquema relacional normalizado en PostgreSQL.
- Modelar colecciones documentales en MongoDB.
- Justificar decisiones arquitectónicas bajo criterios técnicos.
- Aplicar extensiones avanzadas como PostGIS y pg_trgm.
- Definir una estrategia de sincronización mediante CDC.

# Integrantes

- Valentina Rodriguez Romero 
- Andres Santiago Santafe 
- Daniel Saavedra Fonnegra
---
