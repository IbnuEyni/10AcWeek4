from pathlib import Path
from typing import Set, Optional
import networkx as nx
from src.graph.knowledge_graph import KnowledgeGraph
from src.analyzers.sql_lineage import extract_sql_dependencies
from src.analyzers.dag_config_parser import parse_yaml_config
from src.analyzers.python_dataflow import extract_python_dataflow
from src.models.schema import DatasetNode, TransformationNode, ProducesEdge, ConsumesEdge, ConfiguresEdge


class Hydrologist:
    def __init__(self, knowledge_graph: KnowledgeGraph, tracer=None):
        self.kg = knowledge_graph
        self.tracer = tracer
    
    def run(self, repo_path: str, changed_files: set = None):
        """
        Analyze SQL, Python, and YAML files to build data lineage graph.
        
        Args:
            repo_path: Path to repository root
            changed_files: Optional set of changed file paths for incremental mode
        """
        repo = Path(repo_path)
        print(f"Hydrologist: Analyzing data lineage at {repo}")
        
        # Find all relevant files
        sql_files = list(repo.rglob("*.sql"))
        python_files = list(repo.rglob("*.py"))
        yaml_files = list(repo.rglob("*.yml")) + list(repo.rglob("*.yaml"))
        
        # Filter to only changed files if in incremental mode
        if changed_files is not None:
            sql_files = [f for f in sql_files if str(f.relative_to(repo)) in changed_files]
            python_files = [f for f in python_files if str(f.relative_to(repo)) in changed_files]
            yaml_files = [f for f in yaml_files if str(f.relative_to(repo)) in changed_files]
        
        print(f"Hydrologist: Found {len(sql_files)} SQL files")
        print(f"Hydrologist: Found {len(python_files)} Python files")
        print(f"Hydrologist: Found {len(yaml_files)} YAML config files")
        
        # Analyze YAML configs first (for metadata)
        for yaml_file in yaml_files:
            try:
                self._analyze_yaml_config(yaml_file, repo)
            except Exception as e:
                if self.tracer:
                    self.tracer.log_error("Hydrologist", "analyze_yaml", str(yaml_file), str(e))
        
        # Analyze SQL files
        for sql_file in sql_files:
            try:
                self._analyze_sql_file(sql_file, repo)
            except Exception as e:
                if self.tracer:
                    self.tracer.log_error("Hydrologist", "analyze_sql", str(sql_file), str(e))
        
        # Analyze Python files for data IO
        for python_file in python_files:
            try:
                self._analyze_python_dataflow(python_file, repo)
            except Exception as e:
                if self.tracer:
                    self.tracer.log_error("Hydrologist", "analyze_python", str(python_file), str(e))
        
        print("Hydrologist: Data lineage analysis complete")
    
    def _analyze_sql_file(self, file_path: Path, repo_root: Path):
        """Analyze a single SQL file and add to knowledge graph."""
        relative_path = str(file_path.relative_to(repo_root))
        
        try:
            sql_content = file_path.read_text()
        except Exception as e:
            print(f"Hydrologist: Error reading {file_path}: {e}")
            return
        
        # Detect dialect from file path or content
        dialect = "postgres"
        if "bigquery" in str(file_path).lower() or "bq" in str(file_path).lower():
            dialect = "bigquery"
        elif "snowflake" in str(file_path).lower() or "sf" in str(file_path).lower():
            dialect = "snowflake"
        
        lineage = extract_sql_dependencies(sql_content, dialect=dialect)
        
        transformation_node = TransformationNode(
            source_file=relative_path,
            logic_type="sql_transform"
        )
        transformation_id = f"{relative_path}:sql_transform"
        self.kg.graph.add_node(
            transformation_id,
            node_type="transformation",
            **transformation_node.model_dump()
        )
        
        target_name = file_path.stem
        target_dataset = DatasetNode(
            name=target_name,
            storage_type="table",
            schema_snapshot={}
        )
        self.kg.add_dataset_node(target_dataset)
        
        # Add edge with consistent metadata
        self.kg.graph.add_edge(
            transformation_id,
            target_name,
            edge_type="PRODUCES",
            transformation_type="sql",
            line_range=(1, 1)
        )
        
        if self.tracer:
            self.tracer.log_action("Hydrologist", "extract_sql_lineage", relative_path, 
                                   f"Sources: {lineage.get('sources', [])}, Targets: {lineage.get('targets', [])}", "1.0")
        
        for source_table in lineage.get("sources", []):
            source_dataset = DatasetNode(
                name=source_table,
                storage_type="table",
                schema_snapshot={}
            )
            self.kg.add_dataset_node(source_dataset)
            
            self.kg.graph.add_edge(
                source_table,
                transformation_id,
                edge_type="CONSUMES",
                transformation_type="sql",
                line_range=(1, 1)
            )
        
        for target_table in lineage.get("targets", []):
            if target_table != target_name:
                target_dataset = DatasetNode(
                    name=target_table,
                    storage_type="table",
                    schema_snapshot={}
                )
                self.kg.add_dataset_node(target_dataset)
                
                self.kg.graph.add_edge(
                    transformation_id,
                    target_table,
                    edge_type="PRODUCES",
                    transformation_type="sql",
                    line_range=(1, 1)
                )
    
    def _analyze_yaml_config(self, file_path: Path, repo_root: Path):
        """Analyze YAML config file for pipeline metadata."""
        relative_path = str(file_path.relative_to(repo_root))
        
        config = parse_yaml_config(str(file_path))
        if not config:
            return
        
        # Extract sources from dbt schema.yml
        for source in config.get("sources", []):
            # Create dataset nodes for sources
            dataset_node = DatasetNode(
                name=source,
                storage_type="table",
                schema_snapshot={}
            )
            self.kg.add_dataset_node(dataset_node)
        
        # Extract models from dbt config
        for model in config.get("models", []):
            # Create CONFIGURES edge from YAML to model
            if model:
                configures_edge = ConfiguresEdge(
                    source=relative_path,
                    target=model
                )
                self.kg.add_configures_edge(configures_edge)
        
        # Extract pipeline steps (Airflow DAGs)
        for step in config.get("pipeline_steps", []):
            if step:
                # Create transformation node for pipeline step
                transformation_id = f"{relative_path}:{step}"
                self.kg.graph.add_node(
                    transformation_id,
                    node_type="transformation",
                    source_file=relative_path,
                    logic_type="pipeline_step"
                )
    
    def _analyze_python_dataflow(self, file_path: Path, repo_root: Path):
        """Analyze Python file for data IO operations."""
        relative_path = str(file_path.relative_to(repo_root))
        
        result = extract_python_dataflow(file_path)
        
        if result.get('error'):
            if self.tracer:
                self.tracer.log_error("Hydrologist", "parse_python", relative_path, result['error'])
            return
        
        io_operations = result.get('io_operations', [])
        unresolved = result.get('unresolved_dynamics', [])
        
        # Log unresolved dynamics
        for dynamic in unresolved:
            if self.tracer:
                self.tracer.log_action("Hydrologist", "unresolved_dynamic", relative_path,
                                       f"Line {dynamic['line']}: {dynamic['reason']}", "0.5")
        
        if not io_operations:
            return
        
        # Create transformation node for this Python file
        transformation_id = f"{relative_path}:dataflow"
        self.kg.graph.add_node(
            transformation_id,
            node_type="transformation",
            source_file=relative_path,
            logic_type="python_dataflow"
        )
        
        # Process IO operations
        for op in io_operations:
            line_range = op.get('line_range', (op['line'], op['line']))
            
            if op['type'] == 'read':
                source_name = op.get('source', '<unknown>')
                if source_name != '<unknown>':
                    source_dataset = DatasetNode(
                        name=source_name,
                        storage_type=op['framework'],
                        schema_snapshot={}
                    )
                    self.kg.add_dataset_node(source_dataset)
                    
                    self.kg.graph.add_edge(
                        source_name,
                        transformation_id,
                        edge_type="CONSUMES",
                        transformation_type=op['framework'],
                        line_range=line_range
                    )
            
            elif op['type'] == 'write':
                target_name = op.get('target', '<unknown>')
                if target_name != '<unknown>':
                    target_dataset = DatasetNode(
                        name=target_name,
                        storage_type=op['framework'],
                        schema_snapshot={}
                    )
                    self.kg.add_dataset_node(target_dataset)
                    
                    self.kg.graph.add_edge(
                        transformation_id,
                        target_name,
                        edge_type="PRODUCES",
                        transformation_type=op['framework'],
                        line_range=line_range
                    )
        
        if self.tracer:
            self.tracer.log_action("Hydrologist", "extract_python_dataflow", relative_path,
                                   f"Found {len(io_operations)} IO operations", "1.0")
    
    def blast_radius(self, node_id: str) -> Set[str]:
        """
        Calculate the blast radius (all downstream datasets) for a given node.
        
        Args:
            node_id: Node identifier (dataset or transformation)
        
        Returns:
            Set of downstream dataset node IDs
        """
        if not self.kg.graph.has_node(node_id):
            print(f"Hydrologist: Node {node_id} not found in graph")
            return set()
        
        try:
            # Get all descendants (downstream nodes)
            descendants = nx.descendants(self.kg.graph, node_id)
            
            # Filter to only dataset nodes
            downstream_datasets = {
                node for node in descendants
                if self.kg.graph.nodes[node].get("node_type") == "dataset"
            }
            
            print(f"\nHydrologist: Blast radius for '{node_id}':")
            print(f"  Total downstream nodes: {len(descendants)}")
            print(f"  Downstream datasets: {len(downstream_datasets)}")
            
            if downstream_datasets:
                print("  Affected datasets:")
                for dataset in sorted(downstream_datasets):
                    print(f"    - {dataset}")
            
            return downstream_datasets
        
        except Exception as e:
            print(f"Hydrologist: Error calculating blast radius: {e}")
            return set()
    
    def trace_downstream(self, node_id: str, max_depth: Optional[int] = None) -> dict:
        """
        Trace downstream dependencies with depth information.
        
        Args:
            node_id: Starting node identifier
            max_depth: Maximum depth to traverse (None for unlimited)
        
        Returns:
            Dict mapping node IDs to their depth level
        """
        if not self.kg.graph.has_node(node_id):
            return {}
        
        try:
            downstream = {}
            visited = {node_id}
            current_level = {node_id}
            depth = 0
            
            while current_level and (max_depth is None or depth < max_depth):
                next_level = set()
                
                for node in current_level:
                    for successor in self.kg.graph.successors(node):
                        if successor not in visited:
                            visited.add(successor)
                            next_level.add(successor)
                            downstream[successor] = depth + 1
                
                current_level = next_level
                depth += 1
            
            return downstream
        
        except Exception as e:
            print(f"Hydrologist: Error tracing downstream: {e}")
            return {}
    
    def find_sources(self) -> Set[str]:
        """Find all source datasets (nodes with no incoming edges)."""
        sources = set()
        for node, data in self.kg.graph.nodes(data=True):
            if data.get('node_type') == 'dataset':
                if self.kg.graph.in_degree(node) == 0:
                    sources.add(node)
        return sources
    
    def find_sinks(self) -> Set[str]:
        """Find all sink datasets (nodes with no outgoing edges)."""
        sinks = set()
        for node, data in self.kg.graph.nodes(data=True):
            if data.get('node_type') == 'dataset':
                if self.kg.graph.out_degree(node) == 0:
                    sinks.add(node)
        return sinks
