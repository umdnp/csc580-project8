"""Classify command-like text inside Python source without executing it."""

from __future__ import annotations

import ast
import bisect
import io
import tokenize


_EXECUTION_CALLS = frozenset({
    "exec", "eval", "os.system", "os.popen", "subprocess.run",
    "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "subprocess.Popen", "asyncio.create_subprocess_shell",
    "asyncio.create_subprocess_exec",
})
_PRIORITY = {"source_literal": 1, "source_docstring": 2,
             "source_execution": 3, "source_comment": 4}


def _call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else ""
    return ""


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Identify first-statement string literals in Python documentation blocks."""
    result: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)) or not node.body:
            continue
        first = node.body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            result.add(id(first.value))
    return result


class PythonSourceContext:
    """Locate Python comments and literals using tokens and the built-in AST.

    This is a conservative context classifier, not a data-flow analyzer. A
    command passed directly to a known execution API may be supported; text
    inside other string literals remains uncertain. Invalid Python can still
    be classified using tokens alone.
    """

    def __init__(self, source: str) -> None:
        self._lines = source.splitlines(keepends=True)
        self._starts: list[int] = []
        offset = 0
        for line in self._lines:
            self._starts.append(offset)
            offset += len(line)
        self._by_line: dict[int, list[tuple[int, int, str]]] = {}

        try:
            for token in tokenize.generate_tokens(io.StringIO(source).readline):
                if token.type in (tokenize.COMMENT, tokenize.STRING):
                    kind = ("source_comment" if token.type == tokenize.COMMENT
                            else "source_literal")
                    self._mark(self._token_offset(*token.start),
                               self._token_offset(*token.end), kind)
        except (tokenize.TokenError, IndentationError):
            # Preserve the spans already tokenized in malformed/templated files.
            pass

        try:
            tree = ast.parse(source)
        except (SyntaxError, ValueError):
            return
        documentation = _docstring_nodes(tree)
        parents = {id(child): node for node in ast.walk(tree)
                   for child in ast.iter_child_nodes(node)}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.JoinedStr) or
                    isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            if not hasattr(node, "end_lineno") or node.end_lineno is None:
                continue
            ancestor = parents.get(id(node))
            while ancestor is not None and not isinstance(ancestor, ast.Call):
                ancestor = parents.get(id(ancestor))
            # The nearest call controls the literal's use. For example,
            # subprocess.run(print("pip install ...")) only prints the text.
            execution = (isinstance(ancestor, ast.Call)
                         and _call_name(ancestor.func) in _EXECUTION_CALLS)
            kind = ("source_execution" if execution else
                    "source_docstring" if id(node) in documentation else
                    "source_literal")
            self._mark(self._ast_offset(node.lineno, node.col_offset),
                       self._ast_offset(node.end_lineno, node.end_col_offset), kind)

    def kind_at(self, position: int) -> str | None:
        if not self._starts:
            return None
        line = bisect.bisect_right(self._starts, position) - 1
        candidates = (kind for start, end, kind in self._by_line.get(line, ())
                      if start <= position < end)
        return max(candidates, key=_PRIORITY.get, default=None)

    def _token_offset(self, lineno: int, column: int) -> int:
        return self._starts[lineno - 1] + column

    def _ast_offset(self, lineno: int, byte_column: int) -> int:
        # AST columns count UTF-8 bytes, while scanner offsets count characters.
        line = self._lines[lineno - 1]
        column = len(line.encode("utf-8")[:byte_column].decode("utf-8", "ignore"))
        return self._starts[lineno - 1] + column

    def _mark(self, start: int, end: int, kind: str) -> None:
        if start >= end or not self._starts:
            return
        first = bisect.bisect_right(self._starts, start) - 1
        last = bisect.bisect_right(self._starts, end - 1) - 1
        for line in range(first, last + 1):
            beginning = max(start, self._starts[line])
            ending = min(end, self._starts[line] + len(self._lines[line]))
            if beginning < ending:
                self._by_line.setdefault(line, []).append((beginning, ending, kind))
