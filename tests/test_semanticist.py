"""
Test Semanticist Agent - LLM-Powered Semantic Analysis.

Run this to test purpose statement generation and drift detection.
"""

import os
from pathlib import Path
from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.surveyor import Surveyor
from src.agents.semanticist import Semanticist


def test_semanticist_basic():
    """Test basic Semanticist functionality."""
    print("\n" + "="*60)
    print("TEST: Semanticist Basic Functionality")
    print("="*60)
    
    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n⚠ OPENROUTER_API_KEY not set")
        print("Set it with: export OPENROUTER_API_KEY='your-key'")
        return
    
    # Initialize graph
    kg = KnowledgeGraph()
    
    # Run surveyor first to populate graph
    print("\n1. Running Surveyor to populate graph...")
    surveyor = Surveyor(kg)
    surveyor.run(".")
    
    module_count = sum(1 for _, data in kg.graph.nodes(data=True) if data.get("node_type") == "module")
    print(f"   Found {module_count} modules")
    
    # Run semanticist
    print("\n2. Running Semanticist for semantic analysis...")
    semanticist = Semanticist(kg)
    semanticist.generate_purpose_statements(".")
    
    # Print results
    print("\n3. Analysis Results:")
    summary = semanticist.get_analysis_summary()
    print(f"   Modules analyzed: {summary['analysis']['modules_analyzed']}")
    print(f"   Modules skipped: {summary['analysis']['modules_skipped']}")
    print(f"   Drift detected: {summary['analysis']['drift_detected']}")
    print(f"   Total cost: ${summary['budget']['total_cost']:.4f}")
    
    # Show some purpose statements
    print("\n4. Sample Purpose Statements:")
    count = 0
    for node_id, data in kg.graph.nodes(data=True):
        if data.get("node_type") == "module" and data.get("purpose_statement"):
            print(f"\n   Module: {data.get('path')}")
            print(f"   Purpose: {data.get('purpose_statement')[:150]}...")
            count += 1
            if count >= 3:
                break
    
    # Print drift report
    semanticist.print_drift_report()


def test_docstring_extraction():
    """Test docstring extraction."""
    print("\n" + "="*60)
    print("TEST: Docstring Extraction")
    print("="*60)
    
    kg = KnowledgeGraph()
    semanticist = Semanticist(kg)
    
    test_cases = [
        ('"""This is a module docstring."""\n\ndef foo():\n    pass', "This is a module docstring."),
        ("'''Single quote docstring'''\n\nclass Bar:\n    pass", "Single quote docstring"),
        ("# Just a comment\n\ndef baz():\n    pass", None),
        ('"""Multi-line\ndocstring\nhere"""', "Multi-line\ndocstring\nhere"),
    ]
    
    for i, (code, expected) in enumerate(test_cases, 1):
        result = semanticist._extract_docstring(code)
        status = "✓" if result == expected else "✗"
        print(f"\n{i}. {status} Expected: {expected}")
        print(f"   Got: {result}")


def test_response_parsing():
    """Test LLM response parsing."""
    print("\n" + "="*60)
    print("TEST: Response Parsing")
    print("="*60)
    
    kg = KnowledgeGraph()
    semanticist = Semanticist(kg)
    
    test_responses = [
        # JSON in code block
        '''```json
{
  "purpose": "This module handles user authentication",
  "has_drift": false,
  "drift_reason": null
}
```''',
        # Plain JSON
        '{"purpose": "Data processing module", "has_drift": true, "drift_reason": "Docstring mentions API but code does file I/O"}',
        # Plain text (fallback)
        "This module provides utility functions for string manipulation and validation.",
    ]
    
    for i, response in enumerate(test_responses, 1):
        result = semanticist._parse_llm_response(response)
        print(f"\n{i}. Response type: {'JSON' if '{' in response else 'Plain text'}")
        print(f"   Purpose: {result['purpose'][:80]}...")
        print(f"   Has drift: {result['has_drift']}")


def test_small_repo():
    """Test on a small subset of files."""
    print("\n" + "="*60)
    print("TEST: Small Repository Analysis")
    print("="*60)
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n⚠ OPENROUTER_API_KEY not set - skipping")
        return
    
    # Create a minimal graph with just a few modules
    kg = KnowledgeGraph()
    
    # Manually add a few test modules
    from src.models.schema import ModuleNode
    
    test_modules = [
        "src/cli.py",
        "src/orchestrator.py",
        "src/graph/knowledge_graph.py"
    ]
    
    for module_path in test_modules:
        if Path(module_path).exists():
            node = ModuleNode(
                path=module_path,
                language="python",
                complexity_score=1.0,
                change_velocity_30d=0,
                is_dead_code_candidate=False
            )
            kg.add_module_node(node)
    
    print(f"\nAdded {len(test_modules)} test modules")
    
    # Run semanticist
    semanticist = Semanticist(kg)
    semanticist.generate_purpose_statements(".")
    
    # Show results
    print("\nResults:")
    for node_id, data in kg.graph.nodes(data=True):
        if data.get("purpose_statement"):
            print(f"\n  {data.get('path')}:")
            print(f"  {data.get('purpose_statement')}")


def test_domain_clustering():
    """Test domain clustering functionality."""
    print("\n" + "="*60)
    print("TEST: Domain Clustering")
    print("="*60)
    
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n⚠ OPENROUTER_API_KEY not set - skipping")
        return
    
    # Initialize graph
    kg = KnowledgeGraph()
    
    # Run surveyor first
    print("\n1. Running Surveyor...")
    from src.agents.surveyor import Surveyor
    surveyor = Surveyor(kg)
    surveyor.run(".")
    
    # Run semanticist to generate purpose statements
    print("\n2. Generating purpose statements...")
    semanticist = Semanticist(kg)
    semanticist.generate_purpose_statements(".")
    
    # Cluster into domains
    print("\n3. Clustering into domains...")
    semanticist.cluster_into_domains(k=3)  # Use k=3 for small test
    
    # Show domain distribution
    print("\n4. Domain Distribution:")
    distribution = semanticist.get_domain_distribution()
    for domain, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"   {domain}: {count} modules")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Semanticist Agent - Test Suite")
    print("="*60)
    
    # Test 1: Docstring extraction (no API key needed)
    test_docstring_extraction()
    
    # Test 2: Response parsing (no API key needed)
    test_response_parsing()
    
    # Test 3-4: LLM tests (require API key)
    if os.getenv("OPENROUTER_API_KEY"):
        print("\n✓ OPENROUTER_API_KEY found - running LLM tests")
        test_small_repo()
        # test_domain_clustering()  # Uncomment for full clustering test
        # test_semanticist_basic()  # Uncomment for full test
    else:
        print("\n⚠ OPENROUTER_API_KEY not set - skipping LLM tests")
        print("To run LLM tests, set: export OPENROUTER_API_KEY='your-key'")
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)


if __name__ == "__main__":
    main()
