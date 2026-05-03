# Methodology · Spec-Driven Development (SDD)

## Overview

This project follows a **Spec-Driven Development (SDD)** approach adapted to a data engineering context.

The core idea behind SDD is simple:

> **Nothing is implemented without a prior specification.**

Instead of relying on ad-hoc coding or iterative trial-and-error, the system is designed around:

- Explicit definitions of responsibilities
- Clear contracts between components
- Traceable execution from input to output

This results in a pipeline that is predictable, testable and aligned with business requirements.

---

## Why SDD in a Data Pipeline

Typical data workflows suffer from:

- Implicit assumptions hidden in code
- Lack of validation until late stages
- Difficult debugging and poor traceability

By applying SDD:

- Each stage has a clearly defined role
- Validation is enforced as part of the pipeline (not after it)
- Outputs can be audited and explained

In this project, SDD is used to ensure that:

- Data quality rules are explicit and enforced
- Pipeline behavior is deterministic
- Errors and data loss are observable and intentional

---

## Adaptation to Pipeline Architecture

The SDD approach is implemented through a **modular pipeline design**:

```text
Stage 1 -> Consolidation
Stage 2 -> Cleaning
Stage 3 -> Formatting
Stage 4 -> Orchestration
```

Each stage represents a controlled transformation step with a defined contract:

| Stage | Responsibility | Output |
|---|---|---|
| Consolidation | Schema normalization | `df_unified` |
| Cleaning | Validation and quality enforcement | `df_validated` |
| Formatting | Output generation | Excel report |
| Orchestration | Execution control and logging | Execution log |

Key characteristics:

- No stage mixes responsibilities
- Each stage can be tested independently
- Data flows forward with increasing quality guarantees

---

## Core Principles Applied

### 1. Separation of Concerns

Each stage has a single responsibility:

- Structure (Stage 1)
- Data quality (Stage 2)
- Presentation (Stage 3)
- Coordination (Stage 4)

This prevents hidden logic and makes the system maintainable.

### 2. Explicit Data Contracts

The pipeline enforces implicit contracts between stages:

- Stage 1 guarantees structure but not validity
- Stage 2 guarantees validity but not presentation
- Stage 3 assumes valid input

This allows stages to evolve independently without breaking the system.

### 3. Validation as a First-Class Concern

Validation is not optional or external. It is:

- Built into Stage 2
- Enforced through strict business rules
- Reflected in the output (via row filtering and logs)

This ensures that only business-valid data reaches the final report.

### 4. Traceability by Design

Each pipeline execution produces:

- A timestamped output file
- A structured execution log (`execution_log_YYYYMMDD_HHMM.json`)
- Cleaning diagnostics (`cleaning_summary`)

This enables:

- Auditing decisions
- Understanding data loss
- Debugging without re-running blindly

### 5. Deterministic Behavior

Given the same inputs and configuration:

- The pipeline produces the same outputs
- All transformations are predictable
- No hidden heuristics or randomness are applied

This is essential for production-grade data workflows.

---

## Relation to GAIA Framework

This project is inspired by the GAIA framework
(Governed AI for Interactive Applications, 2026).

GAIA defines a structured approach to AI-assisted development based on:

- Specification -> Planning -> Execution -> Validation -> Closure
- Governance of artifacts (Rules, Workflows, Skills)
- Evidence-based development through TDD

In GAIA, implementation is strictly controlled through formal workflows and validation gates.

### Alignment with GAIA

This pipeline aligns with several GAIA principles:

- Clear separation between specification and execution
- Strong emphasis on validation as evidence
- Controlled execution flow through defined stages
- Traceability of outputs and decisions

### Key Differences

This project does not implement GAIA fully:

- No `.agent` layer (Rules / Workflows / Skills)
- No command-based workflow system (e.g. `/execute-plan`)
- No formal planning artifacts (PRD, tickets, etc.)

Instead, GAIA concepts are simplified, embedded directly into the pipeline design and adapted to a data engineering use case.

### Interpretation

The pipeline can be seen as a lightweight, production-oriented adaptation of GAIA, where:

- Pipeline stages act as execution workflows
- Data validation replaces test-driven evidence
- Execution logs provide traceability instead of formal journaling

---

## Design Trade-offs

### Advantages

- Simpler than full SDD frameworks
- Faster to implement and iterate
- Easier to understand for data workflows
- Directly applicable to real business problems

### Limitations

- Less flexible than config-driven or workflow-based systems
- No formal planning layer (spec -> tickets -> execution)
- Harder to generalize to multiple domains without extension

---

## Future Evolution

Potential improvements aligned with SDD / GAIA principles:

- Introduce config-driven validation rules
- Add schema validation (e.g. Pydantic models)
- Extend execution logs with richer lineage metadata
- Separate business rules from implementation logic

---

## Summary

This project demonstrates how SDD principles can be applied to data pipelines:

- Structure first
- Validate early
- Separate responsibilities
- Ensure traceability

Inspired by GAIA, but adapted pragmatically, the result is a system that prioritises data quality, clarity and reproducibility over complexity.