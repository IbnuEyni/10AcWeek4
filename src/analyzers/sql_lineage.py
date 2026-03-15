from pathlib import Path
from typing import List, Dict, Union
import re
import sqlglot
from sqlglot import exp


def preprocess_dbt_jinja(sql_content: str) -> tuple[str, Dict[str, List[str]]]:
    """
    Extract dbt Jinja references and replace with placeholder tables.
    
    Args:
        sql_content: Raw SQL with Jinja templates
    
    Returns:
        Tuple of (cleaned SQL, dict of extracted references)
    """
    dbt_refs = {"sources": [], "refs": []}
    
    # Extract {{ source('schema', 'table') }} patterns
    source_pattern = r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
    for match in re.finditer(source_pattern, sql_content):
        schema, table = match.groups()
        dbt_refs["sources"].append(f"{schema}.{table}")
        # Replace with actual table reference
        sql_content = sql_content.replace(match.group(0), f"{schema}.{table}")
    
    # Extract {{ ref('model') }} patterns
    ref_pattern = r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
    for match in re.finditer(ref_pattern, sql_content):
        model = match.groups()[0]
        dbt_refs["refs"].append(model)
        # Replace with table reference
        sql_content = sql_content.replace(match.group(0), model)
    
    # Remove other Jinja constructs (macros, control flow)
    # Remove {% ... %} blocks
    sql_content = re.sub(r"\{%.*?%\}", "", sql_content, flags=re.DOTALL)
    # Remove {{ ... }} that aren't source/ref (like variables)
    sql_content = re.sub(r"\{\{(?!\s*source|\s*ref).*?\}\}", "'JINJA_VAR'", sql_content, flags=re.DOTALL)
    # Remove {# ... #} comments
    sql_content = re.sub(r"\{#.*?#\}", "", sql_content, flags=re.DOTALL)
    
    return sql_content, dbt_refs


def extract_sql_dependencies(sql_content: str, dialect: str = "postgres") -> Dict[str, List[str]]:
    """Parse SQL and extract source and target tables. Supports postgres, bigquery, snowflake."""
    sources = set()
    targets = set()
    
    cleaned_sql, dbt_refs = preprocess_dbt_jinja(sql_content)
    sources.update(dbt_refs["sources"])
    sources.update(dbt_refs["refs"])
    
    try:
        parsed = sqlglot.parse(cleaned_sql, read=dialect)
        
        for statement in parsed:
            if not statement:
                continue
            
            if isinstance(statement, (exp.Insert, exp.Create)):
                if statement.this:
                    target_name = _get_table_name(statement.this)
                    if target_name:
                        targets.add(target_name)
            
            # Extract from CTEs and subqueries
            for table_node in statement.find_all(exp.Table):
                table_name = _get_table_name(table_node)
                if table_name and not _is_target_in_statement(table_node, statement):
                    sources.add(table_name)
    
    except Exception as e:
        print(f"Error parsing SQL ({dialect}): {e}")
        if not sources:
            return {"sources": [], "targets": []}
    
    return {"sources": sorted(list(sources)), "targets": sorted(list(targets))}


def _get_table_name(node) -> str:
    """Extract fully qualified table name from node."""
    if isinstance(node, exp.Table):
        parts = []
        if node.catalog:
            parts.append(node.catalog)
        if node.db:
            parts.append(node.db)
        parts.append(node.name)
        return ".".join(parts)
    return ""


def _is_target_in_statement(table_node: exp.Table, statement) -> bool:
    """Check if table is the target of INSERT/CREATE in this statement."""
    if isinstance(statement, (exp.Insert, exp.Create)):
        if statement.this == table_node:
            return True
        # Check if it's within the target expression
        if hasattr(statement.this, 'this') and statement.this.this == table_node:
            return True
    return False


def extract_sql_lineage(
    sql_input: Union[str, Path],
    dialect: str = "postgres"
) -> Dict[str, List[str]]:
    """
    Extract source and target tables from SQL.
    
    Args:
        sql_input: Raw SQL string or file path
        dialect: SQL dialect ('postgres' or 'bigquery')
    
    Returns:
        Dict with 'sources' and 'targets' lists
    """
    if isinstance(sql_input, Path) or (isinstance(sql_input, str) and Path(sql_input).exists()):
        sql = Path(sql_input).read_text()
    else:
        sql = sql_input
    
    return extract_sql_dependencies(sql, dialect)
