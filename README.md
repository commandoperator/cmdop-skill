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
- **`Arg()`** — declarative arguments with `help`, `required`, `default`, `choices`
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
| `publish` | Publish skill to the CMDOP marketplace |
| `list` | List your published skills |
| `install <path>` | Symlink skill into system skills directory |
| `uninstall <name>` | Remove skill from system skills directory |
| `run <path> <prompt>` | Run skill via cmdop SDK |
| `test <path>` | Run pytest in skill directory |

### install / uninstall

```bash
cmdop-skill install ./skills/email-macos
# ✓ Installed email-macos → ~/Library/Application Support/cmdop/skills/email-macos (symlink)

cmdop-skill uninstall email-macos
# ✓ Uninstalled email-macos
```

### run

```bash
cmdop-skill run ./skills/email-macos "list my email accounts"
# ✓ Done (2.3s, 1234 tokens)

cmdop-skill run ./skills/email-macos "send test" --machine my-mac --model gpt-4o --json
```

### test

```bash
cmdop-skill test ./skills/email-macos
cmdop-skill test ./skills/email-macos --args "-v -k test_send"
```

### publish

```bash
cmdop-skill publish --api-key cmdop_xxx
cmdop-skill publish --json              # CI mode
```

## Development

```bash
make install          # pip install -e .
make install-local    # use local cmdop package (editable)
make test             # pytest tests/ -v
make lint             # ruff check src/
```

## API

| Export | Description |
|---|---|
| `Skill` | Main class — registers commands, runs CLI |
| `Arg` | Argument descriptor with metadata |
| `TestClient` | Test harness — `client.run("command", "--flag", "value")` |
| `generate_manifest` | Generate skill.md manifest |
| `publish_skill` | Programmatic publish to marketplace |
| `json_output` / `wrap_result` / `format_error` | Output formatting helpers |
