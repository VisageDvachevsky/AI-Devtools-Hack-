from typing import Dict, List, Optional, Set, Tuple
from collections import Counter
import re
from backend.services.normalization import normalize_skill, normalize_skills_batch


def analyze_skill_importance_from_market(
    market_data: Dict[str, any],
    required_skills: List[str]
) -> Dict[str, float]:
    """
    Analyze market data to determine skill importance based on:
    - Frequency in vacancies (how often mentioned)
    - Co-occurrence with other required skills
    - Position in requirements (title vs description)
    """

    if not market_data:
        return {}

    items = market_data.get("items", [])
    if not items:
        return {}

    # Count skill mentions across all vacancies
    skill_mentions = Counter()
    skill_in_title = Counter()
    total_vacancies = len(items)

    for item in items:
        # Skills from vacancy
        vacancy_skills_raw = item.get("skills", [])
        vacancy_skills = normalize_skills_batch(vacancy_skills_raw)

        # Title analysis
        title = item.get("title", "").lower()

        for skill in vacancy_skills:
            skill_mentions[skill] += 1

            # Check if skill mentioned in title
            if skill in title:
                skill_in_title[skill] += 1

    # Calculate importance scores for each required skill
    importance_scores = {}

    for req_skill in required_skills:
        norm_skill = normalize_skill(req_skill)

        # Frequency score: how often appears in market
        frequency = skill_mentions.get(norm_skill, 0)
        frequency_score = frequency / total_vacancies if total_vacancies > 0 else 0

        # Title score: how often in job titles (premium signal)
        title_score = skill_in_title.get(norm_skill, 0) / total_vacancies if total_vacancies > 0 else 0

        # Combined importance (0 to 1)
        # Title mentions weighted heavily (3x) as they indicate core requirements
        importance = min(1.0, frequency_score + (title_score * 3))

        importance_scores[req_skill] = round(importance, 3)

    return importance_scores


def classify_by_importance_threshold(
    importance_scores: Dict[str, float],
    mandatory_threshold: float = 0.7,
    preferred_threshold: float = 0.3
) -> Dict[str, List[str]]:
    """
    Classify skills by importance thresholds:
    - mandatory: appears in >70% of vacancies
    - preferred: appears in 30-70% of vacancies
    - optional: appears in <30% of vacancies
    """

    mandatory = []
    preferred = []
    optional = []

    for skill, importance in importance_scores.items():
        if importance >= mandatory_threshold:
            mandatory.append(skill)
        elif importance >= preferred_threshold:
            preferred.append(skill)
        else:
            optional.append(skill)

    return {
        "mandatory": mandatory,
        "preferred": preferred,
        "optional": optional
    }


def analyze_role_context(role: str, required_skills: List[str]) -> Dict[str, any]:
    """
    Analyze role title to extract context and adjust importance.
    Uses keyword matching for common patterns.
    """

    role_lower = role.lower()

    context = {
        "seniority": "unknown",
        "primary_focus": "general",
        "tech_stack_signals": []
    }

    # Detect seniority
    if any(word in role_lower for word in ["senior", "lead", "principal", "architect", "старший"]):
        context["seniority"] = "senior"
    elif any(word in role_lower for word in ["junior", "младший", "стажер", "intern"]):
        context["seniority"] = "junior"
    elif any(word in role_lower for word in ["middle", "средний"]):
        context["seniority"] = "middle"

    # Detect primary focus
    if any(word in role_lower for word in ["backend", "бэкенд", "back-end"]):
        context["primary_focus"] = "backend"
    elif any(word in role_lower for word in ["frontend", "фронтенд", "front-end"]):
        context["primary_focus"] = "frontend"
    elif any(word in role_lower for word in ["fullstack", "full-stack", "full stack", "фулстек"]):
        context["primary_focus"] = "fullstack"
    elif any(word in role_lower for word in ["devops", "sre", "infrastructure", "инфраструктура"]):
        context["primary_focus"] = "devops"
    elif any(word in role_lower for word in ["ml", "machine learning", "data scien", "ai"]):
        context["primary_focus"] = "ml"
    elif any(word in role_lower for word in ["qa", "test", "тестировщик"]):
        context["primary_focus"] = "qa"

    # Extract tech stack mentions from title
    for skill in required_skills:
        if normalize_skill(skill) in role_lower:
            context["tech_stack_signals"].append(skill)

    return context


def adjust_importance_by_context(
    importance_scores: Dict[str, float],
    role_context: Dict[str, any],
    required_skills: List[str]
) -> Dict[str, float]:
    """
    Adjust importance scores based on role context.
    Skills mentioned in title get boosted.
    """

    adjusted = importance_scores.copy()

    # Boost skills that appear in job title
    tech_stack_signals = role_context.get("tech_stack_signals", [])
    for skill in tech_stack_signals:
        if skill in adjusted:
            # Boost by 0.3 (caps at 1.0)
            adjusted[skill] = min(1.0, adjusted[skill] + 0.3)

    # For senior roles, boost all scores slightly (higher bar)
    if role_context.get("seniority") == "senior":
        for skill in adjusted:
            adjusted[skill] = min(1.0, adjusted[skill] * 1.1)

    return adjusted


def calculate_skill_co_occurrence(
    market_data: Dict[str, any],
    required_skills: List[str]
) -> Dict[str, List[str]]:
    """
    Find which skills commonly appear together.
    Useful for detecting skill clusters (e.g., FastAPI usually with Docker).
    """

    if not market_data:
        return {}

    items = market_data.get("items", [])
    skill_pairs = Counter()

    for item in items:
        vacancy_skills = set(normalize_skills_batch(item.get("skills", [])))

        # Count co-occurrences
        for skill1 in required_skills:
            norm1 = normalize_skill(skill1)
            if norm1 not in vacancy_skills:
                continue

            for skill2 in required_skills:
                if skill1 == skill2:
                    continue

                norm2 = normalize_skill(skill2)
                if norm2 in vacancy_skills:
                    pair = tuple(sorted([skill1, skill2]))
                    skill_pairs[pair] += 1

    # Build co-occurrence map
    co_occurrence = {}
    total_items = len(items)

    for (skill1, skill2), count in skill_pairs.items():
        # If they appear together in >50% of cases, they're related
        if count / total_items > 0.5:
            if skill1 not in co_occurrence:
                co_occurrence[skill1] = []
            if skill2 not in co_occurrence:
                co_occurrence[skill2] = []

            co_occurrence[skill1].append(skill2)
            co_occurrence[skill2].append(skill1)

    return co_occurrence


def smart_classify_skills(
    role: str,
    required_skills: List[str],
    market_data: Dict[str, any],
    mandatory_threshold: float = 0.7,
    preferred_threshold: float = 0.3,
    employer_mandatory: Optional[List[str]] = None,
    employer_preferred: Optional[List[str]] = None
) -> Dict[str, any]:
    """
    Universal skill classification based on market data and role context.

    CRITICAL FIX: Employer's explicit requirements take precedence!
    - Skills in employer_mandatory = MANDATORY (hard requirement)
    - Skills in employer_preferred = PREFERRED (nice to have)
    - Market data used to validate and adjust, not override

    This ensures we respect employer's intent while using market data for validation.
    """

    # Step 1: Analyze market data for skill importance
    importance_scores = analyze_skill_importance_from_market(market_data, required_skills)

    # Step 2: Analyze role context
    role_context = analyze_role_context(role, required_skills)

    # Step 3: Adjust importance based on context
    adjusted_scores = adjust_importance_by_context(importance_scores, role_context, required_skills)

    # Step 4: Classify by thresholds (market-based baseline)
    classification = classify_by_importance_threshold(
        adjusted_scores,
        mandatory_threshold,
        preferred_threshold
    )

    # Step 5: OVERRIDE with employer's explicit requirements
    # This is critical - employer knows what they need!
    if employer_mandatory:
        # Start with employer's mandatory list
        classification["mandatory"] = list(employer_mandatory)

        # Remove from preferred/optional if they're in mandatory
        classification["preferred"] = [
            s for s in classification["preferred"]
            if s not in employer_mandatory
        ]
        classification["optional"] = [
            s for s in classification["optional"]
            if s not in employer_mandatory
        ]

    if employer_preferred:
        # Add employer's preferred to preferred (if not already mandatory)
        for skill in employer_preferred:
            if skill not in classification["mandatory"] and skill not in classification["preferred"]:
                classification["preferred"].append(skill)
                # Remove from optional
                if skill in classification["optional"]:
                    classification["optional"].remove(skill)

    # Step 6: Analyze co-occurrence for skill clusters
    co_occurrence = calculate_skill_co_occurrence(market_data, required_skills)

    return {
        "classification": classification,
        "importance_scores": adjusted_scores,
        "role_context": role_context,
        "skill_clusters": co_occurrence,
        "market_signal": {
            "total_vacancies_analyzed": len(market_data.get("items", [])) if market_data else 0,
            "threshold_mandatory": mandatory_threshold,
            "threshold_preferred": preferred_threshold,
            "employer_override_applied": bool(employer_mandatory or employer_preferred)
        }
    }


def explain_classification(
    skill: str,
    classification_result: Dict[str, any]
) -> str:
    """
    Generate human-readable explanation why skill was classified as mandatory/preferred/optional.
    """

    importance = classification_result["importance_scores"].get(skill, 0)
    role_context = classification_result["role_context"]
    market_signal = classification_result["market_signal"]

    classification = classification_result["classification"]
    level = "optional"
    if skill in classification["mandatory"]:
        level = "mandatory"
    elif skill in classification["preferred"]:
        level = "preferred"

    reasons = []

    # Market frequency
    freq_percent = importance * 100
    reasons.append(f"appears in {freq_percent:.0f}% of market vacancies")

    # Title mention
    if skill in role_context.get("tech_stack_signals", []):
        reasons.append(f"explicitly mentioned in job title '{role_context.get('primary_focus', 'role')}'")

    # Co-occurrence
    clusters = classification_result.get("skill_clusters", {})
    if skill in clusters:
        related = clusters[skill][:2]
        reasons.append(f"commonly paired with {', '.join(related)}")

    explanation = f"Classified as {level.upper()} because: " + "; ".join(reasons)

    return explanation


def generate_market_based_requirements_report(
    classification_result: Dict[str, any]
) -> Dict[str, any]:
    """
    Generate detailed report about requirement classification for transparency.
    """

    classification = classification_result["classification"]
    importance_scores = classification_result["importance_scores"]
    market_signal = classification_result["market_signal"]

    report = {
        "summary": {
            "mandatory_count": len(classification["mandatory"]),
            "preferred_count": len(classification["preferred"]),
            "optional_count": len(classification["optional"]),
            "vacancies_analyzed": market_signal["total_vacancies_analyzed"]
        },
        "mandatory_skills": [
            {
                "skill": skill,
                "importance_score": importance_scores.get(skill, 0),
                "explanation": explain_classification(skill, classification_result)
            }
            for skill in classification["mandatory"]
        ],
        "preferred_skills": [
            {
                "skill": skill,
                "importance_score": importance_scores.get(skill, 0),
                "explanation": explain_classification(skill, classification_result)
            }
            for skill in classification["preferred"]
        ],
        "methodology": {
            "description": "Skills classified automatically based on market data analysis",
            "mandatory_threshold": f">{market_signal['threshold_mandatory']*100}% market frequency",
            "preferred_threshold": f"{market_signal['threshold_preferred']*100}-{market_signal['threshold_mandatory']*100}% market frequency",
            "factors": [
                "Frequency in job postings",
                "Mentions in job titles",
                "Co-occurrence with other skills",
                "Role context analysis"
            ]
        }
    }

    return report
