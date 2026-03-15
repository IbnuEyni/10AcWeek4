"""
Python Data Flow Analyzer - Extract pandas/PySpark/SQLAlchemy IO operations.

Analyzes Python AST to find:
- pandas: read_csv, read_sql, to_csv, to_sql, read_parquet, to_parquet
- PySpark: spark.read, df.write
- SQLAlchemy: create_engine, execute, query
"""

import ast
from typing import List, Dict, Any, Optional
from pathlib import Path


class PythonDataFlowAnalyzer(ast.NodeVisitor):
    """Extract data IO operations from Python code."""
    
    def __init__(self):
        self.io_operations = []
        self.unresolved_dynamics = []
        self.current_line = 0
    
    def visit_Call(self, node: ast.Call):
        """Visit function calls to detect IO operations."""
        self.current_line = node.lineno
        
        # pandas operations
        if self._is_pandas_read(node):
            self._extract_pandas_read(node)
        elif self._is_pandas_write(node):
            self._extract_pandas_write(node)
        
        # PySpark operations
        elif self._is_pyspark_read(node):
            self._extract_pyspark_read(node)
        elif self._is_pyspark_write(node):
            self._extract_pyspark_write(node)
        
        # SQLAlchemy operations
        elif self._is_sqlalchemy_query(node):
            self._extract_sqlalchemy_query(node)
        
        self.generic_visit(node)
    
    def _is_pandas_read(self, node: ast.Call) -> bool:
        """Check if call is pandas read operation."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'pd' and node.func.attr in [
                    'read_csv', 'read_sql', 'read_parquet', 'read_excel', 
                    'read_json', 'read_table', 'read_sql_query', 'read_sql_table'
                ]:
                    return True
        return False
    
    def _is_pandas_write(self, node: ast.Call) -> bool:
        """Check if call is pandas write operation."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['to_csv', 'to_sql', 'to_parquet', 'to_excel', 'to_json']:
                return True
        return False
    
    def _is_pyspark_read(self, node: ast.Call) -> bool:
        """Check if call is PySpark read operation."""
        if isinstance(node.func, ast.Attribute):
            # spark.read.csv, spark.read.parquet, etc.
            if node.func.attr in ['csv', 'parquet', 'json', 'table', 'jdbc']:
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'read':
                        return True
        return False
    
    def _is_pyspark_write(self, node: ast.Call) -> bool:
        """Check if call is PySpark write operation."""
        if isinstance(node.func, ast.Attribute):
            # df.write.csv, df.write.parquet, etc.
            if node.func.attr in ['csv', 'parquet', 'json', 'saveAsTable', 'jdbc']:
                if isinstance(node.func.value, ast.Attribute):
                    if node.func.value.attr == 'write':
                        return True
        return False
    
    def _is_sqlalchemy_query(self, node: ast.Call) -> bool:
        """Check if call is SQLAlchemy query."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['execute', 'query', 'read_sql', 'read_sql_query']:
                return True
        return False
    
    def _extract_pandas_read(self, node: ast.Call):
        """Extract pandas read operation details."""
        operation = node.func.attr
        source = self._extract_string_arg(node, 0) or self._extract_kwarg(node, 'filepath_or_buffer')
        
        if source and self._is_dynamic(source):
            self.unresolved_dynamics.append({
                'line': node.lineno,
                'operation': operation,
                'reason': f'Dynamic path: {source}'
            })
            source = f"<dynamic:{source}>"
        
        self.io_operations.append({
            'type': 'read',
            'framework': 'pandas',
            'operation': operation,
            'source': source or '<unknown>',
            'line': node.lineno,
            'line_range': (node.lineno, node.end_lineno or node.lineno)
        })
    
    def _extract_pandas_write(self, node: ast.Call):
        """Extract pandas write operation details."""
        operation = node.func.attr
        target = self._extract_string_arg(node, 0) or self._extract_kwarg(node, 'path')
        
        if target and self._is_dynamic(target):
            self.unresolved_dynamics.append({
                'line': node.lineno,
                'operation': operation,
                'reason': f'Dynamic path: {target}'
            })
            target = f"<dynamic:{target}>"
        
        self.io_operations.append({
            'type': 'write',
            'framework': 'pandas',
            'operation': operation,
            'target': target or '<unknown>',
            'line': node.lineno,
            'line_range': (node.lineno, node.end_lineno or node.lineno)
        })
    
    def _extract_pyspark_read(self, node: ast.Call):
        """Extract PySpark read operation details."""
        operation = node.func.attr
        source = self._extract_string_arg(node, 0) or self._extract_kwarg(node, 'path')
        
        if source and self._is_dynamic(source):
            self.unresolved_dynamics.append({
                'line': node.lineno,
                'operation': operation,
                'reason': f'Dynamic path: {source}'
            })
            source = f"<dynamic:{source}>"
        
        self.io_operations.append({
            'type': 'read',
            'framework': 'pyspark',
            'operation': operation,
            'source': source or '<unknown>',
            'line': node.lineno,
            'line_range': (node.lineno, node.end_lineno or node.lineno)
        })
    
    def _extract_pyspark_write(self, node: ast.Call):
        """Extract PySpark write operation details."""
        operation = node.func.attr
        target = self._extract_string_arg(node, 0) or self._extract_kwarg(node, 'path')
        
        if target and self._is_dynamic(target):
            self.unresolved_dynamics.append({
                'line': node.lineno,
                'operation': operation,
                'reason': f'Dynamic path: {target}'
            })
            target = f"<dynamic:{target}>"
        
        self.io_operations.append({
            'type': 'write',
            'framework': 'pyspark',
            'operation': operation,
            'target': target or '<unknown>',
            'line': node.lineno,
            'line_range': (node.lineno, node.end_lineno or node.lineno)
        })
    
    def _extract_sqlalchemy_query(self, node: ast.Call):
        """Extract SQLAlchemy query details."""
        operation = node.func.attr
        query = self._extract_string_arg(node, 0) or self._extract_kwarg(node, 'sql')
        
        if query and self._is_dynamic(query):
            self.unresolved_dynamics.append({
                'line': node.lineno,
                'operation': operation,
                'reason': f'Dynamic SQL: {query}'
            })
            query = f"<dynamic:{query}>"
        
        self.io_operations.append({
            'type': 'query',
            'framework': 'sqlalchemy',
            'operation': operation,
            'query': query or '<unknown>',
            'line': node.lineno,
            'line_range': (node.lineno, node.end_lineno or node.lineno)
        })
    
    def _extract_string_arg(self, node: ast.Call, index: int) -> Optional[str]:
        """Extract string argument at given index."""
        if len(node.args) > index:
            arg = node.args[index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            elif isinstance(arg, (ast.Name, ast.Attribute, ast.JoinedStr)):
                return self._ast_to_string(arg)
        return None
    
    def _extract_kwarg(self, node: ast.Call, key: str) -> Optional[str]:
        """Extract keyword argument value."""
        for keyword in node.keywords:
            if keyword.arg == key:
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    return keyword.value.value
                elif isinstance(keyword.value, (ast.Name, ast.Attribute, ast.JoinedStr)):
                    return self._ast_to_string(keyword.value)
        return None
    
    def _ast_to_string(self, node) -> str:
        """Convert AST node to string representation."""
        if isinstance(node, ast.Name):
            return f"${node.id}"
        elif isinstance(node, ast.Attribute):
            return f"${ast.unparse(node)}"
        elif isinstance(node, ast.JoinedStr):
            return f"f-string"
        return "<complex>"
    
    def _is_dynamic(self, value: str) -> bool:
        """Check if value is dynamic (variable, f-string, etc.)."""
        return value.startswith('$') or value == 'f-string' or value == '<complex>'


def extract_python_dataflow(file_path: Path) -> Dict[str, Any]:
    """
    Extract data flow operations from Python file.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        Dict with io_operations and unresolved_dynamics
    """
    try:
        code = file_path.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(code, filename=str(file_path))
        
        analyzer = PythonDataFlowAnalyzer()
        analyzer.visit(tree)
        
        return {
            'io_operations': analyzer.io_operations,
            'unresolved_dynamics': analyzer.unresolved_dynamics
        }
    
    except SyntaxError as e:
        return {
            'io_operations': [],
            'unresolved_dynamics': [],
            'error': f'Syntax error: {e}'
        }
    except Exception as e:
        return {
            'io_operations': [],
            'unresolved_dynamics': [],
            'error': f'Parse error: {e}'
        }
