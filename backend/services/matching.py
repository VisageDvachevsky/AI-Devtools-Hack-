import math
from typing import Dict, List, Set, Tuple
from collections import Counter
from backend.services.normalization import normalize_skill, categorize_skill


def build_skill_vector(skills: List[str], weights: Dict[str, float] = None) -> Dict[str, float]:
    """Build weighted skill vector"""
    vector = {}
    for skill in skills:
        norm = normalize_skill(skill)
        if norm:
            weight = weights.get(norm, 1.0) if weights else 1.0
            vector[norm] = vector.get(norm, 0.0) + weight
    return vector


def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """Calculate cosine similarity between two skill vectors"""
    if not vec1 or not vec2:
        return 0.0

    all_skills = set(vec1.keys()) | set(vec2.keys())

    dot_product = sum(vec1.get(skill, 0.0) * vec2.get(skill, 0.0) for skill in all_skills)

    magnitude1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    magnitude2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def calculate_deep_match(
    vacancy_skills: List[str],
    candidate_skills: List[str],
    vacancy_text: str = "",
    candidate_repos: List[Dict] = None
) -> Dict[str, any]:
    """Deep matching with category-aware scoring"""

    vac_vector = build_skill_vector(vacancy_skills)
    cand_vector = build_skill_vector(candidate_skills)

    # Overall similarity
    similarity = cosine_similarity(vac_vector, cand_vector)

    # Category-based matching
    vac_skills_set = {normalize_skill(s) for s in vacancy_skills if normalize_skill(s)}
    cand_skills_set = {normalize_skill(s) for s in candidate_skills if normalize_skill(s)}

    matched_skills = list(vac_skills_set & cand_skills_set)
    missing_skills = list(vac_skills_set - cand_skills_set)
    extra_skills = list(cand_skills_set - vac_skills_set)

    # Category analysis
    matched_by_category = {}
    missing_by_category = {}

    for skill in matched_skills:
        cat = categorize_skill(skill)
        matched_by_category[cat] = matched_by_category.get(cat, 0) + 1

    for skill in missing_skills:
        cat = categorize_skill(skill)
        missing_by_category[cat] = missing_by_category.get(cat, 0) + 1

    # Calculate match reasons
    reasons = []
    if len(matched_skills) >= len(vacancy_skills) * 0.7:
        reasons.append(f"Strong skill match: {len(matched_skills)}/{len(vacancy_skills)} skills")
    if len(matched_skills) > 0:
        top_matched = matched_skills[:3]
        reasons.append(f"Key skills: {', '.join(top_matched)}")
    if extra_skills:
        top_extra = extra_skills[:3]
        reasons.append(f"Additional skills: {', '.join(top_extra)}")

    # Gap analysis
    gaps = []
    if missing_skills:
        critical_gaps = [s for s in missing_skills if categorize_skill(s) in ["backend", "frontend", "database"]]
        if critical_gaps:
            gaps.append(f"Missing critical: {', '.join(critical_gaps[:3])}")
        if len(missing_skills) > len(critical_gaps):
            gaps.append(f"Missing {len(missing_skills)} skills total")

    return {
        "similarity_score": round(similarity, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills[:10],
        "matched_by_category": matched_by_category,
        "missing_by_category": missing_by_category,
        "match_reasons": reasons,
        "gap_analysis": gaps,
        "coverage_percent": round(len(matched_skills) / len(vacancy_skills) * 100, 1) if vacancy_skills else 0.0
    }


def rank_candidates_by_match(
    vacancy_skills: List[str],
    candidates: List[Dict[str, any]],
    top_n: int = 10
) -> List[Dict[str, any]]:
    """Rank candidates by match quality"""

    ranked = []
    for candidate in candidates:
        cand_skills = candidate.get("skills", [])
        match_result = calculate_deep_match(vacancy_skills, cand_skills)

        ranked.append({
            "username": candidate.get("username", "unknown"),
            "match_score": match_result["similarity_score"],
            "coverage_percent": match_result["coverage_percent"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "match_reasons": match_result["match_reasons"],
            "gap_analysis": match_result["gap_analysis"]
        })

    ranked.sort(key=lambda x: (x["match_score"], x["coverage_percent"]), reverse=True)
    return ranked[:top_n]


def explain_match_decision(
    score: int,
    match_result: Dict[str, any],
    activity_metrics: Dict[str, any] = None
) -> Tuple[str, List[str]]:
    """Generate decision (go/hold/no) with top 3 reasons"""

    reasons = []

    # Skill match reasons
    if match_result.get("coverage_percent", 0) >= 70:
        reasons.append(f"Excellent skill coverage: {match_result['coverage_percent']}%")
    elif match_result.get("coverage_percent", 0) >= 50:
        reasons.append(f"Good skill coverage: {match_result['coverage_percent']}%")
    else:
        reasons.append(f"Low skill coverage: {match_result['coverage_percent']}%")

    # Activity reasons
    if activity_metrics:
        if activity_metrics.get("days_since_last_push", 999) <= 30:
            reasons.append("Very active: recent commits")
        elif activity_metrics.get("days_since_last_push", 999) <= 90:
            reasons.append("Active: commits within 90 days")
        else:
            reasons.append("Inactive: no recent commits")

        if activity_metrics.get("total_stars", 0) > 50:
            reasons.append(f"Popular repos: {activity_metrics['total_stars']} stars")

    # Gap reasons
    gaps = match_result.get("gap_analysis", [])
    if gaps:
        reasons.append(gaps[0])

    # Decision logic
    if score >= 70:
        decision = "go"
    elif score >= 45:
        decision = "hold"
    else:
        decision = "no"

    return decision, reasons[:3]
