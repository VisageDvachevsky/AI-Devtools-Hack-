from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api.v1 import router as api_router
from backend.services.metrics import metrics

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "backend"}


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    metrics_text = metrics.export_prometheus_format()
    return Response(content=metrics_text, media_type="text/plain")
