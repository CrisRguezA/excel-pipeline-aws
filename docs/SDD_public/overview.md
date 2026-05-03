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

Each stage has a clearly defined responsibility and operates on explicit data contracts.

For a detailed description of each stage and execution flow, see:
→ pipeline_design.md

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

This project follows a Spec-Driven Development (SDD) approach.

For a detailed explanation of the methodology, including its alignment with the GAIA framework and AI-assisted development practices, see:
→ `methodology.md`

