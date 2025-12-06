import os
from typing import List, Optional

import httpx
from httpx import TimeoutException
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from ml.mcp_server.tools.registry import tool_registry

HH_DEFAULT_URL = "https://api.hh.ru"


class HHSearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос по названию роли/позиции.")
    location: Optional[str] = Field(
        None, description="ID региона HH (рекомендуется) или название города."
    )
    skills: List[str] = Field(default_factory=list, description="Ключевые навыки/стек.")
    salary_from: Optional[int] = Field(None, ge=0, description="Минимальная зарплата, ₽.")
    salary_to: Optional[int] = Field(None, ge=0, description="Максимальная зарплата, ₽.")
    per_page: int = Field(10, ge=1, le=50, description="Количество результатов на страницу.")
    page: int = Field(0, ge=0, description="Номер страницы (0-индекс).")


class JobItem(BaseModel):
    id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    salary_from: Optional[int]
    salary_to: Optional[int]
    currency: Optional[str]
    skills: List[str]
    url: HttpUrl
    published_at: Optional[str]
    source: str = "hh.ru"


class HHSearchResponse(BaseModel):
    total_found: int
    items: List[JobItem]
    source: str = "hh.ru"


def _build_query_text(query: str, skills: List[str]) -> str:
    if not skills:
        return query
    skills_part = " ".join(f"\"{skill}\"" for skill in skills)
    return f"{query} {skills_part}"


@tool_registry.register(
    name="search_jobs",
    description="Поиск вакансий на HH.ru по роли/локации/навыкам.",
    parameters=HHSearchRequest.model_json_schema(),
)
async def search_jobs(**parameters) -> dict:
    try:
        payload = HHSearchRequest(**parameters)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors()}

    headers = {
        "User-Agent": "AI-HR-Agent/0.1 (+mcp)",
    }
    token = os.getenv("HH_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base_url = os.getenv("HH_API_URL", HH_DEFAULT_URL).rstrip("/")
    query_text = _build_query_text(payload.query, payload.skills)
    params = {
        "text": query_text,
        "per_page": payload.per_page,
        "page": payload.page,
        "only_with_salary": bool(payload.salary_from or payload.salary_to),
    }
    if payload.location:
        params["area"] = payload.location
    if payload.salary_from:
        params["salary"] = payload.salary_from

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/vacancies", params=params, headers=headers)
    except TimeoutException:
        return {"error": "timeout", "details": "HH API request timed out"}
    except httpx.RequestError as exc:
        return {"error": "network_error", "details": str(exc)}

    if response.status_code == 401:
        return {"error": "unauthorized", "details": "HH API token is invalid or missing."}
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        return {"error": "rate_limited", "details": "HH API rate limit exceeded", "retry_after": retry_after}
    if response.status_code >= 400:
        return {
            "error": "http_error",
            "status_code": response.status_code,
            "details": response.text,
        }

    data = response.json()
    items: List[JobItem] = []
    for raw in data.get("items", []):
        salary = raw.get("salary") or {}
        skills = []
        for role in raw.get("professional_roles", []) or []:
            name = role.get("name")
            if name:
                skills.append(name)
        requirement = (raw.get("snippet") or {}).get("requirement")
        if requirement:
            skills.append(requirement)

        url = (
            raw.get("alternate_url")
            or raw.get("url")
            or f"https://hh.ru/vacancy/{raw.get('id')}"
        )

        item = JobItem(
            id=str(raw.get("id")),
            title=raw.get("name") or "vacancy",
            company=(raw.get("employer") or {}).get("name"),
            location=(raw.get("area") or {}).get("name"),
            salary_from=salary.get("from"),
            salary_to=salary.get("to"),
            currency=salary.get("currency"),
            skills=skills,
            url=url,  # type: ignore[arg-type]
            published_at=raw.get("published_at"),
        )
        items.append(item)

    response_payload = HHSearchResponse(
        total_found=data.get("found", len(items)),
        items=items,
    )
    return response_payload.model_dump()
