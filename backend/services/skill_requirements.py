from typing import Dict, List, Set, Tuple
from backend.services.normalization import normalize_skill, categorize_skill


def classify_skill_importance(role: str, skills: List[str]) -> Dict[str, List[str]]:
    """
    Classify skills into mandatory/preferred/optional based on role.

    Mandatory = blocking, no pass without them
    Preferred = important, lower score without them
    Optional = nice to have
    """

    role_lower = role.lower()
    normalized_skills = [normalize_skill(s) for s in skills]

    mandatory = []
    preferred = []
    optional = []

    # Backend roles - framework + database + containerization are mandatory
    if any(word in role_lower for word in ["backend", "бэкенд", "backend developer"]):
        for skill in normalized_skills:
            cat = categorize_skill(skill)

            # Backend framework = mandatory
            if skill in ["fastapi", "django", "flask", "spring", "express", "node"]:
                mandatory.append(skill)
            # Database = mandatory
            elif cat == "database":
                mandatory.append(skill)
            # Docker/containerization = mandatory for modern backend
            elif skill in ["docker", "kubernetes"]:
                mandatory.append(skill)
            # Programming language = preferred
            elif cat == "backend":
                preferred.append(skill)
            else:
                optional.append(skill)

    # Frontend roles - framework + build tools are mandatory
    elif any(word in role_lower for word in ["frontend", "фронтенд", "frontend developer"]):
        for skill in normalized_skills:
            cat = categorize_skill(skill)

            # Frontend framework = mandatory
            if skill in ["react", "vue", "angular"]:
                mandatory.append(skill)
            # JS/TS = mandatory
            elif skill in ["javascript", "typescript"]:
                mandatory.append(skill)
            else:
                optional.append(skill)

    # DevOps roles - all infra tools are mandatory
    elif any(word in role_lower for word in ["devops", "sre", "infrastructure"]):
        for skill in normalized_skills:
            cat = categorize_skill(skill)

            if cat == "devops":
                mandatory.append(skill)
            else:
                preferred.append(skill)

    # ML/Data Science roles - ML frameworks mandatory
    elif any(word in role_lower for word in ["ml", "machine learning", "data scientist", "ai"]):
        for skill in normalized_skills:
            cat = categorize_skill(skill)

            if cat == "ml":
                mandatory.append(skill)
            elif skill == "python":
                mandatory.append(skill)
            else:
                preferred.append(skill)

    # Generic developer - be more flexible
    else:
        # At least one programming language is mandatory
        lang_found = False
        for skill in normalized_skills:
            cat = categorize_skill(skill)
            if cat in ["backend", "frontend"]:
                if not lang_found:
                    mandatory.append(skill)
                    lang_found = True
                else:
                    preferred.append(skill)
            else:
                optional.append(skill)

    return {
        "mandatory": mandatory,
        "preferred": preferred,
        "optional": optional
    }


def check_mandatory_requirements(
    candidate_skills: List[str],
    mandatory_skills: List[str],
    skill_scores: List[Dict],
    min_score: float = 0.5,  # Increased from 0.3 to 0.5 - must have REAL evidence
    min_coverage: float = 0.8  # Must cover at least 80% of mandatory skills
) -> Tuple[bool, List[str]]:
    """
    Check if candidate meets mandatory requirements.

    STRICT CHECK:
    - Each mandatory skill must have score >= min_score (0.5 = real evidence in repos)
    - Must cover >= 80% of mandatory skills to pass
    - Even one critical missing skill = FAIL

    Returns: (passes, missing_mandatory_skills)
    """

    if not mandatory_skills:
        return True, []

    # Check skill scores
    skill_score_map = {
        normalize_skill(entry.get("skill", "")): entry.get("score", 0)
        for entry in skill_scores
    }

    missing = []
    covered = []

    for req_skill in mandatory_skills:
        norm_req = normalize_skill(req_skill)

        # Get score from skill_scores (this is evidence from GitHub repos)
        score = skill_score_map.get(norm_req, 0)

        # STRICT: Must have score >= min_score (0.5 = present in multiple repos)
        if score >= min_score:
            covered.append(req_skill)
        else:
            missing.append(req_skill)

    # Calculate coverage
    coverage = len(covered) / len(mandatory_skills) if mandatory_skills else 0

    # STRICT: Must cover >= min_coverage (80%) of mandatory skills
    passes = coverage >= min_coverage

    return passes, missing


def apply_mandatory_filter(
    score: int,
    decision: str,
    mandatory_missing: List[str],
    mandatory_total: int,
    role: str
) -> Tuple[int, str, List[str]]:
    """
    Apply mandatory skills filter to downgrade decision.

    STRICT RULES:
    - Missing ANY mandatory skill -> automatic "no"
    - Score capped at 30 (hard fail)
    - Clear blocking reasons
    """

    if not mandatory_missing:
        return score, decision, []

    missing_count = len(mandatory_missing)
    coverage_percent = ((mandatory_total - missing_count) / mandatory_total * 100) if mandatory_total > 0 else 0

    # HARD FAIL - automatic reject
    new_decision = "no"
    new_score = min(score, 30)  # Cap at 30 (hard fail)

    blocking_reasons = [
        f"BLOCKING: Missing mandatory skills ({missing_count}/{mandatory_total}): {', '.join(mandatory_missing[:3])}",
        f"Mandatory coverage only {coverage_percent:.0f}% (required 80%+)",
        f"Cannot proceed without: {', '.join(mandatory_missing[:2])}"
    ]

    return new_score, new_decision, blocking_reasons


def calculate_requirement_match_score(
    matched_skills: List[str],
    skill_gaps: List[str],
    mandatory_skills: List[str],
    preferred_skills: List[str]
) -> Dict[str, any]:
    """
    Calculate detailed match score based on requirement levels.
    """

    matched_norm = {normalize_skill(s) for s in matched_skills}
    gaps_norm = {normalize_skill(s) for s in skill_gaps}

    mandatory_norm = {normalize_skill(s) for s in mandatory_skills}
    preferred_norm = {normalize_skill(s) for s in preferred_skills}

    # Mandatory coverage
    mandatory_matched = matched_norm & mandatory_norm
    mandatory_missing = mandatory_norm - matched_norm

    mandatory_coverage = (
        len(mandatory_matched) / len(mandatory_norm) * 100
        if mandatory_norm else 100
    )

    # Preferred coverage
    preferred_matched = matched_norm & preferred_norm
    preferred_missing = preferred_norm - matched_norm

    preferred_coverage = (
        len(preferred_matched) / len(preferred_norm) * 100
        if preferred_norm else 100
    )

    # Overall weighted score
    # Mandatory = 70%, Preferred = 30%
    overall_coverage = (
        mandatory_coverage * 0.7 + preferred_coverage * 0.3
    )

    return {
        "mandatory_coverage": round(mandatory_coverage, 1),
        "preferred_coverage": round(preferred_coverage, 1),
        "overall_coverage": round(overall_coverage, 1),
        "mandatory_matched": list(mandatory_matched),
        "mandatory_missing": list(mandatory_missing),
        "preferred_matched": list(preferred_matched),
        "preferred_missing": list(preferred_missing),
    }


def generate_rejection_reason(
    mandatory_missing: List[str],
    role: str,
    candidate_skills: List[str]
) -> str:
    """
    Generate clear rejection reason for HR.
    """

    if not mandatory_missing:
        return ""

    has_skills = ", ".join(candidate_skills[:3]) if candidate_skills else "limited experience"
    needs_skills = ", ".join(mandatory_missing[:3])

    return (
        f"Candidate shows experience in {has_skills}, "
        f"but lacks required expertise in {needs_skills} "
        f"which are mandatory for the {role} role. "
        f"Recommend screening for roles that match their skill set better."
    )
