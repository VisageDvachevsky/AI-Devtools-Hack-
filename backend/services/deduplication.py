from typing import List, Dict, Set
from difflib import SequenceMatcher
from backend.services.normalization import normalize_skill


def calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings using SequenceMatcher"""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between candidate names/usernames"""

    # Exact match
    if name1.lower() == name2.lower():
        return 1.0

    # Check if one contains the other
    if name1.lower() in name2.lower() or name2.lower() in name1.lower():
        return 0.8

    # Use sequence matcher
    return calculate_string_similarity(name1, name2)


def calculate_skill_overlap(skills1: List[str], skills2: List[str]) -> float:
    """Calculate skill overlap between two candidates"""

    if not skills1 or not skills2:
        return 0.0

    norm_skills1 = {normalize_skill(s) for s in skills1 if normalize_skill(s)}
    norm_skills2 = {normalize_skill(s) for s in skills2 if normalize_skill(s)}

    if not norm_skills1 or not norm_skills2:
        return 0.0

    intersection = len(norm_skills1 & norm_skills2)
    union = len(norm_skills1 | norm_skills2)

    return intersection / union if union > 0 else 0.0


def are_candidates_duplicates(
    cand1: Dict[str, any],
    cand2: Dict[str, any],
    name_threshold: float = 0.85,
    skill_threshold: float = 0.8
) -> bool:
    """Determine if two candidates are likely duplicates"""

    username1 = cand1.get("github_username", "")
    username2 = cand2.get("github_username", "")

    # Same username = definitely same person
    if username1 and username2 and username1.lower() == username2.lower():
        return True

    # Check name similarity
    name_sim = calculate_name_similarity(username1, username2)
    if name_sim >= name_threshold:
        return True

    # Check if skills are almost identical
    skills1 = cand1.get("top_languages", []) + cand1.get("matched_skills", [])
    skills2 = cand2.get("top_languages", []) + cand2.get("matched_skills", [])

    skill_overlap = calculate_skill_overlap(skills1, skills2)

    # High skill overlap + moderate name similarity = likely duplicate
    if skill_overlap >= skill_threshold and name_sim >= 0.5:
        return True

    return False


def deduplicate_candidates(
    candidates: List[Dict[str, any]],
    merge_strategy: str = "keep_best_score"
) -> List[Dict[str, any]]:
    """Remove duplicate candidates from list"""

    if not candidates:
        return []

    unique_candidates = []
    seen_indices = set()

    for i, cand1 in enumerate(candidates):
        if i in seen_indices:
            continue

        duplicates = [cand1]

        # Find all duplicates of this candidate
        for j, cand2 in enumerate(candidates[i+1:], start=i+1):
            if j in seen_indices:
                continue

            if are_candidates_duplicates(cand1, cand2):
                duplicates.append(cand2)
                seen_indices.add(j)

        # Merge duplicates according to strategy
        if merge_strategy == "keep_best_score":
            best = max(duplicates, key=lambda c: c.get("score", 0))
            unique_candidates.append(best)
        elif merge_strategy == "keep_first":
            unique_candidates.append(duplicates[0])
        elif merge_strategy == "merge":
            merged = merge_candidate_data(duplicates)
            unique_candidates.append(merged)
        else:
            unique_candidates.append(duplicates[0])

    return unique_candidates


def merge_candidate_data(candidates: List[Dict[str, any]]) -> Dict[str, any]:
    """Merge data from duplicate candidates"""

    if not candidates:
        return {}

    if len(candidates) == 1:
        return candidates[0]

    # Use first as base
    merged = candidates[0].copy()

    # Take best score
    best_score = max(c.get("score", 0) for c in candidates)
    merged["score"] = best_score

    # Merge skills (union)
    all_skills = set()
    for cand in candidates:
        all_skills.update(cand.get("top_languages", []))
        all_skills.update(cand.get("matched_skills", []))

    merged["all_detected_skills"] = list(all_skills)

    # Keep highest activity score
    best_activity = max(c.get("activity_score", 0) for c in candidates)
    merged["activity_score"] = best_activity

    # Combine risk flags (union)
    all_risks = set()
    for cand in candidates:
        all_risks.update(cand.get("risk_flags", []))
    merged["risk_flags"] = list(all_risks)

    # Mark as merged
    merged["merged_from"] = [c.get("github_username", "") for c in candidates]

    return merged


def clean_candidate_skills(candidate: Dict[str, any]) -> Dict[str, any]:
    """Clean and normalize candidate skills"""

    cleaned = candidate.copy()

    # Normalize top languages
    if "top_languages" in cleaned:
        cleaned["top_languages"] = [
            normalize_skill(lang)
            for lang in cleaned["top_languages"]
        ]
        cleaned["top_languages"] = [l for l in cleaned["top_languages"] if l]

    # Normalize matched skills
    if "matched_skills" in cleaned:
        cleaned["matched_skills"] = [
            normalize_skill(skill)
            for skill in cleaned["matched_skills"]
        ]
        cleaned["matched_skills"] = [s for s in cleaned["matched_skills"] if s]

    # Remove duplicates
    if "top_languages" in cleaned:
        cleaned["top_languages"] = list(set(cleaned["top_languages"]))
    if "matched_skills" in cleaned:
        cleaned["matched_skills"] = list(set(cleaned["matched_skills"]))

    return cleaned
