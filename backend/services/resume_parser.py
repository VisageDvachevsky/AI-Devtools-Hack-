import re
from typing import List, Set, Dict
from backend.services.normalization import normalize_skill, SKILL_TAXONOMY


def extract_skills_from_text(text: str, boost_skills: List[str] = None) -> List[Dict[str, any]]:
    if not text:
        return []

    text_lower = text.lower()
    found_skills: Dict[str, int] = {}

    # Check all known skills from taxonomy
    for canonical, synonyms in SKILL_TAXONOMY.items():
        for synonym in synonyms:
            pattern = r'\b' + re.escape(synonym) + r'\b'
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            if matches > 0:
                found_skills[canonical] = found_skills.get(canonical, 0) + matches

    # Boost specific skills if provided
    if boost_skills:
        for skill in boost_skills:
            norm_skill = normalize_skill(skill)
            if norm_skill in found_skills:
                found_skills[norm_skill] *= 2

    # Convert to scored list
    result = []
    max_count = max(found_skills.values()) if found_skills else 1
    for skill, count in found_skills.items():
        score = min(1.0, count / max_count)
        result.append({
            "skill": skill,
            "score": round(score, 2),
            "mentions": count
        })

    return sorted(result, key=lambda x: x["score"], reverse=True)


def extract_email_from_text(text: str) -> str:
    if not text:
        return ""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""


def extract_phone_from_text(text: str) -> str:
    if not text:
        return ""
    # Russian phone patterns
    phone_pattern = r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""


def extract_experience_years(text: str) -> int:
    if not text:
        return 0

    # Pattern: "N лет опыта", "N years experience", etc.
    patterns = [
        r'(\d+)\s*(лет|год|года)\s*(опыта|работы)',
        r'(\d+)\s*years?\s*(of)?\s*(experience|exp)',
        r'опыт\s*(\d+)\s*(лет|год|года)',
        r'experience:\s*(\d+)\s*years?'
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))

    return 0


def calculate_keyword_match_score(resume_text: str, required_skills: List[str]) -> Dict[str, any]:
    if not resume_text or not required_skills:
        return {
            "overall_score": 0.0,
            "matched_skills": [],
            "missing_skills": required_skills
        }

    extracted = extract_skills_from_text(resume_text, boost_skills=required_skills)
    extracted_map = {item["skill"]: item for item in extracted}

    matched = []
    missing = []

    for req_skill in required_skills:
        norm = normalize_skill(req_skill)
        if norm in extracted_map:
            matched.append({
                "skill": req_skill,
                "score": extracted_map[norm]["score"],
                "mentions": extracted_map[norm]["mentions"]
            })
        else:
            missing.append(req_skill)

    overall_score = len(matched) / len(required_skills) if required_skills else 0.0

    return {
        "overall_score": round(overall_score, 2),
        "matched_skills": matched,
        "missing_skills": missing,
        "all_detected_skills": [item["skill"] for item in extracted[:15]]
    }


def mock_linkedin_analysis(linkedin_url: str) -> Dict[str, any]:
    # Mock analysis since we don't have real LinkedIn integration
    if not linkedin_url or "linkedin.com" not in linkedin_url.lower():
        return {
            "valid": False,
            "profile_strength": 0,
            "connections": 0,
            "endorsements": []
        }

    # Extract username from URL
    username_match = re.search(r'linkedin\.com/in/([^/]+)', linkedin_url)
    username = username_match.group(1) if username_match else "unknown"

    # Generate mock data based on username hash
    profile_hash = hash(username) % 100

    return {
        "valid": True,
        "username": username,
        "profile_strength": min(100, 50 + profile_hash),
        "connections": 200 + (profile_hash * 10),
        "endorsements": ["python", "leadership", "teamwork"][:profile_hash % 4],
        "note": "Mock analysis - real integration not implemented"
    }
