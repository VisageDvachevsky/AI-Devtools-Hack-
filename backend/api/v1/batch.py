"""
Batch Processing API Endpoints
Mass candidate analysis with progress tracking
"""
import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.ml_integration.client import MLClient
from backend.schemas.hr import CandidateInput
from backend.services.batch_processor import (
    BatchProcessRequest,
    BatchProcessResponse,
    batch_processor,
)
from backend.services.normalization import normalize_skills_batch
from pydantic import BaseModel, Field

router = APIRouter()
ml_client = MLClient()


class BatchJobCreateResponse(BaseModel):
    job_id: str
    status: str
    message: str
    total_candidates: int


class BatchCandidateInput(BaseModel):
    """Simplified candidate input for batch processing"""
    github_username: str
    resume_text: Optional[str] = None
    linkedin_url: Optional[str] = None
    repos_limit: int = Field(default=10, ge=1, le=30)
    lookback_days: Optional[int] = None


class BatchHRRequest(BaseModel):
    """Batch HR analysis request"""
    role: str = Field(..., description="Job role")
    skills: list[str] = Field(..., description="Required skills")
    nice_to_have_skills: list[str] = Field(default_factory=list)
    candidates: list[BatchCandidateInput] = Field(..., description="List of candidates")
    concurrency: int = Field(default=5, ge=1, le=20, description="Parallel processing limit")
    timeout_per_candidate: int = Field(default=120, description="Timeout per candidate in seconds")


async def process_single_candidate(
    candidate: dict,
    role: str,
    required_skills: list[str],
    nice_to_have_skills: list[str]
) -> dict:
    """Process single candidate (used by batch processor)"""

    github_username = candidate.get("github_username")
    resume_text = candidate.get("resume_text")
    linkedin_url = candidate.get("linkedin_url")
    repos_limit = candidate.get("repos_limit", 10)
    lookback_days = candidate.get("lookback_days")

    result = {
        "github_username": github_username,
        "status": "failed",
        "error": None,
        "github_data": None,
        "linkedin_data": None,
        "score": 0,
    }

    try:
        # Analyze GitHub
        github_payload = {
            "username": github_username,
            "required_skills": required_skills + nice_to_have_skills,
            "repos_limit": repos_limit,
            "lookback_days": lookback_days,
            "analyze_code": True,
            "analyze_dependencies": True,
        }

        github_resp = await ml_client.call_mcp_tool("analyze_github_advanced", github_payload)
        result["github_data"] = github_resp.get("result") or github_resp

        # Analyze LinkedIn if URL provided
        if linkedin_url:
            linkedin_payload = {
                "linkedin_url": linkedin_url,
                "extract_skills": True,
                "extract_experience": True,
                "extract_education": True,
            }
            linkedin_resp = await ml_client.call_mcp_tool("analyze_linkedin", linkedin_payload)
            result["linkedin_data"] = linkedin_resp.get("result") or linkedin_resp

        # Calculate basic score
        if result["github_data"]:
            skill_scores = result["github_data"].get("skill_scores", [])
            if skill_scores:
                avg_score = sum(s.get("score", 0) for s in skill_scores) / len(skill_scores)
                result["score"] = int(avg_score * 100)

        result["status"] = "completed"

    except Exception as e:
        result["error"] = str(e)
        result["status"] = "failed"

    return result


@router.post("/submit", response_model=BatchJobCreateResponse)
async def submit_batch_job(request: BatchHRRequest, background_tasks: BackgroundTasks):
    """
    Submit a batch job for processing multiple candidates

    Returns job_id for tracking progress
    """

    if not request.candidates:
        raise HTTPException(status_code=400, detail="No candidates provided")

    if len(request.candidates) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 candidates per batch")

    # Normalize skills
    required_skills = normalize_skills_batch(request.skills)
    nice_to_have_skills = normalize_skills_batch(request.nice_to_have_skills)

    # Convert candidates to dict
    candidates_data = [c.model_dump() for c in request.candidates]

    # Create job
    job_id = batch_processor.create_job(
        candidates=candidates_data,
        role=request.role,
        required_skills=required_skills,
        concurrency=request.concurrency,
        metadata={
            "role": request.role,
            "required_skills": required_skills,
            "nice_to_have_skills": nice_to_have_skills,
        }
    )

    # Start processing in background
    async def run_batch():
        await batch_processor.process_batch(
            job_id=job_id,
            candidates=candidates_data,
            role=request.role,
            required_skills=required_skills,
            nice_to_have_skills=nice_to_have_skills,
            processor_func=process_single_candidate,
            timeout_per_candidate=request.timeout_per_candidate
        )

    # Run in background
    background_tasks.add_task(run_batch)

    return BatchJobCreateResponse(
        job_id=job_id,
        status="processing",
        message="Batch job submitted successfully",
        total_candidates=len(candidates_data)
    )


@router.get("/status/{job_id}", response_model=BatchProcessResponse)
async def get_batch_status(job_id: str):
    """Get status of a batch job"""

    status = batch_processor.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return status


@router.get("/results/{job_id}")
async def get_batch_results(job_id: str):
    """Get results of a completed batch job"""

    status = batch_processor.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    if status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {status.status}"
        )

    return {
        "job_id": job_id,
        "total_candidates": status.total_candidates,
        "successful": status.successful,
        "failed": status.failed,
        "results": status.results
    }


@router.delete("/cancel/{job_id}")
async def cancel_batch_job(job_id: str):
    """Cancel a running batch job"""

    success = batch_processor.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled")

    return {"message": "Job cancelled successfully"}


@router.delete("/cleanup/{job_id}")
async def cleanup_batch_job(job_id: str):
    """Remove job from memory"""

    success = batch_processor.cleanup_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"message": "Job cleaned up successfully"}


@router.get("/jobs")
async def list_all_jobs():
    """List all batch jobs"""

    jobs = batch_processor.get_all_jobs()
    return {
        "total": len(jobs),
        "jobs": jobs
    }


@router.get("/stats")
async def get_batch_stats():
    """Get overall batch processing statistics"""

    return batch_processor.get_stats()
