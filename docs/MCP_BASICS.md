# MCP (Model Context Protocol) Basics

## What is MCP?

Model Context Protocol is a standard for connecting AI models with external tools and data sources.

## Key Concepts

### 1. Tools

Tools are functions that AI agents can call to perform actions:

- Search databases
- Call external APIs
- Process data
- Execute business logic

### 2. Agents

Agents use LLMs and tools to accomplish tasks autonomously:

- Understand user intent
- Plan steps to accomplish goal
- Execute tools in sequence
- Return results

### 3. Tool Registry

Central registry where all tools are registered and discoverable by agents.

## MCP in This Project

```
User Request
    |
    v
Backend API
    |
    v
MCP Server
    |
    +-- Tool Registry (your tools)
    +-- Agent Registry (your agents)
    |
    v
External APIs / LLMs
```

## Example Flow

1. User sends request to frontend
2. Frontend calls backend API
3. Backend forwards to MCP server
4. MCP server executes agent
5. Agent calls tools as needed
6. Result flows back to user

## Your Responsibilities

As ML team member:

1. Implement tools (functions with @tool_registry.register)
2. Implement agents (functions with @agent_registry.register)
3. Test your implementations
4. Document what each tool/agent does

Backend team handles:
- API routing
- Authentication
- CORS
- Deployment
- Monitoring

## Best Practices

### Tool Design

- Single responsibility
- Clear parameters
- Descriptive names
- Return structured data

### Agent Design

- Handle errors gracefully
- Validate inputs
- Use appropriate LLM temperature
- Document expected input/output format

## Resources

- MCP Specification: https://spec.modelcontextprotocol.io/
- LangChain Docs: https://python.langchain.com/
- Evolution API Docs: [check cloud.ru documentation]
