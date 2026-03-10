# cmdop-skill

![cmdop-skill](https://raw.githubusercontent.com/commandoperator/cmdop-skill/main/static/cmdop_skill.webp)

Build and publish CMDOP skills.

## Install

```bash
pip install cmdop-skill
```

## Quick Start

### Create a new skill (scaffold wizard)

```bash
cmdop-skill init
```

Interactive wizard: name (with PyPI availability check), description, author. Category, tags, and visibility are determined automatically by the server during publish.

### Or write one from scratch

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

`Skill()` and `SkillConfig()` auto-resolve `name`, `version`, `description` from the nearest `pyproject.toml`. Explicit arguments still win:

```python
skill = Skill(name="override-name")  # only name overridden, rest from pyproject.toml
```

## Framework Features

- **`@skill.command`** — turn async/sync functions into CLI subcommands
- **`Arg()`** — declarative arguments with `help`, `required`, `default`, `choices`, `nargs`, `action`
- **`@skill.setup` / `@skill.teardown`** — lifecycle hooks
- **`TestClient`** — test harness for skills (`client.run()` and `client.run_cli()`)
- **`pyproject.toml` as single source of truth** — `name`, `version`, `description` auto-resolved; no duplication
- **Auto `src/` path** — `src/` is added to `sys.path` automatically
- **JSON output** — all commands return `{"ok": true, ...}` by default

## CLI Commands

| Command | Description |
|---|---|
| `init [path]` | Scaffold a new skill project (interactive wizard) |
| `install <path>` | Symlink skill into system skills directory |
| `uninstall <name>` | Remove skill from system skills directory |
| `run <path> <prompt>` | Run skill via cmdop SDK |
| `test <path>` | Run pytest in skill directory |
| `bump [path]` | Bump version in pyproject.toml (semver) |
| `check-name <name>` | Check if package name is available on PyPI |
| `release [path]` | Bump + build + upload to PyPI + publish to CMDOP |
| `publish` | Publish skill to the CMDOP marketplace |
| `list` | List your published skills |
| `config set-key` | Save API key globally |
| `config show` | Show saved config (key masked) |
| `config reset` | Remove saved API key |

### init

```bash
cmdop-skill init                        # scaffold in current directory
cmdop-skill init ./skills               # scaffold in ./skills/
```

Also available programmatically:

```python
from cmdop_skill.scaffold import ScaffoldConfig, scaffold_skill

config = ScaffoldConfig(name="my-skill", description="Does things")
files = scaffold_skill(config, target_dir=Path("."))
```

### config

API key is resolved in order: `--api-key` flag > `CMDOP_API_KEY` env > saved config > interactive prompt.

```bash
cmdop-skill config set-key              # interactive (masked input)
cmdop-skill config set-key cmdop_xxx    # direct
cmdop-skill config show
cmdop-skill config reset
```

On auth errors (401/403), the CLI prompts for a new key and saves it automatically.

### install / uninstall

```bash
cmdop-skill install ./skills/my-skill
# Installed my-skill -> ~/Library/Application Support/cmdop/skills/my-skill (symlink)

cmdop-skill uninstall my-skill
```

### bump

```bash
cmdop-skill bump                        # patch: 0.1.0 -> 0.1.1
cmdop-skill bump --minor                # minor: 0.1.1 -> 0.2.0
cmdop-skill bump --major                # major: 0.2.0 -> 1.0.0
```

### check-name

```bash
cmdop-skill check-name my-cool-skill
# my-cool-skill is available on PyPI

cmdop-skill check-name requests
# requests is taken on PyPI
```

### release

```bash
cmdop-skill release                     # bump patch + build + PyPI + CMDOP
cmdop-skill release -b minor            # bump minor
cmdop-skill release --no-bump           # current version
cmdop-skill release --test-pypi         # TestPyPI only (skips CMDOP)
cmdop-skill release --no-publish        # PyPI only (skips CMDOP)
```

## Publish

Only the skill name is required to create a skill on the marketplace. Everything else is automatic:

- **Category** — determined by the server from manifest keywords
- **Tags** — extracted from `pyproject.toml` keywords
- **Description** — from README / pyproject.toml
- **Repository URL** — from pyproject.toml
- **Visibility** — public by default
- **Translations** — generated server-side via LLM

```bash
cmdop-skill publish --path .            # publish to prod
cmdop-skill publish --mode local        # publish to localhost:8000
cmdop-skill publish --json              # CI mode (no interactive prompts)
```

## Skill Structure

```
my-skill/
├── pyproject.toml
├── Makefile
├── README.md
├── .gitignore
├── skill/
│   ├── config.py            # SkillConfig manifest (required)
│   ├── skill.md             # skill system prompt / description
│   └── readme.md            # description for marketplace
├── src/my_skill/
│   ├── __init__.py
│   └── ...                  # your code
└── tests/
```

`skill/config.py` — minimal manifest:

```python
from cmdop_skill import SkillConfig

config = SkillConfig()
```

All metadata (`name`, `version`, `description`) is auto-resolved from `pyproject.toml`. Category, tags, and visibility are determined automatically by the server during publish.

## Python API

| Export | Description |
|---|---|
| `Skill` | Main class — registers commands, runs CLI |
| `Arg` | Argument descriptor with metadata |
| `SkillConfig` | Typed skill manifest (pydantic model) |
| `TestClient` | Test harness — `await client.run("cmd", key=val)` / `await client.run_cli("cmd", "--flag")` |
| `resolve_project_meta` | Resolve `name`/`version`/`description` from nearest `pyproject.toml` |
| `generate_manifest` | Generate `skill/config.py` content |
| `publish_skill` | Programmatic publish to marketplace |
| `json_output` / `wrap_result` / `format_error` | Output formatting helpers |
| `scaffold.ScaffoldConfig` | Pydantic model for scaffold parameters |
| `scaffold.scaffold_skill` | Generate a complete skill directory from config |
