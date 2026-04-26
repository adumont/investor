# Investor

Investor es una aplicación web hecha con Streamlit para explorar productos de inversión de MyInvestor de forma rápida y visual. Su objetivo es ayudarte a filtrar cientos de productos, compararlos y revisar sus detalles clave en una sola pantalla.

## Acceso

La aplicación está publicada en:

https://investor26.streamlit.app/

No necesitas instalación para usarla desde navegador.

## Para qué sirve

Esta herramienta está pensada para usuarios que quieren analizar productos antes de invertir, sin tener que abrir manualmente fichas y documentos de cada fondo.

Con Investor puedes:

- buscar productos por nombre o por ISIN,
- aplicar filtros combinados para acotar resultados,
- comparar riesgo, TER y rentabilidades,
- inspeccionar sectores, regiones y comisiones,
- abrir documentación oficial desde la propia ficha del producto.

## Funcionalidades principales

### 1. Búsqueda rápida

- Búsqueda por texto sobre el nombre del producto.
- Búsqueda directa por código ISIN.
- Puedes introducir **varios términos separados por coma** para buscar múltiples productos a la vez (por ejemplo: `IE000ZYRH0Q7, IE00BYX5NX33`). Cada término se trata como un OR independiente sobre nombre e ISIN.

### 2. Filtros rápidos temáticos

Incluye accesos rápidos para estrategias comunes:

- World
- S&P 500
- Emergentes
- Japón
- Small Caps
- Oro y Metales
- Cualquiera (sin filtro rápido)

### 3. Filtros principales

- Divisa
- Tipo de producto
- Gestora

La vista inicial usa por defecto:

- divisa EUR
- tipo de producto FONDOS_INDEXADOS

### 4. Filtros avanzados

En el bloque "Más filtros & Selección de columnas" puedes filtrar por:

- categoría,
- categoría MyInvestor,
- categoría Morningstar,
- tipo de activo,
- zona geográfica,
- sector.

El filtro por sector permite definir un umbral mínimo en porcentaje (por ejemplo, mostrar solo productos con al menos 20% en un sector concreto).

### 5. Personalización de columnas

Puedes mostrar u ocultar columnas para adaptar la tabla a tu análisis:

- rentabilidad de los últimos años (incluido YTD),
- rentabilidad anualizada a 1, 3 y 5 años,
- categorías,
- días de desplazamiento de suscripción y reembolso,
- columnas de sectores seleccionados.

Además, la tabla incluye `TE_1Y`, que corresponde al tracking error a 1 año (`trackingErrorYearUno`).

### 6. Tabla de resultados y ordenación

- Los resultados muestran solo productos con estado OPEN.
- La ordenación principal es por riesgo y después por TER.
- La selección es por fila única para abrir el detalle del producto.
- Si queda un único resultado, el detalle se abre automáticamente.

### 7. Vista de detalle del producto

Al seleccionar un producto, se muestra una ficha completa con:

- nombre, ISIN, tipo de activo e indicador de riesgo,
- descripción (si está disponible),
- enlaces a documentos (ficha técnica, KIID, informe semestral, memoria, Morningstar),
- gráficos de rentabilidad histórica,
- tabla de datos generales,
- tabla de comisiones con TER destacado,
- desglose por sectores,
- desglose por regiones,
- composiciones/posiciones del fondo cuando existan,
- JSON completo del producto para inspección avanzada.

## Guía de uso paso a paso

1. Abre la aplicación en el enlace público.
2. Escribe un nombre o ISIN en el buscador.
3. Aplica filtros rápidos o avanzados según tu objetivo.
4. Activa las columnas que quieras comparar.
5. Haz clic en un producto de la tabla.
6. Revisa su detalle, documentación y métricas.

## Casos de uso frecuentes

- Encontrar opciones con menor riesgo o menor TER.
- Comparar productos similares dentro de una misma categoría.
- Filtrar por geografía o por tipo de activo.
- Revisar concentración sectorial antes de tomar decisión.
- Comprobar tracking error, comisiones y consistencia de rentabilidades.

## Fuente de datos y actualización

- La aplicación trabaja con un snapshot local de datos.
- En esta versión, el listado corresponde a la foto del 22/04/2026.
- Para mejorar rendimiento, los datos se cachean durante 6 horas.

## Importante

- Esta aplicación es una herramienta de exploración y análisis, no una plataforma de ejecución de órdenes.
- Las rentabilidades pasadas no garantizan rentabilidades futuras.
- Invertir en fondos conlleva riesgo de pérdida de capital.