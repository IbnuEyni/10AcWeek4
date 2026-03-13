# Archivist Agent - Documentation & Semantic Indexing

## Overview

The **Archivist** agent generates comprehensive documentation from the knowledge graph and builds a semantic search index for module discovery. It's the final step in the Brownfield Cartographer pipeline, transforming raw analysis data into actionable documentation.

## Features

### 1. CODEBASE.md Generation

Comprehensive architecture documentation with:
- **Architecture Overview**: Statistics and high-level summary
- **Critical Path**: Top 5 modules by PageRank (architectural hubs)
- **Data Sources & Sinks**: Entry/exit datasets for data flow understanding
- **Known Debt**: Dead code candidates and documentation drift
- **Recent Change Velocity**: High-churn modules (last 30 days)
- **Module Purpose Index**: Complete catalog grouped by domain

### 2. Onboarding Brief Generation

Quick-start guide for new engineers with:
- Five FDE Day-One Questions answers
- Next steps and action items
- Links to additional resources
- Generated from Semanticist's Day-One analysis

### 3. Semantic Index Building

Local semantic search with ChromaDB:
- **Embedding Model**: SentenceTransformer (all-MiniLM-L6-v2)
- **Runs Locally**: No API calls required
- **Indexed Data**: Module purpose statements
- **Metadata**: filepath, language, domain, pagerank, complexity, velocity
- **Use Case**: "Find modules related to authentication" → semantic search

## Usage

### Standalone Usage

```python
from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.archivist import Archivist

# Load or create knowledge graph
kg = KnowledgeGraph()
# ... populate graph ...

# Initialize Archivist
archivist = Archivist(kg)

# Generate CODEBASE.md
codebase_path = archivist.generate_CODEBASE_md(".cartography")
print(f"Generated: {codebase_path}")

# Generate onboarding brief (requires Day-One answers)
day_one_answers = "# FDE Day-One Analysis\n\n..."
brief_path = archivist.generate_onboarding_brief(day_one_answers, ".cartography")
print(f"Generated: {brief_path}")

# Build semantic index
index_path = archivist.build_semantic_index(".cartography")
print(f"Generated: {index_path}")
```

### Integrated Usage (via CLI)

```bash
# Full analysis with documentation
.venv/bin/python -m src.cli analyze --repo /path/to/repo

# With LLM analysis (includes semantic index)
.venv/bin/python -m src.cli analyze --repo /path/to/repo --llm
```

## Output Files

### Always Generated

**`.cartography/CODEBASE.md`**
- Comprehensive architecture documentation
- Generated from knowledge graph data
- Updated on every analysis run

**`.cartography/module_graph.json`**
- Raw knowledge graph data
- Programmatic access to all analysis results

### Generated with `--llm` Flag

**`.cartography/onboarding_brief.md`**
- Quick-start guide with Day-One Questions
- Generated from Semanticist's analysis

**`.cartography/semantic_index/`**
- ChromaDB collection directory
- Enables semantic search over modules
- Includes embeddings and metadata

## CODEBASE.md Structure

```markdown
# CODEBASE.md

**Generated**: 2026-03-13 03:17:24
**Total Modules**: 199
**Total Datasets**: 1,490

## Architecture Overview
- Statistics and summary

## Critical Path
1. src/orchestrator.py (PageRank: 0.0312)
2. src/graph/knowledge_graph.py (PageRank: 0.0289)
...

## Data Sources & Sinks
### Entry Datasets
- raw_users_table
- raw_orders_table

### Exit Datasets
- analytics_dashboard
- reporting_tables

## Known Debt
### Dead Code Candidates
- old_module.py (0 commits, PageRank: 0.0001)

### Documentation Drift
- auth_module.py - Docstring doesn't match implementation

## Recent Change Velocity
1. src/main.py - 45 commits
2. src/api.py - 32 commits
...

## Module Purpose Index
### Core (25 modules)
#### src/main.py
- **Language**: python
- **PageRank**: 0.0287
- **Purpose**: Main entry point...
```

## Semantic Search Example

```python
import chromadb

# Load semantic index
client = chromadb.PersistentClient(path=".cartography/semantic_index")
collection = client.get_collection("module_purposes")

# Search for modules
results = collection.query(
    query_texts=["authentication and user login"],
    n_results=5
)

# Print results
for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"{i+1}. {metadata['filepath']}")
    print(f"   Domain: {metadata['domain']}")
    print(f"   PageRank: {metadata['pagerank']:.4f}")
    print(f"   Purpose: {doc[:100]}...")
    print()
```

**Example Output**:
```
1. src/auth/login.py
   Domain: Authentication
   PageRank: 0.0234
   Purpose: Handles user authentication and session management...

2. src/auth/oauth.py
   Domain: Authentication
   PageRank: 0.0189
   Purpose: OAuth2 integration for third-party login providers...
```

## Integration with Orchestrator

The Archivist runs automatically at the end of the analysis pipeline:

```python
# In orchestrator.py
def run_cartographer(repo_path, incremental=False, enable_llm=False):
    # ... Surveyor, Hydrologist, Semanticist ...
    
    # Run Archivist (always)
    archivist = Archivist(kg)
    archivist.generate_CODEBASE_md(f"{repo_path}/.cartography")
    
    # Generate onboarding brief if Day-One answers available
    if day_one_answers:
        archivist.generate_onboarding_brief(day_one_answers, f"{repo_path}/.cartography")
    
    # Build semantic index if LLM analysis was run
    if enable_llm:
        archivist.build_semantic_index(f"{repo_path}/.cartography")
```

## Data Extraction Methods

The Archivist provides helper methods to extract data from the knowledge graph:

- `_get_all_modules()` - All module nodes
- `_get_all_datasets()` - All dataset nodes
- `_get_top_modules_by_pagerank(limit)` - Top N modules by PageRank
- `_get_entry_datasets()` - Data sources (no producers)
- `_get_exit_datasets()` - Data sinks (no consumers)
- `_get_high_velocity_modules(limit)` - High-churn modules
- `_get_dead_code_candidates()` - Modules with zero velocity
- `_get_drift_modules()` - Modules with documentation drift

## Performance

- **CODEBASE.md Generation**: ~1-2 seconds for 200 modules
- **Onboarding Brief**: <1 second (just formatting)
- **Semantic Index**: ~5-10 seconds for 200 modules (local embeddings)

## Dependencies

- **chromadb**: Vector database for semantic search
- **sentence-transformers**: Local embedding generation
- **all-MiniLM-L6-v2**: 384-dim embeddings, fast and accurate

## Use Cases

### 1. New Engineer Onboarding
- Read `onboarding_brief.md` for quick overview
- Review `CODEBASE.md` for detailed architecture
- Use semantic search to find relevant modules

### 2. Bug Investigation
- Check Module Purpose Index for relevant modules
- Review Critical Path for architectural dependencies
- Trace data flow from Sources to Sinks

### 3. Refactoring Planning
- Identify dead code candidates
- Find documentation drift
- Analyze change velocity for risk assessment

### 4. Module Discovery
- Semantic search: "Find modules handling payments"
- Filter by domain, PageRank, or complexity
- Explore related modules via knowledge graph

## Future Enhancements

- [ ] Add interactive HTML documentation
- [ ] Generate architecture diagrams (mermaid/graphviz)
- [ ] Add API documentation extraction
- [ ] Support custom documentation templates
- [ ] Add change history tracking
- [ ] Generate test coverage reports

## Conclusion

The Archivist transforms raw analysis data into actionable documentation, making brownfield codebases accessible to new engineers and enabling efficient module discovery through semantic search.

**Status**: ✅ Implemented and integrated  
**File**: `src/agents/archivist.py`  
**Commit**: `44e6002`  
**Output**: CODEBASE.md, onboarding_brief.md, semantic_index/
