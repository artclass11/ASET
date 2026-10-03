# ASET Research Engine

Python package for deterministic public-equity research analytics and a small versioned FastAPI research API.

## Install

From the repository root:

```bash
python -m pip install -e ./stock_analyzer
```

## CLI

```bash
stock-research --help
stock-research demo
```

## API

```bash
uvicorn stock_analyzer.api:app --host 127.0.0.1 --port 8000
```

The API currently uses a deterministic fixture provider for local development. Production provider wiring belongs in an explicit deployment configuration.

## Design

The package keeps market observations tied to provenance, quality metadata, dates and currency. Analytics functions are deterministic and independently testable.
