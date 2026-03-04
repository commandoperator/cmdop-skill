"""Scaffold subpackage — generate new CMDOP skill projects."""

from cmdop_skill.scaffold._generator import scaffold_skill
from cmdop_skill.scaffold._models import ScaffoldConfig

__all__ = ["ScaffoldConfig", "scaffold_skill"]
