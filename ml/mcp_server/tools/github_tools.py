import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import httpx
from httpx import TimeoutException
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from ml.mcp_server.tools.registry import tool_registry

GITHUB_API_URL = "https://api.github.com"


class GithubAnalysisRequest(BaseModel):
    username: str = Field(..., description="GitHub username кандидата.")
    required_skills: List[str] = Field(default_factory=list, description="Список требуемых навыков.")
    repos_limit: int = Field(5, ge=1, le=30, description="Сколько репозиториев анализировать.")
    lookback_days: Optional[int] = Field(
        None, ge=1, description="Фильтровать репозитории, обновленные за N дней."
    )


class SkillScore(BaseModel):
    skill: str
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: str


class RepoSummary(BaseModel):
    name: str
    url: HttpUrl
    stars: int
    languages: List[str]


class ActivityMetrics(BaseModel):
    days_since_last_push: Optional[int] = None
    commit_frequency_score: int = 0
    total_stars: int = 0
    total_forks: int = 0
    repo_diversity_score: int = 0
    one_commit_repos_count: int = 0
    avg_commits_per_repo: float = 0.0


class GithubAnalysisResponse(BaseModel):
    username: str
    repos_analyzed: int
    top_languages: List[str]
    skill_scores: List[SkillScore]
    risk_flags: List[str]
    repos: List[RepoSummary]
    activity_metrics: Optional[ActivityMetrics] = None
    source: str = "github"


def _auth_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-HR-Agent/0.1 (+mcp)",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _filter_repos_by_date(repos: List[dict], lookback_days: Optional[int]) -> List[dict]:
    if not lookback_days:
        return repos
    threshold = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    filtered = []
    for repo in repos:
        updated_at = repo.get("pushed_at") or repo.get("updated_at")
        if not updated_at:
            continue
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if updated_dt >= threshold:
            filtered.append(repo)
    return filtered


def _score_skills(required_skills: List[str], repo_summaries: List[RepoSummary], languages: Counter) -> List[SkillScore]:
    scores: List[SkillScore] = []
    for skill in required_skills:
        skill_lower = skill.lower()
        lang_matches = sum(1 for lang in languages if lang.lower() == skill_lower)
        repo_hits = 0
        evidence_parts = []
        for repo in repo_summaries:
            name_hit = skill_lower in repo.name.lower()
            lang_hit = any(lang.lower() == skill_lower for lang in repo.languages)
            if name_hit or lang_hit:
                repo_hits += 1
                evidence_parts.append(f"{repo.name}: langs={','.join(repo.languages) or 'n/a'}")
        base = max(1, len(repo_summaries))
        raw_score = min(1.0, (lang_matches + repo_hits) / base)
        evidence = "; ".join(evidence_parts) if evidence_parts else "Нет прямых совпадений, слабый сигнал."
        scores.append(SkillScore(skill=skill, score=round(raw_score, 2), evidence=evidence))
    return scores


def _calculate_activity_metrics(repos: List[dict], repo_summaries: List[RepoSummary]) -> ActivityMetrics:
    """Calculate detailed activity metrics for candidate"""

    if not repos:
        return ActivityMetrics()

    # Find most recent push
    most_recent_push = None
    for repo in repos:
        pushed_at = repo.get("pushed_at")
        if pushed_at:
            try:
                push_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                if not most_recent_push or push_dt > most_recent_push:
                    most_recent_push = push_dt
            except ValueError:
                continue

    days_since_push = None
    if most_recent_push:
        delta = datetime.now(timezone.utc) - most_recent_push
        days_since_push = delta.days

    # Calculate total stars and forks
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)

    # Diversity: unique languages
    all_langs = set()
    for summary in repo_summaries:
        all_langs.update(summary.languages)
    diversity_score = min(100, len(all_langs) * 10)

    # One-commit repos (approximation: very low forks and stars)
    one_commit_count = sum(
        1 for repo in repos
        if repo.get("stargazers_count", 0) == 0 and repo.get("forks_count", 0) == 0
    )

    # Commit frequency score based on days since last push
    if days_since_push is None:
        freq_score = 0
    elif days_since_push <= 7:
        freq_score = 100
    elif days_since_push <= 30:
        freq_score = 80
    elif days_since_push <= 90:
        freq_score = 60
    elif days_since_push <= 180:
        freq_score = 40
    else:
        freq_score = 20

    return ActivityMetrics(
        days_since_last_push=days_since_push,
        commit_frequency_score=freq_score,
        total_stars=total_stars,
        total_forks=total_forks,
        repo_diversity_score=diversity_score,
        one_commit_repos_count=one_commit_count,
        avg_commits_per_repo=0.0  # Would need commits API
    )


@tool_registry.register(
    name="analyze_github",
    description="Анализ публичных GitHub репозиториев кандидата и навыков.",
    parameters=GithubAnalysisRequest.model_json_schema(),
)
async def analyze_github(**parameters) -> dict:
    try:
        payload = GithubAnalysisRequest(**parameters)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors()}

    try:
        async with httpx.AsyncClient(timeout=10.0, headers=_auth_headers()) as client:
            repos_resp = await client.get(
                f"{GITHUB_API_URL}/users/{payload.username}/repos",
                params={"per_page": min(payload.repos_limit, 100), "sort": "updated", "direction": "desc"},
            )

            if repos_resp.status_code == 404:
                return {"error": "not_found", "details": "GitHub пользователь не найден."}
            if repos_resp.status_code == 401:
                return {"error": "unauthorized", "details": "GitHub token неверный или отсутствует."}
            if repos_resp.status_code == 429:
                retry_after = repos_resp.headers.get("Retry-After")
                return {"error": "rate_limited", "details": "GitHub rate limit exceeded.", "retry_after": retry_after}
            if repos_resp.status_code >= 400:
                return {
                    "error": "http_error",
                    "status_code": repos_resp.status_code,
                    "details": repos_resp.text,
                }

            repos_data = repos_resp.json()
            repos = _filter_repos_by_date(repos_data, payload.lookback_days)[: payload.repos_limit]
            repo_summaries: List[RepoSummary] = []
            lang_counter: Counter[str] = Counter()

            for repo in repos:
                languages_resp = await client.get(repo.get("languages_url", ""))
                languages = list(languages_resp.json().keys()) if languages_resp.status_code == 200 else []
                lang_counter.update(languages)
                repo_summaries.append(
                    RepoSummary(
                        name=repo.get("name") or "repo",
                        url=repo.get("html_url") or f"https://github.com/{payload.username}",
                        stars=repo.get("stargazers_count", 0),
                        languages=languages,
                    )
                )
    except TimeoutException:
        return {"error": "timeout", "details": "GitHub API request timed out"}
    except httpx.RequestError as exc:
        return {"error": "network_error", "details": str(exc)}

    skill_scores = _score_skills(payload.required_skills, repo_summaries, lang_counter)

    # Calculate activity metrics
    activity_metrics = _calculate_activity_metrics(repos_data, repo_summaries)

    # Risk flags
    risk_flags = []
    if not repos:
        risk_flags.append("no_repos")
    if not lang_counter:
        risk_flags.append("no_languages_detected")
    if activity_metrics.days_since_last_push and activity_metrics.days_since_last_push > 180:
        risk_flags.append("inactive_180_days")
    if activity_metrics.one_commit_repos_count > len(repos) * 0.7:
        risk_flags.append("mostly_one_commit_repos")
    if activity_metrics.total_stars == 0 and len(repos) > 3:
        risk_flags.append("no_stars")

    response_payload = GithubAnalysisResponse(
        username=payload.username,
        repos_analyzed=len(repos),
        top_languages=[lang for lang, _ in lang_counter.most_common(5)],
        skill_scores=skill_scores,
        risk_flags=risk_flags,
        repos=repo_summaries,
        activity_metrics=activity_metrics,
    )
    return response_payload.model_dump()
