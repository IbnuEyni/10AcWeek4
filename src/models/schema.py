from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel


class ModuleNode(BaseModel):
    path: str
    language: str
    purpose_statement: Optional[str] = None
    domain_cluster: Optional[str] = None
    complexity_score: float
    change_velocity_30d: int
    is_dead_code_candidate: bool
    has_documentation_drift: bool = False


class DatasetNode(BaseModel):
    name: str
    storage_type: Literal["table", "file", "stream", "api"]
    schema_snapshot: Dict[str, Any]


class FunctionNode(BaseModel):
    qualified_name: str
    signature: str
    is_public_api: bool


class TransformationNode(BaseModel):
    source_file: str
    logic_type: str


class ImportsEdge(BaseModel):
    source: str
    target: str


class ProducesEdge(BaseModel):
    source: str
    target: str


class ConsumesEdge(BaseModel):
    source: str
    target: str


class CallsEdge(BaseModel):
    source: str
    target: str


class ConfiguresEdge(BaseModel):
    source: str
    target: str
