import os
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, Request, status

import ml.agents
import ml.mcp_server
from ml.agents.registry import agent_registry
from ml.mcp_server.tools import tool_registry

app = FastAPI(title="MCP Server", version="0.1.0")


def verify_auth(request: Request):
    """
    Простейшая проверка Bearer-токена через MCP_AUTH_TOKEN.
    Если переменная не задана, аутентификация не применяется.
    """
    expected = os.getenv("MCP_AUTH_TOKEN")
    if not expected:
        return

    header = request.headers.get("authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "unauthorized", "message": "Missing Bearer token"},
        )
    token = header.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": "unauthorized", "message": "Invalid token"},
        )


def error_payload(error_code: str, message: str, details: Any | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"success": False, "error_code": error_code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mcp_server"}


@app.post("/tools/call")
async def call_tool(request: Dict[str, Any], _: None = Depends(verify_auth)):
    tool_name = request.get("tool_name")
    parameters = request.get("parameters", {})

    if not tool_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("validation_error", "tool_name is required"),
        )

    try:
        result = await tool_registry.execute_tool(tool_name, parameters)
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_payload(
                    "tool_error",
                    result.get("error") or "tool returned error",
                    details={"tool": tool_name},
                ),
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_payload("server_error", "Tool execution failed", str(exc)),
        ) from exc


@app.get("/tools/list")
async def list_tools(_: None = Depends(verify_auth)):
    tools = tool_registry.list_tools()
    return {"tools": tools}


@app.post("/agents/execute")
async def execute_agent(request: Dict[str, Any], _: None = Depends(verify_auth)):
    agent_name = request.get("agent_name")
    input_data = request.get("input_data", {})
    config = request.get("config", {})

    if not agent_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_payload("validation_error", "agent_name is required"),
        )

    try:
        result = await agent_registry.execute_agent(agent_name, input_data, config)
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_payload(
                    "agent_error",
                    result.get("error") or "agent returned error",
                    details={"agent": agent_name},
                ),
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_payload("server_error", "Agent execution failed", str(exc)),
        ) from exc


@app.get("/agents/list")
async def list_agents(_: None = Depends(verify_auth)):
    agents = agent_registry.list_agents()
    return {"agents": agents}
