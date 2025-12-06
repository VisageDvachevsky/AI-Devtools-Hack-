import asyncio
import os
from typing import List, Optional

import httpx
from httpx import TimeoutException
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from ml.mcp_server.tools.registry import tool_registry
from ml.mcp_server.tools.hh_tools import HHSearchRequest, JobItem, HHSearchResponse, _build_query_text

HH_DEFAULT_URL = "https://api.hh.ru"


class HHMultiPageRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос по названию роли/позиции.")
    location: Optional[str] = Field(
        None, description="ID региона HH (рекомендуется) или название города."
    )
    skills: List[str] = Field(default_factory=list, description="Ключевые навыки/стек.")
    salary_from: Optional[int] = Field(None, ge=0, description="Минимальная зарплата, ₽.")
    salary_to: Optional[int] = Field(None, ge=0, description="Максимальная зарплата, ₽.")
    per_page: int = Field(10, ge=1, le=50, description="Количество результатов на страницу.")
    pages: int = Field(3, ge=1, le=5, description="Количество страниц для загрузки (1-5).")


async def fetch_hh_page(
    base_url: str,
    query_text: str,
    params: dict,
    headers: dict,
    page: int
) -> dict:
    """Fetch single HH page"""
    params_with_page = {**params, "page": page}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/vacancies", params=params_with_page, headers=headers)
    except TimeoutException:
        return {"error": "timeout", "page": page}
    except httpx.RequestError as exc:
        return {"error": "network_error", "details": str(exc), "page": page}

    if response.status_code == 401:
        return {"error": "unauthorized", "page": page}
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        return {"error": "rate_limited", "retry_after": retry_after, "page": page}
    if response.status_code >= 400:
        return {"error": "http_error", "status_code": response.status_code, "page": page}

    return {"success": True, "data": response.json(), "page": page}


@tool_registry.register(
    name="search_jobs_multi_page",
    description="Поиск вакансий на HH.ru с загрузкой 2-3 страниц для более стабильных квантилей.",
    parameters=HHMultiPageRequest.model_json_schema(),
)
async def search_jobs_multi_page(**parameters) -> dict:
    try:
        payload = HHMultiPageRequest(**parameters)
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

    base_params = {
        "text": query_text,
        "per_page": payload.per_page,
        "only_with_salary": bool(payload.salary_from or payload.salary_to),
    }
    if payload.location:
        base_params["area"] = payload.location
    if payload.salary_from:
        base_params["salary"] = payload.salary_from

    # Fetch multiple pages in parallel
    tasks = [
        fetch_hh_page(base_url, query_text, base_params, headers, page)
        for page in range(payload.pages)
    ]

    results = await asyncio.gather(*tasks)

    # Aggregate results
    all_items: List[JobItem] = []
    total_found = 0
    errors = []

    for result in results:
        if result.get("error"):
            errors.append(result)
            continue

        data = result.get("data", {})
        total_found = max(total_found, data.get("found", 0))

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

            # Normalize salary to RUB
            salary_from = salary.get("from")
            salary_to = salary.get("to")
            currency = salary.get("currency", "RUB")

            item = JobItem(
                id=str(raw.get("id")),
                title=raw.get("name") or "vacancy",
                company=(raw.get("employer") or {}).get("name"),
                location=(raw.get("area") or {}).get("name"),
                salary_from=salary_from,
                salary_to=salary_to,
                currency=currency,
                skills=skills,
                url=url,  # type: ignore[arg-type]
                published_at=raw.get("published_at"),
            )
            all_items.append(item)

    if errors and not all_items:
        return {"error": "all_pages_failed", "details": errors}

    response_payload = HHSearchResponse(
        total_found=total_found,
        items=all_items,
    )

    result_dict = response_payload.model_dump()
    result_dict["pages_loaded"] = len([r for r in results if r.get("success")])
    result_dict["pages_errors"] = len(errors)

    return result_dict
