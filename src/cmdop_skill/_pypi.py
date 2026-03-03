"""Build, publish, and check Python packages on PyPI."""

from __future__ import annotations

import json
import shutil
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def _ssl_context() -> ssl.SSLContext:
    """SSL context that works on macOS without certificate hassle."""
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def clean(path: Path) -> None:
    """Remove dist/, build/, *.egg-info before a fresh build."""
    for name in ("dist", "build"):
        d = path / name
        if d.exists():
            shutil.rmtree(d)
    for egg in path.glob("*.egg-info"):
        shutil.rmtree(egg)
    src = path / "src"
    if src.exists():
        for egg in src.rglob("*.egg-info"):
            shutil.rmtree(egg)


def ensure_build_tools() -> None:
    """Install ``build`` and ``twine`` if missing."""
    for tool in ("build", "twine"):
        r = subprocess.run(
            [sys.executable, "-m", "pip", "show", tool],
            capture_output=True,
        )
        if r.returncode != 0:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool, "-q"],
                check=True,
            )


def build(path: Path) -> tuple[bool, str]:
    """Run ``python -m build`` in *path*.

    Returns:
        (success, stderr_or_empty)
    """
    ensure_build_tools()
    r = subprocess.run(
        [sys.executable, "-m", "build"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0, r.stderr


def upload(path: Path, test_pypi: bool = False) -> tuple[bool, str]:
    """Upload dist/* via ``twine upload``.

    Args:
        path: Project root (must contain ``dist/``).
        test_pypi: Upload to TestPyPI instead of production PyPI.

    Returns:
        (success, output)
    """
    dist = path / "dist"
    files = list(dist.glob("*"))
    if not files:
        return False, "No dist files found. Build first."

    cmd = [sys.executable, "-m", "twine", "upload"]
    if test_pypi:
        cmd.extend(["--repository", "testpypi"])
    cmd.extend(str(f) for f in files)

    r = subprocess.run(cmd, cwd=path, capture_output=True, text=True)
    output = r.stdout + r.stderr
    return r.returncode == 0, output


def dist_files(path: Path) -> list[tuple[str, int]]:
    """Return list of (filename, size_bytes) in dist/."""
    dist = path / "dist"
    if not dist.exists():
        return []
    return [(f.name, f.stat().st_size) for f in sorted(dist.glob("*"))]


def check_pypi_name(name: str) -> dict[str, object]:
    """Check if a package name is taken on PyPI.

    Returns:
        Dict with keys: available (bool), name, version (if taken), url.
    """
    url = f"https://pypi.org/pypi/{name}/json"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=_ssl_context()) as resp:
            data = json.loads(resp.read())
            info = data.get("info", {})
            return {
                "available": False,
                "name": info.get("name", name),
                "version": info.get("version", "?"),
                "summary": info.get("summary", ""),
                "url": f"https://pypi.org/project/{name}/",
            }
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"available": True, "name": name}
        return {"available": False, "name": name, "error": f"HTTP {exc.code}"}
    except Exception as exc:
        return {"available": False, "name": name, "error": str(exc)}
