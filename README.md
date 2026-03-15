# The Brownfield Cartographer

A production-grade codebase intelligence system that transforms opaque, undocumented repositories into living, queryable knowledge graphs.

## Overview

The Brownfield Cartographer solves the "Day-One Problem" for Forward Deployed Engineers by automatically analyzing codebases and generating:

- **Module Graph**: Structural analysis with import dependencies, PageRank, and circular dependency detection
- **Data Lineage Graph**: Full data flow tracking across Python, SQL, and YAML
- **Git Velocity Metrics**: Identify high-churn files and dead code candidates
- **Blast Radius Analysis**: Calculate downstream impact of changes

## Features

### Recent Improvements (Feedback-Driven)
- **Robust Deserialization**: Graph loading with automatic Pydantic schema validation
- **Multi-Language Router**: Extended AST parsing for Python, SQL, and YAML files
- **Three SQL Dialects**: PostgreSQL, BigQuery, and Snowflake support with auto-detection
- **Configurable Velocity**: Customizable time windows for git change tracking
- **Impact Reports**: Automated high-churn hotspot and dead code identification
- **Source/Sink Detection**: Utilities to find data pipeline entry and exit points
- **Enriched Metadata**: Edge annotations with transformation types and line numbers
- **GitHub URL Support**: Direct analysis of GitHub repositories via CLI
- **Error Isolation**: Resilient pipeline that continues despite individual file failures
- **Enhanced Logging**: Clear progress indicators and error reporting

### Static Analysis (Surveyor Agent)
- Multi-language AST parsing with tree-sitter (Python, SQL, YAML)
- Module import graph with PageRank for architectural hub identification
- Circular dependency detection using strongly connected components
- Git velocity tracking (commits in last 30 days)
- Dead code candidate identification

### Data Lineage (Hydrologist Agent)
- SQL dependency extraction with sqlglot (supports PostgreSQL, BigQuery, Snowflake)
- dbt Jinja template preprocessing (`{{ source() }}`, `{{ ref() }}`)
- YAML config parsing (dbt schema.yml, Airflow DAGs)
- Blast radius calculation for impact analysis
- Upstream/downstream dependency tracing

### Semantic Analysis (Semanticist Agent)
- LLM-powered purpose statement generation
- Documentation drift detection
- Business context extraction from code
- Automatic docstring validation
- Domain clustering using embeddings and k-means
- Automatic business domain naming
- **FDE Day-One Questions**: Answers the Five Day-One Questions using architectural context

### Knowledge Graph
- NetworkX-based directed graph
- Strongly-typed Pydantic schemas for all nodes and edges
- JSON serialization for downstream tooling
- Node types: Module, Dataset, Function, Transformation
- Edge types: IMPORTS, PRODUCES, CONSUMES, CALLS, CONFIGURES

## Installation

### Prerequisites
- Python 3.10+
- Git (for velocity tracking)
- uv (recommended) or pip

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd 10AcWeek4

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Dependencies
- `tree-sitter` & `tree-sitter-python` - AST parsing
- `sqlglot` - SQL parsing and lineage extraction
- `networkx` - Graph construction and analysis
- `pydantic` - Data validation and schemas
- `pyyaml` - YAML config parsing
- `numpy` - Required for NetworkX PageRank

## Usage

### Basic Analysis

```bash
# Analyze a repository (full analysis)
.venv/bin/python -m src.cli analyze --repo /path/to/repository

# Analyze GitHub repository directly (NEW!)
.venv/bin/python -m src.cli analyze --repo https://github.com/dbt-labs/jaffle-shop

# Analyze current directory
.venv/bin/python -m src.cli analyze --repo .

# Analyze dbt project
.venv/bin/python -m src.cli analyze --repo jaffle-shop

# Incremental analysis (only changed files since last run)
.venv/bin/python -m src.cli analyze --repo . --incremental

# With LLM-powered semantic analysis (requires OPENROUTER_API_KEY)
.venv/bin/python -m src.cli analyze --repo . --llm

# Combined: incremental + LLM
.venv/bin/python -m src.cli analyze --repo . --incremental --llm
```

### Output Artifacts

Analysis generates the following in `.cartography/`:

```
.cartography/
├── module_graph.json       # Complete knowledge graph
├── lineage_graph.json      # Data lineage (same as module_graph)
├── day_one_questions.md    # FDE Day-One analysis (with --llm flag)
└── last_analysis.json      # State for incremental updates
```

### Understanding the Output

**Console Output:**
- List of analyzed files (Python, SQL, YAML)
- Top 5 architectural hubs (by PageRank)
- Circular dependency warnings
- Summary statistics (nodes by type, edges by type)

**Graph Structure:**
```json
{
  "nodes": [
    {
      "id": "src/models/schema.py",
      "node_type": "module",
      "language": "python",
      "complexity_score": 12,
      "change_velocity_30d": 5,
      "pagerank": 0.0234,
      "has_circular_dependency": false
    }
  ],
  "links": [
    {
      "source": "src/cli.py",
      "target": "src/orchestrator.py",
      "edge_type": "IMPORTS"
    }
  ]
}
```

## Architecture

### Agent-Based Pipeline

```
┌─────────────┐
│   CLI       │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Orchestrator   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│Surveyor │ │ Hydrologist  │
└────┬────┘ └──────┬───────┘
     │             │
     └──────┬──────┘
            ▼
    ┌───────────────┐
    │Knowledge Graph│
    └───────────────┘
```

### Components

**Surveyor Agent** (`src/agents/surveyor.py`)
- Analyzes Python files with tree-sitter
- Builds module import graph
- Calculates PageRank and detects cycles
- Tracks git velocity

**Hydrologist Agent** (`src/agents/hydrologist.py`)
- Analyzes SQL files with sqlglot
- Preprocesses dbt Jinja templates
- Parses YAML configs
- Builds data lineage graph

**Knowledge Graph** (`src/graph/knowledge_graph.py`)
- NetworkX DiGraph wrapper
- Strongly-typed node/edge addition
- JSON serialization

**Analyzers** (`src/analyzers/`)
- `tree_sitter_analyzer.py` - Multi-language AST parsing
- `sql_lineage.py` - SQL dependency extraction with dbt support
- `dag_config_parser.py` - YAML config parsing

## Examples

### Answering FDE Day-One Questions

When using the `--llm` flag, the Semanticist automatically generates answers to the Five FDE Day-One Questions:

```bash
.venv/bin/python -m src.cli analyze --repo . --llm
```

**Output** (`.cartography/day_one_questions.md`):
```markdown
# FDE Day-One Analysis

## 1. What does this system do?
The Brownfield Cartographer is a codebase intelligence system that analyzes
undocumented repositories and generates knowledge graphs. The system orchestrates
three agents (Surveyor, Hydrologist, Semanticist) via src/orchestrator.py to
extract structural, data lineage, and semantic insights.

## 2. Where does the data come from?
Data originates from source code files (.py, .sql, .yml) in the target repository.
The Surveyor agent (src/agents/surveyor.py) parses Python modules using tree-sitter,
while the Hydrologist (src/agents/hydrologist.py) extracts SQL dependencies.

## 3. Where does the data go?
Analysis results are serialized to .cartography/module_graph.json and
.cartography/lineage_graph.json. The knowledge graph can be consumed by
downstream visualization tools or queried programmatically.

## 4. What are the critical paths?
The orchestrator (src/orchestrator.py, PageRank: 0.0312) coordinates the pipeline.
The knowledge graph (src/graph/knowledge_graph.py, PageRank: 0.0389) is the
central data structure. The CLI (src/cli.py, PageRank: 0.0287) is the entry point.

## 5. What are the biggest risks?
- LLM API failures could break semantic analysis (no fallback for embeddings)
- Large repositories (>10k files) may exceed token budgets
- Circular dependencies detected in 3 modules could cause import issues
```

### Analyzing dbt Projects

```bash
# The Cartographer handles dbt Jinja templates automatically
.venv/bin/python -m src.cli analyze --repo jaffle-shop
```

**Output:**
- Extracts `{{ source('schema', 'table') }}` references
- Extracts `{{ ref('model') }}` dependencies
- Builds complete data lineage DAG
- Identifies source tables and target models

### Identifying Architectural Hubs

The Surveyor automatically calculates PageRank:

```
Surveyor: Top 5 Architectural Hubs (by PageRank):
  src/models/schema.py: 0.0456
  src/graph/knowledge_graph.py: 0.0389
  src/orchestrator.py: 0.0312
  src/cli.py: 0.0287
  src/agents/surveyor.py: 0.0245
```

### Detecting Circular Dependencies

```
Surveyor: Found 1 circular dependency group(s):
  Cycle 1: 3 modules involved
    - src/module_a.py
    - src/module_b.py
    - src/module_c.py
```

### Calculating Blast Radius

```python
from src.agents.hydrologist import Hydrologist
from src.graph.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
# ... load graph ...

hydrologist = Hydrologist(kg)
affected = hydrologist.blast_radius("users_table")
# Returns set of all downstream datasets
```

## Supported Codebases

### Tested On
- ✅ dbt projects (jaffle-shop)
- ✅ Python data pipelines
- ✅ Mixed Python/SQL repositories

### SQL Dialects
- PostgreSQL (default)
- BigQuery
- Snowflake (auto-detected from file paths)

### File Types
- `.py` - Python modules
- `.sql` - SQL queries and dbt models
- `.yml`, `.yaml` - dbt configs, Airflow DAGs

## Limitations

### Current Limitations
- **dbt Macros**: Jinja macros are stripped, not evaluated
- **Dynamic References**: f-strings and variable table names logged as unresolved
- **Notebook Support**: `.ipynb` files not yet supported
- **Java/Scala**: Only Python currently supported for code analysis

### Known Issues
- Git velocity requires repository to be a git repo
- PageRank requires numpy (automatically installed)
- Very large repos (>10k files) may take several minutes

## Development

### Project Structure

```
src/
├── agents/           # Analysis agents
│   ├── surveyor.py
│   └── hydrologist.py
├── analyzers/        # Language-specific analyzers
│   ├── tree_sitter_analyzer.py
│   ├── sql_lineage.py
│   └── dag_config_parser.py
├── graph/            # Knowledge graph
│   └── knowledge_graph.py
├── models/           # Pydantic schemas
│   └── schema.py
├── utils/            # Utilities
│   └── incremental.py
├── cli.py            # Command-line interface
└── orchestrator.py   # Pipeline orchestration
```

### Running Tests

```bash
# Analyze the cartographer itself (self-audit)
.venv/bin/python -m src.cli analyze --repo .
```

### Adding New Analyzers

1. Create analyzer in `src/analyzers/`
2. Add to appropriate agent (`Surveyor` or `Hydrologist`)
3. Update `orchestrator.py` if needed

## Troubleshooting

### Common Issues

See `QUICK_REFERENCE.md` for detailed usage of new features.

### Import Errors
```bash
# Ensure you're using the virtual environment
.venv/bin/python -m src.cli analyze --repo .
```

### Git Velocity Not Working
```bash
# Ensure the target is a git repository
cd target-repo && git log --oneline | head -5
```

### SQL Parsing Errors
- Expected for dbt Jinja templates
- Preprocessor extracts `source()` and `ref()` calls
- Other Jinja constructs are stripped

### Empty Graph
- Check that target directory contains `.py` or `.sql` files
- Verify file permissions
- Check console output for error messages

## Contributing

This is a TRP 1 Week 4 project. For questions or issues, refer to the project specification.

## License

Educational project - see course materials for details.

## Acknowledgments

Built using:
- tree-sitter (GitHub, Neovim)
- sqlglot (Tobias Mao)
- NetworkX (NetworkX Developers)
- Pydantic (Samuel Colvin)
