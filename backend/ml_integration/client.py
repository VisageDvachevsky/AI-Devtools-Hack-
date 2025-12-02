import httpx
from typing import Dict, Any, List
from backend.core.config import settings


class MLClient:
    """Abstraction layer for ML services communication"""

    def __init__(self):
        self.mcp_server_url = settings.MCP_SERVER_URL
        self.timeout = 30.0

    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.mcp_server_url}/agents/execute",
                json={
                    "agent_name": agent_name,
                    "input_data": input_data,
                    "config": config or {}
                }
            )
            response.raise_for_status()
            return response.json()

    async def list_agents(self) -> List[str]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.mcp_server_url}/agents/list")
            response.raise_for_status()
            return response.json().get("agents", [])

    async def call_mcp_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.mcp_server_url}/tools/call",
                json={
                    "tool_name": tool_name,
                    "parameters": parameters
                }
            )
            response.raise_for_status()
            return response.json()

    async def list_mcp_tools(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.mcp_server_url}/tools/list")
            response.raise_for_status()
            return response.json().get("tools", [])
