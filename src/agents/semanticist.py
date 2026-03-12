"""
Semanticist Agent - LLM-Powered Semantic Analysis.

Generates purpose statements and detects documentation drift using LLMs.
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
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
    
    # Print drift report
    semanticist.print_drift_report()
