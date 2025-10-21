"""
Docstring Extractor for Annotate

Extracts docstrings from Python files and converts them to annotate notes format.
"""
import ast
import os
import json
from typing import Dict, List, Tuple, Any


class DocstringExtractor:
    """Extract docstrings from Python source code."""

    def __init__(self):
        self.notes = {}
        self.note_counter = 0

    def extract_from_file(self, filepath: str, content: str, source_lines: List[str] = None) -> Dict[str, Any]:
        """
        Extract docstrings from a Python file.

        Args:
            filepath: Relative path to the file
            content: Source code content
            source_lines: Source code split into lines

        Returns:
            Dictionary of notes in annotate format
        """
        if source_lines is None:
            source_lines = content.split('\n')

        try:
            tree = ast.parse(content)
            file_notes = {}

            # Extract module-level docstring
            if ast.get_docstring(tree):
                docstring = ast.get_docstring(tree)
                # Module docstring is at line 0
                key = self._generate_key()
                file_notes[key] = self._create_note(
                    filepath, 0, 0, docstring, "Module Documentation", source_lines
                )

            # Walk the AST to find all docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        # Get the line number where the node starts
                        start_line = node.lineno - 1  # Convert to 0-indexed
                        end_line = start_line

                        # Try to find the end of the docstring
                        if node.body and isinstance(node.body[0], ast.Expr):
                            if isinstance(node.body[0].value, ast.Constant):
                                end_line = node.body[0].end_lineno - 1

                        key = self._generate_key()
                        name = node.name
                        if isinstance(node, ast.ClassDef):
                            title = f"Class: {name}"
                        else:
                            title = f"Function: {name}"

                        file_notes[key] = self._create_note(
                            filepath, start_line, end_line, docstring, title, source_lines
                        )

            return file_notes
        except SyntaxError:
            # Not a valid Python file or has syntax errors
            return {}

    def _generate_key(self) -> str:
        """Generate a unique key for a note."""
        key = f"note_{self.note_counter}"
        self.note_counter += 1
        return key

    def _create_note(self, path: str, start: int, end: int,
                     docstring: str, title: str = "",
                     source_lines: List[str] = None) -> Dict[str, Any]:
        """
        Create a note in annotate format.

        Args:
            path: File path
            start: Start line number (0-indexed)
            end: End line number (0-indexed)
            docstring: The docstring content
            title: Optional title for the note
            source_lines: All source lines for this file

        Returns:
            Note dictionary in annotate format
        """
        # Format the note with title if provided
        if title:
            note_content = f"## {title}\n\n{docstring}"
        else:
            note_content = docstring

        # Get the code lines being annotated
        if source_lines:
            code = source_lines[start:end+1]
        else:
            code = []

        # Get context lines (2 lines before and after)
        if source_lines:
            pre_start = max(0, start - 2)
            pre = source_lines[pre_start:start]

            post_end = min(len(source_lines), end + 3)
            post = source_lines[end+1:post_end]
        else:
            pre = []
            post = []

        return {
            "path": path,
            "pre": pre,
            "post": post,
            "code": code,
            "note": note_content,
            "collapsed": False,
            "codeCollapsed": False
        }

    def extract_from_directory(self, source_files: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract docstrings from all Python files.

        Args:
            source_files: Dictionary mapping file paths to lines of code

        Returns:
            Dictionary of all notes organized by file
        """
        all_notes = {}

        for filepath, lines in source_files.items():
            if not filepath.endswith('.py'):
                continue

            content = '\n'.join(lines)
            file_notes = self.extract_from_file(filepath, content, lines)
            all_notes.update(file_notes)

        return all_notes


def extract_docstrings(source_files: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Main function to extract docstrings from source files.

    Args:
        source_files: Dictionary mapping file paths to lines of code

    Returns:
        Notes dictionary in annotate format
    """
    extractor = DocstringExtractor()
    return extractor.extract_from_directory(source_files)


if __name__ == "__main__":
    # Test the extractor
    test_code = '''
"""
This is a module docstring.
It has multiple lines.
"""

class MyClass:
    """
    This is a class docstring.

    It describes the class.
    """

    def my_method(self):
        """This is a method docstring."""
        pass

def my_function():
    """
    This is a function docstring.

    Args:
        None

    Returns:
        Nothing
    """
    return None
'''

    extractor = DocstringExtractor()
    notes = extractor.extract_from_file("test.py", test_code)
    print(json.dumps(notes, indent=2))
