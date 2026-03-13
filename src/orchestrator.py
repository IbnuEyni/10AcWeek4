from pathlib import Path
from src.graph.knowledge_graph import KnowledgeGraph
from src.agents.surveyor import Surveyor
from src.agents.hydrologist import Hydrologist
from src.agents.semanticist import Semanticist
from src.agents.archivist import Archivist
from src.utils.incremental import IncrementalTracker
from src.utils.tracer import CartographyTracer
import time


def run_cartographer(repo_path: str, incremental: bool = False, enable_llm: bool = False):
    """
    Run the Brownfield Cartographer analysis pipeline.
    
    Args:
        repo_path: Path to repository root
        incremental: If True, only analyze changed files since last run
        enable_llm: If True, run Semanticist agent for LLM-powered analysis
    """
    repo = Path(repo_path)
    
    # Initialize tracer
    tracer = CartographyTracer(str(repo / ".cartography" / "cartography_trace.jsonl"))
    tracer.log_action(
        agent="Orchestrator",
        action="start_analysis",
        target=str(repo),
        evidence=f"Mode: {'Incremental' if incremental else 'Full'}, LLM: {enable_llm}",
        confidence="1.0"
    )
    
    # Performance tracking
    start_time = time.time()
    timings = {}
    
    print("="*60)
    print("Brownfield Cartographer - Codebase Intelligence System")
    print("="*60)
    print(f"Repository: {repo}")
    print(f"Mode: {'Incremental' if incremental else 'Full'} Analysis\n")
    
    # Initialize incremental tracker
    tracker = None
    changed_files = None
    if incremental:
        tracker_start = time.time()
        tracker = IncrementalTracker(str(repo))
        changed_files = tracker.get_changed_files()
        timings['incremental_tracker'] = time.time() - tracker_start
        
        tracer.log_action(
            agent="IncrementalTracker",
            action="detect_changes",
            target=str(repo),
            evidence=f"Found {len(changed_files)} changed files",
            confidence="1.0"
        )
        
        if not changed_files:
            print("No changes detected since last analysis. Skipping.")
            tracer.log_action(
                agent="Orchestrator",
                action="skip_analysis",
                target=str(repo),
                evidence="No changes detected",
                confidence="1.0"
            )
            return
        
        print(f"Analyzing {len(changed_files)} changed files...\n")
    
    # Initialize Knowledge Graph
    kg = KnowledgeGraph()
    tracer.log_action(
        agent="Orchestrator",
        action="initialize_graph",
        target="KnowledgeGraph",
        evidence="Created empty NetworkX DiGraph",
        confidence="1.0"
    )
    
    # Run Surveyor Agent (Static Analysis)
    print("\n" + "="*60)
    surveyor_start = time.time()
    surveyor = Surveyor(kg, tracer=tracer)
    if incremental and changed_files:
        surveyor.run(str(repo), changed_files=changed_files)
    else:
        surveyor.run(str(repo))
    timings['surveyor'] = time.time() - surveyor_start
    
    # Run Hydrologist Agent (Data Lineage)
    print("\n" + "="*60)
    hydrologist_start = time.time()
    hydrologist = Hydrologist(kg, tracer=tracer)
    if incremental and changed_files:
        hydrologist.run(str(repo), changed_files=changed_files)
    else:
        hydrologist.run(str(repo))
    timings['hydrologist'] = time.time() - hydrologist_start
    
    # Run Semanticist Agent (LLM-Powered Semantic Analysis) - Optional
    day_one_answers = None
    if enable_llm:
        print("\n" + "="*60)
        semanticist_start = time.time()
        semanticist = Semanticist(kg, tracer=tracer)
        semanticist.generate_purpose_statements(str(repo))
        
        # Cluster into domains
        semanticist.cluster_into_domains(k=5)
        
        # Answer Day-One Questions
        day_one_answers = semanticist.answer_day_one_questions()
        timings['semanticist'] = time.time() - semanticist_start
        
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
    
    # Run Archivist Agent (Documentation Generation)
    print("\n" + "="*60)
    print("Archivist: Generating Documentation")
    print("="*60)
    
    archivist_start = time.time()
    archivist = Archivist(kg, tracer=tracer)
    
    # Always generate CODEBASE.md (works with or without LLM)
    try:
        codebase_path = archivist.generate_CODEBASE_md(str(repo / ".cartography"))
        print(f"\n✓ CODEBASE.md generated: {codebase_path}")
        tracer.log_action(
            agent="Archivist",
            action="generate_codebase_md",
            target=str(codebase_path),
            evidence=f"Generated documentation for {kg.graph.number_of_nodes()} nodes",
            confidence="1.0"
        )
    except Exception as e:
        print(f"\n✗ Error generating CODEBASE.md: {e}")
        tracer.log_error(
            agent="Archivist",
            action="generate_codebase_md",
            target="CODEBASE.md",
            error_message=str(e)
        )
    
    # Generate onboarding brief if Day-One answers available
    if day_one_answers:
        try:
            brief_path = archivist.generate_onboarding_brief(
                day_one_answers,
                str(repo / ".cartography")
            )
            print(f"✓ onboarding_brief.md generated: {brief_path}")
            tracer.log_action(
                agent="Archivist",
                action="generate_onboarding_brief",
                target=str(brief_path),
                evidence="Generated FDE Day-One onboarding brief",
                confidence="1.0"
            )
        except Exception as e:
            print(f"✗ Error generating onboarding_brief.md: {e}")
            tracer.log_error(
                agent="Archivist",
                action="generate_onboarding_brief",
                target="onboarding_brief.md",
                error_message=str(e)
            )
    
    # Build semantic index if LLM analysis was run
    if enable_llm:
        try:
            index_path = archivist.build_semantic_index(str(repo / ".cartography"))
            print(f"✓ Semantic index built: {index_path}")
            tracer.log_action(
                agent="Archivist",
                action="build_semantic_index",
                target=str(index_path),
                evidence="Built ChromaDB semantic search index",
                confidence="1.0"
            )
        except Exception as e:
            print(f"✗ Error building semantic index: {e}")
            tracer.log_error(
                agent="Archivist",
                action="build_semantic_index",
                target="semantic_index",
                error_message=str(e)
            )
    
    timings['archivist'] = time.time() - archivist_start
    
    # Print performance summary
    total_time = time.time() - start_time
    timings['total'] = total_time
    
    print("\n" + "="*60)
    print("Performance Summary")
    print("="*60)
    for component, duration in sorted(timings.items()):
        print(f"  {component:25} {duration:8.2f}s")
    
    tracer.log_action(
        agent="Orchestrator",
        action="complete_analysis",
        target=str(repo),
        evidence=f"Total time: {total_time:.2f}s, Nodes: {kg.graph.number_of_nodes()}, Edges: {kg.graph.number_of_edges()}",
        confidence="1.0"
    )
    
    print("\n" + "="*60)
    print("✓ Cartography complete!")
    print("="*60)
    print(f"\nTrace file: {repo / '.cartography' / 'cartography_trace.jsonl'}")
    tracer.print_summary()
