"""cmdop-skill — Decorator-based CLI framework for CMDOP skills.

Eliminates boilerplate by turning async functions into CLI subcommands::

    from cmdop_skill import Skill, Arg

    skill = Skill()  # name, version, description from pyproject.toml

    @skill.command
    async def greet(name: str = Arg(help="Who to greet", required=True)) -> dict:
        return {"message": f"Hello, {name}!"}

    if __name__ == "__main__":
        skill.run()
"""

from cmdop_skill._arg import Arg
from cmdop_skill._manifest import generate_manifest
from cmdop_skill._output import format_error, json_output, wrap_result
from cmdop_skill._publish import publish_skill
from cmdop_skill._resolve import resolve_project_meta
from cmdop_skill._skill import Skill
from cmdop_skill._skill_config import SkillCategory, SkillConfig
from cmdop_skill._testing import TestClient

__all__ = [
    "Arg",
    "Skill",
    "SkillCategory",
    "SkillConfig",
    "TestClient",
    "generate_manifest",
    "publish_skill",
    "resolve_project_meta",
    "json_output",
    "wrap_result",
    "format_error",
]
