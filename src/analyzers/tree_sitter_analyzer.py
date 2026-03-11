from pathlib import Path
from typing import Dict, List, Union, Optional
from tree_sitter import Language, Parser
import tree_sitter_python


class LanguageRouter:
    def __init__(self):
        self.python_parser = Parser(Language(tree_sitter_python.language()))
    
    def analyze_python_module(self, filepath: str) -> Optional[Dict[str, List[str]]]:
        """
        Parse a Python file and extract imports and definitions.
        
        Args:
            filepath: Path to Python file
        
        Returns:
            Dict with 'imports' and 'definitions' lists, or None on error
        """
        try:
            source = Path(filepath).read_bytes()
        except (FileNotFoundError, PermissionError, OSError) as e:
            print(f"Error reading file {filepath}: {e}")
            return None
        
        try:
            tree = self.python_parser.parse(source)
            root = tree.root_node
            
            imports = self._extract_imports(root, source)
            definitions = self._extract_definitions(root, source)
            
            return {
                "imports": imports,
                "definitions": definitions
            }
        except Exception as e:
            print(f"Error parsing file {filepath}: {e}")
            return None
    
    def _extract_imports(self, node, source: bytes) -> List[str]:
        """Extract all imported modules."""
        imports = []
        
        for child in node.children:
            if child.type == "import_statement":
                module = child.child_by_field_name("name")
                if module:
                    module_name = source[module.start_byte:module.end_byte].decode('utf-8')
                    imports.append(module_name)
            
            elif child.type == "import_from_statement":
                module = child.child_by_field_name("module_name")
                if module:
                    module_name = source[module.start_byte:module.end_byte].decode('utf-8')
                    imports.append(module_name)
            
            # Recurse for nested structures
            if child.children:
                imports.extend(self._extract_imports(child, source))
        
        return imports
    
    def _extract_definitions(self, node, source: bytes) -> List[str]:
        """Extract all function and class names."""
        definitions = []
        
        for child in node.children:
            if child.type in ("function_definition", "class_definition"):
                name_node = child.child_by_field_name("name")
                if name_node:
                    name = source[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    definitions.append(name)
            
            # Recurse for nested structures
            if child.children:
                definitions.extend(self._extract_definitions(child, source))
        
        return definitions


class PythonDataFlowAnalyzer:
    def __init__(self):
        self.parser = Parser(Language(tree_sitter_python.language()))
    
    def analyze(self, file_input: Union[str, Path]) -> Dict[str, List[Dict[str, str]]]:
        """
        Extract imports and function definitions from Python file.
        
        Args:
            file_input: Python file path or source code string
        
        Returns:
            Dict with 'imports' and 'functions' lists
        """
        if isinstance(file_input, Path) or (isinstance(file_input, str) and Path(file_input).exists()):
            source = Path(file_input).read_bytes()
        else:
            source = file_input.encode('utf-8')
        
        tree = self.parser.parse(source)
        root = tree.root_node
        
        imports = self._extract_imports(root, source)
        functions = self._extract_functions(root, source)
        
        return {
            "imports": imports,
            "functions": functions
        }
    
    def _extract_imports(self, node, source: bytes) -> List[Dict[str, str]]:
        """Extract all import statements."""
        imports = []
        
        for child in node.children:
            if child.type == "import_statement":
                module = child.child_by_field_name("name")
                if module:
                    imports.append({
                        "type": "import",
                        "module": source[module.start_byte:module.end_byte].decode('utf-8')
                    })
            
            elif child.type == "import_from_statement":
                module = child.child_by_field_name("module_name")
                module_name = source[module.start_byte:module.end_byte].decode('utf-8') if module else ""
                
                for name_node in child.children:
                    if name_node.type == "dotted_name" and name_node != module:
                        imports.append({
                            "type": "from_import",
                            "module": module_name,
                            "name": source[name_node.start_byte:name_node.end_byte].decode('utf-8')
                        })
                    elif name_node.type == "aliased_import":
                        name = name_node.child_by_field_name("name")
                        if name:
                            imports.append({
                                "type": "from_import",
                                "module": module_name,
                                "name": source[name.start_byte:name.end_byte].decode('utf-8')
                            })
            
            # Recurse for nested structures
            if child.children:
                imports.extend(self._extract_imports(child, source))
        
        return imports
    
    def _extract_functions(self, node, source: bytes) -> List[Dict[str, str]]:
        """Extract all function definitions."""
        functions = []
        
        for child in node.children:
            if child.type == "function_definition":
                name_node = child.child_by_field_name("name")
                params_node = child.child_by_field_name("parameters")
                
                if name_node:
                    name = source[name_node.start_byte:name_node.end_byte].decode('utf-8')
                    signature = name
                    
                    if params_node:
                        params = source[params_node.start_byte:params_node.end_byte].decode('utf-8')
                        signature = f"{name}{params}"
                    
                    functions.append({
                        "name": name,
                        "signature": signature
                    })
            
            # Recurse for nested structures (classes, nested functions)
            if child.children:
                functions.extend(self._extract_functions(child, source))
        
        return functions
