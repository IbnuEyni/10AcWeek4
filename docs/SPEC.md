# SPECIFICATION: The Brownfield Cartographer (v1.0)

## 1. Executive Summary

**The Brownfield Cartographer** is a production-grade codebase intelligence system designed to solve the "Day-One Problem" for Forward Deployed Engineers (FDEs). It transforms an opaque, undocumented repository into a living, queryable knowledge graph.

### Core Objectives

- **Mapping:** Extract structural and data lineage relationships across Python, SQL, and YAML.
- **Contextualizing:** Generate implementation-grounded semantic descriptions, bypassing stale documentation.
- **Onboarding:** Answer the "Five FDE Day-One Questions" with evidence-based citations.
- **Persistence:** Maintain a `CODEBASE.md` file to give AI coding agents instant architectural awareness.

---

## 2. System Architecture

The system utilizes a **Multi-Agent Enrichment Pipeline** feeding a central **Knowledge Graph**.

| Agent           | Responsibility                                           | Toolset              |
| :-------------- | :------------------------------------------------------- | :------------------- |
| **Surveyor**    | Static analysis, Import/Call graphs, Git velocity        | `tree-sitter`, `git` |
| **Hydrologist** | Data lineage, SQL parsing, Pipeline DAGs                 | `sqlglot`, `PyYAML`  |
| **Semanticist** | Intent extraction, Domain clustering, Question answering | LLM (Gemini/Claude)  |
| **Archivist**   | Markdown synthesis, Context injection, Trace logging     | Pydantic, Jinja2     |
| **Navigator**   | Interactive Query Interface (LangGraph)                  | Tool-calling LLM     |

---

## 3. Data Contracts (Pydantic Models)

All internal state must be strictly typed using Pydantic V2.

### 3.1 Node Definitions (`src/models/nodes.py`)

- **ModuleNode**: Represents a source file.
  - `path`: str (Primary Key)
  - `language`: str
  - `purpose_statement`: Optional[str]
  - `domain_cluster`: Optional[str]
  - `complexity_score`: float
  - `change_velocity_30d`: int
  - `is_dead_code_candidate`: bool
- **DatasetNode**: Represents a data entity (Table, File, Stream).
  - `name`: str (Primary Key)
  - `storage_type`: Literal["table", "file", "stream", "api"]
  - `schema_snapshot`: Dict[str, Any]
- **FunctionNode**: Represents a code unit.
  - `qualified_name`: str
  - `signature`: str
  - `is_public_api`: bool
- **TransformationNode**: Represents logic moving data.
  - `source_file`: str
  - `logic_type`: str (e.g., "spark_sql", "pandas_transform")

### 3.2 Edge Definitions (`src/models/edges.py`)

- `IMPORTS`: Module → Module
- `PRODUCES`: Transformation → Dataset
- `CONSUMES`: Transformation → Dataset
- `CALLS`: Function → Function
- `CONFIGURES`: YAML/Config → Module/Pipeline

---

## 4. Technical Requirements

### 4.1 Static Analysis (The Surveyor)

- **Multi-Language AST:** Use `tree-sitter` with a `LanguageRouter` to parse `.py`, `.sql`, and `.yaml`.
- **Structural Analysis:** Identify the "Architectural Hubs" using NetworkX PageRank on the import graph.
- **Git Velocity:** Parse `git log` to identify the "Hot Path" (20% of files causing 80% of churn).

### 4.2 Data Lineage (The Hydrologist)

- **SQL Analysis:** Use `sqlglot` to parse dbt models and raw SQL strings. Extract `SELECT/FROM/JOIN/CTE` dependencies.
- **Python Data Flow:** Detect Pandas `read_*/to_*`, Spark `load/save`, and SQLAlchemy operations.
- **Blast Radius:** Implement `trace_downstream(node_id)` to calculate the impact of a schema change.

### 4.3 Semantic Reasoning (The Semanticist)

- **Cost Discipline:** Use `ContextWindowBudget` to monitor token usage. Tiered model usage (Flash for bulk, Sonnet for synthesis).
- **Purpose Extraction:** Generate 2-3 sentence summaries based on **actual code implementation**, not docstrings.
- **Documentation Drift:** Flag instances where the implementation significantly deviates from the file's docstring.

---

## 5. Deliverables & Artifacts

### 5.1 CODEBASE.md (The Living Context)

A structured file for AI coding agents containing:

- **Critical Path:** Top 5 architectural hubs.
- **Data Flow:** Primary sources and sinks.
- **High-Velocity Files:** Churn hotspots.
- **Module Index:** Semantic purpose of every core module.

### 5.2 onboarding_brief.md (The Day-One Brief)

Evidence-backed answers to:

1. What is the primary data ingestion path?
2. What are the 3-5 most critical output datasets?
3. What is the blast radius if the most critical module fails?
4. Where is business logic concentrated vs. distributed?
5. What has changed most frequently in the last 90 days?

---

## 6. Implementation Roadmap

### Phase 1: Foundations (Interim Target)

- [ ] Initialize `uv` environment and Pydantic models.
- [ ] Implement `Surveyor` (tree-sitter) and `Hydrologist` (sqlglot).
- [ ] Generate `.cartography/module_graph.json` and `lineage_graph.json`.

### Phase 2: Intelligence (Final Target)

- [ ] Integrate LLM-powered `Semanticist` for purpose extraction.
- [ ] Implement `Archivist` to generate `CODEBASE.md` and the `onboarding_brief.md`.
- [ ] Build the `Navigator` LangGraph CLI with interactive tools.
- [ ] Add **Incremental Mode** to re-analyze only files changed in the last git commit.

---

## 7. Safety and Resilience

- **Incremental Processing:** Use `git diff` to prevent redundant LLM calls on unchanged code.
- **Graceful Failure:** If an AST parser fails on a malformed file, log the error to `cartography_trace.jsonl` and continue analysis.
- **Context Management:** Use `ContextWindowBudget` to prevent runaway costs during bulk analysis.
