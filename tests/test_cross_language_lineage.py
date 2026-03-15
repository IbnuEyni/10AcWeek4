"""
Integration test for cross-language lineage merging.

Tests that SQL, Python, and YAML-derived lineage are merged into one coherent graph.
"""

from pathlib import Path
from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.hydrologist import Hydrologist
from src.utils.tracer import CartographyTracer


def test_cross_language_lineage_merge(tmp_path):
    """Test that SQL, Python, and YAML lineage are merged correctly."""
    
    # Create test files
    sql_file = tmp_path / "transform.sql"
    sql_file.write_text("""
        SELECT * FROM raw.users
        WHERE created_at > '2024-01-01'
    """)
    
    python_file = tmp_path / "load_data.py"
    python_file.write_text("""
import pandas as pd

# Read from CSV
df = pd.read_csv('data/users.csv')

# Write to database
df.to_sql('raw.users', engine, if_exists='replace')
    """)
    
    yaml_file = tmp_path / "dbt_schema.yml"
    yaml_file.write_text("""
version: 2

sources:
  - name: raw
    tables:
      - name: users

models:
  - name: transformed_users
    """)
    
    # Initialize graph and hydrologist
    kg = KnowledgeGraph()
    tracer = CartographyTracer(str(tmp_path / "trace.jsonl"))
    hydrologist = Hydrologist(kg, tracer=tracer)
    
    # Run analysis
    hydrologist.run(str(tmp_path))
    
    # Verify nodes exist
    nodes = list(kg.graph.nodes(data=True))
    node_ids = [n[0] for n in nodes]
    
    # Check for dataset nodes
    assert any('users' in n for n in node_ids), "users dataset should exist"
    assert any('raw.users' in n for n in node_ids), "raw.users dataset should exist"
    
    # Check for transformation nodes
    assert any('transform.sql' in n for n in node_ids), "SQL transformation should exist"
    assert any('load_data.py' in n for n in node_ids), "Python transformation should exist"
    
    # Verify edges exist
    edges = list(kg.graph.edges(data=True))
    edge_types = [e[2].get('edge_type') for e in edges]
    
    assert 'PRODUCES' in edge_types, "Should have PRODUCES edges"
    assert 'CONSUMES' in edge_types, "Should have CONSUMES edges"
    
    # Verify edge metadata
    for source, target, data in edges:
        assert 'edge_type' in data, "Edge should have edge_type"
        assert 'transformation_type' in data, "Edge should have transformation_type"
        assert 'line_range' in data, "Edge should have line_range"
    
    # Verify trace log
    trace_summary = tracer.get_trace_summary()
    assert trace_summary['total_entries'] > 0, "Should have trace entries"
    assert 'Hydrologist' in trace_summary['agents'], "Hydrologist should be in trace"
    
    print(f"✓ Cross-language lineage test passed")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Edges: {len(edges)}")
    print(f"  Trace entries: {trace_summary['total_entries']}")


def test_unresolved_dynamics_logged(tmp_path):
    """Test that unresolved dynamic references are logged."""
    
    python_file = tmp_path / "dynamic.py"
    python_file.write_text("""
import pandas as pd

# Dynamic path (f-string)
table_name = 'users'
df = pd.read_sql(f'SELECT * FROM {table_name}', engine)

# Dynamic path (variable)
output_path = get_output_path()
df.to_csv(output_path)
    """)
    
    kg = KnowledgeGraph()
    tracer = CartographyTracer(str(tmp_path / "trace.jsonl"))
    hydrologist = Hydrologist(kg, tracer=tracer)
    
    hydrologist.run(str(tmp_path))
    
    # Check trace for unresolved dynamics
    trace_summary = tracer.get_trace_summary()
    assert 'unresolved_dynamic' in trace_summary['actions'], "Should log unresolved dynamics"
    
    print(f"✓ Unresolved dynamics test passed")


def test_edge_metadata_consistency(tmp_path):
    """Test that all edges have consistent metadata."""
    
    sql_file = tmp_path / "test.sql"
    sql_file.write_text("SELECT * FROM source_table")
    
    python_file = tmp_path / "test.py"
    python_file.write_text("import pandas as pd\ndf = pd.read_csv('data.csv')")
    
    kg = KnowledgeGraph()
    hydrologist = Hydrologist(kg)
    hydrologist.run(str(tmp_path))
    
    # Verify all edges have required metadata
    for source, target, data in kg.graph.edges(data=True):
        assert 'edge_type' in data, f"Edge {source}->{target} missing edge_type"
        assert 'transformation_type' in data, f"Edge {source}->{target} missing transformation_type"
        assert 'line_range' in data, f"Edge {source}->{target} missing line_range"
        
        # Verify line_range is a tuple
        assert isinstance(data['line_range'], tuple), f"line_range should be tuple, got {type(data['line_range'])}"
        assert len(data['line_range']) == 2, f"line_range should have 2 elements"
    
    print(f"✓ Edge metadata consistency test passed")


if __name__ == "__main__":
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        print("Running cross-language lineage tests...\n")
        
        test_cross_language_lineage_merge(tmp_path)
        print()
        
        test_unresolved_dynamics_logged(tmp_path)
        print()
        
        test_edge_metadata_consistency(tmp_path)
        print()
        
        print("✓ All tests passed!")
