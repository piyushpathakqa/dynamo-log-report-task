"""Verifier for dynamo/access-review-backfill.

Compares /app/access_review.csv against ground truth held here. The
request columns and the issued rows are checked against the snapshot
kept in this directory (not the agent-writable copy under /app/data),
so tampering with inputs cannot influence grading.
"""

import hashlib
import os

APP = "/app"
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(APP, "access_review.csv")
EXPECTED = os.path.join(HERE, "expected_access_review.csv")
PARTIAL = os.path.join(HERE, "partial_snapshot.csv")
HEADER = "row_id,user,path,operation,decision"


def _read(path):
    with open(path, "rb") as f:
        data = f.read()
    return data


def _lines(data):
    return data.decode("utf-8").split("\n")


def test_report_exists_and_well_formed():
    """Criterion 4: /app/access_review.csv exists with the exact header,
    rows R0001 through R0240 in ascending row_id whose request fields
    match the worksheet, LF line endings, and every decision PERMIT or
    DENY."""
    assert os.path.isfile(REPORT), "/app/access_review.csv is missing"
    data = _read(REPORT)
    assert b"\r" not in data, "report must use LF line endings"
    assert data.endswith(b"\n"), "report must end with a newline"
    lines = _lines(data)
    assert lines[-1] == ""
    lines = lines[:-1]
    assert lines[0] == HEADER, "header line differs from the specification"
    assert len(lines) == 241, f"expected 240 data rows, found {len(lines) - 1}"
    partial = _lines(_read(PARTIAL))[:-1]
    for i, line in enumerate(lines[1:]):
        fields = line.split(",")
        assert len(fields) == 5, f"row {i + 1} malformed: {line!r}"
        assert fields[0] == f"R{i + 1:04d}", f"row_id off at data row {i + 1}"
        pfields = partial[1 + i].split(",")
        assert fields[:4] == pfields[:4], \
            f"request fields differ from the worksheet at {fields[0]}"
        assert fields[4] in ("PERMIT", "DENY"), \
            f"decision at {fields[0]} is {fields[4]!r}"


def test_issued_rows_reproduced():
    """Criterion 3: the 90 rows the audit tool completed and issued are
    reproduced byte for byte."""
    report = _lines(_read(REPORT))
    partial = _lines(_read(PARTIAL))
    assert report[1:91] == partial[1:91], \
        "issued rows R0001-R0090 were not reproduced unchanged"


def test_decisions_match_filer_enforcement():
    """Criterion 2: every completed decision equals the outcome the filer
    enforces under the captured ACLs per audit_spec.md §6 — the whole
    report must match the expected report exactly."""
    got = _read(REPORT)
    want = _read(EXPECTED)
    if got != want:
        g, w = _lines(got), _lines(want)
        wrong = [g[i].split(",")[0] for i in range(1, min(len(g), len(w)) - 1)
                 if g[i] != w[i]]
        raise AssertionError(
            f"{len(wrong)} rows differ from the enforced outcome "
            f"(e.g. {wrong[:5]}); sha256 {hashlib.sha256(got).hexdigest()[:12]} "
            f"!= {hashlib.sha256(want).hexdigest()[:12]}")
