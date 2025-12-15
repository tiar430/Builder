import re
import logging
from typing import List, Dict, Tuple, Optional
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import TerminalFormatter
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeParser:
    """Parser for analyzing code in multiple languages."""
    
    # Language detection patterns
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".sql": "sql",
    }
    
    # Common error patterns
    PYTHON_ERRORS = {
        r"IndentationError": "Indentation error - check spacing",
        r"SyntaxError": "Syntax error - check code structure",
        r"NameError": "Name error - variable not defined",
        r"TypeError": "Type error - operation not supported",
        r"ValueError": "Value error - invalid value",
        r"AttributeError": "Attribute error - object has no attribute",
        r"KeyError": "Key error - dictionary key not found",
        r"IndexError": "Index error - list index out of range",
    }
    
    JAVASCRIPT_ERRORS = {
        r"SyntaxError": "Syntax error - check code structure",
        r"TypeError": "Type error - operation not supported",
        r"ReferenceError": "Reference error - variable not defined",
        r"RangeError": "Range error - value out of acceptable range",
        r"Cannot read propert(y|ies) of": "Property access error",
    }
    
    JAVA_ERRORS = {
        r"Exception": "Exception thrown",
        r"NullPointerException": "Null pointer exception",
        r"ArrayIndexOutOfBoundsException": "Array index out of bounds",
        r"ClassNotFoundException": "Class not found",
        r"IOException": "IO error",
    }
    
    def __init__(self):
        self.error_patterns = {
            "python": self.PYTHON_ERRORS,
            "javascript": self.JAVASCRIPT_ERRORS,
            "java": self.JAVA_ERRORS,
        }
    
    def detect_language(self, code: str, filename: Optional[str] = None) -> str:
        """Detect programming language from code."""
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in self.LANGUAGE_EXTENSIONS:
                return self.LANGUAGE_EXTENSIONS[ext]
        
        try:
            lexer = guess_lexer(code)
            return lexer.name.lower()
        except Exception:
            return "text"
    
    def extract_functions(self, code: str, language: str) -> List[Dict[str, any]]:
        """Extract function definitions from code."""
        functions = []
        
        if language == "python":
            # Python functions
            pattern = r'^\s*def\s+(\w+)\s*\((.*?)\)'
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                functions.append({
                    "name": match.group(1),
                    "params": match.group(2),
                    "line": code[:match.start()].count('\n') + 1,
                })
        
        elif language in ["javascript", "typescript"]:
            # JS/TS functions
            patterns = [
                r'function\s+(\w+)\s*\((.*?)\)',
                r'const\s+(\w+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>',
            ]
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    functions.append({
                        "name": match.group(1),
                        "params": match.group(2),
                        "line": code[:match.start()].count('\n') + 1,
                    })
        
        elif language == "java":
            # Java methods
            pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*\((.*?)\)'
            matches = re.finditer(pattern, code)
            for match in matches:
                functions.append({
                    "name": match.group(1),
                    "params": match.group(2),
                    "line": code[:match.start()].count('\n') + 1,
                })
        
        return functions
    
    def find_syntax_errors(self, code: str, language: str) -> List[Dict[str, any]]:
        """Find common syntax errors in code."""
        errors = []
        
        # Check for unmatched brackets
        bracket_pairs = [('(', ')'), ('[', ']'), ('{', '}')]
        for open_b, close_b in bracket_pairs:
            open_count = code.count(open_b)
            close_count = code.count(close_b)
            if open_count != close_count:
                errors.append({
                    "type": "bracket_mismatch",
                    "message": f"Mismatched {open_b}{close_b} brackets",
                    "severity": "high",
                })
        
        # Language-specific error patterns
        error_dict = self.error_patterns.get(language, {})
        for pattern, message in error_dict.items():
            if re.search(pattern, code):
                # Find lines with the pattern
                for i, line in enumerate(code.split('\n'), 1):
                    if re.search(pattern, line):
                        errors.append({
                            "type": "error_pattern",
                            "message": message,
                            "line": i,
                            "code": line.strip(),
                            "severity": "high",
                        })
        
        return errors
    
    def analyze_code_quality(self, code: str, language: str) -> Dict[str, any]:
        """Analyze code quality metrics."""
        lines = code.split('\n')
        
        metrics = {
            "total_lines": len(lines),
            "non_empty_lines": len([l for l in lines if l.strip()]),
            "comment_lines": len([l for l in lines if l.strip().startswith('#' if language == 'python' else '//')]),
            "average_line_length": sum(len(l) for l in lines) / len(lines) if lines else 0,
            "functions": len(self.extract_functions(code, language)),
            "indentation_issues": 0,
            "long_lines": 0,
        }
        
        # Check indentation consistency
        if language == "python":
            uses_tabs = any('\t' in line for line in lines)
            uses_spaces = any(line.startswith(' ') for line in lines)
            if uses_tabs and uses_spaces:
                metrics["indentation_issues"] = 1
        
        # Check for long lines (>100 chars)
        metrics["long_lines"] = len([l for l in lines if len(l) > 100])
        
        return metrics
    
    def extract_imports(self, code: str, language: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        
        if language == "python":
            patterns = [
                r'^\s*import\s+(.+)$',
                r'^\s*from\s+(.+?)\s+import\s+(.+)$',
            ]
        elif language in ["javascript", "typescript"]:
            patterns = [
                r'^\s*import\s+.+?\s+from\s+[\'"](.+?)[\'"]',
                r'^\s*require\([\'"](.+?)[\'"]\)',
            ]
        elif language == "java":
            patterns = [
                r'^\s*import\s+(.+);',
            ]
        else:
            return imports
        
        for pattern in patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                imports.append(match.group(1))
        
        return imports
    
    def get_syntax_highlighting(self, code: str, language: str) -> str:
        """Get syntax highlighted code."""
        try:
            lexer = get_lexer_by_name(language)
            return highlight(code, lexer, TerminalFormatter())
        except Exception as e:
            logger.warning(f"Syntax highlighting failed: {e}")
            return code
