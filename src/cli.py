import argparse
from pathlib import Path
from dotenv import load_dotenv
from src.orchestrator import run_cartographer

# Load environment variables from .env file
load_dotenv()


def query_command(args):
    """Handle the query command for interactive agent queries."""
    from src.graph.knowledge_graph import KnowledgeGraph
    from src.agents.navigator import create_navigator_agent
    import json
    
    repo_path = Path(args.repo).resolve()
    cartography_dir = repo_path / ".cartography"
    graph_file = cartography_dir / "module_graph.json"
    semantic_index_path = str(cartography_dir / "semantic_index")
    
    if not graph_file.exists():
        print(f"Error: No analysis found. Run 'analyze' first.")
        print(f"Expected: {graph_file}")
        return 1
    
    # Load knowledge graph
    print(f"Loading knowledge graph from {graph_file}...")
    kg = KnowledgeGraph()
    with open(graph_file, "r") as f:
        graph_data = json.load(f)
    
    # Reconstruct graph
    for node in graph_data.get("nodes", []):
        kg.graph.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    
    for link in graph_data.get("links", []):
        kg.graph.add_edge(link["source"], link["target"], **{k: v for k, v in link.items() if k not in ["source", "target"]})
    
    print(f"Loaded {len(kg.graph.nodes)} nodes, {len(kg.graph.edges)} edges")
    
    # Check for semantic index
    semantic_index_exists = Path(semantic_index_path).exists()
    if not semantic_index_exists:
        print("Warning: Semantic index not found. Run 'analyze --llm' to enable semantic search.")
        semantic_index_path = None
    
    # Create agent
    try:
        print("Creating Navigator agent...")
        agent = create_navigator_agent(kg, semantic_index_path)
        print("Agent ready!\n")
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Interactive or single query mode
    if args.interactive:
        print("Interactive mode. Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                query = input("Query> ").strip()
                if query.lower() in ["exit", "quit", "q"]:
                    break
                if not query:
                    continue
                
                result = agent.invoke({"messages": [("user", query)]})
                print("\n" + result["messages"][-1].content + "\n")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    else:
        # Single query mode
        if not args.query:
            print("Error: --query required in non-interactive mode")
            return 1
        
        result = agent.invoke({"messages": [("user", args.query)]})
        print(result["messages"][-1].content)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Brownfield Cartographer - Codebase Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli analyze --repo /path/to/repository
  python -m src.cli analyze --repo . --llm
  python -m src.cli query --repo . --interactive
  python -m src.cli query --repo . --query "What does src/cli.py do?"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a repository and generate knowledge graph"
    )
    analyze_parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Path to repository to analyze"
    )
    analyze_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only analyze files changed since last analysis"
    )
    analyze_parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM-powered semantic analysis (requires OPENROUTER_API_KEY)"
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        "query",
        help="Query the knowledge graph using the Navigator agent"
    )
    query_parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Path to repository (must have been analyzed)"
    )
    query_parser.add_argument(
        "--query",
        type=str,
        help="Single query to execute"
    )
    query_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Start interactive query session"
    )
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        repo_path = Path(args.repo).resolve()
        
        if not repo_path.exists():
            print(f"Error: Repository path does not exist: {repo_path}")
            return 1
        
        if not repo_path.is_dir():
            print(f"Error: Path is not a directory: {repo_path}")
            return 1
        
        try:
            run_cartographer(str(repo_path), incremental=args.incremental, enable_llm=args.llm)
            return 0
        except Exception as e:
            print(f"\nError during analysis: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    elif args.command == "query":
        return query_command(args)


if __name__ == "__main__":
    exit(main())
