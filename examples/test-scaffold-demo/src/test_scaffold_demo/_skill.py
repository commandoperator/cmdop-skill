"""test-scaffold-demo — CMDOP skill entry point."""

from __future__ import annotations

from cmdop_skill import Arg, Skill

skill = Skill(
    name="test-scaffold-demo",
    description="Auto-generated demo skill for testing scaffold",
    version="0.1.0",
)


@skill.command
def hello(
    name: str = Arg(help="Name to greet", required=True),
) -> dict:
    """Say hello."""
    return {"message": f"Hello, {name}!"}


def main() -> None:
    skill.run()


if __name__ == "__main__":
    main()
