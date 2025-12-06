from .registry import tool_registry

# Импортируем инструменты, чтобы они зарегистрировались при импорте пакета.
# Original tools
from . import hh_tools  # noqa: F401
from . import hh_tools_multi  # noqa: F401
from . import github_tools  # noqa: F401

# Enterprise tools - NEW!
from . import github_tools_advanced  # noqa: F401
from . import linkedin_tools  # noqa: F401
from . import stackoverflow_tools  # noqa: F401

__all__ = ["tool_registry"]
