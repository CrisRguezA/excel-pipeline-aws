# Pipeline Design

This document describes the internal structure and execution flow of the Excel Sales Pipeline.
The system is designed as a modular pipeline with strict separation of responsibilities between stages.

---

## Pipeline Overview

```text
Stage 1 -> Consolidation
Stage 2 -> Cleaning
Stage 3 -> Formatting
Stage 4 -> Orchestration
```

Each stage operates on well-defined inputs and outputs, ensuring loose coupling and testability.

---

## Stage 1 · Consolidation

**Responsibility:**

- Ingest multiple Excel files
- Normalize heterogeneous schemas
- Produce a unified dataset

**Key features:**

- Column mapping via JSON configuration
- Handling of schema variability across sources
- Addition of `source_file` for row-level traceability

**Output:** `df_unified`

- Standardized schema (12 columns)
- No rows removed
- Includes `source_file`

**Does NOT:**

- Clean or validate data
- Drop rows

---

## Stage 2 · Cleaning

**Responsibility:**

- Ensure data quality and consistency

**Processing steps:**

1. Type coercion (dates and numerics)
2. Deduplication by `id_venta`
3. Null handling and standardization
4. Business validation

**Key design choices:**

- Strict validation: rows with missing or invalid required fields are discarded
- Completeness-based deduplication: for duplicate `id_venta`, the most complete row is kept
- Multi-format date parsing: supports multiple formats with a Spanish-first priority

**Output:**

- `df_validated`
- `cleaning_summary` (diagnostics of row transformations and removals)

**Does NOT:**

- Generate reports
- Apply formatting

---

## Stage 3 · Formatting

**Responsibility:**

- Transform validated data into a business-ready Excel report

**Output:** Excel file with two sheets:

- `Weekly_Report`
- `Report_Info`

**Features:**

- Structured layout
- Conditional formatting:
  - Row color based on `estado`
  - Cell color based on `certificacion`
- Totals and metadata
- Autofit columns and freeze panes

**Does NOT:**

- Validate data
- Modify business logic

---

## Stage 4 · Orchestration

**Responsibility:**

- Coordinate the execution of the full pipeline

**Main function:**

```python
run_pipeline(input_path, output_path, config_path)
```

**Flow:**

1. Load configuration
2. Execute Stage 1 -> Stage 2 -> Stage 3
3. Collect execution metrics
4. Generate execution log

**Output:**

- Excel report
- `execution_log_YYYYMMDD_HHMM.json`

---

## Execution Log

Each pipeline run generates a structured log containing:

- Timestamp
- Files processed
- Rows per stage
- Errors and warnings
- Execution duration
- Cleaning diagnostics (`cleaning_summary`)

This enables full traceability and auditability.

---

## Design Principles

- Separation of concerns: each stage has a single responsibility
- Explicit contracts: clear inputs and outputs between stages
- Traceability: all transformations are logged
- Idempotency: outputs are timestamped to avoid overwriting
- Extensibility: designed to support cloud deployment without rewriting core logic

---

## Extensibility

The architecture is designed to support future phases:

- Cloud execution (AWS Lambda + S3)
- Automated report delivery
- API layer for external access
- Interactive dashboards

The core pipeline remains unchanged across environments, with cloud-specific logic implemented as adapters.