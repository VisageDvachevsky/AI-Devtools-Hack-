from ml.agents.registry import agent_registry
from typing import Dict, Any


@agent_registry.register(
    name="simple_agent",
    description="Simple example agent"
)
async def simple_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    query = input_data.get("query", "")

    response = f"Processed query: {query}"

    return {
        "response": response,
        "metadata": {
            "processed": True,
            "config_used": config
        }
    }
