from fastapi import APIRouter
from backend.api.v1 import agents, mcp

router = APIRouter()

router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
