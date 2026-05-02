# Decisions Log

This document captures the key architectural and technical decisions taken during the development of the pipeline.

It focuses on decisions that affect system design, data quality and extensibility.

---

## [2026-04-04] Modular pipeline with strict separation of concerns

**Decision:** The system is structured into independent stages: consolidation, cleaning, formatting and orchestration. Each stage has a single responsibility.

**Rationale:** Ensures maintainability, testability and clear ownership of logic. Prevents mixing data processing, validation and presentation concerns.

**Impact:** Defines the overall architecture of the system and the structure of the codebase.

**Status:** Implemented

---

## [2026-04-04] Explicit contracts between pipeline stages

**Decision:** Each stage exposes well-defined input/output contracts:
- Stage 1 → `df_unified`
- Stage 2 → `df_validated`
- Stage 3 → Excel report

**Rationale:** Decouples implementation details and ensures compatibility between stages without tight coupling.

**Impact:** Enables independent testing and future extensibility.

**Status:** Implemented

---

## [2026-04-04] Standard schema with canonical columns

**Decision:** A fixed schema of 12 canonical columns is enforced across all datasets.

**Rationale:** Source files contain multiple naming variants. A canonical schema ensures consistency and simplifies downstream processing.

**Impact:** Affects Stage 1 mapping and all subsequent stages.

**Status:** Implemented

---

## [2026-04-04] Row-level traceability via `source_file`

**Decision:** Add `source_file` column to all records during consolidation.

**Rationale:** Enables data lineage and traceability of each row back to its origin.

**Impact:** Supports debugging, auditing and future lineage extensions.

**Status:** Implemented

---

## [2026-04-23] Standardized numeric and date parsing

**Decision:**
- Numeric values use English format (`.` decimal, `,` thousands)
- Dates use day-first parsing with support for multiple formats

**Rationale:** Avoid ambiguity and ensure deterministic parsing across heterogeneous inputs.

**Impact:** Affects type coercion and validation logic in Stage 2.

**Status:** Implemented

---

## [2026-04-23] Conservative text standardization

**Decision:** Text fields are only minimally transformed (strip whitespace). Unknown categorical values are preserved.

**Rationale:** Prevent irreversible data degradation and preserve business semantics.

**Impact:** Affects `standardization.py` and validation behavior.

**Status:** Implemented

---

## [2026-04-27] JSON-based configuration for MVP

**Decision:** Use JSON as the only configuration mechanism in the MVP.

**Rationale:** Keeps configuration simple, explicit and testable while avoiding premature abstraction.

**Impact:** Configuration defines schema, required fields and column mapping.

**Status:** Implemented

---

## [2026-04-27] Cleaning diagnostics integrated into execution log

**Decision:** Cleaning metrics are returned as `cleaning_summary` and stored within the execution log instead of generating a separate report.

**Rationale:** Centralizes traceability and avoids duplication of outputs.

**Impact:** Affects Stage 2 and orchestration layer.

**Status:** Implemented

---

## [2026-05-01] Completeness-based deduplication

**Decision:** For duplicate `id_venta`, keep the row with the highest completeness in required fields instead of the first occurrence.

**Rationale:** Source datasets overlap and may contain partial duplicates. Prioritizing completeness preserves better data.

**Impact:** Affects deduplication logic in Stage 2.

**Status:** Implemented

---

## [2026-05-01] Strict validation despite high row removal

**Decision:** Required fields (`id_venta`, `fecha_venta`, `importe`) must be present and valid. Rows failing these rules are discarded.

**Rationale:** Ensures data reliability and prevents incorrect reporting.

**Impact:** May result in high row removal when source data quality is poor. This is expected and tracked via diagnostics.

**Status:** Implemented

---

## [2026-05-02] Separation of local CLI and cloud entry point

**Decision:** Keep `cli.py` for local execution and introduce a separate `lambda_handler.py` for cloud execution. Both reuse the same pipeline core.

**Rationale:** Maintains separation between business logic and deployment-specific adapters.

**Impact:** Enables cloud deployment without modifying core pipeline logic.

**Status:** Approved

---

## [2026-05-02] AWS CLI as initial deployment strategy

**Decision:** Use AWS CLI for initial deployment instead of Terraform or SAM.

**Rationale:** Provides a reproducible and lightweight approach without introducing unnecessary complexity at this stage.

**Impact:** Defines Phase 2 deployment workflow.

**Status:** Approved