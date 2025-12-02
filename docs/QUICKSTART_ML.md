# Quick Start for ML Team

## First Time Setup

1. Clone the repository

2. Copy environment file:
```bash
cp .env.example .env
```

3. Add your API key to `.env`:
```bash
EVOLUTION_API_KEY=your_key_here
```

4. Start services:
```bash
make dev
```

This will start:
- Backend: http://localhost:8000
- MCP Server: http://localhost:8001
- Frontend: http://localhost:3000

## Your First Agent

Create `ml/agents/my_first_agent.py`:

```python
from ml.agents.registry import agent_registry
from typing import Dict, Any

@agent_registry.register(
    name="hello_agent",
    description="Simple hello agent"
)
async def hello_agent(input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    name = input_data.get("name", "World")
    return {
        "response": f"Hello, {name}!",
        "metadata": {"greeted": True}
    }
```

Register it in `ml/agents/__init__.py`:

```python
from ml.examples import example_agent
from ml.agents import my_first_agent
```

Restart services:
```bash
docker-compose restart mcp_server
```

Test it:
```bash
curl -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "hello_agent",
    "input_data": {"name": "Alice"},
    "config": {}
  }'
```

## Your First Tool

Create `ml/mcp_server/my_first_tool.py`:

```python
from ml.mcp_server.tools import tool_registry
from typing import Dict, Any

@tool_registry.register(
    name="add_numbers",
    description="Add two numbers"
)
async def add_numbers(a: int, b: int) -> Dict[str, Any]:
    return {"result": a + b}
```

Register it in `ml/mcp_server/__init__.py`:

```python
from ml.examples import example_tool
from ml.mcp_server import my_first_tool
```

Restart and test:
```bash
docker-compose restart mcp_server

curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "add_numbers",
    "parameters": {"a": 5, "b": 3}
  }'
```

## Common Tasks

### View logs
```bash
make logs
```

### Restart after code changes
```bash
docker-compose restart mcp_server
```

### Run tests
```bash
make test
```

### Format code
```bash
make format
```

## Next Steps

1. Read `docs/MCP_BASICS.md` for MCP concepts
2. Read `docs/ML_INTEGRATION_GUIDE.md` for detailed guide
3. Look at examples in `ml/examples/`
4. Start implementing your agents

## Getting Help

- Check logs: `make logs`
- Check API docs: http://localhost:8000/docs
- Read the integration guide: `docs/ML_INTEGRATION_GUIDE.md`

## Common Issues

### Import errors
```bash
poetry install
docker-compose restart mcp_server
```

### Port already in use
```bash
make down
make dev
```

### Changes not reflected
Always restart mcp_server after code changes:
```bash
docker-compose restart mcp_server
```
