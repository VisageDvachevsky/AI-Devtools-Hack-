from .registry import tool_registry

# Импортируем инструменты, чтобы они зарегистрировались при импорте пакета.
from . import hh_tools  # noqa: F401
from . import hh_tools_multi  # noqa: F401
from . import github_tools  # noqa: F401

__all__ = ["tool_registry"]
