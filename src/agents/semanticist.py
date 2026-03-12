"""
Semanticist Agent - LLM-Powered Semantic Analysis.

Generates purpose statements and detects documentation drift using LLMs.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from sklearn.cluster import KMeans
from litellm import embedding
from src.graph.knowledge_graph import KnowledgeGraph
from src.utils.llm_budget import ContextWindowBudget


class Semanticist:
    """
    Analyzes code semantics using LLMs to generate purpose statements
    and detect documentation drift.
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph):
        """
        Initialize the Semanticist agent.
        
        Args:
            knowledge_graph: The knowledge graph to enrich with semantic analysis
        """
        self.kg = knowledge_graph
        self.budget = ContextWindowBudget()
        self.analysis_results = {
            "modules_analyzed": 0,
            "modules_skipped": 0,
            "drift_detected": 0,
            "errors": 0
        }
    
    def generate_purpose_statements(self, repo_path: str):
        """
        Generate purpose statements for all modules in the knowledge graph.
        
        Iterates through all ModuleNodes, reads their source code, and uses
        an LLM to generate a business purpose statement and detect documentation drift.
        
        Args:
            repo_path: Path to repository root
        """
        repo = Path(repo_path)
        
        print("="*60)
        print("Semanticist: Generating Purpose Statements")
        print("="*60)
        
        # Find all module nodes
        module_nodes = [
            (node_id, data) 
            for node_id, data in self.kg.graph.nodes(data=True)
            if data.get("node_type") == "module"
        ]
        
        print(f"Semanticist: Found {len(module_nodes)} modules to analyze\n")
        
        for i, (node_id, node_data) in enumerate(module_nodes, 1):
            module_path = node_data.get("path")
            if not module_path:
                print(f"  [{i}/{len(module_nodes)}] Skipping node {node_id}: no path")
                self.analysis_results["modules_skipped"] += 1
                continue
            
            print(f"  [{i}/{len(module_nodes)}] Analyzing: {module_path}")
            
            try:
                # Read file content
                file_path = repo / module_path
                if not file_path.exists():
                    print(f"    ⚠ File not found: {file_path}")
                    self.analysis_results["modules_skipped"] += 1
                    continue
                
                code_content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Skip empty or very small files
                if len(code_content.strip()) < 50:
                    print(f"    ⚠ File too small, skipping")
                    self.analysis_results["modules_skipped"] += 1
                    continue
                
                # Truncate very large files to avoid token limits
                max_chars = 8000  # ~2000 tokens
                if len(code_content) > max_chars:
                    code_content = code_content[:max_chars] + "\n\n# ... (truncated)"
                    print(f"    ℹ File truncated to {max_chars} characters")
                
                # Generate purpose statement
                result = self._analyze_module(module_path, code_content)
                
                if result:
                    # Update node in graph
                    self.kg.graph.nodes[node_id]["purpose_statement"] = result["purpose"]
                    self.kg.graph.nodes[node_id]["has_documentation_drift"] = result["has_drift"]
                    
                    print(f"    ✓ Purpose: {result['purpose'][:80]}...")
                    if result["has_drift"]:
                        print(f"    ⚠ Documentation drift detected!")
                        self.analysis_results["drift_detected"] += 1
                    
                    self.analysis_results["modules_analyzed"] += 1
                else:
                    print(f"    ✗ Analysis failed")
                    self.analysis_results["errors"] += 1
            
            except Exception as e:
                print(f"    ✗ Error: {e}")
                self.analysis_results["errors"] += 1
        
        # Print summary
        print("\n" + "="*60)
        print("Semanticist: Analysis Summary")
        print("="*60)
        print(f"  Modules analyzed:        {self.analysis_results['modules_analyzed']}")
        print(f"  Modules skipped:         {self.analysis_results['modules_skipped']}")
        print(f"  Documentation drift:     {self.analysis_results['drift_detected']}")
        print(f"  Errors:                  {self.analysis_results['errors']}")
        print("="*60)
        
        # Print budget summary
        self.budget.print_summary()
    
    def _analyze_module(self, module_path: str, code_content: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a single module using LLM.
        
        Args:
            module_path: Relative path to module
            code_content: Source code content
        
        Returns:
            Dict with 'purpose' and 'has_drift' keys, or None on failure
        """
        # Extract existing docstring if present
        docstring = self._extract_docstring(code_content)
        
        # Construct prompt
        prompt = self._build_analysis_prompt(module_path, code_content, docstring)
        
        try:
            # Call LLM (cheap tier for bulk analysis)
            response = self.budget.call_llm(
                prompt=prompt,
                tier="cheap",
                max_tokens=300,
                temperature=0.3  # Lower temperature for more consistent output
            )
            
            # Parse response
            result = self._parse_llm_response(response)
            return result
        
        except Exception as e:
            print(f"      LLM call failed: {e}")
            return None
    
    def _extract_docstring(self, code_content: str) -> Optional[str]:
        """
        Extract module-level docstring from Python code.
        
        Args:
            code_content: Python source code
        
        Returns:
            Docstring text or None
        """
        # Match module-level docstring (first string literal)
        patterns = [
            r'^"""(.*?)"""',  # Triple double quotes
            r"^'''(.*?)'''",  # Triple single quotes
            r'^"(.*?)"',      # Single double quotes
            r"^'(.*?)'"       # Single single quotes
        ]
        
        for pattern in patterns:
            match = re.search(pattern, code_content.strip(), re.DOTALL | re.MULTILINE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _build_analysis_prompt(
        self, 
        module_path: str, 
        code_content: str, 
        docstring: Optional[str]
    ) -> str:
        """
        Build the LLM prompt for module analysis.
        
        Args:
            module_path: Relative path to module
            code_content: Source code
            docstring: Existing docstring (if any)
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this Python module and provide:

1. A 2-3 sentence business purpose statement describing what this module does and why it exists
2. Whether the existing docstring (if any) contradicts the actual code implementation

Module: {module_path}

Existing Docstring:
{docstring if docstring else "(No docstring found)"}

Code:
```python
{code_content}
```

Respond in JSON format:
{{
  "purpose": "2-3 sentence description of what this module does",
  "has_drift": true/false,
  "drift_reason": "explanation if drift detected, otherwise null"
}}

Focus on:
- What business problem does this solve?
- What are the key responsibilities?
- Does the docstring accurately describe the code?
"""
        return prompt
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response into structured data.
        
        Args:
            response: Raw LLM response text
        
        Returns:
            Dict with 'purpose' and 'has_drift' keys, or None on parse failure
        """
        try:
            # Try to extract JSON from response
            # LLMs sometimes wrap JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    # Fallback: treat entire response as purpose
                    return {
                        "purpose": response.strip()[:500],  # Limit length
                        "has_drift": False,
                        "drift_reason": None
                    }
            
            # Parse JSON
            data = json.loads(json_str)
            
            return {
                "purpose": data.get("purpose", "").strip(),
                "has_drift": bool(data.get("has_drift", False)),
                "drift_reason": data.get("drift_reason")
            }
        
        except json.JSONDecodeError as e:
            print(f"      JSON parse error: {e}")
            # Fallback: use raw response as purpose
            return {
                "purpose": response.strip()[:500],
                "has_drift": False,
                "drift_reason": None
            }
        except Exception as e:
            print(f"      Parse error: {e}")
            return None
    
    def get_modules_with_drift(self) -> list:
        """
        Get all modules with detected documentation drift.
        
        Returns:
            List of (module_path, purpose_statement) tuples
        """
        drift_modules = []
        
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module" and data.get("has_documentation_drift"):
                drift_modules.append((
                    data.get("path"),
                    data.get("purpose_statement")
                ))
        
        return drift_modules
    
    def print_drift_report(self):
        """Print a report of all modules with documentation drift."""
        drift_modules = self.get_modules_with_drift()
        
        if not drift_modules:
            print("\n✓ No documentation drift detected")
            return
        
        print("\n" + "="*60)
        print(f"Documentation Drift Report ({len(drift_modules)} modules)")
        print("="*60)
        
        for i, (path, purpose) in enumerate(drift_modules, 1):
            print(f"\n{i}. {path}")
            print(f"   Purpose: {purpose[:100]}...")
        
        print("\n" + "="*60)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of semantic analysis.
        
        Returns:
            Dict with analysis statistics and budget info
        """
        return {
            "analysis": self.analysis_results,
            "budget": self.budget.get_summary(),
            "drift_modules": len(self.get_modules_with_drift())
        }
    
    def cluster_into_domains(self, k: int = 5):
        """
        Cluster modules into business domains using embeddings and LLM.
        
        Uses vector embeddings of purpose statements to group similar modules,
        then asks an LLM to name each domain cluster.
        
        Args:
            k: Number of clusters (default: 5)
        """
        print("\n" + "="*60)
        print(f"Semanticist: Clustering Modules into {k} Domains")
        print("="*60)
        
        # Step 1: Extract all purpose statements from ModuleNodes
        modules_with_purpose = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module" and data.get("purpose_statement"):
                modules_with_purpose.append({
                    "node_id": node_id,
                    "path": data.get("path"),
                    "purpose": data.get("purpose_statement")
                })
        
        if len(modules_with_purpose) < k:
            print(f"\n⚠ Only {len(modules_with_purpose)} modules with purpose statements")
            print(f"  Need at least {k} modules for {k} clusters")
            print("  Skipping clustering.")
            return
        
        print(f"\nFound {len(modules_with_purpose)} modules with purpose statements")
        
        # Step 2: Get embeddings for each purpose statement
        print("\nGenerating embeddings...")
        embeddings_list = []
        
        for i, module in enumerate(modules_with_purpose, 1):
            try:
                # Get embedding using litellm
                response = embedding(
                    model="text-embedding-3-small",  # OpenAI's cheap embedding model
                    input=[module["purpose"]]
                )
                
                # Extract embedding vector
                embedding_vector = response.data[0]["embedding"]
                embeddings_list.append(embedding_vector)
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(modules_with_purpose)} embeddings generated")
            
            except Exception as e:
                print(f"  ✗ Error getting embedding for {module['path']}: {e}")
                # Use zero vector as fallback
                embeddings_list.append([0.0] * 1536)  # text-embedding-3-small dimension
        
        print(f"✓ Generated {len(embeddings_list)} embeddings")
        
        # Step 3: Cluster embeddings using KMeans
        print(f"\nClustering into {k} groups...")
        embeddings_array = np.array(embeddings_list)
        
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_array)
        
        # Step 4: Group purpose statements by cluster
        clusters = {i: [] for i in range(k)}
        for module, label in zip(modules_with_purpose, cluster_labels):
            module["cluster"] = int(label)
            clusters[label].append(module)
        
        print("✓ Clustering complete")
        print("\nCluster sizes:")
        for cluster_id, modules in clusters.items():
            print(f"  Cluster {cluster_id}: {len(modules)} modules")
        
        # Step 5: Generate domain names for each cluster
        print("\nGenerating domain names...")
        domain_names = {}
        
        for cluster_id, modules in clusters.items():
            print(f"\n  Cluster {cluster_id}:")
            
            # Build prompt with purpose statements
            purposes = [m["purpose"] for m in modules[:10]]  # Limit to 10 for token budget
            domain_name = self._generate_domain_name(cluster_id, purposes)
            
            if domain_name:
                domain_names[cluster_id] = domain_name
                print(f"    ✓ Domain: '{domain_name}'")
            else:
                domain_names[cluster_id] = f"Domain_{cluster_id}"
                print(f"    ⚠ Using fallback: 'Domain_{cluster_id}'")
        
        # Step 6: Update ModuleNode.domain_cluster in graph
        print("\nUpdating module domain clusters...")
        updated_count = 0
        
        for module in modules_with_purpose:
            cluster_id = module["cluster"]
            domain_name = domain_names.get(cluster_id, f"Domain_{cluster_id}")
            
            # Update node in graph
            node_id = module["node_id"]
            if self.kg.graph.has_node(node_id):
                self.kg.graph.nodes[node_id]["domain_cluster"] = domain_name
                updated_count += 1
        
        print(f"✓ Updated {updated_count} modules with domain clusters")
        
        # Print summary
        self._print_domain_summary(domain_names, clusters)
    
    def _generate_domain_name(self, cluster_id: int, purposes: List[str]) -> Optional[str]:
        """
        Generate a domain name for a cluster using LLM.
        
        Args:
            cluster_id: Cluster identifier
            purposes: List of purpose statements in this cluster
        
        Returns:
            1-2 word domain name, or None on failure
        """
        # Build prompt
        purposes_text = "\n".join([f"- {p[:150]}..." for p in purposes])
        
        prompt = f"""Analyze these module purposes and generate a 1-2 word Business Domain Name.

The domain name should capture the common theme or business function.

Examples of good domain names:
- "Data Ingestion"
- "API Serving"
- "Authentication"
- "Analytics"
- "Storage"
- "Orchestration"

Module purposes in this cluster:
{purposes_text}

Respond with ONLY the domain name (1-2 words, no explanation).
"""
        
        try:
            response = self.budget.call_llm(
                prompt=prompt,
                tier="cheap",
                max_tokens=20,
                temperature=0.3
            )
            
            # Clean up response
            domain_name = response.strip().strip('"').strip("'")
            
            # Validate it's short (1-3 words)
            words = domain_name.split()
            if len(words) <= 3:
                return domain_name
            else:
                # Take first 2 words if too long
                return " ".join(words[:2])
        
        except Exception as e:
            print(f"      LLM call failed: {e}")
            return None
    
    def _print_domain_summary(self, domain_names: Dict[int, str], clusters: Dict[int, List[Dict]]):
        """Print a summary of domain clustering results."""
        print("\n" + "="*60)
        print("Domain Clustering Summary")
        print("="*60)
        
        for cluster_id in sorted(domain_names.keys()):
            domain_name = domain_names[cluster_id]
            modules = clusters[cluster_id]
            
            print(f"\n{cluster_id + 1}. {domain_name} ({len(modules)} modules)")
            
            # Show first 3 modules as examples
            for module in modules[:3]:
                print(f"   - {module['path']}")
            
            if len(modules) > 3:
                print(f"   ... and {len(modules) - 3} more")
        
        print("\n" + "="*60)
    
    def get_domain_distribution(self) -> Dict[str, int]:
        """
        Get the distribution of modules across domains.
        
        Returns:
            Dict mapping domain names to module counts
        """
        distribution = {}
        
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module":
                domain = data.get("domain_cluster", "Unclustered")
                distribution[domain] = distribution.get(domain, 0) + 1
        
        return distribution
    
    def answer_day_one_questions(self) -> str:
        """
        Answer the Five FDE Day-One Questions using architectural context.
        
        Gathers:
        - Top 5 modules by PageRank (architectural hubs)
        - Entry/exit datasets (data sources and sinks)
        - Domain clusters (business domains)
        
        Uses expensive LLM tier to generate comprehensive answers with
        specific file paths and line numbers.
        
        Returns:
            Markdown string with answers to the five questions
        """
        print("\n" + "="*60)
        print("Semanticist: Answering FDE Day-One Questions")
        print("="*60)
        
        # Gather architectural context
        context = self._gather_architectural_context()
        
        # Build prompt
        prompt = self._build_day_one_prompt(context)
        
        print("\nCalling expensive LLM tier for comprehensive analysis...")
        
        try:
            # Call expensive LLM for high-quality analysis
            response = self.budget.call_llm(
                prompt=prompt,
                tier="expensive",
                max_tokens=1200,  # Reduced to fit credit limits
                temperature=0.4
            )
            
            print("✓ Analysis complete\n")
            return response
        
        except Exception as e:
            error_msg = f"Error generating Day-One answers: {e}"
            print(f"✗ {error_msg}\n")
            return f"# FDE Day-One Questions\n\n**Error:** {error_msg}"
    
    def _gather_architectural_context(self) -> Dict[str, Any]:
        """
        Gather architectural context from the knowledge graph.
        
        Returns:
            Dict with top_modules, entry_datasets, exit_datasets, domains
        """
        context = {
            "top_modules": [],
            "entry_datasets": [],
            "exit_datasets": [],
            "domains": {},
            "total_modules": 0,
            "total_datasets": 0
        }
        
        # Get top 5 modules by PageRank
        modules_with_pagerank = []
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "module":
                context["total_modules"] += 1
                pagerank = data.get("pagerank", 0.0)
                if pagerank > 0:
                    modules_with_pagerank.append({
                        "path": data.get("path"),
                        "pagerank": pagerank,
                        "purpose": data.get("purpose_statement", "No purpose statement"),
                        "domain": data.get("domain_cluster", "Unclustered")
                    })
        
        # Sort by PageRank and take top 5
        modules_with_pagerank.sort(key=lambda x: x["pagerank"], reverse=True)
        context["top_modules"] = modules_with_pagerank[:5]
        
        # Get entry datasets (no incoming PRODUCES edges)
        # Get exit datasets (no outgoing CONSUMES edges)
        for node_id, data in self.kg.graph.nodes(data=True):
            if data.get("node_type") == "dataset":
                context["total_datasets"] += 1
                
                # Check for incoming PRODUCES edges
                has_producers = any(
                    edge_data.get("edge_type") == "PRODUCES"
                    for _, _, edge_data in self.kg.graph.in_edges(node_id, data=True)
                )
                
                # Check for outgoing CONSUMES edges
                has_consumers = any(
                    edge_data.get("edge_type") == "CONSUMES"
                    for _, _, edge_data in self.kg.graph.out_edges(node_id, data=True)
                )
                
                dataset_info = {
                    "name": data.get("name", node_id),
                    "path": data.get("path", "N/A"),
                    "schema": data.get("schema", "Unknown")
                }
                
                if not has_producers:
                    context["entry_datasets"].append(dataset_info)
                
                if not has_consumers:
                    context["exit_datasets"].append(dataset_info)
        
        # Get domain distribution
        context["domains"] = self.get_domain_distribution()
        
        return context
    
    def _build_day_one_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build the prompt for answering Day-One questions.
        
        Args:
            context: Architectural context from knowledge graph
        
        Returns:
            Formatted prompt string
        """
        # Format top modules
        top_modules_text = "\n".join([
            f"{i+1}. {m['path']} (PageRank: {m['pagerank']:.4f}, Domain: {m['domain']})\n   Purpose: {m['purpose']}"
            for i, m in enumerate(context["top_modules"])
        ])
        
        # Format entry datasets
        entry_datasets_text = "\n".join([
            f"- {d['name']} (Schema: {d['schema']}, Path: {d['path']})"
            for d in context["entry_datasets"][:10]  # Limit to 10
        ]) or "None identified"
        
        # Format exit datasets
        exit_datasets_text = "\n".join([
            f"- {d['name']} (Schema: {d['schema']}, Path: {d['path']})"
            for d in context["exit_datasets"][:10]  # Limit to 10
        ]) or "None identified"
        
        # Format domains
        domains_text = "\n".join([
            f"- {domain}: {count} modules"
            for domain, count in sorted(context["domains"].items(), key=lambda x: x[1], reverse=True)
        ]) or "No domains identified"
        
        prompt = f"""You are a Forward Deployed Engineer analyzing a new codebase on Day One.

Answer the Five FDE Day-One Questions clearly and concisely, citing specific file paths from the architectural context below.

## THE FIVE FDE DAY-ONE QUESTIONS:

1. **What does this system do?** (Business purpose in 2-3 sentences)
2. **Where does the data come from?** (Entry points and data sources)
3. **Where does the data go?** (Exit points and data sinks)
4. **What are the critical paths?** (Most important modules/flows)
5. **What are the biggest risks?** (Technical debt, bottlenecks, failure points)

## ARCHITECTURAL CONTEXT:

### Repository Statistics:
- Total Modules: {context['total_modules']}
- Total Datasets: {context['total_datasets']}

### Top 5 Architectural Hubs (by PageRank):
{top_modules_text}

### Entry Datasets (Data Sources):
{entry_datasets_text}

### Exit Datasets (Data Sinks):
{exit_datasets_text}

### Business Domains:
{domains_text}

## INSTRUCTIONS:

- Answer each question with 2-4 sentences
- Cite specific file paths (e.g., "src/cli.py", "models/customers.sql")
- Be concrete and actionable
- Focus on what an FDE needs to know on Day One
- Use markdown formatting

Respond in this format:

# FDE Day-One Analysis

## 1. What does this system do?
[Your answer with file citations]

## 2. Where does the data come from?
[Your answer with file citations]

## 3. Where does the data go?
[Your answer with file citations]

## 4. What are the critical paths?
[Your answer with file citations]

## 5. What are the biggest risks?
[Your answer with file citations]
"""
        
        return prompt


# Example usage
if __name__ == "__main__":
    from src.graph.knowledge_graph import KnowledgeGraph
    from src.agents.surveyor import Surveyor
    
    # Initialize graph and run surveyor first
    kg = KnowledgeGraph()
    surveyor = Surveyor(kg)
    surveyor.run(".")
    
    # Run semanticist
    semanticist = Semanticist(kg)
    semanticist.generate_purpose_statements(".")
    
    # Cluster into domains
    semanticist.cluster_into_domains(k=5)
    
    # Print drift report
    semanticist.print_drift_report()
    
    # Print domain distribution
    distribution = semanticist.get_domain_distribution()
    print("\nDomain Distribution:")
    for domain, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count} modules")


# Example usage
if __name__ == "__main__":
    from src.graph.knowledge_graph import KnowledgeGraph
    from src.agents.surveyor import Surveyor
    
    # Initialize graph and run surveyor first
    kg = KnowledgeGraph()
    surveyor = Surveyor(kg)
    surveyor.run(".")
    
    # Run semanticist
    semanticist = Semanticist(kg)
    semanticist.generate_purpose_statements(".")
    
    # Cluster into domains
    semanticist.cluster_into_domains(k=5)
    
    # Print drift report
    semanticist.print_drift_report()
    
    # Print domain distribution
    distribution = semanticist.get_domain_distribution()
    print("\nDomain Distribution:")
    for domain, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count} modules")
