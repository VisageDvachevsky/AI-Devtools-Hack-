#!/bin/bash

echo "Testing setup..."

echo "1. Checking if services are running..."
curl -s http://localhost:8000/health || echo "Backend not running"
curl -s http://localhost:8001/health || echo "MCP server not running"
curl -s http://localhost:3000 || echo "Frontend not running"

echo ""
echo "2. Testing MCP tools list..."
curl -s http://localhost:8001/tools/list | python3 -m json.tool

echo ""
echo "3. Testing agents list..."
curl -s http://localhost:8001/agents/list | python3 -m json.tool

echo ""
echo "4. Testing example agent..."
curl -s -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "simple_agent", "input_data": {"query": "test"}, "config": {}}' \
  | python3 -m json.tool

echo ""
echo "Done!"
