from fastapi import APIRouter
from backend.api.v1 import agents, mcp, hr

router = APIRouter()

router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
router.include_router(hr.router, prefix="/hr", tags=["hr"])
