import json
from pathlib import Path
import networkx as nx
from src.models.schema import (
    ModuleNode, DatasetNode, FunctionNode, TransformationNode,
    ImportsEdge, ProducesEdge, ConsumesEdge, CallsEdge, ConfiguresEdge
)


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_module_node(self, node: ModuleNode):
        self.graph.add_node(node.path, node_type="module", **node.model_dump())
    
    def add_dataset_node(self, node: DatasetNode):
        self.graph.add_node(node.name, node_type="dataset", **node.model_dump())
    
    def add_function_node(self, node: FunctionNode):
        self.graph.add_node(node.qualified_name, node_type="function", **node.model_dump())
    
    def add_transformation_node(self, node: TransformationNode):
        node_id = f"{node.source_file}:{node.logic_type}"
        self.graph.add_node(node_id, node_type="transformation", **node.model_dump())
    
    def add_imports_edge(self, edge: ImportsEdge):
        self.graph.add_edge(edge.source, edge.target, edge_type="IMPORTS")
    
    def add_produces_edge(self, edge: ProducesEdge):
        self.graph.add_edge(edge.source, edge.target, edge_type="PRODUCES")
    
    def add_consumes_edge(self, edge: ConsumesEdge):
        self.graph.add_edge(edge.source, edge.target, edge_type="CONSUMES")
    
    def add_calls_edge(self, edge: CallsEdge):
        self.graph.add_edge(edge.source, edge.target, edge_type="CALLS")
    
    def add_configures_edge(self, edge: ConfiguresEdge):
        self.graph.add_edge(edge.source, edge.target, edge_type="CONFIGURES")
    
    def serialize_to_json(self, output_path: str = ".cartography/module_graph.json"):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_json(self, input_path: str):
        """Load knowledge graph from JSON file with typed node/edge reconstruction."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        edges_key = 'edges' if 'edges' in data else 'links'
        self.graph = nx.node_link_graph(data, directed=True, edges=edges_key)
        self._validate_graph_schema()
    
    def _validate_graph_schema(self):
        """Validate that graph nodes and edges conform to Pydantic schemas."""
        for node, attrs in self.graph.nodes(data=True):
            node_type = attrs.get('node_type')
            if node_type == 'module':
                try:
                    ModuleNode(**{k: v for k, v in attrs.items() if k in ModuleNode.model_fields})
                except Exception as e:
                    print(f"Warning: Invalid module node {node}: {e}")
            elif node_type == 'dataset':
                try:
                    DatasetNode(**{k: v for k, v in attrs.items() if k in DatasetNode.model_fields})
                except Exception as e:
                    print(f"Warning: Invalid dataset node {node}: {e}")
        
        for src, tgt, attrs in self.graph.edges(data=True):
            edge_type = attrs.get('edge_type')
            if edge_type == 'IMPORTS':
                try:
                    ImportsEdge(source=src, target=tgt)
                except Exception as e:
                    print(f"Warning: Invalid IMPORTS edge {src}->{tgt}: {e}")
