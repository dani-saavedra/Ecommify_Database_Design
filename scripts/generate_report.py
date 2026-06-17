#!/usr/bin/env python3
"""
generate_report.py  —  Unidad 5: Optimización de Bases de Datos
Genera el informe completo en PDF con gráficas reales embebidas.

pip install reportlab matplotlib numpy
Uso: python3 scripts/generate_report.py
"""

import os
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak,
)
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas as pdfcanvas

# ── Dimensiones ────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 2.54 * cm
CW = PAGE_W - 2 * MARGIN   # ≈ 453 pt / 16 cm de ancho de contenido

# ── Paleta ─────────────────────────────────────────────────────────────────────
ROJO    = HexColor('#C62828')
VERDE   = HexColor('#2E7D32')
AMBAR   = HexColor('#E65100')
AZUL_T  = HexColor('#1A237E')
AZUL_S  = HexColor('#1565C0')
GRIS_H  = HexColor('#F5F5F5')
GRIS_B  = HexColor('#BDBDBD')
GRIS_TXT= HexColor('#616161')
NEGRO   = HexColor('#212121')
AML_BG  = HexColor('#FFF8E1')
AML_BD  = HexColor('#FFB300')
GRN_BG  = HexColor('#E8F5E9')
GRN_BD  = HexColor('#66BB6A')
CODE_BG = HexColor('#F5F5F5')
CODE_BD = HexColor('#B0BEC5')

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parent.parent
OUTPUT = BASE / 'informe_unidad5_ecommify.pdf'

# ── Datos ──────────────────────────────────────────────────────────────────────
def pg_data():
    p = BASE / 'evidencias' / 'postgresql' / 'metrics_raw.json'
    if p.exists():
        return json.loads(p.read_text())['queries']
    return {
        'Q1_btree_orders_customer':    {'before': {'execution_time_ms': 9.19},   'after': {'execution_time_ms': 5.74},  'improvement_pct': 37.5},
        'Q2_btree_products_category':  {'before': {'execution_time_ms': 336.95}, 'after': {'execution_time_ms': 4.95},  'improvement_pct': 98.5},
        'Q3_gin_jsonb_specifications': {'before': {'execution_time_ms': 4.98},   'after': {'execution_time_ms': 0.19},  'improvement_pct': 96.2},
        'Q4_gin_trigram_product_name': {'before': {'execution_time_ms': 150.37}, 'after': {'execution_time_ms': 0.95},  'improvement_pct': 99.4},
        'Q5_gist_geospatial':          {'before': {'execution_time_ms': 83.13},  'after': {'execution_time_ms': 11.53}, 'improvement_pct': 86.1},
    }

# ── Gráficas ───────────────────────────────────────────────────────────────────
PLT_STYLE = {
    'figure.facecolor': 'white',
    'axes.facecolor':   'white',
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'axes.grid':        True,
    'grid.alpha':       0.22,
    'grid.linestyle':   '--',
    'font.family':      'sans-serif',
}

def _save(fig, tmp, name):
    path = os.path.join(tmp, name)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def graf_pg_tiempos(tmp):
    q = pg_data()
    keys = ['Q1_btree_orders_customer','Q2_btree_products_category',
            'Q3_gin_jsonb_specifications','Q4_gin_trigram_product_name','Q5_gist_geospatial']
    labels = ['Q1\nB-Tree\norders', 'Q2\nB-Tree\nproducts', 'Q3\nGIN\nJSONB',
              'Q4\nGIN\ntrigram', 'Q5\nGiST\ngeom']
    antes   = [q[k]['before']['execution_time_ms'] for k in keys]
    despues = [q[k]['after']['execution_time_ms']  for k in keys]

    with plt.rc_context(PLT_STYLE):
        fig, ax = plt.subplots(figsize=(9, 4.0))
        x, w = np.arange(5), 0.35
        b1 = ax.bar(x - w/2, antes,   w, color='#C62828', alpha=0.82, label='Antes del índice',   edgecolor='white')
        b2 = ax.bar(x + w/2, despues, w, color='#2E7D32', alpha=0.82, label='Después del índice', edgecolor='white')
        for bar, v in zip(b1, antes):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+3,
                    f'{v:.2f}', ha='center', va='bottom', fontsize=7.5, color='#C62828', fontweight='bold')
        for bar, v in zip(b2, despues):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+3,
                    f'{v:.2f}', ha='center', va='bottom', fontsize=7.5, color='#2E7D32', fontweight='bold')
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
        ax.set_ylabel('Tiempo de ejecución (ms)', fontsize=9)
        ax.set_title('Figura 1. Tiempo de ejecución antes y después de la indexación — PostgreSQL',
                     fontsize=9.5, fontweight='bold', pad=10)
        ax.legend(fontsize=9, framealpha=0.85)
        ax.set_ylim(0, max(antes) * 1.22)
        fig.tight_layout()
    return _save(fig, tmp, 'pg_tiempos.png')


def graf_pg_reduccion(tmp):
    q = pg_data()
    keys = ['Q1_btree_orders_customer','Q2_btree_products_category',
            'Q3_gin_jsonb_specifications','Q4_gin_trigram_product_name','Q5_gist_geospatial']
    pcts   = [q[k]['improvement_pct'] for k in keys]
    labels = ['Q1\nB-Tree', 'Q2\nB-Tree', 'Q3\nGIN\nJSONB', 'Q4\nGIN\ntrigram', 'Q5\nGiST']
    colores= ['#9E9D24', '#2E7D32', '#1565C0', '#1B5E20', '#00695C']

    with plt.rc_context(PLT_STYLE):
        fig, ax = plt.subplots(figsize=(7.5, 3.5))
        bars = ax.bar(labels, pcts, color=colores, alpha=0.85, width=0.55, edgecolor='white')
        for bar, v in zip(bars, pcts):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.7,
                    f'{v}%', ha='center', va='bottom', fontsize=9.5, fontweight='bold')
        ax.set_ylim(0, 112)
        ax.set_ylabel('Reducción (%)', fontsize=9)
        ax.set_title('Figura 2. Reducción relativa por query — PostgreSQL',
                     fontsize=9.5, fontweight='bold', pad=8)
        ax.axhline(90, color='#9E9E9E', linestyle='--', linewidth=0.9, alpha=0.6)
        ax.text(4.5, 91.5, '90%', fontsize=7.5, color='#9E9E9E')
        fig.tight_layout()
    return _save(fig, tmp, 'pg_reduccion.png')


def graf_mg_docs(tmp):
    labels  = ['Q1 — ESR compound\n(products_catalog)', 'Q2 — Índice parcial\n(order_reviews)']
    antes   = [32951, 99224]
    despues = [583,   76470]

    with plt.rc_context(PLT_STYLE):
        fig, ax = plt.subplots(figsize=(7.5, 3.8))
        x, w = np.arange(2), 0.35
        b1 = ax.bar(x - w/2, antes,   w, color='#C62828', alpha=0.82, label='Antes del índice',  edgecolor='white')
        b2 = ax.bar(x + w/2, despues, w, color='#2E7D32', alpha=0.82, label='Después del índice', edgecolor='white')
        for bar, v in zip(b1, antes):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+300,
                    f'{v:,}', ha='center', va='bottom', fontsize=8.5, color='#C62828', fontweight='bold')
        for bar, v in zip(b2, despues):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+300,
                    f'{v:,}', ha='center', va='bottom', fontsize=8.5, color='#2E7D32', fontweight='bold')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda v, _: f'{int(v/1000)}K' if v >= 1000 else str(int(v))))
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_ylabel('Documentos examinados', fontsize=9)
        ax.set_title('Figura 3. Documentos examinados antes y después — MongoDB',
                     fontsize=9.5, fontweight='bold', pad=10)
        ax.legend(fontsize=9, framealpha=0.85)
        fig.tight_layout()
    return _save(fig, tmp, 'mg_docs.png')


def graf_mg_tiempos(tmp):
    labels  = ['Q1 — ESR\nproducts_catalog', 'Q2 — Índice parcial\norder_reviews']
    antes   = [28, 68]
    despues = [4, 100]

    with plt.rc_context(PLT_STYLE):
        fig, ax = plt.subplots(figsize=(6.5, 3.6))
        x, w = np.arange(2), 0.35
        b1 = ax.bar(x - w/2, antes,   w, color='#C62828', alpha=0.82, edgecolor='white')
        b2 = ax.bar(x + w/2, despues, w, color=['#2E7D32', '#E65100'], alpha=0.82, edgecolor='white')
        for bar, v in zip(b1, antes):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
                    f'{v} ms', ha='center', va='bottom', fontsize=9, color='#C62828', fontweight='bold')
        for bar, v in zip(b2, despues):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
                    f'{v} ms', ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5)
        ax.set_ylabel('Tiempo de ejecución (ms)', fontsize=9)
        ax.set_title('Figura 4. Tiempo de ejecución antes y después — MongoDB',
                     fontsize=9.5, fontweight='bold', pad=10)
        p_rojo  = mpatches.Patch(color='#C62828', alpha=0.82, label='Antes del índice')
        p_verde = mpatches.Patch(color='#2E7D32', alpha=0.82, label='Después (mejora)')
        p_ambar = mpatches.Patch(color='#E65100', alpha=0.82, label='Después (regresión)')
        ax.legend(handles=[p_rojo, p_verde, p_ambar], fontsize=8.5, framealpha=0.85)
        ax.set_ylim(0, 130)
        fig.tight_layout()
    return _save(fig, tmp, 'mg_tiempos.png')


# ── Estilos ────────────────────────────────────────────────────────────────────
def estilos():
    E = {}
    b = dict(fontName='Helvetica', fontSize=11, leading=17, textColor=NEGRO,
             spaceAfter=7, alignment=TA_JUSTIFY)
    E['b']    = ParagraphStyle('b',    **b)
    E['bl']   = ParagraphStyle('bl',   **{**b, 'alignment': TA_LEFT})
    E['bc']   = ParagraphStyle('bc',   **{**b, 'alignment': TA_CENTER})
    E['h1']   = ParagraphStyle('h1',   fontName='Helvetica-Bold', fontSize=16, leading=22,
                                textColor=AZUL_T, spaceBefore=22, spaceAfter=8)
    E['h2']   = ParagraphStyle('h2',   fontName='Helvetica-Bold', fontSize=13, leading=18,
                                textColor=AZUL_S, spaceBefore=15, spaceAfter=6)
    E['h3']   = ParagraphStyle('h3',   fontName='Helvetica-Bold', fontSize=11.5, leading=16,
                                textColor=HexColor('#37474F'), spaceBefore=11, spaceAfter=4)
    E['bul']  = ParagraphStyle('bul',  fontName='Helvetica', fontSize=11, leading=17,
                                leftIndent=16, textColor=NEGRO, spaceAfter=3)
    E['cod']  = ParagraphStyle('cod',  fontName='Courier', fontSize=7.5, leading=11.5,
                                textColor=HexColor('#263238'), spaceAfter=0, spaceBefore=0)
    E['fig']  = ParagraphStyle('fig',  fontName='Helvetica-Oblique', fontSize=9, leading=13,
                                textColor=GRIS_TXT, alignment=TA_CENTER, spaceAfter=12, spaceBefore=3)
    E['nota'] = ParagraphStyle('nota', fontName='Helvetica-Oblique', fontSize=9.5, leading=14,
                                textColor=HexColor('#5D4037'))
    E['notg'] = ParagraphStyle('notg', fontName='Helvetica-Oblique', fontSize=9, leading=13,
                                textColor=HexColor('#1B5E20'))
    E['ref']  = ParagraphStyle('ref',  fontName='Helvetica-Oblique', fontSize=9.5, leading=14,
                                textColor=GRIS_TXT, alignment=TA_CENTER, spaceAfter=4)
    # portada
    E['pt']   = ParagraphStyle('pt',   fontName='Helvetica-Bold', fontSize=17, leading=25,
                                textColor=AZUL_T, alignment=TA_CENTER, spaceAfter=20)
    E['ps']   = ParagraphStyle('ps',   fontName='Helvetica', fontSize=12, leading=18,
                                textColor=HexColor('#424242'), alignment=TA_CENTER, spaceAfter=6)
    E['pm']   = ParagraphStyle('pm',   fontName='Helvetica', fontSize=11, leading=16,
                                textColor=GRIS_TXT, alignment=TA_CENTER, spaceAfter=4)
    E['etq']  = ParagraphStyle('etq',  fontName='Helvetica', fontSize=13, leading=18,
                                textColor=HexColor('#78909C'), alignment=TA_CENTER, spaceAfter=10)
    return E


# ── Helpers ────────────────────────────────────────────────────────────────────
def hr():
    return HRFlowable(width='100%', thickness=0.4, color=GRIS_B, spaceAfter=6, spaceBefore=2)

def sp(n=0.3):
    return Spacer(1, n*cm)

def _c(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def code_block(text):
    html = _c(text.strip()).replace('\n', '<br/>')
    p = Paragraph(html, E_GLOBAL['cod'])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), CODE_BG),
        ('BOX',           (0,0),(-1,-1), 0.5, CODE_BD),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
    ]))
    return t

def amber_box(text):
    p = Paragraph(text, E_GLOBAL['nota'])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), AML_BG),
        ('BOX',           (0,0),(-1,-1), 0.4, AML_BD),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
    ]))
    return t

def green_box(text):
    p = Paragraph(text, E_GLOBAL['notg'])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), GRN_BG),
        ('BOX',           (0,0),(-1,-1), 0.3, GRN_BD),
        ('LEFTPADDING',   (0,0),(-1,-1), 12),
        ('RIGHTPADDING',  (0,0),(-1,-1), 12),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
    ]))
    return t

def tbl(data, widths, hdr=None, first_bold=False, fsize=9.5):
    """Tabla con celdas Paragraph para word-wrap correcto."""
    _n = ParagraphStyle('_tn', fontName='Helvetica',      fontSize=fsize,
                        leading=fsize * 1.42, textColor=NEGRO, spaceAfter=0, spaceBefore=0)
    _b = ParagraphStyle('_tb', fontName='Helvetica-Bold', fontSize=fsize,
                        leading=fsize * 1.42, textColor=NEGRO, spaceAfter=0, spaceBefore=0)

    def w(c, bold):
        if not isinstance(c, str):
            return c
        safe = (c.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                 .replace('\n', '<br/>'))
        return Paragraph(safe, _b if bold else _n)

    wrapped = []
    for i, row in enumerate(data):
        hrow = (i == 0)
        wrapped.append([w(c, hrow or (first_bold and j == 0)) for j, c in enumerate(row)])

    t = Table(wrapped, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  hdr or GRIS_H),
        ('ALIGN',         (0,0),(-1,-1), 'LEFT'),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 7),
        ('RIGHTPADDING',  (0,0),(-1,-1), 7),
        ('GRID',          (0,0),(-1,-1), 0.35, GRIS_B),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [white, HexColor('#FAFAFA')]),
    ]))
    return t

def cimg(path, w, ratio):
    img = Image(path, width=w, height=w*ratio)
    wrapper = Table([[img]], colWidths=[CW])
    wrapper.setStyle(TableStyle([('ALIGN',(0,0),(0,0),'CENTER'),
                                  ('TOPPADDING',(0,0),(0,0),0),
                                  ('BOTTOMPADDING',(0,0),(0,0),0)]))
    return wrapper


# ── Canvas con numeración ──────────────────────────────────────────────────────
class NumCanvas(pdfcanvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdfcanvas.Canvas.__init__(self, *args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        for i, state in enumerate(self._pages):
            self.__dict__.update(state)
            if i > 0:   # sin número en portada
                self.setFont('Helvetica', 9)
                self.setFillColor(HexColor('#9E9E9E'))
                self.drawCentredString(PAGE_W/2, 1.4*cm, str(i))
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)


# ── Secciones ──────────────────────────────────────────────────────────────────
E_GLOBAL = {}   # se rellena en main()

def portada():
    E = E_GLOBAL
    return [
        sp(4.0),
        Paragraph('Unidad 5', E['etq']),
        Paragraph(
            'Optimización de Rendimiento en MongoDB y<br/>'
            'Arquitectura Híbrida PostgreSQL–MongoDB para Ecommify',
            E['pt']),
        sp(1.2),
        Paragraph(
            'Valentina Rodríguez Romero<br/>'
            'Andrés Santiago Santafe Silva<br/>'
            'Daniel Orlando Saavedra Fonnegra',
            E['ps']),
        sp(1.2),
        Paragraph('Facultad de Ingeniería, Universidad de La Sabana', E['pm']),
        sp(0.35),
        Paragraph('Diseño y Optimización de Bases de Datos', E['pm']),
        sp(0.35),
        Paragraph('Miguel Alfonso Varela Fonseca', E['pm']),
        sp(1.6),
        Paragraph('16 de junio de 2026', E['pm']),
        PageBreak(),
    ]


def s1_resumen():
    E = E_GLOBAL
    return [
        Paragraph('1. Resumen Ejecutivo', E['h1']), hr(),
        Paragraph(
            'El presente documento describe la implementación técnica y optimización de la arquitectura '
            'híbrida de bases de datos de Ecommify, una plataforma marketplace que integra clientes, '
            'vendedores, productos, pedidos, pagos e inventario. La solución combina PostgreSQL '
            '(Supabase) para los procesos transaccionales críticos y MongoDB Atlas para el catálogo '
            'de productos y el módulo analítico.', E['b']),
        Paragraph(
            'En PostgreSQL se implementaron estrategias avanzadas de indexación con índices B-Tree, '
            'GIN y GiST sobre un dataset real de 32.951 productos y 99.441 órdenes (Olist Brazilian '
            'E-Commerce, Kaggle), más particionamiento declarativo por rango de fecha en la tabla '
            'Orders. Las optimizaciones lograron reducciones de hasta el <b>99,4%</b> en tiempos '
            'de ejecución para búsquedas difusas y del <b>98,5%</b> para consultas por categoría.', E['b']),
        Paragraph(
            'En MongoDB Atlas se desarrollaron índices compuestos con la regla ESR, índices parciales '
            'y de texto completo sobre 32.951 documentos de catálogo y 99.224 reseñas. El índice ESR '
            'redujo los documentos examinados de 32.951 a 583 (<b>98,2% de reducción</b>). Se '
            'optimizó un Aggregation Pipeline de 5 etapas que procesó 4.536 documentos en 114 ms.', E['b']),
        Paragraph(
            'Como evidencia se presentan tablas comparativas antes/después con '
            '<font name="Courier" size="9">EXPLAIN ANALYZE</font> (PostgreSQL) y '
            '<font name="Courier" size="9">executionStats</font> (MongoDB), efficiency ratios y '
            'gráficas de rendimiento. Se propone también arquitectura de Replica Sets, estrategia '
            'de Sharding con shard key justificada y estrategias de Read/Write Concern diferenciadas '
            'por tipo de operación.', E['b']),
        sp(0.4),
    ]


def s2_postgres():
    E = E_GLOBAL
    items = [
        Paragraph('2. Implementación PostgreSQL', E['h1']), hr(),
        Paragraph(
            'PostgreSQL fue seleccionado como motor transaccional de Ecommify por sus garantías ACID, '
            'soporte de tipos avanzados (JSONB, arrays, tipos geoespaciales) y extensiones para '
            'búsquedas difusas y geolocalización.', E['b']),

        Paragraph('2.1 Scripts DDL ejecutados en Supabase', E['h2']),
        Paragraph(
            'La implementación se realizó en Supabase (PostgreSQL 15) mediante el script principal '
            '<font name="Courier" size="9">postgresql/optimization/00_setup_and_explain.sql</font>, '
            'ejecutado programáticamente vía la Management API con '
            '<font name="Courier" size="9">scripts/setup_full.py</font>.', E['b']),
        Paragraph('<b>Extensiones activadas:</b>', E['bl']), sp(0.15),
        tbl([
            ['Extensión', 'Propósito'],
            ['uuid-ossp', 'Generación de UUIDs como claves primarias'],
            ['pg_trgm',   'Búsquedas difusas con similitud de trigramas'],
            ['postgis',   'Tipos y funciones geoespaciales (ST_MakePoint, ST_DWithin)'],
        ], [3.5*cm, CW-3.5*cm]),
        sp(0.25),
        Paragraph('<b>Tablas creadas:</b>', E['bl']), sp(0.15),
        tbl([
            ['Tabla', 'Tipo', 'Descripción'],
            ['geolocations', 'Regular',     'Coordenadas con GEOMETRY(Point, 4326)'],
            ['categories',   'Regular',     'Catálogo de categorías (73 en dataset)'],
            ['customers',    'Regular',     'Clientes con referencia a geolocalización'],
            ['sellers',      'Regular',     'Vendedores con referencia a geolocalización'],
            ['products',     'Regular',     'Catálogo con campo JSONB specifications'],
            ['orders',       'Particionada','Pedidos por rango order_purchase_timestamp'],
            ['payments',     'Regular',     'Pagos con FK compuesta a orders'],
            ['order_items',  'Regular',     'Ítems con FK compuesta a orders'],
            ['inventory',    'Regular',     'Stock por producto y vendedor'],
        ], [3.3*cm, 3.0*cm, CW-6.3*cm]),
        sp(0.2),
        Paragraph('<b>Tipos avanzados utilizados:</b>', E['bl']),
        Paragraph('• <b>JSONB</b> en <font name="Courier" size="9">products.specifications</font>: atributos variables por categoría (weight_g, length_cm, height_cm, width_cm).', E['bul']),
        Paragraph('• <b>GEOMETRY(Point, 4326)</b> en <font name="Courier" size="9">geolocations.geom</font>: habilita funciones PostGIS para distancias y consultas espaciales.', E['bul']),
        Paragraph('• <b>TIMESTAMPTZ</b> en todas las columnas temporales para garantizar zona horaria explícita.', E['bul']),
        Paragraph('• <b>TEXT[]</b> en <font name="Courier" size="9">products.photos</font>: múltiples URLs de fotografías por producto.', E['bul']),
        Paragraph('• <b>TSTZRANGE</b> en <font name="Courier" size="9">products.promotion_period</font>: períodos de promoción con tipos rango nativos.', E['bul']),
        sp(0.2),

        Paragraph('2.2 Estrategia de indexación implementada', E['h2']),
        Paragraph('2.2.1 Índices B-Tree', E['h3']),
        Paragraph(
            'Los índices B-Tree son la estructura de acceso por defecto de PostgreSQL, óptimos para '
            'búsquedas de igualdad y rango sobre columnas escalares con alta cardinalidad.', E['b']),
        Paragraph(
            '<b>idx_orders_customer</b> (<font name="Courier" size="9">orders.customer_id</font>): '
            'localiza el historial de pedidos de un cliente sin recorrer secuencialmente las '
            'particiones. El planificador combina resultados con el nodo Append.', E['b']),
        Paragraph(
            '<b>idx_products_category</b> (<font name="Courier" size="9">products.category_id</font>): '
            'acelera la navegación por catálogo. Con selectividad del 4,5% (1.478 filas por categoría '
            'sobre 32.951 productos), el planificador usa Bitmap Heap Scan en lugar de Seq Scan.', E['b']),

        Paragraph('2.2.2 Índice GIN sobre JSONB', E['h3']),
        Paragraph(
            'El índice <font name="Courier" size="9">idx_products_specifications_gin</font> sobre '
            '<font name="Courier" size="9">products.specifications</font> (JSONB) usa la estructura '
            'GIN (Generalized Inverted Index) para indexar colecciones. Habilita el operador '
            '<font name="Courier" size="9">@&gt;</font> para buscar productos con atributos '
            'específicos sin deserializar cada documento durante el escaneo.', E['b']),

        Paragraph('2.2.3 Índice GIN Trigram (pg_trgm)', E['h3']),
        Paragraph(
            'El índice <font name="Courier" size="9">idx_products_name_trgm</font> sobre '
            '<font name="Courier" size="9">products.product_name</font> usa '
            '<font name="Courier" size="9">gin_trgm_ops</font>: descompone cada texto en trigramas '
            'de 3 caracteres e indexa cada uno, habilitando búsquedas difusas con el operador '
            '<font name="Courier" size="9">%</font> incluso ante errores tipográficos.', E['b']),
        sp(0.1),
        amber_box(
            '<b>Nota sobre BRIN:</b> El índice BRIN (Block Range Index) es ideal para columnas con '
            'valores monotónicamente crecientes en tablas muy grandes. En el caso de '
            '<font name="Courier" size="9">orders.order_purchase_timestamp</font>, el particionamiento '
            'declarativo ya cumple esa función al restringir físicamente el rango de datos por '
            'partición, haciendo redundante añadir un índice BRIN sobre la columna de partición.'
        ),
        sp(0.2),

        Paragraph('2.2.4 Índice GiST para consultas espaciales', E['h3']),
        Paragraph(
            'El índice <font name="Courier" size="9">idx_geolocations_spatial</font> sobre '
            '<font name="Courier" size="9">geolocations.geom</font> usa GiST (Generalized Search '
            'Tree) para tipos complejos como geometrías y rangos. Habilita '
            '<font name="Courier" size="9">ST_DWithin</font> y '
            '<font name="Courier" size="9">ST_DistanceSphere</font> sin evaluar la función sobre '
            'cada fila de la tabla.', E['b']),

        Paragraph('2.3 Estrategia de particionamiento', E['h2']),
        Paragraph(
            'La tabla <font name="Courier" size="9">orders</font> usa '
            '<b>Range Partitioning</b> sobre '
            '<font name="Courier" size="9">order_purchase_timestamp</font>, con cuatro particiones '
            'que cubren el dataset Olist (septiembre 2016–agosto 2018):', E['b']),
        sp(0.1),
        tbl([
            ['Partición', 'Rango cubierto'],
            ['orders_2016', '2016-01-01 → 2017-01-01'],
            ['orders_2017', '2017-01-01 → 2018-01-01'],
            ['orders_2018', '2018-01-01 → 2019-01-01'],
            ['orders_otros','2019-01-01 → 2030-01-01 (desbordamiento)'],
        ], [4.5*cm, CW-4.5*cm]),
        sp(0.15),
        Paragraph('• <b>Partition pruning automático:</b> consultas con filtro por fecha solo acceden a las particiones relevantes.', E['bul']),
        Paragraph('• <b>Mejor aprovechamiento de caché:</b> cada partición es más pequeña y cabe completamente en memoria.', E['bul']),
        Paragraph('• <b>Mantenimiento independiente:</b> se pueden archivar particiones antiguas sin afectar las activas.', E['bul']),
        Paragraph(
            'PostgreSQL exige que el campo de partición forme parte de la clave primaria. Por ello, '
            'la PK de <font name="Courier" size="9">orders</font> es compuesta: '
            '<font name="Courier" size="9">(order_id, order_purchase_timestamp)</font>, restricción '
            'que se propagó en cascada hacia '
            '<font name="Courier" size="9">payments</font> y '
            '<font name="Courier" size="9">order_items</font> (ver lección 5.3).', E['b']),

        Paragraph('2.4 Consultas críticas optimizadas', E['h2']),
        sp(0.1),
        tbl([
            ['#', 'Consulta', 'Índice aplicado'],
            ['Q1','Historial de pedidos por cliente',    'B-Tree idx_orders_customer'],
            ['Q2','Búsqueda de productos por categoría', 'B-Tree idx_products_category'],
            ['Q3','Búsqueda sobre atributos JSONB',      'GIN idx_products_specifications_gin'],
            ['Q4','Búsqueda difusa de productos (pg_trgm)','GIN idx_products_name_trgm'],
            ['Q5','Consultas geoespaciales (PostGIS)',   'GiST idx_geolocations_spatial'],
        ], [1.2*cm, 6.0*cm, CW-7.2*cm]),
        sp(0.2),

        Paragraph('2.5 Monitoreo de rendimiento PostgreSQL', E['h2']),
        Paragraph(
            'El análisis se realizó mediante '
            '<font name="Courier" size="9">pg_stat_statements</font> disponible en Supabase y '
            'comparación directa de planes de ejecución capturados con '
            '<font name="Courier" size="9">EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)</font>.', E['b']),
        sp(0.1),
        tbl([
            ['Métrica', 'Valor'],
            ['Queries con Seq Scan eliminadas tras indexación', '4 de 5 (80%)'],
            ['Reducción promedio de tiempo de ejecución',       '83,5%'],
            ['Mayor reducción absoluta',  'Q2: 332 ms ahorrados (336,95 ms → 4,95 ms)'],
            ['Mayor reducción relativa',  'Q4: 99,4% (150,37 ms → 0,95 ms)'],
        ], [7.5*cm, CW-7.5*cm]),
        sp(0.15),
        Paragraph(
            'El planificador usó Bitmap Heap Scan en Q2, Q3 y Q4, confirmando que el costo del '
            'recorrido de índice es menor que el Seq Scan. Q5 mantuvo Seq Scan sobre '
            '<font name="Courier" size="9">geolocations</font> (20 filas) porque el acceso '
            'secuencial a tablas muy pequeñas resulta más eficiente; el índice GiST sí redujo '
            'el tiempo de planificación espacial de 191,62 ms a 30,26 ms.', E['b']),
    ]
    return items


def s3_mongo():
    E = E_GLOBAL
    return [
        Paragraph('3. Implementación MongoDB', E['h1']), hr(),
        Paragraph(
            'MongoDB fue seleccionado como componente NoSQL de la arquitectura por su capacidad para '
            'manejar información semiestructurada, atributos dinámicos y grandes volúmenes de '
            'consultas orientadas al catálogo de productos.', E['b']),

        Paragraph('3.1 Colecciones y esquemas documentales', E['h2']),
        Paragraph('3.1.1 Colección products_catalog', E['h3']),
        Paragraph(
            'Almacena el catálogo flexible de productos con validación estructural mediante JSON '
            'Schema en Atlas. Se aplicó la decisión de <b>embedding</b> para las especificaciones '
            'técnicas, siempre consultadas junto con el documento padre.', E['b']),
        Paragraph(
            '<b>Patrón Attribute Pattern:</b> las especificaciones se almacenan como array de pares '
            '<font name="Courier" size="9">{attribute, value}</font>, permitiendo indexar cualquier '
            'atributo sin conocer el esquema de antemano:', E['b']),
        code_block('''{
  "product_id": "uuid",
  "product_name": "Smartphone Pro X5A23F",
  "category": { "name": "Celulares y Smartphones" },
  "specifications": [
    { "attribute": "weight_g",  "value": "185" },
    { "attribute": "height_cm", "value": "15"  }
  ],
  "dimensions": { "weight_g": 185, "height_cm": 15, "length_cm": 7, "width_cm": 0.8 }
}'''),
        sp(0.1),

        Paragraph('3.1.2 Colección order_reviews', E['h3']),
        Paragraph(
            'Almacena reseñas de clientes con decisión de <b>referenciado</b> hacia los pedidos '
            '(se guarda <font name="Courier" size="9">order_id</font> como referencia a PostgreSQL). '
            '<b>Patrón Extended Reference:</b> se embebe '
            '<font name="Courier" size="9">customer_summary</font> para evitar lookups frecuentes '
            'en consultas analíticas de satisfacción.', E['b']),

        Paragraph('3.1.3 Colección inventory_movements (Patrón Bucket)', E['h3']),
        Paragraph(
            'Para el seguimiento de movimientos de inventario se aplica el <b>Patrón Bucket</b>: '
            'en lugar de un documento por movimiento (venta, reabastecimiento, devolución), todos '
            'los eventos de un producto dentro de una franja horaria se agrupan en un único '
            'documento. Esto reduce el número de documentos en colecciones de alta escritura, '
            'mejora la eficiencia de consultas de tendencias y disminuye el overhead de índices.', E['b']),
        code_block('''{
  "product_id": "uuid-prod-8f2a",
  "date":       "2026-06-16",
  "hour":       14,
  "movements": [
    { "ts": "2026-06-16T14:03Z", "operation": "sale",    "qty_change": -2  },
    { "ts": "2026-06-16T14:17Z", "operation": "restock", "qty_change":  50 },
    { "ts": "2026-06-16T14:45Z", "operation": "return",  "qty_change":   1 }
  ],
  "total_delta":  49,
  "closing_qty": 156
}'''),
        sp(0.1),
        tbl([
            ['Dimensión',                'Sin Bucket Pattern',        'Con Bucket Pattern'],
            ['Documentos/día (1.000 SKU, 10 mov/h)', '240.000 docs', '24.000 docs (−90%)'],
            ['Stock actual',             'Suma de todos los docs',    'Campo closing_qty precalculado'],
            ['Análisis granular',        'Consulta directa',          '$unwind sobre movements array'],
            ['Índices necesarios',       'Índice sobre cada mov.',    'Índice sobre (product_id, date, hour)'],
        ], [CW*0.36, CW*0.32, CW*0.32], hdr=AZUL_T),
        sp(0.15),

        Paragraph('3.2 Estrategia de indexación implementada', E['h2']),
        Paragraph('3.2.1 Índice compuesto ESR (Equality, Sort, Range)', E['h3']),
        Paragraph(
            '<b>Índice:</b> <font name="Courier" size="9">{ "category.name": 1, "product_name": 1, '
            '"dimensions.weight_g": 1 }</font><br/>'
            'La regla ESR coloca primero el campo de igualdad (E), luego el de ordenamiento (S) y '
            'finalmente el de rango (R). Esta configuración permite a MongoDB satisfacer '
            'simultáneamente filtro, sort y restricción de peso con un único recorrido de índice, '
            'eliminando la operación de SORT en memoria.', E['b']),

        Paragraph('3.2.2 Índice parcial para reseñas positivas', E['h3']),
        Paragraph(
            '<b>Índice:</b> <font name="Courier" size="9">{ "review_score": 1 }</font> con '
            '<font name="Courier" size="9">partialFilterExpression: { review_score: { $gte: 4 } }</font>. '
            'Indexa solo reseñas con calificación ≥ 4. El resultado mostró overhead negativo '
            'porque el subconjunto indexado representaba el 77% de la colección (lección 5.1).', E['b']),

        Paragraph('3.2.3 Índice de texto completo', E['h3']),
        Paragraph(
            '<b>Índice:</b> <font name="Courier" size="9">{ "review_comment_title": "text", '
            '"review_comment_message": "text" }</font>. Habilita búsquedas semánticas con '
            '<font name="Courier" size="9">$text</font> sin un Seq Scan sobre los 99.224 documentos.', E['b']),

        Paragraph('3.3 Aggregation Pipeline optimizado', E['h2']),
        Paragraph(
            'El pipeline cumple los requisitos mínimos de 5 stages e incluye '
            '<font name="Courier" size="9">$unwind</font>. El '
            '<font name="Courier" size="9">$match</font> en Stage 1 reduce de 32.951 a 4.536 '
            'documentos antes de las etapas costosas (reducción del 86,2%):', E['b']),
        code_block("""db.products_catalog.aggregate([
  { $match:  { "category.name": "Celulares y Smartphones" } },  // Stage 1
  { $unwind: "$specifications" },                               // Stage 2
  { $group: {                                                   // Stage 3
      _id:                "$category.name",
      total_products:     { $sum: 1 },
      attributes_detected:{ $addToSet: "$specifications.attribute" },
      avg_weight_g:       { $avg: { $toDouble: "$specifications.value" } }
  }},
  { $project: {                                                 // Stage 4
      category: "$_id", total_products: 1,
      attributes_detected: 1,
      avg_weight_g: { $round: ["$avg_weight_g", 1] }, _id: 0
  }},
  { $sort: { total_products: -1 } }                            // Stage 5
], { allowDiskUse: true, maxTimeMS: 30000 })"""),
        Paragraph(
            '<b>Resultado:</b> category: "Celulares y Smartphones", total_products: 4.536, '
            'attributes_detected: ["weight_g","width_cm","height_cm","length_cm"], '
            'avg_weight_g: 68,8 — Tiempo: <b>114 ms</b>.', E['b']),
        sp(0.2),

        Paragraph('3.4 Diseño teórico de Replica Sets', E['h2']),
        Paragraph(
            'La arquitectura de alta disponibilidad propuesta usa un Replica Set de tres nodos:', E['b']),
        sp(0.1),
        tbl([
            ['Nodo',     'Rol',                   'Configuración'],
            ['Primary',  'Escritura',              'priority: 1, votes: 1'],
            ['Secondary','Lectura analítica',      'priority: 0.5, votes: 1, hidden: false'],
            ['Arbiter',  'Elección en failover',   'priority: 0, votes: 1, arbiterOnly: true'],
        ], [2.8*cm, 4.0*cm, CW-6.8*cm]),
        sp(0.2),
        Paragraph('<b>Read/Write Concern diferenciado por operación:</b>', E['bl']),
        sp(0.1),
        tbl([
            ['Operación',                           'Read Preference',    'Read Concern', 'Write Concern'],
            ['Consultas catálogo (alta frecuencia)','secondary Preferred','local',         '—'],
            ['Lectura de reseñas (análisis)',       'secondary',          'majority',      '—'],
            ['Inserción de nuevas reseñas',         'Primary',            '—',             '{ w: "majority", j: true }'],
            ['Actualización inventario crítico',    'Primary',            '—',             '{ w: "majority", wtimeout: 5000 }'],
            ['Batch no crítico',                    'Primary',            '—',             '{ w: 1 }'],
        ], [4.3*cm, 4.0*cm, 2.5*cm, CW-10.8*cm]),
        sp(0.2),

        Paragraph('3.5 Diseño teórico de Sharding', E['h2']),
        Paragraph(
            '<b>Shard key:</b> <font name="Courier" size="9">{ category: 1, seller_id: "hashed" }</font>. '
            'El campo <font name="Courier" size="9">category</font> permite colocation de productos '
            'de la misma categoría en el mismo shard, optimizando consultas de catálogo. El '
            'componente hashed sobre <font name="Courier" size="9">seller_id</font> distribuye '
            'uniformemente vendedores con alto volumen (hotspot prevention).', E['b']),
        sp(0.1),
        tbl([
            ['Shard',  'Categorías (aprox.)', 'Documentos (aprox.)'],
            ['Shard 1','cama_mesa_banho, beleza_saude, esporte_lazer... (25)', '~10.900'],
            ['Shard 2','informatica_acessorios, telefonia, eletrônicos... (25)', '~11.200'],
            ['Shard 3','moveis_decoracao, brinquedos, automotivo... (23)', '~10.851'],
        ], [2.5*cm, 9.0*cm, CW-11.5*cm]),
        sp(0.2),

        Paragraph('3.6 Monitoreo de rendimiento MongoDB', E['h2']),
        Paragraph(
            'El monitoreo se realizó con <b>MongoDB Atlas Performance Advisor</b> y la inspección '
            'del log de consultas lentas. Recomendaciones detectadas: creación del índice ESR '
            '(implementada), índice de texto en order_reviews (implementada) y alerta de '
            '<font name="Courier" size="9">$lookup</font> sin índice de soporte (workaround: '
            'pipeline sin $lookup).', E['b']),
        sp(0.1),
        tbl([
            ['Métrica',                                          'Antes',       'Después'],
            ['Avg query execution time (Q1 ESR)',                '28 ms',       '4 ms'],
            ['Index hit ratio (products_catalog)',               '0% (COLLSCAN)','100% (IXSCAN)'],
            ['Documentos examinados por query (Q1)',             '32.951',      '583'],
            ['Efficiency ratio Q1 (docs_returned/docs_examined)','0,018',       '1,0'],
            ['Pipeline execution time',                          '—',           '114 ms'],
        ], [7.0*cm, 3.5*cm, CW-10.5*cm]),
    ]


def s4_evidencias(charts):
    E = E_GLOBAL

    # Tabla PG con estilo especial
    data_pg = [
        ['#', 'Consulta / Índice aplicado', 'Scan ANTES', 'ms ANTES', 'Scan DESPUÉS', 'ms DESPUÉS', 'Reducción'],
        ['Q1','B-Tree idx_orders_customer',          'Append',   '9,19',  'Append',          '5,74', '37,5%'],
        ['Q2','B-Tree idx_products_category',        'Seq Scan', '336,95','Bitmap Heap Scan', '4,95', '98,5%'],
        ['Q3','GIN idx_products_\nspecifications_gin', 'Seq Scan', '4,98',  'Bitmap Heap Scan', '0,19', '96,2%'],
        ['Q4','GIN trigram\nidx_products_name_trgm',  'Seq Scan', '150,37','Bitmap Heap Scan', '0,95', '99,4%'],
        ['Q5','GiST idx_geolocations_spatial',       'Seq Scan', '83,13', 'Seq Scan*',       '11,53', '86,1%'],
    ]
    t_pg = Table(data_pg, colWidths=[0.8*cm,4.9*cm,2.8*cm,1.5*cm,2.8*cm,1.5*cm,1.7*cm], repeatRows=1)
    t_pg.setStyle(TableStyle([
        ('FONTNAME',       (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0),(-1,-1), 8.5),
        ('LEADING',        (0,0),(-1,-1), 13),
        ('BACKGROUND',     (0,0),(-1,0),  HexColor('#E8EAF6')),
        ('TEXTCOLOR',      (0,0),(-1,0),  AZUL_T),
        ('ALIGN',          (0,0),(0,-1),  'CENTER'),
        ('ALIGN',          (3,0),(3,-1),  'RIGHT'),
        ('ALIGN',          (5,0),(5,-1),  'RIGHT'),
        ('ALIGN',          (6,0),(6,-1),  'RIGHT'),
        ('VALIGN',         (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',     (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 5),
        ('LEFTPADDING',    (0,0),(-1,-1), 5),
        ('RIGHTPADDING',   (0,0),(-1,-1), 5),
        ('GRID',           (0,0),(-1,-1), 0.35, GRIS_B),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [white, HexColor('#FAFAFA')]),
        ('TEXTCOLOR',      (6,2),(6,5),   VERDE),
        ('FONTNAME',       (6,2),(6,5),   'Helvetica-Bold'),
    ]))

    # Tabla MongoDB
    data_mg = [
        ['#','Consulta / Índice','Stage ANTES','Docs ANTES','ms ANTES','Docs DESPUÉS','ms DESPUÉS','Eff. ratio','Red. docs'],
        ['Q1','ESR compound\nproducts_catalog', 'COLLSCAN','32.951','28',  '583',    '4',   '1,0',  '98,2%'],
        ['Q2','Parcial score≥4\norder_reviews',  'COLLSCAN','99.224','68',  '76.470','100',  '1,0',  '22,9%'],
        ['Q3','Full-text\norder_reviews',         '—',      '—',     '—',   '8.652',  '60',  '1,0',  '91,3%*'],
    ]
    t_mg = Table(data_mg, colWidths=[0.7*cm,3.9*cm,2.2*cm,1.6*cm,1.2*cm,1.8*cm,1.5*cm,1.4*cm,1.7*cm], repeatRows=1)
    t_mg.setStyle(TableStyle([
        ('FONTNAME',       (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0),(-1,-1), 8),
        ('LEADING',        (0,0),(-1,-1), 12),
        ('BACKGROUND',     (0,0),(-1,0),  HexColor('#E8F5E9')),
        ('TEXTCOLOR',      (0,0),(-1,0),  HexColor('#1B5E20')),
        ('ALIGN',          (0,0),(0,-1),  'CENTER'),
        ('ALIGN',          (3,0),(-1,-1), 'RIGHT'),
        ('VALIGN',         (0,0),(-1,-1), 'MIDDLE'),
        ('TOPPADDING',     (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 5),
        ('LEFTPADDING',    (0,0),(-1,-1), 4),
        ('RIGHTPADDING',   (0,0),(-1,-1), 4),
        ('GRID',           (0,0),(-1,-1), 0.35, GRIS_B),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [white, HexColor('#FAFAFA')]),
        ('TEXTCOLOR',      (6,2),(6,2),   ROJO),
        ('FONTNAME',       (6,2),(6,2),   'Helvetica-Bold'),
        ('TEXTCOLOR',      (8,1),(8,1),   VERDE),
        ('FONTNAME',       (8,1),(8,1),   'Helvetica-Bold'),
    ]))

    items = [
        Paragraph('4. Evidencias cuantitativas de mejora', E['h1']), hr(),

        Paragraph('4.1 Resultados PostgreSQL', E['h2']),
        Paragraph(
            'Las pruebas se realizaron sobre el dataset real Olist cargado en Supabase: '
            '<b>32.951 productos, 99.441 órdenes, 103.886 pagos, 73 categorías y 99.441 clientes</b>, '
            'con la tabla Orders particionada por rango de fecha. Métricas capturadas con '
            '<font name="Courier" size="9">EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)</font> vía '
            'Management API de Supabase (PostgreSQL 15).', E['b']),
        sp(0.1),
        t_pg,
        sp(0.15),
        amber_box(
            '* Q5 mantiene Seq Scan en geolocations (20 filas) porque el planificador considera '
            'más eficiente el acceso secuencial a tablas muy pequeñas. La mejora proviene de la '
            'reducción del tiempo de planificación espacial (191,62 ms → 30,26 ms) y del tiempo '
            'de ejecución total.'
        ),
        sp(0.3),
    ]

    if charts.get('pg_tiempos'):
        items.append(cimg(charts['pg_tiempos'], CW, 0.445))
        items.append(sp(0.4))
    if charts.get('pg_reduccion'):
        items.append(cimg(charts['pg_reduccion'], CW*0.8, 0.467))
        items.append(sp(0.5))

    items += [
        Paragraph('4.2 Resultados MongoDB', E['h2']),
        Paragraph(
            'Pruebas sobre datos reales en MongoDB Atlas: <b>32.951 documentos</b> en '
            '<font name="Courier" size="9">products_catalog</font> y <b>99.224 documentos</b> en '
            '<font name="Courier" size="9">order_reviews</font>. Métricas capturadas con '
            '<font name="Courier" size="9">.explain("executionStats")</font>.', E['b']),
        sp(0.1),
        t_mg,
        sp(0.15),
        green_box(
            '* Q3: reducción calculada respecto al total de la colección (99.224 docs), ya que '
            'la búsqueda full-text no es ejecutable sin el índice de texto. — '
            '<b>Efficiency ratio</b> = docs retornados / docs examinados; valor 1,0 indica 0% '
            'de desperdicio. En Q1 sin índice el ratio era 583/32.951 = <b>0,018</b> '
            '(examinó 56 documentos por cada uno retornado).'
        ),
        sp(0.35),
    ]

    if charts.get('mg_docs'):
        items.append(cimg(charts['mg_docs'], CW*0.8, 0.507))
        items.append(sp(0.4))
    if charts.get('mg_tiempos'):
        items.append(cimg(charts['mg_tiempos'], CW*0.72, 0.554))
        items.append(sp(0.4))

    items += [
        Paragraph('<b>Aggregation Pipeline — resultados cuantitativos:</b>', E['bl']),
        sp(0.1),
        tbl([
            ['Métrica', 'Valor'],
            ['Etapas del pipeline',                  '5 ($match, $unwind, $group, $project, $sort)'],
            ['Documentos en $match (entrada)',        '32.951'],
            ['Documentos después de $match',         '4.536 (reducción 86,2%)'],
            ['Atributos detectados',                 'weight_g, length_cm, height_cm, width_cm'],
            ['avg_weight_g calculado',               '68,8 g'],
            ['Tiempo de ejecución total',            '114 ms'],
        ], [6.5*cm, CW-6.5*cm]),
        sp(0.25),

        Paragraph('4.3 Sincronización entre sistemas', E['h2']),
        Paragraph(
            'Ecommify opera una arquitectura políglota donde PostgreSQL gestiona las transacciones y '
            'MongoDB gestiona el catálogo y la analítica. Los flujos de sincronización entre ambos '
            'sistemas se rigen por las siguientes estrategias:', E['b']),
        sp(0.1),
        tbl([
            ['Evento',                     'Fuente',                         'Destino',                          'Tipo'],
            ['Alta de nuevo producto',     'PostgreSQL products (INSERT)',    'MongoDB products_catalog (INSERT)', 'Síncrona — job'],
            ['Modificación de precio',     'PostgreSQL products (UPDATE)',    'MongoDB products_catalog (UPDATE)', 'Eventual (5 min)'],
            ['Nueva reseña confirmada',    'PostgreSQL orders (DELIVERED)',   'MongoDB order_reviews (INSERT)',    'Eventual — queue'],
            ['Actualización specs',        'MongoDB products_catalog',        'PostgreSQL specifications (JSONB)', 'Eventual (5 min)'],
        ], [3.5*cm, 4.3*cm, 4.3*cm, CW-12.1*cm]),
        sp(0.15),
        Paragraph(
            'La <b>consistencia fuerte</b> se aplica a operaciones transaccionales (pedidos, pagos) '
            'exclusivamente en PostgreSQL bajo ACID. La <b>consistencia eventual</b> rige la '
            'sincronización del catálogo, aceptando un lag máximo de 5 minutos, tolerable para '
            'un catálogo de consulta. El <font name="Courier" size="9">product_id</font> (UUID '
            'generado en PostgreSQL) se replica en MongoDB como campo '
            '<font name="Courier" size="9">product_id</font> en '
            '<font name="Courier" size="9">products_catalog</font>, permitiendo lookups cruzados '
            'sin uniones costosas.', E['b']),
    ]
    return items


def s5_lecciones():
    E = E_GLOBAL
    return [
        Paragraph('5. Lecciones aprendidas', E['h1']), hr(),
        Paragraph(
            'La implementación de la arquitectura híbrida durante la fase de optimización generó '
            'cinco aprendizajes técnicos con impacto directo en las decisiones de diseño.', E['b']),

        Paragraph('5.1 Los índices parciales requieren alta selectividad para ser efectivos', E['h2']),
        Paragraph(
            'El índice parcial sobre '
            '<font name="Courier" size="9">order_reviews</font> para reseñas con score ≥ 4 produjo '
            'un resultado inesperado: la consulta fue un <b>47% más lenta</b> con el índice '
            '(68 ms sin índice vs. 100 ms con índice). La causa fue que el subconjunto indexado '
            'representaba el <b>77% de la colección</b> (76.470 de 99.224 documentos). En ese '
            'escenario el overhead de leer el índice más recuperar los documentos en disco supera '
            'al costo del recorrido secuencial. Los índices parciales son efectivos únicamente '
            'cuando el subconjunto filtrado representa <b>menos del 30% de la colección</b>.', E['b']),

        Paragraph('5.2 El $lookup sin filtro previo supera el límite de tiempo del free tier', E['h2']),
        Paragraph(
            'La primera versión del pipeline aplicaba '
            '<font name="Courier" size="9">$lookup</font> entre '
            '<font name="Courier" size="9">products_catalog</font> (32.951 docs) y '
            '<font name="Courier" size="9">order_reviews</font> (99.224 docs) sin '
            '<font name="Courier" size="9">$match</font> previo, generando repetidamente '
            '<font name="Courier" size="9">MaxTimeMSExpired</font> en Atlas free tier. La solución '
            'fue colocar <font name="Courier" size="9">$match</font> como Stage 1, reduciendo '
            'la entrada de 32.951 a 4.536 documentos antes del join. El pipeline final eliminó '
            'el <font name="Courier" size="9">$lookup</font> para consultas analíticas puras.', E['b']),

        Paragraph('5.3 El particionamiento PostgreSQL impone restricciones en cascada sobre claves foráneas', E['h2']),
        Paragraph(
            'El Range Partitioning sobre '
            '<font name="Courier" size="9">orders</font> requirió incluir '
            '<font name="Courier" size="9">order_purchase_timestamp</font> en la PK compuesta. '
            'Esta restricción se propagó en cascada: '
            '<font name="Courier" size="9">payments</font> y '
            '<font name="Courier" size="9">order_items</font> deben replicar el campo de '
            'partición en sus FKs, aumentando el almacenamiento y la complejidad de los JOINs.', E['b']),

        Paragraph('5.4 La conexión directa a Supabase requiere IPv6 o add-on IPv4', E['h2']),
        Paragraph(
            'Los intentos de conexión directa con '
            '<font name="Courier" size="9">psycopg2</font> al host '
            '<font name="Courier" size="9">db.litdnoxzcbdecgrjjewt.supabase.co</font> fallaron '
            'porque Supabase usa <b>IPv6 por defecto</b> en el tier gratuito. El workaround '
            'implementado fue usar la Management API de Supabase vía HTTPS (puerto 443). '
            'El script <font name="Courier" size="9">scripts/setup_full.py</font> implementa '
            'DDL vía Management API y carga de datos vía REST API (supabase-py), eliminando '
            'la dependencia de psycopg2.', E['b']),

        Paragraph('5.5 La regla ESR es determinante para maximizar índices compuestos en MongoDB', E['h2']),
        Paragraph(
            'La aplicación correcta de ESR en el índice de '
            '<font name="Courier" size="9">products_catalog</font> fue el factor decisivo para '
            'lograr el 98,2% de reducción en documentos examinados. El orden '
            '<font name="Courier" size="9">category.name</font> (Equality) → '
            '<font name="Courier" size="9">product_name</font> (Sort) → '
            '<font name="Courier" size="9">dimensions.weight_g</font> (Range) permite satisfacer '
            'simultáneamente filtro, ordenamiento y restricción de rango con un solo recorrido '
            'de índice, eliminando la operación de SORT en memoria. Un índice con orden incorrecto '
            '(por ejemplo, Range primero) no puede usarse para la etapa de Sort, forzando al '
            'planificador a materializar y ordenar el resultado en memoria.', E['b']),

        sp(0.6),
        HRFlowable(width='100%', thickness=0.4, color=GRIS_B, spaceAfter=8),
        Paragraph(
            'Repositorio: github.com/dani-saavedra/Ecommify_Database_Design  ·  '
            'Evidencias: evidencias/postgresql/ y evidencias/mongodb/',
            E['ref']),
    ]


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    global E_GLOBAL
    E_GLOBAL = estilos()

    with tempfile.TemporaryDirectory() as tmp:
        print('Generando gráficas...')
        charts = {
            'pg_tiempos':   graf_pg_tiempos(tmp),
            'pg_reduccion': graf_pg_reduccion(tmp),
            'mg_docs':      graf_mg_docs(tmp),
            'mg_tiempos':   graf_mg_tiempos(tmp),
        }

        print('Construyendo PDF...')
        doc = SimpleDocTemplate(
            str(OUTPUT),
            pagesize=A4,
            leftMargin=MARGIN, rightMargin=MARGIN,
            topMargin=2.2*cm,  bottomMargin=2.3*cm,
            title='Unidad 5 — Optimización de Bases de Datos Híbridas — Ecommify',
            author='Valentina Rodríguez · Andrés Santafe · Daniel Saavedra',
            subject='Diseño y Optimización de Bases de Datos — Universidad de La Sabana',
        )

        story = []
        story += portada()
        story += s1_resumen()
        story += s2_postgres()
        story += [PageBreak()]
        story += s3_mongo()
        story += [PageBreak()]
        story += s4_evidencias(charts)
        story += [PageBreak()]
        story += s5_lecciones()

        doc.build(story, canvasmaker=NumCanvas)

    size_kb = OUTPUT.stat().st_size / 1024
    print(f'\n✅  PDF listo: {OUTPUT}')
    print(f'    Tamaño:   {size_kb:.0f} KB')


if __name__ == '__main__':
    main()
