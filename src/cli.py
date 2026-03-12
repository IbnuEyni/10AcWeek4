import argparse
from pathlib import Path
from src.orchestrator import run_cartographer


def main():
    parser = argparse.ArgumentParser(
        description="Brownfield Cartographer - Codebase Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli analyze --repo /path/to/repository
  python -m src.cli analyze --repo .
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


if __name__ == "__main__":
    exit(main())
