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


def _pip_install(tool: str) -> None:
    """Install *tool* using the best available installer (uv pip > pip > pip3)."""
    # 1. uv pip — works with uv-created venvs that have no pip
    uv = shutil.which("uv")
    if uv:
        r = subprocess.run([uv, "pip", "install", tool, "-q"], capture_output=True)
        if r.returncode == 0:
            return
    # 2. pip via sys.executable — standard venvs
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", tool, "-q"],
        capture_output=True,
    )
    if r.returncode == 0:
        return
    # 3. pip3 — fallback for system Python without pip module
    pip3 = shutil.which("pip3")
    if pip3:
        r = subprocess.run([pip3, "install", tool, "-q"], capture_output=True)
        if r.returncode == 0:
            return
    raise RuntimeError(
        f"Could not install '{tool}'. "
        "Install it manually: pip install build twine"
    )


def ensure_build_tools() -> None:
    """Install ``build`` and ``twine`` if missing."""
    for tool in ("build", "twine"):
        r = subprocess.run(
            [sys.executable, "-m", tool, "--version"],
            capture_output=True,
        )
        if r.returncode != 0:
            _pip_install(tool)


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


CMDOP_SKILLS_URL = "https://cmdop.com/skills"

CMDOP_README_BADGE = """\
> **[CMDOP Skill]({url})** — install and use via [CMDOP agent](https://cmdop.com):
> ```
> cmdop-skill install {name}
> ```

"""


def inject_readme_badge(path: Path, name: str) -> bool:
    """Add CMDOP badge block to top of README.md (after the title).

    Returns True if modified, False if already present or no README.
    """
    readme = path / "README.md"
    if not readme.is_file():
        return False

    text = readme.read_text(encoding="utf-8")
    if "CMDOP Skill" in text:
        return False  # already has badge

    url = f"{CMDOP_SKILLS_URL}/{name}/"
    badge = CMDOP_README_BADGE.format(url=url, name=name)

    lines = text.split("\n", 2)
    # Insert after first heading line (# title)
    if lines and lines[0].startswith("#"):
        # title + blank line + badge + rest
        parts = [lines[0], "", badge.rstrip()]
        if len(lines) > 1:
            rest = "\n".join(lines[1:]).lstrip("\n")
            parts.append(rest)
        text = "\n".join(parts)
    else:
        text = badge + text

    readme.write_text(text, encoding="utf-8")
    return True


def patch_pyproject_urls(path: Path, name: str) -> bool:
    """Add/update Homepage URL in pyproject.toml to point to CMDOP skills page.

    Returns True if modified.
    """
    pyproject = path / "pyproject.toml"
    if not pyproject.is_file():
        return False

    import re

    text = pyproject.read_text(encoding="utf-8")
    skill_url = f"{CMDOP_SKILLS_URL}/{name}/"
    changed = False

    # Update or add Homepage
    if re.search(r'^Homepage\s*=', text, re.MULTILINE):
        new_text = re.sub(
            r'^(Homepage\s*=\s*)["\'].*?["\']',
            f'\\1"{skill_url}"',
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if new_text != text:
            text = new_text
            changed = True
    elif "[project.urls]" in text:
        text = text.replace(
            "[project.urls]",
            f'[project.urls]\nHomepage = "{skill_url}"',
            1,
        )
        changed = True

    if changed:
        pyproject.write_text(text, encoding="utf-8")
    return changed


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
