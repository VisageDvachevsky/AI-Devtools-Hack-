from ml.mcp_server.tools import tool_registry
from typing import Dict, Any


@tool_registry.register(
    name="calculate_sum",
    description="Calculate sum of two numbers"
)
async def calculate_sum(a: int, b: int) -> Dict[str, Any]:
    result = a + b
    return {"sum": result}


@tool_registry.register(
    name="get_weather",
    description="Get weather for a city"
)
async def get_weather(city: str) -> Dict[str, Any]:
    return {
        "city": city,
        "temperature": 20,
        "condition": "sunny"
    }
