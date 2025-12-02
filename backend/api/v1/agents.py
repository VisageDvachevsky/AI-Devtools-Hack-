from fastapi import APIRouter, HTTPException
from backend.schemas.agent import AgentRequest, AgentResponse
from backend.ml_integration.client import MLClient

router = APIRouter()
ml_client = MLClient()


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest):
    try:
        result = await ml_client.execute_agent(
            agent_name=request.agent_name,
            input_data=request.input_data,
            config=request.config
        )
        return AgentResponse(
            success=True,
            result=result,
            agent_name=request.agent_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_agents():
    agents = await ml_client.list_agents()
    return {"agents": agents}
