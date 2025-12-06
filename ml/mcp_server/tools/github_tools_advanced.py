"""
Advanced GitHub Analysis Tool with Deep Code Scanning
Analyzes dependencies, imports, and code patterns for accurate skill detection
"""
import asyncio
import base64
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple

import httpx
from httpx import TimeoutException
from pydantic import BaseModel, Field, HttpUrl, ValidationError

from ml.mcp_server.tools.registry import tool_registry

GITHUB_API_URL = "https://api.github.com"

# Dependency file patterns for different ecosystems
DEPENDENCY_FILES = {
    "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "environment.yml"],
    "javascript": ["package.json", "package-lock.json", "yarn.lock"],
    "typescript": ["package.json", "tsconfig.json"],
    "go": ["go.mod", "go.sum"],
    "rust": ["Cargo.toml", "Cargo.lock"],
    "ruby": ["Gemfile", "Gemfile.lock"],
    "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
    "csharp": ["*.csproj", "packages.config"],
    "php": ["composer.json", "composer.lock"],
}

# Framework and library patterns
FRAMEWORK_PATTERNS = {
    "fastapi": {
        "imports": [r"from\s+fastapi\s+import", r"import\s+fastapi"],
        "dependencies": ["fastapi"],
        "files": ["main.py", "app.py"],
    },
    "django": {
        "imports": [r"from\s+django", r"import\s+django"],
        "dependencies": ["django", "Django"],
        "files": ["settings.py", "urls.py", "models.py"],
    },
    "flask": {
        "imports": [r"from\s+flask\s+import", r"import\s+flask"],
        "dependencies": ["flask", "Flask"],
        "files": ["app.py", "application.py"],
    },
    "react": {
        "dependencies": ["react", "react-dom"],
        "files": ["App.jsx", "App.tsx", "index.jsx", "index.tsx"],
        "patterns": [r"import\s+.*\s+from\s+['\"]react['\"]"],
    },
    "vue": {
        "dependencies": ["vue", "@vue/cli"],
        "files": ["App.vue", "main.js"],
        "patterns": [r"import\s+.*\s+from\s+['\"]vue['\"]"],
    },
    "angular": {
        "dependencies": ["@angular/core", "@angular/common"],
        "files": ["app.component.ts", "app.module.ts"],
        "patterns": [r"import\s+.*\s+from\s+['\"]@angular"],
    },
    "docker": {
        "files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    },
    "kubernetes": {
        "files": ["*.yaml", "*.yml"],
        "patterns": [r"apiVersion:\s*apps/v1", r"kind:\s*Deployment"],
    },
    "postgresql": {
        "dependencies": ["psycopg2", "psycopg2-binary", "pg"],
        "patterns": [r"PostgreSQL", r"postgres://"],
    },
    "redis": {
        "dependencies": ["redis", "redis-py"],
        "patterns": [r"import\s+redis", r"from\s+redis\s+import"],
    },
}


class AdvancedGithubRequest(BaseModel):
    username: str = Field(..., description="GitHub username")
    required_skills: List[str] = Field(default_factory=list, description="Required skills to analyze")
    repos_limit: int = Field(10, ge=1, le=50, description="Number of repos to analyze")
    lookback_days: Optional[int] = Field(None, ge=1, description="Filter repos by last update")
    analyze_code: bool = Field(True, description="Enable deep code analysis")
    analyze_dependencies: bool = Field(True, description="Analyze dependency files")


class EnhancedSkillScore(BaseModel):
    skill: str
    score: float = Field(..., ge=0.0, le=1.0)
    evidence: str
    confidence: str = Field(default="medium", description="low/medium/high/very_high")
    sources: List[str] = Field(default_factory=list, description="Where skill was found")
    weight: float = Field(default=1.0, description="Importance weight")
    dependency_count: int = Field(default=0)
    import_count: int = Field(default=0)
    file_count: int = Field(default=0)


class CodeAnalysisMetrics(BaseModel):
    total_files_scanned: int = 0
    dependency_files_found: int = 0
    imports_analyzed: int = 0
    frameworks_detected: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class AdvancedGithubResponse(BaseModel):
    username: str
    repos_analyzed: int
    top_languages: List[str]
    skill_scores: List[EnhancedSkillScore]
    risk_flags: List[str]
    activity_metrics: Dict
    code_analysis: CodeAnalysisMetrics
    source: str = "github_advanced"


def _auth_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-HR-Agent-Advanced/1.0 (+mcp)",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _fetch_file_content(client: httpx.AsyncClient, repo_full_name: str, file_path: str) -> Optional[str]:
    """Fetch file content from GitHub API"""
    try:
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/{file_path}"
        resp = await client.get(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("encoding") == "base64":
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                return content
    except Exception:
        pass
    return None


async def _analyze_dependencies(
    client: httpx.AsyncClient, repo_full_name: str, required_skills: List[str]
) -> Tuple[Dict[str, int], List[str]]:
    """Analyze dependency files to detect skills"""
    skill_counts: Dict[str, int] = defaultdict(int)
    files_found = []

    # Check common dependency files
    all_dep_files = set()
    for files in DEPENDENCY_FILES.values():
        all_dep_files.update(files)

    for dep_file in all_dep_files:
        if "*" in dep_file:
            continue
        content = await _fetch_file_content(client, repo_full_name, dep_file)
        if content:
            files_found.append(dep_file)
            content_lower = content.lower()

            # Check each required skill
            for skill in required_skills:
                skill_lower = skill.lower()
                # Direct mentions in dependencies
                if skill_lower in content_lower:
                    skill_counts[skill] += 3  # Higher weight for dependency files

                # Check framework patterns
                if skill_lower in FRAMEWORK_PATTERNS:
                    pattern_data = FRAMEWORK_PATTERNS[skill_lower]
                    for dep in pattern_data.get("dependencies", []):
                        if dep.lower() in content_lower:
                            skill_counts[skill] += 5

    return dict(skill_counts), files_found


async def _analyze_code_imports(
    client: httpx.AsyncClient, repo_full_name: str, required_skills: List[str], languages: List[str]
) -> Tuple[Dict[str, int], int]:
    """Analyze code files for imports and patterns"""
    skill_counts: Dict[str, int] = defaultdict(int)
    imports_found = 0

    # Sample files to analyze based on language
    files_to_check = []
    if "Python" in languages:
        files_to_check.extend(["main.py", "app.py", "__init__.py", "setup.py"])
    if "JavaScript" in languages or "TypeScript" in languages:
        files_to_check.extend(["index.js", "index.ts", "app.js", "app.ts", "main.js"])
    if "Go" in languages:
        files_to_check.extend(["main.go", "server.go"])

    for file_path in files_to_check:
        content = await _fetch_file_content(client, repo_full_name, file_path)
        if content:
            imports_found += 1

            for skill in required_skills:
                skill_lower = skill.lower()

                # Check framework patterns
                if skill_lower in FRAMEWORK_PATTERNS:
                    pattern_data = FRAMEWORK_PATTERNS[skill_lower]

                    # Check import patterns
                    for pattern in pattern_data.get("imports", []) + pattern_data.get("patterns", []):
                        if re.search(pattern, content, re.IGNORECASE):
                            skill_counts[skill] += 2

                # Generic import check
                import_patterns = [
                    rf"import\s+{re.escape(skill_lower)}",
                    rf"from\s+{re.escape(skill_lower)}\s+import",
                    rf"require\(['\"]{ re.escape(skill_lower)}['\"]",
                ]
                for pattern in import_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        skill_counts[skill] += 2

    return dict(skill_counts), imports_found


async def _check_framework_files(
    client: httpx.AsyncClient, repo_full_name: str, required_skills: List[str]
) -> Dict[str, int]:
    """Check for framework-specific files"""
    skill_counts: Dict[str, int] = defaultdict(int)

    for skill in required_skills:
        skill_lower = skill.lower()
        if skill_lower in FRAMEWORK_PATTERNS:
            pattern_data = FRAMEWORK_PATTERNS[skill_lower]
            for file_name in pattern_data.get("files", []):
                if "*" in file_name:
                    continue
                content = await _fetch_file_content(client, repo_full_name, file_name)
                if content:
                    skill_counts[skill] += 3

    return dict(skill_counts)


def _calculate_weighted_score(
    base_score: float,
    dependency_count: int,
    import_count: int,
    file_count: int,
    repo_stars: int,
    repo_recent: bool,
) -> Tuple[float, str, float]:
    """Calculate weighted score with confidence"""

    # Start with base score
    weighted = base_score

    # Dependency evidence (strongest signal)
    if dependency_count > 0:
        weighted += min(0.3, dependency_count * 0.1)

    # Import evidence (strong signal)
    if import_count > 0:
        weighted += min(0.2, import_count * 0.05)

    # File evidence (medium signal)
    if file_count > 0:
        weighted += min(0.15, file_count * 0.05)

    # Popularity weight
    if repo_stars > 100:
        weighted *= 1.2
    elif repo_stars > 20:
        weighted *= 1.1

    # Recency weight
    if repo_recent:
        weighted *= 1.1

    # Cap at 1.0
    weighted = min(1.0, weighted)

    # Determine confidence
    total_evidence = dependency_count + import_count + file_count
    if total_evidence >= 5:
        confidence = "very_high"
        confidence_weight = 1.0
    elif total_evidence >= 3:
        confidence = "high"
        confidence_weight = 0.9
    elif total_evidence >= 1:
        confidence = "medium"
        confidence_weight = 0.7
    else:
        confidence = "low"
        confidence_weight = 0.5

    return weighted, confidence, confidence_weight


@tool_registry.register(
    name="analyze_github_advanced",
    description="Advanced GitHub analysis with dependency scanning and code pattern detection",
    parameters=AdvancedGithubRequest.model_json_schema(),
)
async def analyze_github_advanced(**parameters) -> dict:
    """
    Advanced GitHub analysis that goes beyond basic metadata:
    - Scans dependency files (requirements.txt, package.json, etc)
    - Analyzes code imports and patterns
    - Detects frameworks and libraries in use
    - Provides weighted confidence scores
    """
    try:
        payload = AdvancedGithubRequest(**parameters)
    except ValidationError as exc:
        return {"error": "validation_error", "details": exc.errors()}

    try:
        async with httpx.AsyncClient(timeout=30.0, headers=_auth_headers()) as client:
            # Fetch repositories
            repos_resp = await client.get(
                f"{GITHUB_API_URL}/users/{payload.username}/repos",
                params={"per_page": payload.repos_limit, "sort": "updated", "direction": "desc"},
            )

            if repos_resp.status_code == 404:
                return {"error": "not_found", "details": "GitHub user not found"}
            if repos_resp.status_code == 401:
                return {"error": "unauthorized", "details": "Invalid GitHub token"}
            if repos_resp.status_code == 429:
                return {"error": "rate_limited", "details": "GitHub rate limit exceeded"}
            if repos_resp.status_code >= 400:
                return {"error": "http_error", "status_code": repos_resp.status_code}

            repos = repos_resp.json()[:payload.repos_limit]

            # Filter by date if needed
            if payload.lookback_days:
                threshold = datetime.now(timezone.utc) - timedelta(days=payload.lookback_days)
                repos = [
                    r for r in repos
                    if r.get("pushed_at")
                    and datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) >= threshold
                ]

            # Collect languages
            lang_counter = Counter()
            total_stars = 0
            dependency_skills: Dict[str, int] = defaultdict(int)
            import_skills: Dict[str, int] = defaultdict(int)
            file_skills: Dict[str, int] = defaultdict(int)

            total_files_scanned = 0
            dependency_files_found = []
            imports_analyzed = 0
            frameworks_detected = set()

            # Analyze each repository
            for repo in repos:
                repo_name = repo.get("full_name", "")
                total_stars += repo.get("stargazers_count", 0)

                # Get languages
                languages_url = repo.get("languages_url")
                if languages_url:
                    lang_resp = await client.get(languages_url, timeout=5.0)
                    if lang_resp.status_code == 200:
                        languages = list(lang_resp.json().keys())
                        lang_counter.update(languages)

                # Deep analysis if enabled
                if payload.analyze_dependencies and languages:
                    dep_counts, dep_files = await _analyze_dependencies(
                        client, repo_name, payload.required_skills
                    )
                    for skill, count in dep_counts.items():
                        dependency_skills[skill] += count
                    dependency_files_found.extend(dep_files)
                    total_files_scanned += len(dep_files)

                if payload.analyze_code and languages:
                    import_counts, imports = await _analyze_code_imports(
                        client, repo_name, payload.required_skills, languages
                    )
                    for skill, count in import_counts.items():
                        import_skills[skill] += count
                    imports_analyzed += imports

                    file_counts = await _check_framework_files(client, repo_name, payload.required_skills)
                    for skill, count in file_counts.items():
                        file_skills[skill] += count

            # Detect frameworks
            for skill in payload.required_skills:
                if skill.lower() in FRAMEWORK_PATTERNS:
                    if dependency_skills.get(skill, 0) > 0 or import_skills.get(skill, 0) > 0:
                        frameworks_detected.add(skill)

            # Calculate enhanced skill scores
            skill_scores = []
            top_languages = [lang for lang, _ in lang_counter.most_common(5)]

            for skill in payload.required_skills:
                skill_lower = skill.lower()

                # Base score from language matching
                base_score = 0.0
                for lang in top_languages:
                    if skill_lower == lang.lower():
                        base_score = 0.5

                # Get evidence counts
                dep_count = dependency_skills.get(skill, 0)
                imp_count = import_skills.get(skill, 0)
                file_count = file_skills.get(skill, 0)

                # Determine if repos are recent
                recent = any(
                    r.get("pushed_at")
                    and (datetime.now(timezone.utc) - datetime.fromisoformat(
                        r["pushed_at"].replace("Z", "+00:00")
                    )).days <= 90
                    for r in repos
                )

                # Calculate weighted score
                weighted_score, confidence, conf_weight = _calculate_weighted_score(
                    base_score, dep_count, imp_count, file_count, total_stars, recent
                )

                # Build evidence
                evidence_parts = []
                if dep_count > 0:
                    evidence_parts.append(f"{dep_count} dependency refs")
                if imp_count > 0:
                    evidence_parts.append(f"{imp_count} import statements")
                if file_count > 0:
                    evidence_parts.append(f"{file_count} framework files")
                if base_score > 0:
                    evidence_parts.append(f"language match")

                evidence = "; ".join(evidence_parts) if evidence_parts else "No direct evidence"

                # Sources
                sources = []
                if dep_count > 0:
                    sources.append("dependencies")
                if imp_count > 0:
                    sources.append("imports")
                if file_count > 0:
                    sources.append("framework_files")

                skill_scores.append(
                    EnhancedSkillScore(
                        skill=skill,
                        score=round(weighted_score, 2),
                        evidence=evidence,
                        confidence=confidence,
                        sources=sources,
                        weight=conf_weight,
                        dependency_count=dep_count,
                        import_count=imp_count,
                        file_count=file_count,
                    )
                )

            # Activity metrics
            most_recent_push = None
            for repo in repos:
                pushed_at = repo.get("pushed_at")
                if pushed_at:
                    push_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    if not most_recent_push or push_dt > most_recent_push:
                        most_recent_push = push_dt

            days_since_push = None
            if most_recent_push:
                days_since_push = (datetime.now(timezone.utc) - most_recent_push).days

            activity_metrics = {
                "days_since_last_push": days_since_push,
                "total_stars": total_stars,
                "total_forks": sum(r.get("forks_count", 0) for r in repos),
                "repo_diversity_score": min(100, len(lang_counter) * 10),
                "commit_frequency_score": 100 if days_since_push and days_since_push <= 7 else 50,
            }

            # Risk flags
            risk_flags = []
            if not repos:
                risk_flags.append("no_repos")
            if days_since_push and days_since_push > 180:
                risk_flags.append("inactive_180_days")
            if total_files_scanned == 0:
                risk_flags.append("no_dependency_files")

            # Code analysis metrics
            code_analysis = CodeAnalysisMetrics(
                total_files_scanned=total_files_scanned,
                dependency_files_found=len(set(dependency_files_found)),
                imports_analyzed=imports_analyzed,
                frameworks_detected=list(frameworks_detected),
                confidence_score=round(
                    sum(s.weight for s in skill_scores) / len(skill_scores) if skill_scores else 0.0, 2
                ),
            )

            response = AdvancedGithubResponse(
                username=payload.username,
                repos_analyzed=len(repos),
                top_languages=top_languages,
                skill_scores=skill_scores,
                risk_flags=risk_flags,
                activity_metrics=activity_metrics,
                code_analysis=code_analysis,
            )

            return response.model_dump()

    except TimeoutException:
        return {"error": "timeout", "details": "GitHub API request timed out"}
    except httpx.RequestError as exc:
        return {"error": "network_error", "details": str(exc)}
    except Exception as exc:
        return {"error": "unexpected_error", "details": str(exc)}
