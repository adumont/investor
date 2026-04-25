# Investor

Streamlit app for exploring MyInvestor investment products from local snapshot.

## What it does

App lets user scan, filter, compare, inspect funds and pension products without digging through product PDFs one by one.

## Features

- Search by product name or ISIN.
- Quick filters for `World`, `S&P 500`, `Emergentes`, `Japón`, `Small Caps`, `Oro y Metales`, or no preset.
- Main filters for currency, product type, and manager.
- Advanced filters for:
  - category
  - MyInvestor category
  - Morningstar category
  - asset type
  - geographic zone
  - sector exposure
- Sector filter supports minimum threshold. Example: show products with at least `20%` in selected sector.
- Optional sector columns in results table for selected sectors.
- Optional columns for:
  - last 6 calendar-year returns including current year YTD
  - annualized `1Y`, `3Y`, `5Y` returns
  - category fields
  - subscription and redemption settlement lag days
- Results include `TE_1Y`: tracking error over 1 year (`trackingErrorYearUno`).
- Results table sorted by risk first, then TER.
- Single-row selection. Pick product from table to open full detail panel.
- Auto-open product detail when only 1 result remains.
- Product detail view includes:
  - name, ISIN, asset type, risk indicator
  - description
  - links to factsheet, KIID, semiannual report, memory/report docs, Morningstar
  - historical return charts
  - general metadata table
  - fee table with TER highlighted
  - sector breakdown
  - region breakdown
  - composition/holdings table when available
  - raw JSON payload for full inspection
- Data cached for 6 hours to keep UI fast.

## Data source

- App reads local file `myinvestor.json`.
- Current snapshot in repo dated `22/04/2026`.
- Only products with status `OPEN` appear in results.

## What user sees first

- Table of products.
- Default filters: currency `EUR`, product type `FONDOS_INDEXADOS`.
- SQL query used for current view in expandable block.
- Detail panel after row selection.

## How to use

App is live at: https://investor26.streamlit.app/

### Work with results

1. Type part of product name or ISIN in search box.
2. Add quick filter or advanced filters.
3. Toggle extra columns if needed.
4. Click row in table.
5. Review charts, fees, sectors, regions, and raw product payload.

## Typical uses

- Find low-risk or low-TER products fast.
- Narrow list to one geography, category, manager, or currency.
- Check sector concentration before buying.
- Compare historical returns across candidate products.
- Open product documents from one place.

## Notes

- This is exploration tool, not execution platform.
- Returns shown are historical. They do not guarantee future returns.
- Data freshness depends on `myinvestor.json` snapshot, not live API calls in current setup.