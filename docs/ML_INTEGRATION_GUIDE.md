# ML Integration Guide

## Overview

This guide explains how ML team members can add their agents and MCP tools to the system without touching backend code.

## Architecture

```
Backend (FastAPI)
    |
    v (HTTP)
MCP Server (FastAPI) <-- ML team works here
    |
    +-- Tools (ml/mcp_server/tools.py)
    +-- Agents (ml/agents/)
```

## Adding MCP Tools

### Step 1: Create a new tool file

Create a file in `ml/mcp_server/` or `ml/examples/`:

```python
from ml.mcp_server.tools import tool_registry
from typing import Dict, Any

@tool_registry.register(
    name="my_tool",
    description="What your tool does"
)
async def my_tool(param1: str, param2: int) -> Dict[str, Any]:
    result = f"Processed {param1} with {param2}"
    return {"output": result}
```

### Step 2: Import your tool

Add to `ml/mcp_server/__init__.py`:

```python
from ml.examples import my_tool_file
```

### Step 3: Test

```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "my_tool", "parameters": {"param1": "test", "param2": 42}}'
```

## Adding Agents

### Step 1: Create agent file

Create a file in `ml/agents/`:

```python
from ml.agents.registry import agent_registry
from typing import Dict, Any

@agent_registry.register(
    name="my_agent",
    description="What your agent does"
)
async def my_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    query = input_data.get("query")

    response = f"Agent response for: {query}"

    return {
        "response": response,
        "metadata": {"processed": True}
    }
```

### Step 2: Import your agent

Add to `ml/agents/__init__.py`:

```python
from ml.agents import my_agent_file
```

### Step 3: Test

```bash
curl -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "my_agent", "input_data": {"query": "test"}, "config": {}}'
```

## Using LangChain

Example with LangChain:

```python
from ml.agents.registry import agent_registry
from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI

@agent_registry.register(name="langchain_agent", description="LangChain agent")
async def langchain_agent(input_data: Dict, config: Dict) -> Dict:
    llm = OpenAI(temperature=0.7)

    tools = [
        Tool(
            name="Search",
            func=lambda x: "search result",
            description="Search tool"
        )
    ]

    agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
    result = agent.run(input_data["query"])

    return {"response": result}
```

## Integration with Backend

Your tools and agents are automatically available through backend API:

- Backend API: `http://localhost:8000/api/v1/agents/execute`
- MCP Server: `http://localhost:8001/agents/execute`

Backend handles all HTTP routing, CORS, and API management. You only implement agent logic.

## Environment Variables

Add your API keys to `.env`:

```bash
EVOLUTION_API_KEY=your_key_here
EVOLUTION_API_URL=https://api.cloud.ru/v1
```

Access in code:

```python
import os
api_key = os.getenv("EVOLUTION_API_KEY")
```

## Development Workflow

1. Create your agent/tool file
2. Register it in `__init__.py`
3. Run `make dev` to start services
4. Test with curl or frontend
5. Iterate

## Common Patterns

### Calling Evolution API

```python
import httpx
import os

@tool_registry.register(name="evolution_call", description="Call Evolution API")
async def evolution_call(prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("EVOLUTION_API_KEY")
    api_url = os.getenv("EVOLUTION_API_URL")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"prompt": prompt}
        )
        return response.json()
```

### Error Handling

```python
@agent_registry.register(name="safe_agent", description="Agent with error handling")
async def safe_agent(input_data: Dict, config: Dict) -> Dict:
    try:
        result = some_operation()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Debugging

Check logs:

```bash
make logs
```

Or specific service:

```bash
docker-compose logs -f mcp_server
```
