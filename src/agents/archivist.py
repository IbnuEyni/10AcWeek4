"""
Archivist Agent - Documentation Generation and Semantic Indexing.

Generates comprehensive documentation from the knowledge graph and builds
a semantic search index for module discovery.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from src.graph.knowledge_graph import KnowledgeGraph


class Archivist:
    """
    Generates documentation and semantic indexes from the knowledge graph.
    
    Responsibilities:
    - Generate CODEBASE.md with architecture overview
    - Generate onboarding briefs for new engineers
    - Build semantic search index with ChromaDB
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize the Archivist agent.
        
        Args:
            knowledge_graph: The knowledge graph to document
        """
        self.kg = knowledge_graph
    
    def generate_CODEBASE_md(self, output_dir: str) -> str:
        """
        Generate CODEBASE.md with comprehensive architecture documentation.
        
        Sections:
        - Architecture Overview
        - Critical Path (top 5 by PageRank)
        - Data Sources & Sinks
        - Known Debt
        - Recent Change Velocity
        - Module Purpose Index
        
        Args:
            output_dir: Directory to write CODEBASE.md
        
        Returns:
            Path to generated CODEBASE.md file
        """
        output_path = Path(output_dir) / "CODEBASE.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("Archivist: Generating CODEBASE.md")
        print("="*60)
        
        # Gather data from knowledge graph
        modules = self._get_all_modules()
        datasets = self._get_all_datasets()
        top_modules = self._get_top_modules_by_pagerank(limit=5)
        entry_datasets = self._get_entry_datasets()
        exit_datasets = self._get_exit_datasets()
        high_velocity_modules = self._get_high_velocity_modules(limit=10)
        dead_code_candidates = self._get_dead_code_candidates()
        drift_modules = self._get_drift_modules()
        
        # Build markdown content
        content = self._build_codebase_markdown(
            modules=modules,
            datasets=datasets,
            top_modules=top_modules,
            entry_datasets=entry_datasets,
            exit_datasets=exit_datasets,
            high_velocity_modules=high_velocity_modules,
            dead_code_candidates=dead_code_candidates,
            drift_modules=drift_modules
        )
        
        # Write to file
        output_path.write_text(content, encoding="utf-8")
        
        print(f"✓ CODEBASE.md generated: {output_path}")
        print(f"  Total modules: {len(modules)}")
        print(f"  Total datasets: {len(datasets)}")
        print(f"  Critical modules: {len(top_modules)}")
        print(f"  High velocity: {len(high_velocity_modules)}")
        print(f"  Dead code candidates: {len(dead_code_candidates)}")
        
        return str(output_path)
    
    def generate_onboarding_brief(self, day_one_answers: str, output_dir: str) -> str:
        """
        Generate onboarding_brief.md from Day-One Questions answers.
        
        Args:
            day_one_answers: Markdown content with Day-One Questions answers
            output_dir: Directory to write onboarding_brief.md
        
        Returns:
            Path to generated onboarding_brief.md file
        """
        output_path = Path(output_dir) / "onboarding_brief.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("Archivist: Generating onboarding_brief.md")
        print("="*60)
        
        # Build onboarding brief with additional context
        content = self._build_onboarding_brief(day_one_answers)
        
        # Write to file
        output_path.write_text(content, encoding="utf-8")
        
        print(f"✓ onboarding_brief.md generated: {output_path}")
        
        return str(output_path)
    
    def build_semantic_index(self, output_dir: str) -> str:
        """
        Build semantic search index with ChromaDB.
        
        Creates a local ChromaDB collection with module purpose statements
        embedded using SentenceTransformer (all-MiniLM-L6-v2).
        
        Args:
            output_dir: Directory to store ChromaDB collection
        
        Returns:
            Path to ChromaDB collection directory
        """
        index_path = Path(output_dir) / "semantic_index"
        index_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "="*60)
        print("Archivist: Building Semantic Index")
        print("="*60)
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=str(index_path))
        
        # Create embedding function (runs locally)
        embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        collection_name = "module_purposes"
        try:
            # Delete existing collection if it exists
            client.delete_collection(name=collection_name)
        except:
            pass
        
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"description": "Module purpose statements for semantic search"}
        )
        
        # Gather modules with purpose statements
        modules_with_purpose = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module" and data.get("purpose_statement"):
                modules_with_purpose.append({
                    "id": node_id,
                    "path": data.get("path"),
                    "purpose": data.get("purpose_statement"),
                    "language": data.get("language", "unknown"),
                    "domain": data.get("domain_cluster", "unclustered"),
                    "pagerank": data.get("pagerank", 0.0),
                    "complexity": data.get("complexity_score", 0.0),
                    "velocity": data.get("change_velocity_30d", 0)
                })
        
        if not modules_with_purpose:
            print("⚠ No modules with purpose statements found")
            return str(index_path)
        
        print(f"Found {len(modules_with_purpose)} modules with purpose statements")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for module in modules_with_purpose:
            ids.append(module["id"])
            documents.append(module["purpose"])
            metadatas.append({
                "filepath": module["path"],
                "language": module["language"],
                "domain": module["domain"],
                "pagerank": float(module["pagerank"]),
                "complexity": float(module["complexity"]),
                "velocity": int(module["velocity"])
            })
        
        # Add to collection (ChromaDB will generate embeddings)
        print("Generating embeddings and indexing...")
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Semantic index built: {index_path}")
        print(f"  Indexed modules: {len(modules_with_purpose)}")
        print(f"  Collection: {collection_name}")
        print(f"  Embedding model: all-MiniLM-L6-v2 (local)")
        
        return str(index_path)
    
    # Helper methods for data extraction
    
    def _get_all_modules(self) -> List[Dict[str, Any]]:
        """Get all module nodes from the graph."""
        modules = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module":
                modules.append({
                    "id": node_id,
                    "path": data.get("path", node_id),
                    "language": data.get("language", "unknown"),
                    "purpose": data.get("purpose_statement", "No purpose statement"),
                    "domain": data.get("domain_cluster", "Unclustered"),
                    "pagerank": data.get("pagerank", 0.0) or 0.0,
                    "complexity": data.get("complexity_score", 0.0) or 0.0,
                    "velocity": data.get("change_velocity_30d", 0) or 0,
                    "is_dead_code": data.get("is_dead_code_candidate", False) or False,
                    "has_drift": data.get("has_documentation_drift", False) or False
                })
        return modules
    
    def _get_all_datasets(self) -> List[Dict[str, Any]]:
        """Get all dataset nodes from the graph."""
        datasets = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "dataset":
                datasets.append({
                    "id": node_id,
                    "name": data.get("name", node_id),
                    "storage_type": data.get("storage_type", "unknown"),
                    "path": data.get("path", "N/A")
                })
        return datasets
    
    def _get_top_modules_by_pagerank(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top N modules by PageRank score."""
        modules = self._get_all_modules()
        modules_with_pagerank = [m for m in modules if m["pagerank"] > 0]
        modules_with_pagerank.sort(key=lambda x: x["pagerank"], reverse=True)
        return modules_with_pagerank[:limit]
    
    def _get_entry_datasets(self) -> List[Dict[str, Any]]:
        """Get entry datasets (no incoming PRODUCES edges)."""
        entry_datasets = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "dataset":
                has_producers = any(
                    edge_data.get("edge_type") == "PRODUCES"
                    for _, _, edge_data in self.kg.graph.in_edges(node_id, data=True)
                )
                if not has_producers:
                    entry_datasets.append({
                        "id": node_id,
                        "name": data.get("name", node_id),
                        "path": data.get("path", "N/A")
                    })
        return entry_datasets
    
    def _get_exit_datasets(self) -> List[Dict[str, Any]]:
        """Get exit datasets (no outgoing CONSUMES edges)."""
        exit_datasets = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "dataset":
                has_consumers = any(
                    edge_data.get("edge_type") == "CONSUMES"
                    for _, _, edge_data in self.kg.graph.out_edges(node_id, data=True)
                )
                if not has_consumers:
                    exit_datasets.append({
                        "id": node_id,
                        "name": data.get("name", node_id),
                        "path": data.get("path", "N/A")
                    })
        return exit_datasets
    
    def _get_high_velocity_modules(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get modules with highest change velocity."""
        modules = self._get_all_modules()
        modules_with_velocity = [m for m in modules if m["velocity"] > 0]
        modules_with_velocity.sort(key=lambda x: x["velocity"], reverse=True)
        return modules_with_velocity[:limit]
    
    def _get_dead_code_candidates(self) -> List[Dict[str, Any]]:
        """Get modules marked as dead code candidates."""
        modules = self._get_all_modules()
        return [m for m in modules if m["is_dead_code"]]
    
    def _get_drift_modules(self) -> List[Dict[str, Any]]:
        """Get modules with documentation drift."""
        modules = self._get_all_modules()
        return [m for m in modules if m["has_drift"]]
    
    # Markdown generation methods
    
    def _build_codebase_markdown(
        self,
        modules: List[Dict[str, Any]],
        datasets: List[Dict[str, Any]],
        top_modules: List[Dict[str, Any]],
        entry_datasets: List[Dict[str, Any]],
        exit_datasets: List[Dict[str, Any]],
        high_velocity_modules: List[Dict[str, Any]],
        dead_code_candidates: List[Dict[str, Any]],
        drift_modules: List[Dict[str, Any]]
    ) -> str:
        """Build CODEBASE.md markdown content."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# CODEBASE.md

**Generated**: {timestamp}  
**Total Modules**: {len(modules)}  
**Total Datasets**: {len(datasets)}  
**Analysis Tool**: Brownfield Cartographer

---

## Architecture Overview

This codebase contains **{len(modules)} modules** and **{len(datasets)} datasets**. The architecture has been analyzed using static analysis, data lineage extraction, and semantic analysis.

### Statistics

- **Modules**: {len(modules)}
- **Datasets**: {len(datasets)}
- **Critical Modules** (top 5 by PageRank): {len(top_modules)}
- **Entry Datasets** (data sources): {len(entry_datasets)}
- **Exit Datasets** (data sinks): {len(exit_datasets)}
- **High Velocity Modules**: {len(high_velocity_modules)}
- **Dead Code Candidates**: {len(dead_code_candidates)}
- **Documentation Drift**: {len(drift_modules)}

---

## Critical Path

The following modules are architectural hubs (highest PageRank scores):

"""
        
        # Add top modules
        for i, module in enumerate(top_modules, 1):
            content += f"""### {i}. {module['path']}

- **PageRank**: {module['pagerank']:.4f}
- **Domain**: {module['domain']}
- **Complexity**: {module['complexity']:.1f}
- **Change Velocity**: {module['velocity']} commits (30d)
- **Purpose**: {module['purpose'][:200]}{'...' if len(module['purpose']) > 200 else ''}

"""
        
        content += """---

## Data Sources & Sinks

### Entry Datasets (Data Sources)

These datasets have no producers (external data sources):

"""
        
        # Add entry datasets
        if entry_datasets:
            for dataset in entry_datasets[:10]:
                content += f"- **{dataset['name']}** (`{dataset['path']}`)\n"
        else:
            content += "*No entry datasets identified*\n"
        
        content += """
### Exit Datasets (Data Sinks)

These datasets have no consumers (final outputs):

"""
        
        # Add exit datasets
        if exit_datasets:
            for dataset in exit_datasets[:10]:
                content += f"- **{dataset['name']}** (`{dataset['path']}`)\n"
        else:
            content += "*No exit datasets identified*\n"
        
        content += """
---

## Known Debt

### Dead Code Candidates

Modules with zero change velocity and low PageRank:

"""
        
        # Add dead code candidates
        if dead_code_candidates:
            for module in dead_code_candidates[:10]:
                content += f"- **{module['path']}** (Velocity: {module['velocity']}, PageRank: {module['pagerank']:.4f})\n"
        else:
            content += "*No dead code candidates identified*\n"
        
        content += """
### Documentation Drift

Modules where docstrings don't match implementation:

"""
        
        # Add drift modules
        if drift_modules:
            for module in drift_modules[:10]:
                content += f"- **{module['path']}** - {module['purpose'][:100]}...\n"
        else:
            content += "*No documentation drift detected*\n"
        
        content += """
---

## Recent Change Velocity

Modules with highest change frequency (last 30 days):

"""
        
        # Add high velocity modules
        if high_velocity_modules:
            for i, module in enumerate(high_velocity_modules, 1):
                content += f"{i}. **{module['path']}** - {module['velocity']} commits\n"
        else:
            content += "*No change velocity data available*\n"
        
        content += """
---

## Module Purpose Index

Complete index of all modules with purpose statements:

"""
        
        # Group modules by domain
        modules_by_domain = {}
        for module in modules:
            domain = module['domain']
            if domain not in modules_by_domain:
                modules_by_domain[domain] = []
            modules_by_domain[domain].append(module)
        
        # Add modules by domain
        for domain in sorted(modules_by_domain.keys()):
            domain_modules = modules_by_domain[domain]
            content += f"\n### {domain} ({len(domain_modules)} modules)\n\n"
            
            for module in sorted(domain_modules, key=lambda x: x['path']):
                content += f"#### {module['path']}\n\n"
                content += f"- **Language**: {module['language']}\n"
                content += f"- **PageRank**: {module['pagerank']:.4f}\n"
                content += f"- **Complexity**: {module['complexity']:.1f}\n"
                content += f"- **Velocity**: {module['velocity']} commits (30d)\n"
                content += f"- **Purpose**: {module['purpose']}\n\n"
        
        content += """
---

## How to Use This Document

1. **New Engineers**: Start with Architecture Overview and Critical Path
2. **Bug Fixes**: Check Module Purpose Index for relevant modules
3. **Refactoring**: Review Known Debt section for improvement opportunities
4. **Data Flow**: Trace from Data Sources through Critical Path to Data Sinks

**Generated by**: Brownfield Cartographer Archivist Agent  
**Last Updated**: {timestamp}
""".format(timestamp=timestamp)
        
        return content
    
    def _build_onboarding_brief(self, day_one_answers: str) -> str:
        """Build onboarding_brief.md markdown content."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Onboarding Brief

**Generated**: {timestamp}  
**Purpose**: Quick-start guide for new engineers  
**Source**: Brownfield Cartographer Day-One Analysis

---

## Welcome!

This brief provides answers to the Five FDE Day-One Questions to help you understand this codebase quickly.

---

{day_one_answers}

---

## Next Steps

1. **Read CODEBASE.md** for detailed architecture documentation
2. **Explore Critical Path** modules (highest PageRank)
3. **Set up local environment** following project README
4. **Review Recent Changes** to understand current development focus
5. **Ask questions** - the team is here to help!

---

## Additional Resources

- **CODEBASE.md**: Comprehensive architecture documentation
- **Module Purpose Index**: Complete module catalog with purposes
- **Semantic Search**: Query the semantic index for module discovery
- **Knowledge Graph**: `.cartography/module_graph.json` for programmatic access

---

**Generated by**: Brownfield Cartographer Archivist Agent  
**Last Updated**: {timestamp}
"""
        
        return content


# Example usage
if __name__ == "__main__":
    from src.graph.knowledge_graph import KnowledgeGraph
    from src.models.schema import ModuleNode
    
    # Create test graph
    kg = KnowledgeGraph()
    
    kg.add_module_node(ModuleNode(
        path="src/main.py",
        language="python",
        complexity_score=15.0,
        change_velocity_30d=10,
        is_dead_code_candidate=False,
        pagerank=0.05
    ))
    kg.graph.nodes["src/main.py"]["purpose_statement"] = "Main entry point for the application"
    kg.graph.nodes["src/main.py"]["domain_cluster"] = "Core"
    
    # Initialize Archivist
    archivist = Archivist(kg)
    
    # Generate CODEBASE.md
    codebase_path = archivist.generate_CODEBASE_md(".cartography")
    print(f"\nGenerated: {codebase_path}")
    
    # Generate onboarding brief
    day_one_answers = """# FDE Day-One Analysis

## 1. What does this system do?
This is a test system for demonstration purposes.

## 2. Where does the data come from?
Data comes from test sources.

## 3. Where does the data go?
Data goes to test destinations.

## 4. What are the critical paths?
src/main.py is the critical path.

## 5. What are the biggest risks?
No major risks identified in this test system.
"""
    
    brief_path = archivist.generate_onboarding_brief(day_one_answers, ".cartography")
    print(f"Generated: {brief_path}")
    
    # Build semantic index
    index_path = archivist.build_semantic_index(".cartography")
    print(f"Generated: {index_path}")
