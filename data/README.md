# ASET Original Research Data

This directory is reserved for **original ASET research artifacts** generated from the official source registry. The repository does not ship fabricated prices, financial statements, rankings, or investment conclusions.

## Rule

Every material value in a future data file must map to a `source_ref` in [`official_source_registry.csv`](official_source_registry.csv), include `retrieved_at`, `data_as_of`, `period`, `currency`, `unit`, and `status`, and preserve the original official URL or file locator.

The current downloadable workbook is a blank, formula-driven research template. It is intentionally not populated with market data.
