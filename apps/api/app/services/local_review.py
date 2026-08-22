"""Safe parsing for user-supplied, local unified diffs.

Patch content is untrusted data. This module only parses line prefixes and never
executes, imports, opens, or otherwise follows a path from a patch.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath


MAX_CHANGED_FILES = 100
MAX_HUNKS = 500
HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


class InvalidPatch(ValueError):
    pass


@dataclass(frozen=True)
class ChangedHunk:
    file_path: str
    start_line: int
    end_line: int


def _validated_path(header_value: str, prefix: str) -> str:
    value = header_value.strip().split("\t", maxsplit=1)[0]
    if not value.startswith(prefix):
        raise InvalidPatch(f"patch paths must use the {prefix} unified-diff prefix")
    path = value[2:]
    pure_path = PurePosixPath(path)
    if (
        not path
        or path.startswith("/")
        or "\x00" in path
        or any(part in {"", ".", ".."} for part in pure_path.parts)
    ):
        raise InvalidPatch("patch contains an unsafe file path")
    return path


def parse_unified_diff(patch: str) -> list[ChangedHunk]:
    """Return changed new-file line ranges from a bounded, text-only unified diff."""
    if "\x00" in patch or "GIT binary patch" in patch or "Binary files " in patch:
        raise InvalidPatch("binary patches are not supported")

    hunks: list[ChangedHunk] = []
    seen_paths: set[str] = set()
    current_path: str | None = None
    hunk_start: int | None = None
    hunk_end: int | None = None

    def finish_hunk() -> None:
        nonlocal hunk_start, hunk_end
        if hunk_start is not None and hunk_end is not None and current_path is not None:
            hunks.append(ChangedHunk(current_path, hunk_start, hunk_end))
        hunk_start = None
        hunk_end = None

    for raw_line in patch.splitlines():
        if raw_line.startswith(("rename ", "copy ")):
            raise InvalidPatch("renamed and copied files are not supported")
        if raw_line.startswith("--- ") and raw_line[4:].strip() != "/dev/null":
            _validated_path(raw_line[4:], "a/")
        if raw_line.startswith("+++ "):
            finish_hunk()
            current_path = _validated_path(raw_line[4:], "b/")
            seen_paths.add(current_path)
            if len(seen_paths) > MAX_CHANGED_FILES:
                raise InvalidPatch("patch exceeds the changed-file limit")
            continue

        hunk = HUNK_HEADER.match(raw_line)
        if hunk:
            if current_path is None:
                raise InvalidPatch("hunk appears before a new-file path")
            finish_hunk()
            hunk_start = int(hunk.group(1))
            line_count = int(hunk.group(2) or "1")
            hunk_end = hunk_start + max(line_count - 1, 0)
            if len(hunks) >= MAX_HUNKS:
                raise InvalidPatch("patch exceeds the hunk limit")

    finish_hunk()
    if not hunks:
        raise InvalidPatch("patch does not contain a supported unified-diff hunk")
    return hunks
