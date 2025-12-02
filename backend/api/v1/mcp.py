from fastapi import APIRouter, HTTPException
from backend.schemas.mcp import MCPRequest, MCPResponse
from backend.ml_integration.client import MLClient

router = APIRouter()
ml_client = MLClient()


@router.post("/call", response_model=MCPResponse)
async def call_mcp_tool(request: MCPRequest):
    try:
        result = await ml_client.call_mcp_tool(
            tool_name=request.tool_name,
            parameters=request.parameters
        )
        return MCPResponse(
            success=True,
            result=result,
            tool_name=request.tool_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_mcp_tools():
    tools = await ml_client.list_mcp_tools()
    return {"tools": tools}
