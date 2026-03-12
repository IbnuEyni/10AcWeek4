"""
Tests for Day-One Questions feature in Semanticist agent.
"""

from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.semanticist import Semanticist
from src.models.schema import ModuleNode, DatasetNode, ConsumesEdge, ProducesEdge


def test_gather_architectural_context():
    """Test gathering architectural context from knowledge graph."""
    kg = KnowledgeGraph()
    
    # Add modules with PageRank
    kg.add_module_node(ModuleNode(
        path="src/main.py",
        language="python",
        complexity_score=10.0,
        change_velocity_30d=5,
        is_dead_code_candidate=False,
        pagerank=0.05
    ))
    kg.graph.nodes["src/main.py"]["purpose_statement"] = "Main entry point"
    kg.graph.nodes["src/main.py"]["domain_cluster"] = "Core"
    
    kg.add_module_node(ModuleNode(
        path="src/utils.py",
        language="python",
        complexity_score=5.0,
        change_velocity_30d=2,
        is_dead_code_candidate=False,
        pagerank=0.03
    ))
    kg.graph.nodes["src/utils.py"]["purpose_statement"] = "Utility functions"
    kg.graph.nodes["src/utils.py"]["domain_cluster"] = "Core"
    
    # Add datasets
    kg.add_dataset_node(DatasetNode(
        name="users_table",
        storage_type="table",
        schema_snapshot={"schema": "public", "path": "models/users.sql"}
    ))
    
    kg.add_dataset_node(DatasetNode(
        name="output_table",
        storage_type="table",
        schema_snapshot={"schema": "analytics", "path": "models/output.sql"}
    ))
    
    # Add edges to define entry/exit
    kg.add_consumes_edge(ConsumesEdge(source="src/main.py", target="users_table"))
    kg.add_produces_edge(ProducesEdge(source="src/main.py", target="output_table"))
    
    # Test context gathering
    semanticist = Semanticist(kg)
    context = semanticist._gather_architectural_context()
    
    # Basic assertions
    assert context["total_modules"] == 2
    assert context["total_datasets"] == 2
    assert "Core" in context["domains"]
    assert context["domains"]["Core"] == 2
    print("✓ test_gather_architectural_context passed")


def test_build_day_one_prompt():
    """Test building the Day-One questions prompt."""
    kg = KnowledgeGraph()
    semanticist = Semanticist(kg)
    
    context = {
        "top_modules": [
            {
                "path": "src/main.py",
                "pagerank": 0.05,
                "purpose": "Main entry point",
                "domain": "Core"
            }
        ],
        "entry_datasets": [
            {"name": "users", "schema": "public", "path": "models/users.sql"}
        ],
        "exit_datasets": [
            {"name": "output", "schema": "analytics", "path": "models/output.sql"}
        ],
        "domains": {"Core": 5, "Analytics": 3},
        "total_modules": 8,
        "total_datasets": 10
    }
    
    prompt = semanticist._build_day_one_prompt(context)
    
    # Verify prompt contains key elements
    assert "Five FDE Day-One Questions" in prompt
    assert "What does this system do?" in prompt
    assert "Where does the data come from?" in prompt
    assert "Where does the data go?" in prompt
    assert "What are the critical paths?" in prompt
    assert "What are the biggest risks?" in prompt
    assert "src/main.py" in prompt
    assert "PageRank: 0.0500" in prompt
    assert "users" in prompt
    assert "output" in prompt
    assert "Total Modules: 8" in prompt
    assert "Total Datasets: 10" in prompt
    print("✓ test_build_day_one_prompt passed")


def test_answer_day_one_questions_structure():
    """Test that answer_day_one_questions returns markdown string."""
    kg = KnowledgeGraph()
    
    # Add minimal data
    kg.add_module_node(ModuleNode(
        path="src/main.py",
        language="python",
        complexity_score=10.0,
        change_velocity_30d=5,
        is_dead_code_candidate=False,
        pagerank=0.05
    ))
    kg.graph.nodes["src/main.py"]["purpose_statement"] = "Main entry point"
    
    semanticist = Semanticist(kg)
    
    # Mock the LLM call to avoid actual API calls in tests
    def mock_call_llm(prompt, tier, max_tokens, temperature):
        return """# FDE Day-One Analysis

## 1. What does this system do?
This is a test system.

## 2. Where does the data come from?
From test sources.

## 3. Where does the data go?
To test destinations.

## 4. What are the critical paths?
src/main.py is critical.

## 5. What are the biggest risks?
No major risks identified.
"""
    
    semanticist.budget.call_llm = mock_call_llm
    
    result = semanticist.answer_day_one_questions()
    
    assert isinstance(result, str)
    assert "# FDE Day-One Analysis" in result
    assert "What does this system do?" in result
    assert "Where does the data come from?" in result
    assert "Where does the data go?" in result
    assert "What are the critical paths?" in result
    assert "What are the biggest risks?" in result
    print("✓ test_answer_day_one_questions_structure passed")


if __name__ == "__main__":
    print("Running Day-One Questions tests...\n")
    test_gather_architectural_context()
    test_build_day_one_prompt()
    test_answer_day_one_questions_structure()
    print("\n✓ All tests passed!")
