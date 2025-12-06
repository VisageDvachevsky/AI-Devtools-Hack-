import asyncio
import hashlib
import json
import logging
import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter

from backend.ml_integration.client import MLClient
from backend.schemas.hr import (
    CandidateResult,
    CandidateScore,
    HRReport,
    HRRunRequest,
    HRRunResponse,
    MarketResult,
    MarketSummary,
    SalaryStats,
    TopSkill,
)
from backend.services.cache import cache_get, cache_set

router = APIRouter()
ml_client = MLClient()
logger = logging.getLogger(__name__)


def _percentile(values: List[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    values_sorted = sorted(values)
    k = (len(values_sorted) - 1) * percentile
    f = int(k)
    c = min(f + 1, len(values_sorted) - 1)
    if f == c:
        return values_sorted[int(k)]
    d0 = values_sorted[f] * (c - k)
    d1 = values_sorted[c] * (k - f)
    return d0 + d1


def summarize_market(market_data: Dict[str, any]) -> Optional[MarketSummary]:
    if not market_data:
        return None

    items = market_data.get("items", [])
    salaries = []
    currency = None
    skills_counter: Counter[str] = Counter()

    for item in items:
        salary_from = item.get("salary_from")
        salary_to = item.get("salary_to")
        curr = item.get("currency")
        if curr and not currency:
            currency = curr
        # Рассчитываем медианную точку вилки, если есть цифры
        if salary_from and salary_to:
            salaries.append((salary_from + salary_to) / 2)
        elif salary_from:
            salaries.append(salary_from)
        elif salary_to:
            salaries.append(salary_to)

        for skill in item.get("skills") or []:
            normalized = (
                skill.replace("<highlighttext>", "")
                .replace("</highlighttext>", "")
                .replace("…", " ")
                .strip()
            )
            normalized = normalized.replace("  ", " ")
            normalized = normalized.strip().lower()
            if normalized:
                skills_counter[normalized] += 1

    salary_stats = None
    if salaries:
        salary_stats = SalaryStats(
            count=len(salaries),
            minimum=min(salaries),
            maximum=max(salaries),
            median=_percentile(salaries, 0.5),
            p25=_percentile(salaries, 0.25),
            p75=_percentile(salaries, 0.75),
            currency=currency,
        )

    top_skills = [TopSkill(skill=s, count=c) for s, c in skills_counter.most_common(10)]

    return MarketSummary(
        total_found=market_data.get("total_found", len(items)),
        salary_stats=salary_stats,
        top_skills=top_skills,
        source=market_data.get("source", "hh.ru"),
    )


def score_candidate(candidate_data: Dict[str, any], required_skills: List[str], username: str) -> Optional[CandidateScore]:
    if not candidate_data:
        return None

    skill_scores = candidate_data.get("skill_scores") or []
    repos_analyzed = candidate_data.get("repos_analyzed", 0)
    risk_flags = candidate_data.get("risk_flags") or []
    top_languages = candidate_data.get("top_languages") or []

    coverage_scores = []
    evidence: Dict[str, str] = {}
    for entry in skill_scores:
        skill = entry.get("skill")
        score = entry.get("score", 0)
        evidence[skill] = entry.get("evidence", "")
        coverage_scores.append(score)

    match_score = int(statistics.mean(coverage_scores) * 100) if coverage_scores else 0
    activity_score = 0
    if repos_analyzed > 0:
        activity_score = min(100, 40 + min(30, repos_analyzed * 5) + min(30, len(top_languages) * 5))

    risk_penalty = min(60, len(risk_flags) * 15)

    raw_score = max(0, min(100, match_score + activity_score - risk_penalty))

    decision = "go"
    if raw_score < 45:
        decision = "no"
    elif raw_score < 70:
        decision = "hold"

    skill_gaps = [entry.get("skill") for entry in skill_scores if entry.get("score", 0) < 0.5]

    return CandidateScore(
        github_username=username,
        score=raw_score,
        decision=decision,
        match_score=match_score,
        activity_score=activity_score,
        risk_penalty=risk_penalty,
        skill_gaps=skill_gaps,
        risk_flags=risk_flags,
        repos_analyzed=repos_analyzed,
        top_languages=top_languages,
        evidence=evidence,
    )


def cache_key(prefix: str, payload: Dict[str, any]) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    digest = hashlib.md5(serialized.encode("utf-8")).hexdigest()  # noqa: S324
    return f"hr:{prefix}:{digest}"


def build_summary(report: HRReport) -> str:
    parts: List[str] = []
    ms = report.market_summary
    if ms and ms.salary_stats:
        parts.append(
            f"Рынок: найдено {ms.total_found}, медиана ~{int(ms.salary_stats.median)} {ms.salary_stats.currency or ''}".strip()
        )
    if report.candidate_scores:
        top = sorted(report.candidate_scores, key=lambda x: x.score, reverse=True)[:3]
        shortlist = ", ".join(f"{c.github_username} ({c.decision}, {c.score})" for c in top)
        parts.append(f"Кандидаты: {shortlist}")
    return " | ".join(parts) if parts else "Нет данных"


@router.post("/run", response_model=HRRunResponse)
async def run_hr_analysis(request: HRRunRequest) -> HRRunResponse:
    market_data = None
    market_error = None
    market_payload = {
        "query": request.role,
        "location": request.location,
        "skills": request.skills,
        "salary_from": request.salary_from,
        "salary_to": request.salary_to,
        "per_page": request.per_page,
        "page": 0,
    }
    try:
        cached_market = await cache_get(cache_key("market", market_payload))
    except Exception:  # noqa: BLE001
        cached_market = None

    if cached_market:
        market_data = cached_market
    else:
        try:
            market_resp = await ml_client.call_mcp_tool("search_jobs", market_payload)
            market_data = market_resp.get("result") or market_resp
            await cache_set(cache_key("market", market_payload), market_data, ttl_seconds=900)
        except Exception as exc:  # noqa: BLE001
            market_error = str(exc)

    candidates_results: list[CandidateResult] = []
    candidate_scores: list[CandidateScore] = []

    async def handle_candidate(candidate) -> Tuple[CandidateResult, Optional[CandidateScore]]:
        cand_data = None
        cand_error = None
        cand_payload = {
            "username": candidate.github_username,
            "required_skills": request.skills,
            "repos_limit": candidate.repos_limit,
            "lookback_days": candidate.lookback_days,
        }
        try:
            cached_cand = await cache_get(cache_key("candidate", cand_payload))
        except Exception:  # noqa: BLE001
            cached_cand = None

        if cached_cand:
            cand_data = cached_cand
        else:
            try:
                cand_resp = await ml_client.call_mcp_tool("analyze_github", cand_payload)
                cand_data = cand_resp.get("result") or cand_resp
                await cache_set(cache_key("candidate", cand_payload), cand_data, ttl_seconds=900)
            except Exception as exc:  # noqa: BLE001
                cand_error = str(exc)

        result = CandidateResult(
            github_username=candidate.github_username,
            data=cand_data,
            error=cand_error,
        )
        scored = None
        if cand_data and not cand_error:
            scored = score_candidate(cand_data, request.skills, candidate.github_username)
        return result, scored

    candidate_tasks = [handle_candidate(candidate) for candidate in request.candidates]
    results = await asyncio.gather(*candidate_tasks)
    for res, scored in results:
        candidates_results.append(res)
        if scored:
            candidate_scores.append(scored)

    market_summary = summarize_market(market_data) if market_data and not market_error else None
    report = HRReport(
        role=request.role,
        skills=request.skills,
        market_summary=market_summary,
        candidate_scores=candidate_scores,
        summary=None,
    )
    report.summary = build_summary(report)

    return HRRunResponse(
        market=MarketResult(data=market_data, error=market_error),
        candidates=candidates_results,
        report=report,
    )
