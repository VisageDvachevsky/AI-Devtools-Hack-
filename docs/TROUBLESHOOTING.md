# Troubleshooting Guide

## Services won't start

### Check logs
```bash
make logs
```

### Clean rebuild
```bash
make clean
make dev
```

## Import errors in MCP server

### Symptom
```
ModuleNotFoundError: No module named 'ml'
```

### Solution
Make sure Docker is copying files correctly. Check docker-compose logs:
```bash
docker-compose logs mcp_server
```

Restart:
```bash
docker-compose restart mcp_server
```

## Tools/Agents not registered

### Check if examples are loaded
```bash
curl http://localhost:8001/tools/list
curl http://localhost:8001/agents/list
```

### If empty
1. Check that imports are in `__init__.py` files
2. Restart MCP server: `docker-compose restart mcp_server`
3. Check logs: `docker-compose logs mcp_server`

## Backend can't connect to MCP server

### Symptom
```
httpx.ConnectError: [Errno 111] Connection refused
```

### Solution
1. Check MCP server is running:
```bash
curl http://localhost:8001/health
```

2. Check docker network:
```bash
docker network ls
docker network inspect ai-devtools-hack_app_network
```

3. Restart all services:
```bash
make down
make up
```

## Frontend can't connect to backend

### Symptom
Frontend shows connection errors

### Solution
1. Check REACT_APP_API_URL in docker-compose.yml
2. Check CORS settings in backend/core/config.py
3. Check backend is running:
```bash
curl http://localhost:8000/health
```

## Poetry install fails

### Symptom
```
SolverProblemError: package conflicts
```

### Solution
1. Delete poetry.lock:
```bash
rm poetry.lock
```

2. Try again:
```bash
poetry install
```

Or in Docker:
```bash
make clean
make dev
```

## Agent execution fails

### Check agent is registered
```bash
curl http://localhost:8001/agents/list
```

### Check agent syntax
Look for Python errors in logs:
```bash
docker-compose logs mcp_server | grep -i error
```

### Test directly
```bash
curl -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "simple_agent", "input_data": {"query": "test"}, "config": {}}'
```

## Docker build fails

### Disk space
```bash
docker system df
docker system prune
```

### Network issues
Check internet connection and retry

### Cached layers
```bash
docker-compose build --no-cache
```

## Redis connection issues

### Check Redis is running
```bash
docker-compose ps redis
```

### Test connection
```bash
docker-compose exec redis redis-cli ping
```

## Performance issues

### Check resource usage
```bash
docker stats
```

### Restart services
```bash
make down
make up
```

## Still having issues?

1. Check all services status:
```bash
docker-compose ps
```

2. Full clean rebuild:
```bash
make clean
rm -rf frontend/node_modules
make dev
```

3. Check logs for specific errors:
```bash
docker-compose logs backend
docker-compose logs mcp_server
docker-compose logs frontend
```
