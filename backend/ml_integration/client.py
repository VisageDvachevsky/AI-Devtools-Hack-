import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from httpx import HTTPStatusError

from backend.core.config import settings

logger = logging.getLogger(__name__)


class MLClientMetrics:
    def __init__(self):
        self.total_calls = 0
        self.total_errors = 0
        self.total_retries = 0
        self.total_duration_ms = 0
        self.calls_by_tool: Dict[str, int] = {}

    def record_call(self, tool_name: str, duration_ms: int, error: bool = False, retried: bool = False):
        self.total_calls += 1
        self.total_duration_ms += duration_ms
        self.calls_by_tool[tool_name] = self.calls_by_tool.get(tool_name, 0) + 1
        if error:
            self.total_errors += 1
        if retried:
            self.total_retries += 1

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "total_retries": self.total_retries,
            "avg_duration_ms": int(self.total_duration_ms / max(1, self.total_calls)),
            "calls_by_tool": self.calls_by_tool
        }


class MLClient:
    def __init__(self):
        self.mcp_server_url = settings.MCP_SERVER_URL
        self.timeout = 60.0
        self.max_retries = 3
        self.retry_delay = 1.0
        self.headers = {}
        if settings.MCP_AUTH_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.MCP_AUTH_TOKEN}"
        self.metrics = MLClientMetrics()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        try:
            response.raise_for_status()
        except HTTPStatusError as exc:
            status_code = response.status_code

            # Parse error details
            try:
                detail = response.json()
            except Exception:  # noqa: BLE001
                detail = response.text

            # Handle specific error codes
            if status_code == 401:
                raise RuntimeError("MCP authentication failed (401): Invalid or missing token") from exc
            if status_code == 404:
                raise RuntimeError(f"MCP resource not found (404): {detail}") from exc
            if status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RuntimeError(f"MCP rate limited (429): Retry after {retry_after}s") from exc
            if status_code >= 500:
                raise RuntimeError(f"MCP server error ({status_code}): {detail}") from exc

            raise RuntimeError(f"MCP request failed ({status_code}): {detail}") from exc

        try:
            return response.json()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError("Failed to parse MCP response as JSON") from exc

    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.post(
                f"{self.mcp_server_url}/agents/execute",
                json={
                    "agent_name": agent_name,
                    "input_data": input_data,
                    "config": config or {}
                }
            )
            return self._handle_response(response)

    async def list_agents(self) -> List[str]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.get(f"{self.mcp_server_url}/agents/list")
            data = self._handle_response(response)
            return data.get("agents", [])

    async def call_mcp_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        last_error = None
        retried = False

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    response = await client.post(
                        f"{self.mcp_server_url}/tools/call",
                        json={
                            "tool_name": tool_name,
                            "parameters": parameters
                        }
                    )
                    result = self._handle_response(response)

                    duration_ms = int((time.time() - start_time) * 1000)
                    self.metrics.record_call(tool_name, duration_ms, error=False, retried=retried)

                    return result

            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
                last_error = exc
                retried = True
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"MCP tool {tool_name} failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"MCP tool {tool_name} failed after {self.max_retries} attempts: {exc}")

            except RuntimeError as exc:
                # Don't retry on authentication or validation errors
                if "401" in str(exc) or "404" in str(exc):
                    duration_ms = int((time.time() - start_time) * 1000)
                    self.metrics.record_call(tool_name, duration_ms, error=True, retried=False)
                    raise

                # Retry on rate limit or server errors
                last_error = exc
                retried = True
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"MCP tool {tool_name} failed (attempt {attempt + 1}/{self.max_retries}), "
                        f"retrying in {delay}s: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"MCP tool {tool_name} failed after {self.max_retries} attempts: {exc}")

        duration_ms = int((time.time() - start_time) * 1000)
        self.metrics.record_call(tool_name, duration_ms, error=True, retried=retried)

        raise RuntimeError(f"MCP tool {tool_name} failed after {self.max_retries} retries: {last_error}")

    async def list_mcp_tools(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.get(f"{self.mcp_server_url}/tools/list")
            data = self._handle_response(response)
            return data.get("tools", [])
