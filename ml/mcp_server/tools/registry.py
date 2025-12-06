from typing import Dict, Any, Callable, List
import inspect


class ToolRegistry:
    """
    Простой реестр MCP-инструментов. Инструменты регистрируются через декоратор
    @tool_registry.register(name="...", description="...", parameters={...})
    и могут быть вызваны по имени.
    """

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str = "",
        parameters: Dict[str, Any] | None = None,
    ):
        def decorator(func: Callable):
            self._tools[name] = {
                "name": name,
                "description": description,
                "function": func,
                "parameters": parameters or self._extract_parameters(func),
                "is_async": inspect.iscoroutinefunction(func),
            }
            return func

        return decorator

    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        params = {}
        for param_name, param in sig.parameters.items():
            params[param_name] = {
                "type": param.annotation.__name__
                if param.annotation != inspect.Parameter.empty
                else "any",
                "required": param.default == inspect.Parameter.empty,
            }
        return params

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}")

        tool = self._tools[tool_name]
        func = tool["function"]

        try:
            if tool["is_async"]:
                result = await func(**parameters)
            else:
                result = func(**parameters)

            return {"success": True, "result": result}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e), "tool": tool_name}

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for tool in self._tools.values()
        ]


tool_registry = ToolRegistry()
