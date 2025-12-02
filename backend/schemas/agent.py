from pydantic import BaseModel
from typing import Dict, Any, Optional


class AgentRequest(BaseModel):
    agent_name: str
    input_data: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    agent_name: str
    error: Optional[str] = None
