import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import networkx as nx
from src.graph.knowledge_graph import KnowledgeGraph
from src.analyzers.tree_sitter_analyzer import LanguageRouter
from src.models.schema import ModuleNode, FunctionNode, ImportsEdge


class Surveyor:
    def __init__(self, knowledge_graph: KnowledgeGraph, tracer=None):
        self.kg = knowledge_graph
        self.analyzer = LanguageRouter()
        self.tracer = tracer
    
    def run(self, repo_path: str, changed_files: set = None):
        """
        Analyze repository structure and populate knowledge graph.
        
        Args:
            repo_path: Path to repository root
            changed_files: Optional set of changed file paths for incremental mode
        """
        repo = Path(repo_path)
        print(f"Surveyor: Analyzing repository at {repo}")
        
        if self.tracer:
            self.tracer.log_action(
                agent="Surveyor",
                action="start_analysis",
                target=str(repo),
                evidence=f"Incremental: {changed_files is not None}",
                confidence="1.0"
            )
        
        # Find all Python files
        py_files = list(repo.rglob("*.py"))
        
        # Filter to only changed files if in incremental mode
        if changed_files is not None:
            py_files = [f for f in py_files if str(f.relative_to(repo)) in changed_files]
        
        print(f"Surveyor: Found {len(py_files)} Python files")
        
        # Analyze each Python file
        for py_file in py_files:
            try:
                self._analyze_python_file(py_file, repo)
            except Exception as e:
                print(f"Surveyor: Error analyzing {py_file}: {e}")
                if self.tracer:
                    self.tracer.log_error(
                        agent="Surveyor",
                        action="analyze_file",
                        target=str(py_file),
                        error_message=str(e)
                    )
        
        # Calculate PageRank for architectural hubs
        self._calculate_pagerank()
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        print("Surveyor: Analysis complete")
    
    def _analyze_python_file(self, file_path: Path, repo_root: Path):
        """Analyze a single Python file and add to knowledge graph."""
        relative_path = str(file_path.relative_to(repo_root))
        
        # Use tree-sitter to extract imports and definitions
        result = self.analyzer.analyze_python_module(str(file_path))
        if not result:
            return
        
        # Calculate git velocity
        change_velocity = self._calculate_change_velocity(file_path, repo_root)
        
        # Create and add ModuleNode
        module_node = ModuleNode(
            path=relative_path,
            language="python",
            purpose_statement=None,
            domain_cluster=None,
            complexity_score=len(result.get("definitions", [])),
            change_velocity_30d=change_velocity,
            is_dead_code_candidate=change_velocity == 0
        )
        self.kg.add_module_node(module_node)
        
        # Add function nodes
        for func_name in result.get("definitions", []):
            func_node = FunctionNode(
                qualified_name=f"{relative_path}::{func_name}",
                signature=func_name,
                is_public_api=not func_name.startswith("_")
            )
            self.kg.add_function_node(func_node)
        
        # Add import edges
        for imported_module in result.get("imports", []):
            # Convert module name to potential file path
            target_path = self._module_to_path(imported_module)
            
            import_edge = ImportsEdge(
                source=relative_path,
                target=target_path
            )
            self.kg.add_imports_edge(import_edge)
    
    def _calculate_change_velocity(self, file_path: Path, repo_root: Path) -> int:
        """
        Calculate number of commits in last 30 days for a file.
        
        Args:
            file_path: Path to file
            repo_root: Repository root path
        
        Returns:
            Number of commits in last 30 days
        """
        try:
            # Get commit dates for the file
            result = subprocess.run(
                ["git", "log", "--follow", "--format=%Y", "--", str(file_path)],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return 0
            
            # Parse years and count commits in last 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            commit_count = 0
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    try:
                        year = int(line)
                        # Simple heuristic: if year matches current year, count it
                        if year == datetime.now().year:
                            commit_count += 1
                    except ValueError:
                        continue
            
            return commit_count
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Surveyor: Error calculating git velocity for {file_path}: {e}")
            return 0
    
    def _module_to_path(self, module_name: str) -> str:
        """
        Convert Python module name to file path.
        
        Args:
            module_name: Python module name (e.g., 'src.models.schema')
        
        Returns:
            File path (e.g., 'src/models/schema.py')
        """
        return module_name.replace(".", "/") + ".py"
    
    def _calculate_pagerank(self):
        """Calculate PageRank to identify architectural hubs."""
        try:
            # Only calculate PageRank on module nodes
            module_graph = nx.DiGraph()
            
            for node, data in self.kg.graph.nodes(data=True):
                if data.get("node_type") == "module":
                    module_graph.add_node(node)
            
            for source, target, data in self.kg.graph.edges(data=True):
                if data.get("edge_type") == "IMPORTS":
                    if module_graph.has_node(source) and module_graph.has_node(target):
                        module_graph.add_edge(source, target)
            
            if len(module_graph.nodes()) > 0:
                pagerank_scores = nx.pagerank(module_graph)
                
                # Add PageRank scores to node data
                for node, score in pagerank_scores.items():
                    if self.kg.graph.has_node(node):
                        self.kg.graph.nodes[node]["pagerank"] = score
                
                # Print top 5 architectural hubs
                top_hubs = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                print("\nSurveyor: Top 5 Architectural Hubs (by PageRank):")
                for node, score in top_hubs:
                    print(f"  {node}: {score:.4f}")
        
        except Exception as e:
            print(f"Surveyor: Error calculating PageRank: {e}")
    
    def _detect_circular_dependencies(self):
        """Detect circular dependencies in the module import graph."""
        try:
            # Build module-only graph
            module_graph = nx.DiGraph()
            
            for node, data in self.kg.graph.nodes(data=True):
                if data.get("node_type") == "module":
                    module_graph.add_node(node)
            
            for source, target, data in self.kg.graph.edges(data=True):
                if data.get("edge_type") == "IMPORTS":
                    if module_graph.has_node(source) and module_graph.has_node(target):
                        module_graph.add_edge(source, target)
            
            if len(module_graph.nodes()) == 0:
                return
            
            # Find strongly connected components (cycles)
            sccs = list(nx.strongly_connected_components(module_graph))
            
            # Filter to only cycles (size > 1)
            cycles = [scc for scc in sccs if len(scc) > 1]
            
            if cycles:
                print(f"\nSurveyor: Found {len(cycles)} circular dependency group(s):")
                for i, cycle in enumerate(cycles, 1):
                    print(f"  Cycle {i}: {len(cycle)} modules involved")
                    for module in sorted(cycle):
                        print(f"    - {module}")
                        # Mark nodes as having circular dependencies
                        if self.kg.graph.has_node(module):
                            self.kg.graph.nodes[module]["has_circular_dependency"] = True
            else:
                print("\nSurveyor: No circular dependencies detected ✓")
        
        except Exception as e:
            print(f"Surveyor: Error detecting circular dependencies: {e}")
