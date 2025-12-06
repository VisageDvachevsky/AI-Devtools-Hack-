"""
Batch Processing System for Mass Candidate Analysis
Handles large-scale candidate evaluation with progress tracking and resource management
"""
import asyncio
import hashlib
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class BatchStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CandidateStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchJob:
    """Represents a batch processing job"""
    job_id: str
    status: BatchStatus
    total_candidates: int
    processed: int = 0
    successful: int = 0
    failed: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    results: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CandidateTask:
    """Individual candidate processing task"""
    task_id: str
    candidate_data: Dict
    status: CandidateStatus = CandidateStatus.PENDING
    result: Optional[Dict] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


class BatchProcessRequest(BaseModel):
    candidates: List[Dict] = Field(..., description="List of candidate data dicts")
    role: str = Field(..., description="Job role")
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    concurrency: int = Field(default=5, ge=1, le=20, description="Max parallel tasks")
    priority: str = Field(default="normal", description="low/normal/high")
    timeout_per_candidate: int = Field(default=60, description="Timeout in seconds")


class BatchProcessResponse(BaseModel):
    job_id: str
    status: BatchStatus
    total_candidates: int
    processed: int
    successful: int
    failed: int
    progress_percent: float
    estimated_time_remaining_seconds: Optional[float] = None
    results: List[Dict] = Field(default_factory=list)
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchProcessor:
    """
    High-performance batch processor for candidate analysis
    Features:
    - Concurrent processing with semaphore control
    - Progress tracking
    - Error recovery
    - Resource management
    - Cancellation support
    """

    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.job_semaphores: Dict[str, asyncio.Semaphore] = {}

    def create_job(
        self,
        candidates: List[Dict],
        role: str,
        required_skills: List[str],
        concurrency: int = 5,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create a new batch job"""

        job_id = str(uuid.uuid4())

        job = BatchJob(
            job_id=job_id,
            status=BatchStatus.PENDING,
            total_candidates=len(candidates),
            metadata=metadata or {}
        )

        self.jobs[job_id] = job
        self.job_semaphores[job_id] = asyncio.Semaphore(concurrency)

        return job_id

    async def process_batch(
        self,
        job_id: str,
        candidates: List[Dict],
        role: str,
        required_skills: List[str],
        nice_to_have_skills: List[str],
        processor_func,
        timeout_per_candidate: int = 60
    ) -> BatchJob:
        """
        Process batch of candidates

        Args:
            job_id: Job identifier
            candidates: List of candidate data
            role: Job role
            required_skills: Required skills
            nice_to_have_skills: Optional skills
            processor_func: Async function to process each candidate
            timeout_per_candidate: Max seconds per candidate

        Returns:
            Completed BatchJob
        """

        job = self.jobs.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = BatchStatus.PROCESSING
        job.started_at = time.time()

        semaphore = self.job_semaphores[job_id]

        # Create tasks for all candidates
        tasks = []
        for i, candidate in enumerate(candidates):
            task_id = f"{job_id}_{i}"
            candidate_task = CandidateTask(
                task_id=task_id,
                candidate_data=candidate
            )
            tasks.append(
                self._process_candidate(
                    candidate_task,
                    role,
                    required_skills,
                    nice_to_have_skills,
                    processor_func,
                    semaphore,
                    timeout_per_candidate
                )
            )

        # Process all candidates
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                job.failed += 1
                job.results.append({
                    "candidate_index": i,
                    "error": str(result),
                    "status": "failed"
                })
            elif isinstance(result, dict):
                if result.get("status") == "failed":
                    job.failed += 1
                else:
                    job.successful += 1
                job.results.append(result)

            job.processed += 1

        job.completed_at = time.time()
        job.status = BatchStatus.COMPLETED

        return job

    async def _process_candidate(
        self,
        task: CandidateTask,
        role: str,
        required_skills: List[str],
        nice_to_have_skills: List[str],
        processor_func,
        semaphore: asyncio.Semaphore,
        timeout: int
    ) -> Dict:
        """Process single candidate with timeout and semaphore"""

        async with semaphore:
            task.status = CandidateStatus.PROCESSING
            start_time = time.time()

            try:
                # Process with timeout
                result = await asyncio.wait_for(
                    processor_func(
                        task.candidate_data,
                        role,
                        required_skills,
                        nice_to_have_skills
                    ),
                    timeout=timeout
                )

                task.status = CandidateStatus.COMPLETED
                task.result = result
                task.processing_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "task_id": task.task_id,
                    "status": "completed",
                    "result": result,
                    "processing_time_ms": task.processing_time_ms
                }

            except asyncio.TimeoutError:
                task.status = CandidateStatus.FAILED
                task.error = f"Timeout after {timeout}s"
                task.processing_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": task.error,
                    "processing_time_ms": task.processing_time_ms
                }

            except Exception as e:
                task.status = CandidateStatus.FAILED
                task.error = str(e)
                task.processing_time_ms = int((time.time() - start_time) * 1000)

                return {
                    "task_id": task.task_id,
                    "status": "failed",
                    "error": task.error,
                    "processing_time_ms": task.processing_time_ms
                }

    def get_job_status(self, job_id: str) -> Optional[BatchProcessResponse]:
        """Get current job status"""

        job = self.jobs.get(job_id)
        if not job:
            return None

        progress = (job.processed / job.total_candidates * 100) if job.total_candidates > 0 else 0

        # Estimate remaining time
        estimated_remaining = None
        if job.started_at and job.processed > 0:
            elapsed = time.time() - job.started_at
            avg_time_per_candidate = elapsed / job.processed
            remaining_candidates = job.total_candidates - job.processed
            estimated_remaining = avg_time_per_candidate * remaining_candidates

        return BatchProcessResponse(
            job_id=job.job_id,
            status=job.status,
            total_candidates=job.total_candidates,
            processed=job.processed,
            successful=job.successful,
            failed=job.failed,
            progress_percent=round(progress, 2),
            estimated_time_remaining_seconds=round(estimated_remaining, 1) if estimated_remaining else None,
            results=job.results if job.status == BatchStatus.COMPLETED else [],
            created_at=datetime.fromtimestamp(job.created_at).isoformat(),
            started_at=datetime.fromtimestamp(job.started_at).isoformat() if job.started_at else None,
            completed_at=datetime.fromtimestamp(job.completed_at).isoformat() if job.completed_at else None
        )

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""

        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status == BatchStatus.PROCESSING:
            job.status = BatchStatus.CANCELLED
            # Cancel the asyncio task if it's running
            if job_id in self.active_jobs:
                self.active_jobs[job_id].cancel()
            return True

        return False

    def cleanup_job(self, job_id: str) -> bool:
        """Remove job from memory"""

        if job_id in self.jobs:
            del self.jobs[job_id]
        if job_id in self.job_semaphores:
            del self.job_semaphores[job_id]
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
        return True

    def get_all_jobs(self) -> List[BatchProcessResponse]:
        """Get status of all jobs"""

        return [
            self.get_job_status(job_id)
            for job_id in self.jobs.keys()
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get overall batch processing statistics"""

        total_jobs = len(self.jobs)
        active_jobs = sum(1 for j in self.jobs.values() if j.status == BatchStatus.PROCESSING)
        completed_jobs = sum(1 for j in self.jobs.values() if j.status == BatchStatus.COMPLETED)
        failed_jobs = sum(1 for j in self.jobs.values() if j.status == BatchStatus.FAILED)

        total_candidates = sum(j.total_candidates for j in self.jobs.values())
        total_processed = sum(j.processed for j in self.jobs.values())
        total_successful = sum(j.successful for j in self.jobs.values())
        total_failed = sum(j.failed for j in self.jobs.values())

        return {
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "total_candidates": total_candidates,
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": round(total_successful / total_processed * 100, 2) if total_processed > 0 else 0
        }


# Global batch processor instance
batch_processor = BatchProcessor()


async def example_candidate_processor(
    candidate: Dict,
    role: str,
    required_skills: List[str],
    nice_to_have_skills: List[str]
) -> Dict:
    """
    Example processor function for candidates
    Replace with actual HR analysis logic
    """

    # Simulate processing time
    await asyncio.sleep(0.5)

    github_username = candidate.get("github_username", "unknown")

    # Mock result
    return {
        "github_username": github_username,
        "score": 75,
        "decision": "go",
        "matched_skills": required_skills[:3],
        "processing_timestamp": datetime.utcnow().isoformat()
    }
