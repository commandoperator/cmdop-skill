# cmdop-skill

Decorator-based CLI framework for CMDOP skills + dev toolchain.

## Install

```bash
pip install cmdop-skill
```

## Quick Start

```python
from cmdop_skill import Skill, Arg

skill = Skill(name="my-skill", description="Does things", version="1.0.0")

@skill.command
async def greet(name: str = Arg(help="Who to greet", required=True)) -> dict:
    """Say hello."""
    return {"message": f"Hello, {name}!"}

if __name__ == "__main__":
    skill.run()
```

## Framework Features

- **`@skill.command`** — turn async/sync functions into CLI subcommands
- **`Arg()`** — declarative arguments with `help`, `required`, `default`, `choices`, `nargs`, `action`
- **`@skill.setup` / `@skill.teardown`** — lifecycle hooks
- **`TestClient`** — test harness for skills
- **Auto `src/` path** — `src/` is added to `sys.path` automatically
- **JSON output** — all commands return `{"ok": true, ...}` by default

## CLI Commands

```
cmdop-skill --help
```

| Command | Description |
|---|---|
| `install <path>` | Symlink skill into system skills directory |
| `uninstall <name>` | Remove skill from system skills directory |
| `publish` | Publish skill to the CMDOP marketplace |
| `list` | List your published skills |
| `bump [path]` | Bump version in pyproject.toml (semver) |
| `check-name <name>` | Check if package name is available on PyPI |
| `release [path]` | Bump + build + upload to PyPI + publish to CMDOP |
| `run <path> <prompt>` | Run skill via cmdop SDK |
| `test <path>` | Run pytest in skill directory |
| `config set-key` | Save API key globally |
| `config show` | Show saved config (key masked) |
| `config reset` | Remove saved API key |

### Config

API key is resolved in order: `--api-key` flag > `CMDOP_API_KEY` env > saved config > interactive prompt.

```bash
cmdop-skill config set-key              # interactive (masked input)
cmdop-skill config set-key cmdop_xxx    # direct
cmdop-skill config show
# api_key: cmdop_xx...xxxx
# path:    ~/Library/Application Support/cmdop/configs/apikey.json

cmdop-skill config reset
```

On auth errors (401/403), the CLI prompts for a new key and saves it automatically.

### install / uninstall

```bash
cmdop-skill install ./skills/email-macos
# ✓ Installed email-macos → ~/Library/Application Support/cmdop/skills/email-macos (symlink)

cmdop-skill uninstall email-macos
```

### publish

```bash
cmdop-skill publish                     # interactive wizard
cmdop-skill publish --json              # CI mode
```

### bump

```bash
cmdop-skill bump                        # patch: 0.1.0 → 0.1.1
cmdop-skill bump --minor                # minor: 0.1.1 → 0.2.0
cmdop-skill bump --major                # major: 0.2.0 → 1.0.0
cmdop-skill bump ./path/to/skill
```

### check-name

```bash
cmdop-skill check-name my-cool-skill
# ✓ my-cool-skill is available on PyPI

cmdop-skill check-name requests
# ✗ requests is taken on PyPI
# v2.31.0  Python HTTP for Humans.
# https://pypi.org/project/requests/
```

### release

```bash
cmdop-skill release                     # bump patch + build + PyPI + CMDOP
cmdop-skill release -b minor            # bump minor
cmdop-skill release --no-bump           # current version
cmdop-skill release --test-pypi         # TestPyPI only (skips CMDOP)
cmdop-skill release --no-publish        # PyPI only (skips CMDOP)
cmdop-skill release ./path/to/skill
```

### run

```bash
cmdop-skill run ./skills/email-macos "list my email accounts"
cmdop-skill run ./skills/email-macos "send test" --machine my-mac --model gpt-4o --json
```

### test

```bash
cmdop-skill test ./skills/email-macos
cmdop-skill test ./skills/email-macos --args "-v -k test_send"
```

## Development

```bash
make install          # pip install -e .
make test             # pytest tests/ -v
make lint             # ruff check src/
```

## Skill Structure

```
my-skill/
├── src/my_skill/
├── tests/
├── skill/
│   ├── config.py           # SkillConfig manifest (required)
│   └── readme.md           # description for LLM / marketplace
├── pyproject.toml
└── Makefile
```

`skill/config.py` — typed manifest:

```python
from cmdop_skill import SkillConfig

config = SkillConfig(
    name="my-skill",
    visibility="public",
)
```

Fields like `version`, `description`, `requires`, `tags`, `repository_url` are auto-filled from `pyproject.toml` if not set in config.

## API

| Export | Description |
|---|---|
| `Skill` | Main class — registers commands, runs CLI |
| `SkillConfig` | Typed skill manifest (pydantic model) |
| `Arg` | Argument descriptor with metadata |
| `TestClient` | Test harness — `client.run("command", "--flag", "value")` |
| `generate_manifest` | Generate `skill/config.py` content |
| `publish_skill` | Programmatic publish to marketplace |
| `json_output` / `wrap_result` / `format_error` | Output formatting helpers |
