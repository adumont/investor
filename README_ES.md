# Investor

App Streamlit para explorar productos de inversión de MyInvestor desde snapshot local.

## Qué hace

App permite buscar, filtrar, comparar e inspeccionar fondos y planes sin abrir PDFs producto por producto.

## Funcionalidades

- Búsqueda por nombre o ISIN.
- Filtros rápidos para `World`, `S&P 500`, `Emergentes`, `Japón`, `Small Caps`, `Oro y Metales`, o sin preset.
- Filtros principales por divisa, tipo de producto y gestora.
- Filtros avanzados por:
  - categoría
  - categoría MyInvestor
  - categoría Morningstar
  - tipo de activo
  - zona geográfica
  - exposición sectorial
- Filtro sector con umbral mínimo. Ejemplo: mostrar productos con al menos `20%` en sector seleccionado.
- Columnas sectoriales opcionales en tabla para sectores elegidos.
- Columnas opcionales para:
  - rentabilidad de últimos 6 años naturales, incluido YTD del año actual
  - rentabilidad anualizada `1Y`, `3Y`, `5Y`
  - campos de categoría
  - días de desplazamiento en suscripción y reembolso
- Resultados incluyen `TE_1Y`: tracking error a 1 año (`trackingErrorYearUno`).
- Tabla ordenada por riesgo y luego TER.
- Selección de una sola fila. Al elegir fila, abre panel de detalle.
- Apertura automática de detalle cuando queda un solo resultado.
- Vista detalle de producto incluye:
  - nombre, ISIN, tipo de activo, indicador de riesgo
  - descripción
  - enlaces a ficha técnica, KIID, informe semestral, memoria/informes, Morningstar
  - gráficos de rentabilidad histórica
  - tabla de datos generales
  - tabla de comisiones con TER destacado
  - desglose por sectores
  - desglose por regiones
  - tabla de composiciones/posiciones cuando existe
  - payload JSON crudo para inspección completa
- Caché de datos por 6 horas para mejorar velocidad.

## Fuente de datos

- App lee archivo local `myinvestor.json`.
- Snapshot actual en repo fechado `22/04/2026`.
- Solo aparecen productos con estado `OPEN`.

## Qué ve usuario al inicio

- Tabla de productos.
- Filtros por defecto: divisa `EUR`, tipo de producto `FONDOS_INDEXADOS`.
- Consulta SQL usada para vista actual dentro de bloque expandible.
- Panel de detalle tras seleccionar fila.

## Cómo usar

App publicada en: https://investor26.streamlit.app/

### Trabajar con resultados

1. Escribe parte del nombre o ISIN en buscador.
2. Añade filtro rápido o filtros avanzados.
3. Activa columnas extra si hace falta.
4. Haz clic en fila de tabla.
5. Revisa gráficos, comisiones, sectores, regiones y payload crudo.

## Usos típicos

- Encontrar productos con menor riesgo o menor TER.
- Reducir lista por geografía, categoría, gestora o divisa.
- Revisar concentración sectorial antes de invertir.
- Comparar rentabilidades históricas entre candidatos.
- Abrir documentación de producto desde un solo punto.

## Notas

- Herramienta de exploración, no plataforma de ejecución de órdenes.
- Rentabilidades mostradas son históricas. No garantizan rentabilidades futuras.
- Frescura de datos depende del snapshot en `myinvestor.json`, no de llamadas live a API en configuración actual.