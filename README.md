# cmdop-skill

![cmdop-skill](https://raw.githubusercontent.com/markolofsen/assets/main/libs/cmdop/cmdop-skill.webp)

Build and publish CMDOP skills.

## Install

```bash
pip install cmdop-skill
```

## Quick Start

### Scaffold a new skill

```bash
cmdop-skill init
```

Interactive wizard: name (with PyPI availability check), description, author.

### Or write from scratch

```python
from cmdop_skill import Skill, Arg

skill = Skill()  # name, version, description from pyproject.toml

@skill.command
async def greet(name: str = Arg(help="Who to greet", required=True)) -> dict:
    """Say hello."""
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    skill.run()
```

`Skill()` auto-resolves `name`, `version`, `description` from the nearest `pyproject.toml`. Explicit arguments still win.

## Core Features

| Feature | Description |
|---|---|
| `@skill.command` | Turn async/sync functions into CLI subcommands |
| `Arg()` | Declarative arguments: `help`, `required`, `default`, `choices`, `nargs`, `action` |
| `@skill.setup` / `@skill.teardown` | Lifecycle hooks (run before/after every command) |
| `SkillCache` | Typed disk cache with TTL, scoped per skill — [docs](./@docs/cache.md) |
| `TestClient` | Test harness: `client.run("cmd", key=val)` / `client.run_cli("cmd --flag")` |
| JSON output | All commands return `{"ok": true, ...}` — exit 0 on success, exit 1 on error |
| Auto `src/` path | `src/` added to `sys.path` automatically |
| Single source of truth | `name`, `version`, `description` from `pyproject.toml`, no duplication |

## SkillCache

Built-in typed disk cache — no extra dependencies, platform-aware paths:

```python
from cmdop_skill import SkillCache

cache = SkillCache("my-skill")
cache.set("data", payload, ttl=86400)   # 24 hours
data = cache.get("data")                # None if missing or expired
```

Paths: `~/Library/Caches/cmdop/skills/<skill>/` (macOS), `~/.cache/cmdop/skills/<skill>/` (Linux).
Full reference → [`@docs/cache.md`](./@docs/cache.md)

## Skill Structure

```
my-skill/
├── pyproject.toml
├── Makefile
├── README.md
├── skill/
│   ├── config.py       # SkillConfig manifest (required)
│   └── readme.md       # description shown in marketplace
├── src/my_skill/
│   ├── __init__.py
│   └── ...
└── tests/
```

`skill/config.py` — minimal manifest:

```python
from cmdop_skill import SkillConfig

config = SkillConfig()  # all fields auto-resolved from pyproject.toml
```

## CLI

| Command | Description |
|---|---|
| `init [path]` | Scaffold a new skill project |
| `install <path>` | Symlink skill into system skills directory |
| `uninstall <name>` | Remove skill |
| `bump [--minor\|--major]` | Bump version in pyproject.toml |
| `check-name <name>` | Check PyPI availability |
| `release [--no-bump\|--no-publish]` | Bump + build + PyPI + CMDOP |
| `publish [--path]` | Publish to CMDOP marketplace |
| `list` | List your published skills |
| `config set-key / show / reset` | Manage API key |

API key resolution order: `--api-key` flag → `CMDOP_API_KEY` env → saved config → interactive prompt.

## Python API

| Export | Description |
|---|---|
| `Skill` | Main class — registers commands, runs CLI |
| `Arg` | Argument descriptor |
| `SkillConfig` | Typed skill manifest (Pydantic model) |
| `SkillCache` | Disk cache — see [`@docs/cache.md`](./@docs/cache.md) |
| `CacheEntry` | Pydantic model for a cached value with metadata |
| `TestClient` | Test harness |
| `resolve_project_meta` | Resolve `name`/`version`/`description` from `pyproject.toml` |
| `generate_manifest` | Generate `skill/config.py` content |
| `publish_skill` | Programmatic publish |
| `json_output` / `wrap_result` / `format_error` | Output helpers |
| `scaffold.ScaffoldConfig` / `scaffold.scaffold_skill` | Programmatic scaffolding |

## Developer Docs

Deep-dive references in [`@docs/`](./@docs/README.md):

- [Architecture](./@docs/architecture.md) — system diagram, components, data flow
- [Publish Flow](./@docs/publish-flow.md) — CLI → Django → DB
- [Install Flow](./@docs/install-flow.md) — deep link → Go loader → validation
- [Package Environment](./@docs/package-env.md) — venv, PATH enrichment
- [Skill Format](./@docs/skill-format.md) — skill.md frontmatter rules
- [SkillCache](./@docs/cache.md) — cache API, paths, testing
