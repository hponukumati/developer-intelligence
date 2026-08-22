from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.services.local_review import ChangedHunk, InvalidPatch, parse_unified_diff
from app.services.review import _evidence_for_hunk


PATCH = """diff --git a/src/payments.py b/src/payments.py
--- a/src/payments.py
+++ b/src/payments.py
@@ -10,2 +10,3 @@
 def charge():
+    retry()
     return True
"""


def test_parses_changed_hunk_new_file_range():
    assert parse_unified_diff(PATCH) == [
        ChangedHunk(file_path="src/payments.py", start_line=10, end_line=12)
    ]


def test_rejects_binary_and_traversal_patches():
    with pytest.raises(InvalidPatch, match="binary"):
        parse_unified_diff("GIT binary patch\n+++ b/image.png\n@@ -1 +1 @@")
    with pytest.raises(InvalidPatch, match="unsafe"):
        parse_unified_diff("+++ b/../secret.txt\n@@ -1 +1 @@\n+secret")
    with pytest.raises(InvalidPatch, match="renamed"):
        parse_unified_diff("rename from old.txt\n+++ b/new.txt\n@@ -1 +1 @@\n+value")
    with pytest.raises(InvalidPatch, match="unsafe"):
        parse_unified_diff("--- a/../secret.txt\n+++ b/src/safe.txt\n@@ -1 +1 @@\n+value")


def test_review_evidence_is_scoped_to_overlapping_chunks():
    captured = []
    chunk = SimpleNamespace(
        id=uuid4(),
        file_path="src/payments.py",
        start_line=10,
        end_line=14,
        content="def charge():\n    retry()",
    )

    class Result:
        def scalars(self):
            return self

        def all(self):
            return [chunk]

    class Session:
        def execute(self, statement):
            captured.append(statement)
            return Result()

    repository = SimpleNamespace(id=uuid4())
    hunk = parse_unified_diff(PATCH)[0]
    evidence = _evidence_for_hunk(Session(), repository, uuid4(), hunk)

    assert evidence[0].status == "matched"
    assert evidence[0].chunk_id == chunk.id
    compiled = str(captured[0].compile(dialect=postgresql.dialect()))
    assert "organization_id" in compiled
    assert "repository_id" in compiled
    assert "file_path" in compiled
    assert "start_line <=" in compiled
    assert "end_line >=" in compiled


def test_review_evidence_reports_missing_local_context():
    class Result:
        def scalars(self):
            return self

        def all(self):
            return []

    class Session:
        def execute(self, _statement):
            return Result()

    evidence = _evidence_for_hunk(
        Session(),
        SimpleNamespace(id=uuid4()),
        uuid4(),
        parse_unified_diff(PATCH)[0],
    )

    assert evidence[0].status == "no_local_context"
    assert evidence[0].chunk_id is None
