# Spec-Driven Development (SDD) — Overview

This project follows a Spec-Driven Development (SDD) approach, where all architectural and technical decisions are defined before implementation.

---

## Why SDD

The goal is to build a pipeline that is:

- predictable
- traceable
- maintainable
- production-ready

SDD ensures that:

- no code is written without prior specification
- all decisions are documented and justified
- implementation follows clearly defined contracts

---

## Pipeline Architecture

The system is structured as a modular pipeline with strict separation of concerns:

```text
Stage 1 -> Consolidation
Stage 2 -> Cleaning
Stage 3 -> Formatting
Stage 4 -> Orchestration
```

Each stage has a single responsibility:

- Stage 1 -> schema normalization and data consolidation
- Stage 2 -> data quality (types, nulls, validation, deduplication)
- Stage 3 -> report generation (Excel output)
- Stage 4 -> pipeline execution and logging

---

## Core Design Principles

- Strict separation between data processing and presentation
- Explicit contracts between stages
- Config-driven evolution (JSON-based)
- Idempotent outputs via timestamping
- Full traceability via execution logs

---

## Traceability

Every pipeline run generates:

- a business-ready Excel report
- a structured execution log (`execution_log.json`)

The log includes:

- rows processed per stage
- errors and warnings
- cleaning diagnostics (`cleaning_summary`)

This enables full auditability of data transformations.

---

## Scope

This public SDD documentation is a curated version of the full internal specification, focused on:

- architecture
- key decisions
- design rationale

Internal working documents and exploratory notes are intentionally excluded.

---

## Development Approach

The project follows a Spec-Driven Development (SDD) methodology.
Implementation is assisted by AI tools, with an independent validation step to ensure correctness, robustness and alignment with specifications.
All final decisions and design direction are defined and validated by the project lead.

---

## Methodological Context

This project’s SDD approach is conceptually aligned with the GAIA framework (Governed AI for Interactive Applications, 2026).

GAIA defines a structured system for AI-assisted development based on:

- Artifact governance (Rules, Workflows, Skills)
- Intent-driven execution flows (feature, bug, refactor)
- Evidence-based development through TDD
- Strict separation between specification, planning, execution and closure

Although this project does not implement GAIA formally (no .agent layer or workflow commands), it applies several of its principles in a simplified and pragmatic way adapted to data engineering pipelines.

Reference:
Cristina Cachero (2026). Spec-Driven Development con GAIA.