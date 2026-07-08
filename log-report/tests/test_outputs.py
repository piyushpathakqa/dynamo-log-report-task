# checks report.json against the known access.log fixture.
# expected: total=6, ips=3 (192.168.0.1, 192.168.0.2, 10.0.0.5), top=/index.html

import json
from pathlib import Path

import pytest

REPORT = Path("/app/report.json")
REQUIRED_KEYS = {"total_requests", "unique_ips", "top_path"}


@pytest.fixture(scope="module")
def report():
    if not REPORT.exists():
        pytest.fail("no /app/report.json found")
    with REPORT.open() as f:
        return json.load(f)


def test_report_is_valid_json_object():
    # criterion 1: report.json exists and is a single JSON object
    assert REPORT.exists(), "no /app/report.json found"
    with REPORT.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "report.json must contain a JSON object"


def test_report_has_exact_keys(report):
    # criterion 2: exactly total_requests, unique_ips, top_path
    assert set(report.keys()) == REQUIRED_KEYS, (
        f"expected keys {sorted(REQUIRED_KEYS)}, got {sorted(report.keys())}"
    )


def test_total_requests(report):
    # criterion 3: total_requests == number of non-empty log lines
    assert report["total_requests"] == 6


def test_unique_ips(report):
    # criterion 4: unique_ips == number of distinct client IPs
    assert report["unique_ips"] == 3


def test_top_path(report):
    # criterion 5: top_path == most frequently requested path
    assert report["top_path"] == "/index.html"
