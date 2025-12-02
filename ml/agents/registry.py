from typing import Dict, Any, Callable, List
import inspect


class AgentRegistry:
    """
    Example:
        @agent_registry.register(name="research_agent", description="Research agent")
        async def research_agent(input_data: Dict, config: Dict) -> Dict[str, Any]:
            return {"answer": "..."}
    """

    def __init__(self):
        self._agents: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str = "",
    ):
        def decorator(func: Callable):
            self._agents[name] = {
                "name": name,
                "description": description,
                "function": func,
                "is_async": inspect.iscoroutinefunction(func)
            }
            return func
        return decorator

    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' not found. Available: {list(self._agents.keys())}")

        agent = self._agents[agent_name]
        func = agent["function"]

        try:
            if agent["is_async"]:
                result = await func(input_data=input_data, config=config)
            else:
                result = func(input_data=input_data, config=config)

            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())


agent_registry = AgentRegistry()
