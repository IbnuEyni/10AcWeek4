from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


def parse_yaml_config(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Safely load a YAML configuration file and extract relevant metadata.
    
    Args:
        filepath: Path to YAML file (dbt_project.yml, Airflow DAG config, etc.)
    
    Returns:
        Dict with extracted configuration, or None on error
    """
    try:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config or not isinstance(config, dict):
            return None
        
        extracted = {
            "raw_config": config,
            "models": _extract_models(config),
            "sources": _extract_sources(config),
            "pipeline_steps": _extract_pipeline_steps(config),
            "dependencies": _extract_dependencies(config)
        }
        
        return extracted
    
    except (FileNotFoundError, PermissionError, OSError) as e:
        print(f"Error reading file {filepath}: {e}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML in {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing {filepath}: {e}")
        return None


def _extract_models(config: Dict[str, Any]) -> List[str]:
    """Extract model names from dbt-style configuration."""
    models = []
    
    # dbt models
    if "models" in config:
        models.extend(_flatten_keys(config["models"]))
    
    # dbt model-paths
    if "model-paths" in config:
        if isinstance(config["model-paths"], list):
            models.extend(config["model-paths"])
    
    return models


def _extract_sources(config: Dict[str, Any]) -> List[str]:
    """Extract source names from configuration."""
    sources = []
    
    # dbt sources
    if "sources" in config:
        if isinstance(config["sources"], list):
            for source in config["sources"]:
                if isinstance(source, dict):
                    if "name" in source:
                        sources.append(source["name"])
                    if "tables" in source and isinstance(source["tables"], list):
                        for table in source["tables"]:
                            if isinstance(table, dict) and "name" in table:
                                sources.append(f"{source.get('name', '')}.{table['name']}")
                            elif isinstance(table, str):
                                sources.append(table)
    
    # source-paths
    if "source-paths" in config:
        if isinstance(config["source-paths"], list):
            sources.extend(config["source-paths"])
    
    return sources


def _extract_pipeline_steps(config: Dict[str, Any]) -> List[str]:
    """Extract pipeline steps from Airflow-style configuration."""
    steps = []
    
    # Airflow tasks
    if "tasks" in config:
        if isinstance(config["tasks"], list):
            for task in config["tasks"]:
                if isinstance(task, dict) and "task_id" in task:
                    steps.append(task["task_id"])
                elif isinstance(task, str):
                    steps.append(task)
    
    # Generic steps/stages
    for key in ["steps", "stages", "jobs", "operations"]:
        if key in config:
            if isinstance(config[key], list):
                for item in config[key]:
                    if isinstance(item, dict) and "name" in item:
                        steps.append(item["name"])
                    elif isinstance(item, str):
                        steps.append(item)
    
    return steps


def _extract_dependencies(config: Dict[str, Any]) -> List[str]:
    """Extract dependencies from configuration."""
    dependencies = []
    
    # Package dependencies
    for key in ["dependencies", "packages", "requires"]:
        if key in config:
            if isinstance(config[key], list):
                for dep in config[key]:
                    if isinstance(dep, dict):
                        if "package" in dep:
                            dependencies.append(dep["package"])
                        elif "git" in dep:
                            dependencies.append(dep["git"])
                        elif "name" in dep:
                            dependencies.append(dep["name"])
                    elif isinstance(dep, str):
                        dependencies.append(dep)
    
    return dependencies


def _flatten_keys(obj: Any, prefix: str = "") -> List[str]:
    """Recursively flatten nested dictionary keys."""
    keys = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            if isinstance(value, dict):
                keys.extend(_flatten_keys(value, full_key))
    
    return keys
