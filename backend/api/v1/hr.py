import asyncio
import hashlib
import json
import logging
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter

from backend.ml_integration.client import MLClient
from backend.schemas.hr import (
    ActivityMetrics,
    CandidateResult,
    CandidateScore,
    HRReport,
    HRRecommendations,
    HRRunRequest,
    HRRunResponse,
    InterviewSupport,
    MarketInsights,
    MarketResult,
    MarketSummary,
    RequirementMatch,
    SalaryStats,
    ShortlistCandidate,
    SkillClassificationReport,
    TopSkill,
)
from backend.services.cache import cache_get, cache_set
from backend.services.communications import generate_outreach_template
from backend.services.deduplication import clean_candidate_skills, deduplicate_candidates
from backend.services.interview_support import prepare_interview_script
from backend.services.market_analytics import (
    calculate_salary_ranges_by_skill,
    extract_top_companies,
    extract_top_locations,
    generate_market_insights,
)
from backend.services.matching import calculate_deep_match, explain_match_decision
from backend.services.normalization import (
    convert_salary_to_rub,
    extract_seniority_from_text,
    normalize_skills_batch,
)
from backend.services.resume_parser import (
    calculate_keyword_match_score,
    mock_linkedin_analysis,
)
from backend.services.skill_requirements import (
    check_mandatory_requirements,
    apply_mandatory_filter,
    calculate_requirement_match_score,
    generate_rejection_reason,
)
from backend.services.smart_requirements import (
    smart_classify_skills,
    generate_market_based_requirements_report,
)

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


def summarize_market(market_data: Dict[str, any], required_skills: List[str]) -> Optional[MarketSummary]:
    if not market_data:
        return None

    items = market_data.get("items", [])
    salaries_rub = []
    skills_counter: Counter[str] = Counter()

    for item in items:
        salary_from = item.get("salary_from")
        salary_to = item.get("salary_to")
        currency = item.get("currency", "RUB")

        # Convert to RUB and calculate median
        if salary_from and salary_to:
            mid = (salary_from + salary_to) / 2
            salaries_rub.append(convert_salary_to_rub(mid, currency))
        elif salary_from:
            salaries_rub.append(convert_salary_to_rub(salary_from, currency))
        elif salary_to:
            salaries_rub.append(convert_salary_to_rub(salary_to, currency))

        # Normalize skills
        raw_skills = item.get("skills") or []
        normalized = normalize_skills_batch(raw_skills)
        for skill in normalized:
            skills_counter[skill] += 1

    salary_stats = None
    if salaries_rub:
        salary_stats = SalaryStats(
            count=len(salaries_rub),
            minimum=min(salaries_rub),
            maximum=max(salaries_rub),
            median=_percentile(salaries_rub, 0.5),
            p25=_percentile(salaries_rub, 0.25),
            p75=_percentile(salaries_rub, 0.75),
            currency="RUB",
        )

    top_skills = [TopSkill(skill=s, count=c) for s, c in skills_counter.most_common(15)]

    return MarketSummary(
        total_found=market_data.get("total_found", len(items)),
        salary_stats=salary_stats,
        top_skills=top_skills,
        source=market_data.get("source", "hh.ru"),
    )


def score_candidate(
    candidate_data: Dict[str, any],
    required_skills: List[str],
    username: str,
    role: str,
    skill_classification: Dict[str, List[str]],
    resume_text: Optional[str] = None,
    linkedin_url: Optional[str] = None
) -> Optional[CandidateScore]:
    if not candidate_data:
        return None

    skill_scores = candidate_data.get("skill_scores") or []
    repos_analyzed = candidate_data.get("repos_analyzed", 0)
    risk_flags = candidate_data.get("risk_flags") or []
    top_languages = candidate_data.get("top_languages") or []
    activity_data = candidate_data.get("activity_metrics") or {}

    # Parse activity metrics
    activity_metrics = None
    if activity_data:
        activity_metrics = ActivityMetrics(**activity_data)

    # Calculate match score from skill coverage
    coverage_scores = []
    evidence: Dict[str, str] = {}
    matched_skills = []

    for entry in skill_scores:
        skill = entry.get("skill")
        score = entry.get("score", 0)
        evidence[skill] = entry.get("evidence", "")
        coverage_scores.append(score)
        if score >= 0.5:
            matched_skills.append(skill)

    match_score = int(statistics.mean(coverage_scores) * 100) if coverage_scores else 0

    # Calculate activity score with enhanced metrics
    activity_score = 0
    if repos_analyzed > 0:
        base_score = min(40, repos_analyzed * 5)
        lang_score = min(30, len(top_languages) * 5)

        # Bonus for recent activity
        freshness_bonus = 0
        if activity_metrics and activity_metrics.days_since_last_push is not None:
            if activity_metrics.days_since_last_push <= 30:
                freshness_bonus = 20
            elif activity_metrics.days_since_last_push <= 90:
                freshness_bonus = 10

        # Bonus for popularity
        popularity_bonus = 0
        if activity_metrics:
            if activity_metrics.total_stars > 100:
                popularity_bonus = 10
            elif activity_metrics.total_stars > 20:
                popularity_bonus = 5

        activity_score = min(100, base_score + lang_score + freshness_bonus + popularity_bonus)

    # Risk penalty
    risk_penalty = min(60, len(risk_flags) * 15)

    # Resume match boost
    resume_boost = 0
    resume_match_score = None
    if resume_text:
        resume_match = calculate_keyword_match_score(resume_text, required_skills)
        resume_match_score = resume_match.get("overall_score", 0.0)
        resume_boost = int(resume_match_score * 20)

    # LinkedIn data
    linkedin_data = None
    if linkedin_url:
        linkedin_data = mock_linkedin_analysis(linkedin_url)

    raw_score = max(0, min(100, match_score + activity_score + resume_boost - risk_penalty))

    skill_gaps = [entry.get("skill") for entry in skill_scores if entry.get("score", 0) < 0.5]

    # Check mandatory requirements - STRICT
    mandatory_skills = skill_classification.get("mandatory", [])
    passes_mandatory, missing_mandatory = check_mandatory_requirements(
        top_languages + matched_skills,
        mandatory_skills,
        skill_scores,
        min_score=0.5,  # STRICT: must have real evidence (score >= 0.5)
        min_coverage=0.8  # STRICT: must cover 80%+ of mandatory
    )

    # Explain decision
    match_result = {
        "coverage_percent": (len(matched_skills) / len(required_skills) * 100) if required_skills else 0,
        "gap_analysis": [f"Missing {len(skill_scores) - len(matched_skills)} skills"]
    }
    decision, decision_reasons = explain_match_decision(raw_score, match_result, activity_data)

    # Apply mandatory filter - HARD BLOCK if missing mandatory skills
    if not passes_mandatory:
        raw_score, decision, blocking_reasons = apply_mandatory_filter(
            raw_score,
            decision,
            missing_mandatory,
            len(mandatory_skills),
            role
        )
        decision_reasons = blocking_reasons  # Replace with blocking reasons (no soft reasons)

        # Add rejection reason
        rejection_reason = generate_rejection_reason(
            missing_mandatory,
            role,
            matched_skills
        )
        if rejection_reason:
            risk_flags.append(f"mandatory_skills_missing: {', '.join(missing_mandatory[:2])}")

    # Calculate detailed match scores
    req_match = calculate_requirement_match_score(
        matched_skills,
        skill_gaps,
        skill_classification.get("mandatory", []),
        skill_classification.get("preferred", [])
    )

    # Update decision reasons with requirement details
    if req_match["mandatory_coverage"] < 100:
        decision_reasons.insert(0,
            f"Mandatory skills coverage: {req_match['mandatory_coverage']}% "
            f"(missing: {', '.join(req_match['mandatory_missing'][:2])})"
        )

    # Create requirement match object
    requirement_match = RequirementMatch(**req_match)

    return CandidateScore(
        github_username=username,
        score=raw_score,
        decision=decision,
        decision_reasons=decision_reasons,
        match_score=match_score,
        activity_score=activity_score,
        risk_penalty=risk_penalty,
        skill_gaps=skill_gaps,
        matched_skills=matched_skills,
        risk_flags=risk_flags,
        repos_analyzed=repos_analyzed,
        top_languages=top_languages,
        evidence=evidence,
        activity_metrics=activity_metrics,
        resume_match_score=resume_match_score,
        linkedin_data=linkedin_data,
        requirement_match=requirement_match,
    )


def cache_key(prefix: str, payload: Dict[str, any]) -> str:
    serialized = json.dumps(payload, sort_keys=True)
    digest = hashlib.md5(serialized.encode("utf-8")).hexdigest()  # noqa: S324
    return f"hr:{prefix}:{digest}"


def build_recommendations(
    candidate_scores: List[CandidateScore],
    market_insights: Optional[MarketInsights],
    required_skills: List[str]
) -> HRRecommendations:
    # Build shortlist
    shortlist = []
    for cand in sorted(candidate_scores, key=lambda x: x.score, reverse=True)[:10]:
        shortlist.append(
            ShortlistCandidate(
                github_username=cand.github_username,
                score=cand.score,
                decision=cand.decision,
                top_reasons=cand.decision_reasons[:3]
            )
        )

    # Who to interview next
    go_candidates = [c.github_username for c in candidate_scores if c.decision == "go"]
    hold_candidates = [c.github_username for c in candidate_scores if c.decision == "hold"]
    interview_next = go_candidates[:5] + hold_candidates[:2]

    # Skills to train
    all_gaps = []
    for cand in candidate_scores:
        all_gaps.extend(cand.skill_gaps)
    gap_counter = Counter(all_gaps)
    skills_to_train = [skill for skill, _ in gap_counter.most_common(5) if gap_counter[skill] >= 2]

    # Risks
    risks = []
    inactive_count = sum(
        1 for c in candidate_scores
        if c.activity_metrics and c.activity_metrics.days_since_last_push and c.activity_metrics.days_since_last_push > 90
    )
    if inactive_count > len(candidate_scores) * 0.5:
        risks.append(f"High inactivity: {inactive_count}/{len(candidate_scores)} candidates inactive >90 days")

    no_github_count = sum(1 for c in candidate_scores if "no_repos" in c.risk_flags)
    if no_github_count > 0:
        risks.append(f"{no_github_count} candidates with limited GitHub presence")

    # Competitive offer
    competitive_offer = None
    if market_insights and market_insights.supply_demand:
        if market_insights.supply_demand.get("interpretation") in ["high_demand", "very_high_demand"]:
            risks.append("High market demand - expect competitive offers")

    return HRRecommendations(
        shortlist=shortlist,
        interview_next=interview_next,
        skills_to_train=skills_to_train,
        risks=risks,
        competitive_offer_range=competitive_offer
    )


def build_summary(report: HRReport) -> str:
    parts: List[str] = []
    ms = report.market_summary
    if ms and ms.salary_stats:
        parts.append(
            f"Рынок: {ms.total_found} вакансий, медиана ~{int(ms.salary_stats.median)} RUB"
        )

    if report.candidate_scores:
        go_count = sum(1 for c in report.candidate_scores if c.decision == "go")
        hold_count = sum(1 for c in report.candidate_scores if c.decision == "hold")
        parts.append(f"Кандидаты: {go_count} GO, {hold_count} HOLD из {len(report.candidate_scores)}")

    if report.recommendations and report.recommendations.risks:
        parts.append(f"Риски: {len(report.recommendations.risks)}")

    return " | ".join(parts) if parts else "Нет данных"


@router.post("/run", response_model=HRRunResponse)
async def run_hr_analysis(request: HRRunRequest) -> HRRunResponse:
    start_time = time.time()

    cache_hits = 0
    cache_misses = 0

    # Normalize required skills
    normalized_skills = normalize_skills_batch(request.skills)

    # Fetch market data (2-3 pages for better quantiles)
    market_data = None
    market_error = None
    market_payload = {
        "query": request.role,
        "location": request.location,
        "skills": normalized_skills,
        "salary_from": request.salary_from,
        "salary_to": request.salary_to,
        "per_page": request.per_page,
        "pages": 3,
    }

    try:
        cached_market = await cache_get(cache_key("market_multi", market_payload))
    except Exception:  # noqa: BLE001
        cached_market = None

    if cached_market:
        market_data = cached_market
        cache_hits += 1
    else:
        cache_misses += 1
        try:
            market_resp = await ml_client.call_mcp_tool("search_jobs_multi_page", market_payload)
            market_data = market_resp.get("result") or market_resp
            await cache_set(cache_key("market_multi", market_payload), market_data, ttl_seconds=1800)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Market data fetch failed: {exc}")
            market_error = str(exc)

    # Smart classify skills based on market data (universal, no hardcode)
    # CRITICAL: Respect employer's explicit requirements!
    # request.skills = mandatory (what employer needs)
    # request.nice_to_have_skills = preferred (what employer wants but not blocking)
    mandatory_threshold = request.mandatory_threshold if request.mandatory_threshold is not None else 0.7
    preferred_threshold = request.preferred_threshold if request.preferred_threshold is not None else 0.3

    # Normalize nice_to_have_skills
    normalized_nice_to_have = normalize_skills_batch(request.nice_to_have_skills) if request.nice_to_have_skills else []

    # Combine all skills for market analysis
    all_skills_for_analysis = normalized_skills + normalized_nice_to_have

    classification_result = smart_classify_skills(
        role=request.role,
        required_skills=all_skills_for_analysis,
        market_data=market_data,
        mandatory_threshold=mandatory_threshold,
        preferred_threshold=preferred_threshold,
        employer_mandatory=normalized_skills,  # Employer's required skills = MANDATORY
        employer_preferred=normalized_nice_to_have  # Employer's nice-to-have = PREFERRED
    )

    skill_classification = classification_result["classification"]

    logger.info(f"Smart skill classification for {request.role}:")
    logger.info(f"  Mandatory: {skill_classification['mandatory']}")
    logger.info(f"  Preferred: {skill_classification['preferred']}")
    logger.info(f"  Optional: {skill_classification['optional']}")
    logger.info(f"  Market analysis: {classification_result['market_signal']}")
    logger.info(f"  Employer override applied: {classification_result['market_signal'].get('employer_override_applied', False)}")

    # Fetch candidate data
    candidates_results: list[CandidateResult] = []
    candidate_scores: list[CandidateScore] = []

    async def handle_candidate(candidate) -> Tuple[CandidateResult, Optional[CandidateScore]]:
        nonlocal cache_hits, cache_misses

        cand_data = None
        cand_error = None
        cand_payload = {
            "username": candidate.github_username,
            "required_skills": all_skills_for_analysis,  # Include both mandatory and preferred skills
            "repos_limit": candidate.repos_limit,
            "lookback_days": candidate.lookback_days,
        }

        try:
            cached_cand = await cache_get(cache_key("candidate", cand_payload))
        except Exception:  # noqa: BLE001
            cached_cand = None

        if cached_cand:
            cand_data = cached_cand
            cache_hits += 1
        else:
            cache_misses += 1
            try:
                cand_resp = await ml_client.call_mcp_tool("analyze_github", cand_payload)
                cand_data = cand_resp.get("result") or cand_resp
                await cache_set(cache_key("candidate", cand_payload), cand_data, ttl_seconds=1800)
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Candidate {candidate.github_username} fetch failed: {exc}")
                cand_error = str(exc)

        result = CandidateResult(
            github_username=candidate.github_username,
            data=cand_data,
            error=cand_error,
        )

        scored = None
        if cand_data and not cand_error:
            scored = score_candidate(
                cand_data,
                all_skills_for_analysis,  # Include both mandatory and preferred skills
                candidate.github_username,
                role=request.role,
                skill_classification=skill_classification,
                resume_text=candidate.resume_text,
                linkedin_url=candidate.linkedin_url
            )

        return result, scored

    candidate_tasks = [handle_candidate(candidate) for candidate in request.candidates]
    results = await asyncio.gather(*candidate_tasks)

    for res, scored in results:
        candidates_results.append(res)
        if scored:
            candidate_scores.append(scored)

    # Deduplicate candidates
    if candidate_scores:
        candidate_scores_dict = [
            {
                "github_username": c.github_username,
                "score": c.score,
                "top_languages": c.top_languages,
                "matched_skills": c.matched_skills,
                **c.model_dump()
            }
            for c in candidate_scores
        ]
        deduped = deduplicate_candidates(candidate_scores_dict, merge_strategy="keep_best_score")

        # Rebuild candidate_scores from deduped
        candidate_scores = [
            CandidateScore(**d)
            for d in deduped
        ]

    # Market summary and insights
    market_summary = summarize_market(market_data, all_skills_for_analysis) if market_data and not market_error else None

    market_insights = None
    if market_data and not market_error:
        market_insights_data = generate_market_insights(
            market_data,
            all_skills_for_analysis,
            candidate_count=len(candidate_scores)
        )
        market_insights = MarketInsights(**market_insights_data)

    # Build recommendations
    recommendations = None
    if candidate_scores:
        recommendations = build_recommendations(candidate_scores, market_insights, all_skills_for_analysis)

    # Generate skill classification report
    skill_classification_report = None
    if classification_result:
        report_data = generate_market_based_requirements_report(classification_result)
        skill_classification_report = SkillClassificationReport(**report_data)

    # Build report
    report = HRReport(
        role=request.role,
        skills=all_skills_for_analysis,  # Include all skills (mandatory + preferred)
        market_summary=market_summary,
        market_insights=market_insights,
        candidate_scores=candidate_scores,
        recommendations=recommendations,
        skill_classification_report=skill_classification_report,
        summary=None,
    )
    report.summary = build_summary(report)

    processing_time_ms = int((time.time() - start_time) * 1000)

    return HRRunResponse(
        market=MarketResult(data=market_data, error=market_error),
        candidates=candidates_results,
        report=report,
        processing_time_ms=processing_time_ms,
        cache_stats={
            "hits": cache_hits,
            "misses": cache_misses,
            "total": cache_hits + cache_misses
        }
    )


@router.get("/interview/{username}")
async def get_interview_support(username: str):
    """Generate interview support materials for a candidate"""
    # This would typically fetch candidate data, but for now we'll return a template
    return {
        "username": username,
        "script": prepare_interview_script(
            username,
            matched_skills=["python", "fastapi"],
            skill_gaps=["kubernetes", "terraform"],
            risk_flags=["inactive_90_days"],
            seniority="middle"
        )
    }


@router.get("/outreach/{username}")
async def generate_outreach(username: str, role: str = "Backend Developer"):
    """Generate outreach template for a candidate"""
    return generate_outreach_template(
        username,
        role,
        matched_skills=["python", "docker"],
        company_name="TechCorp"
    )
