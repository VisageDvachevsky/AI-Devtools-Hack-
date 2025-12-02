from pydantic import BaseModel
from typing import Dict, Any, Optional


class MCPRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class MCPResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    tool_name: str
    error: Optional[str] = None
