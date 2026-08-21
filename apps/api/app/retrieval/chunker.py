"""Bounded, code-aware chunking for local ingestion.

Repository text remains untrusted data. This module never executes, imports, or
interprets submitted source beyond parsing Python syntax for boundaries.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import PurePosixPath

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".md": "markdown",
    ".txt": "text",
}
MAX_CHUNK_LINES = 180


@dataclass(frozen=True)
class Chunk:
    content: str
    start_line: int
    end_line: int
    language: str
    symbol_name: str | None = None
    symbol_type: str | None = None


def detect_language(file_path: str) -> str:
    return SUPPORTED_EXTENSIONS.get(PurePosixPath(file_path).suffix.lower(), "text")


def _line_chunks(content: str, language: str) -> list[Chunk]:
    lines = content.splitlines()
    return [
        Chunk(
            content="\n".join(lines[start : start + MAX_CHUNK_LINES]),
            start_line=start + 1,
            end_line=min(start + MAX_CHUNK_LINES, len(lines)),
            language=language,
        )
        for start in range(0, len(lines), MAX_CHUNK_LINES)
        if any(line.strip() for line in lines[start : start + MAX_CHUNK_LINES])
    ]


def _python_chunks(content: str) -> list[Chunk]:
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _line_chunks(content, "python")

    chunks: list[Chunk] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        end_line = getattr(node, "end_lineno", node.lineno)
        if end_line - node.lineno + 1 > MAX_CHUNK_LINES:
            chunks.extend(_line_chunks("\n".join(lines[node.lineno - 1 : end_line]), "python"))
            continue
        chunks.append(
            Chunk(
                content="\n".join(lines[node.lineno - 1 : end_line]),
                start_line=node.lineno,
                end_line=end_line,
                language="python",
                symbol_name=node.name,
                symbol_type="class" if isinstance(node, ast.ClassDef) else "function",
            )
        )
    return chunks or _line_chunks(content, "python")


def chunk_document(file_path: str, content: str) -> list[Chunk]:
    language = detect_language(file_path)
    if language == "python":
        return _python_chunks(content)
    return _line_chunks(content, language)
