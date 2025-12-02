from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
from ml.mcp_server.tools import tool_registry
from ml.agents.registry import agent_registry

import ml.mcp_server
import ml.agents

app = FastAPI(title="MCP Server", version="0.1.0")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "mcp_server"}


@app.post("/tools/call")
async def call_tool(request: Dict[str, Any]):
    tool_name = request.get("tool_name")
    parameters = request.get("parameters", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name is required")

    try:
        result = await tool_registry.execute_tool(tool_name, parameters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/list")
async def list_tools():
    tools = tool_registry.list_tools()
    return {"tools": tools}


@app.post("/agents/execute")
async def execute_agent(request: Dict[str, Any]):
    agent_name = request.get("agent_name")
    input_data = request.get("input_data", {})
    config = request.get("config", {})

    if not agent_name:
        raise HTTPException(status_code=400, detail="agent_name is required")

    try:
        result = await agent_registry.execute_agent(agent_name, input_data, config)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/list")
async def list_agents():
    agents = agent_registry.list_agents()
    return {"agents": agents}
