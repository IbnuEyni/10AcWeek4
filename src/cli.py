import argparse
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import subprocess
import shutil
from src.orchestrator import run_cartographer

load_dotenv()


def clone_github_repo(url: str) -> Path:
    """Clone a GitHub repository to a temporary directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="cartographer_"))
    print(f"Cloning {url} to {temp_dir}...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(temp_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ Repository cloned successfully")
        return temp_dir
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def query_command(args):
    """Handle the query command for Navigator agent queries."""
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
    kg.load_from_json(str(graph_file))  # Use the built-in load method
    
    print(f"Loaded {kg.graph.number_of_nodes()} nodes, {kg.graph.number_of_edges()} edges")
    
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
    
    # Execute query
    result = agent.invoke({"messages": [("user", args.question)]})
    print(result["messages"][-1].content)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Brownfield Cartographer - Codebase Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli analyze --repo /path/to/repository
  python -m src.cli analyze --repo https://github.com/user/repo
  python -m src.cli analyze --repo . --incremental
  python -m src.cli analyze --repo . --llm
  python -m src.cli query --repo . --question "What does src/cli.py do?"
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
        help="Path to repository or GitHub URL (e.g., https://github.com/user/repo)"
    )
    analyze_parser.add_argument(
        "--incremental",
        action="store_true",
        help="Only analyze files changed since HEAD~1 (git diff --name-only HEAD~1)"
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
        "--question",
        type=str,
        required=True,
        help="Question to ask the Navigator agent"
    )
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        repo_input = args.repo
        temp_dir = None
        
        # Check if input is a GitHub URL
        if repo_input.startswith("https://github.com/") or repo_input.startswith("git@github.com:"):
            try:
                temp_dir = clone_github_repo(repo_input)
                repo_path = temp_dir
            except Exception as e:
                print(f"Error: Failed to clone repository: {e}")
                return 1
        else:
            repo_path = Path(repo_input).resolve()
        
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
        finally:
            if temp_dir:
                print(f"\nCleaning up temporary directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    elif args.command == "query":
        return query_command(args)


if __name__ == "__main__":
    exit(main())
