from pathlib import Path
from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.surveyor import Surveyor
from src.agents.hydrologist import Hydrologist
from src.agents.semanticist import Semanticist
from src.utils.incremental import IncrementalTracker


def run_cartographer(repo_path: str, incremental: bool = False, enable_llm: bool = False):
    """
    Run the Brownfield Cartographer analysis pipeline.
    
    Args:
        repo_path: Path to repository root
        incremental: If True, only analyze changed files since last run
        enable_llm: If True, run Semanticist agent for LLM-powered analysis
    """""
    repo = Path(repo_path)
    
    print("="*60)
    print("Brownfield Cartographer - Codebase Intelligence System")
    print("="*60)
    print(f"Repository: {repo}")
    print(f"Mode: {'Incremental' if incremental else 'Full'} Analysis\n")
    
    # Initialize incremental tracker
    tracker = None
    changed_files = None
    if incremental:
        tracker = IncrementalTracker(str(repo))
        changed_files = tracker.get_changed_files()
        
        if not changed_files:
            print("No changes detected since last analysis. Skipping.")
            return
        
        print(f"Analyzing {len(changed_files)} changed files...\n")
    
    # Initialize Knowledge Graph
    kg = KnowledgeGraph()
    
    # Run Surveyor Agent (Static Analysis)
    print("\n" + "="*60)
    surveyor = Surveyor(kg)
    if incremental and changed_files:
        surveyor.run(str(repo), changed_files=changed_files)
    else:
        surveyor.run(str(repo))
    
    # Run Hydrologist Agent (Data Lineage)
    print("\n" + "="*60)
    hydrologist = Hydrologist(kg)
    if incremental and changed_files:
        hydrologist.run(str(repo), changed_files=changed_files)
    else:
        hydrologist.run(str(repo))
    
    # Run Semanticist Agent (LLM-Powered Semantic Analysis) - Optional
    if enable_llm:
        print("\n" + "="*60)
        semanticist = Semanticist(kg)
        semanticist.generate_purpose_statements(str(repo))
        
        # Cluster into domains
        semanticist.cluster_into_domains(k=5)
        
        # Answer Day-One Questions
        day_one_answers = semanticist.answer_day_one_questions()
        
        # Save Day-One answers
        day_one_path = repo / ".cartography" / "day_one_questions.md"
        day_one_path.write_text(day_one_answers, encoding='utf-8')
        print(f"✓ Day-One answers saved to: {day_one_path}")
        
        # Print reports
        semanticist.print_drift_report()
    
    # Save results
    print("\n" + "="*60)
    print("Saving results...")
    
    # Save module graph (includes all nodes and edges)
    module_graph_path = repo / ".cartography" / "module_graph.json"
    kg.serialize_to_json(str(module_graph_path))
    print(f"✓ Module graph saved to: {module_graph_path}")
    
    # Save lineage graph (same graph, different name for clarity)
    lineage_graph_path = repo / ".cartography" / "lineage_graph.json"
    kg.serialize_to_json(str(lineage_graph_path))
    print(f"✓ Lineage graph saved to: {lineage_graph_path}")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("Analysis Summary:")
    print(f"  Total nodes: {kg.graph.number_of_nodes()}")
    print(f"  Total edges: {kg.graph.number_of_edges()}")
    
    # Count by node type
    node_types = {}
    for node, data in kg.graph.nodes(data=True):
        node_type = data.get("node_type", "unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print("\n  Nodes by type:")
    for node_type, count in sorted(node_types.items()):
        print(f"    {node_type}: {count}")
    
    # Count by edge type
    edge_types = {}
    for source, target, data in kg.graph.edges(data=True):
        edge_type = data.get("edge_type", "unknown")
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    print("\n  Edges by type:")
    for edge_type, count in sorted(edge_types.items()):
        print(f"    {edge_type}: {count}")
    
    # Save incremental state if enabled
    if incremental and tracker:
        tracker.save_state()
    
    print("\n" + "="*60)
    print("✓ Cartography complete!")
    print("="*60)
