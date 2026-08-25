"""Packaging checks for PEP 561 typing support."""

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_wheel_includes_py_typed(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv not on PATH")

    subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(tmp_path)],
        check=True,
        cwd=REPO_ROOT,
    )

    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()

    assert "structlog_config/py.typed" in names
