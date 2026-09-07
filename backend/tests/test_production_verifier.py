import os
import subprocess
from pathlib import Path


def test_verifier_reports_inconclusive_for_a_network_timeout(tmp_path: Path):
    fake_curl = tmp_path / "curl"
    fake_curl.write_text("#!/bin/sh\nexit 28\n")
    fake_curl.chmod(0o755)
    script = Path(__file__).parents[2] / "scripts" / "verify-production.sh"

    result = subprocess.run(
        [str(script), "https://example.test"],
        env={**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout.strip() == "inconclusive"


def test_verifier_reports_healthy_for_a_healthy_payload(tmp_path: Path):
    fake_curl = tmp_path / "curl"
    fake_curl.write_text('#!/bin/sh\nprintf %s \'{"status":"healthy"}\'\n')
    fake_curl.chmod(0o755)
    script = Path(__file__).parents[2] / "scripts" / "verify-production.sh"

    result = subprocess.run([str(script), "https://example.test"], env={**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}"}, text=True, capture_output=True, check=False)

    assert result.returncode == 0
    assert result.stdout.strip() == "healthy"
