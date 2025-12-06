"""
Candidate Recommendation System
Find similar candidates using collaborative filtering and content-based filtering
NO ML APIs - pure similarity algorithms!
"""
import math
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class CandidateRecommendation(BaseModel):
    candidate_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    matching_skills: List[str]
    matching_reasons: List[str]
    profile_url: Optional[str] = None


class SimilarCandidatesResponse(BaseModel):
    query_candidate_id: str
    recommendations: List[CandidateRecommendation]
    algorithm_used: str
    total_candidates_analyzed: int


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same length")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def jaccard_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets"""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0


class CandidateRecommendationEngine:
    """
    Recommendation engine using collaborative and content-based filtering
    """

    def __init__(self):
        self.candidate_database: List[Dict] = []
        self.skill_index: Dict[str, List[str]] = defaultdict(list)  # skill -> candidate_ids

    def add_candidate(self, candidate_data: Dict):
        """Add candidate to database"""
        candidate_id = candidate_data.get("github_username") or candidate_data.get("candidate_id")
        if not candidate_id:
            return

        self.candidate_database.append(candidate_data)

        # Index skills
        skills = self._extract_skills(candidate_data)
        for skill in skills:
            if candidate_id not in self.skill_index[skill]:
                self.skill_index[skill].append(candidate_id)

    def bulk_add_candidates(self, candidates: List[Dict]):
        """Add multiple candidates at once"""
        for candidate in candidates:
            self.add_candidate(candidate)

    def find_similar_candidates(
        self,
        candidate_id: str,
        top_n: int = 10,
        algorithm: str = "hybrid"  # "content", "collaborative", "hybrid"
    ) -> SimilarCandidatesResponse:
        """
        Find similar candidates

        Args:
            candidate_id: Source candidate ID
            top_n: Number of recommendations to return
            algorithm: Similarity algorithm to use

        Returns:
            Recommended similar candidates
        """

        # Find source candidate
        source_candidate = None
        for candidate in self.candidate_database:
            cid = candidate.get("github_username") or candidate.get("candidate_id")
            if cid == candidate_id:
                source_candidate = candidate
                break

        if not source_candidate:
            return SimilarCandidatesResponse(
                query_candidate_id=candidate_id,
                recommendations=[],
                algorithm_used=algorithm,
                total_candidates_analyzed=0
            )

        # Calculate similarities
        similarities = []

        for candidate in self.candidate_database:
            cid = candidate.get("github_username") or candidate.get("candidate_id")
            if cid == candidate_id:
                continue  # Skip self

            if algorithm == "content":
                similarity = self._content_based_similarity(source_candidate, candidate)
            elif algorithm == "collaborative":
                similarity = self._collaborative_similarity(source_candidate, candidate)
            else:  # hybrid
                content_sim = self._content_based_similarity(source_candidate, candidate)
                collab_sim = self._collaborative_similarity(source_candidate, candidate)
                similarity = (content_sim * 0.7) + (collab_sim * 0.3)  # Weight content more

            if similarity > 0.1:  # Filter out very low similarities
                matching_skills = self._find_matching_skills(source_candidate, candidate)
                matching_reasons = self._explain_similarity(source_candidate, candidate, similarity)

                similarities.append((
                    cid,
                    similarity,
                    matching_skills,
                    matching_reasons,
                    candidate
                ))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Build recommendations
        recommendations = []
        for cid, sim_score, matching_skills, reasons, candidate in similarities[:top_n]:
            github_username = candidate.get("github_username")
            profile_url = f"https://github.com/{github_username}" if github_username else None

            recommendations.append(CandidateRecommendation(
                candidate_id=cid,
                similarity_score=round(sim_score, 3),
                matching_skills=matching_skills,
                matching_reasons=reasons,
                profile_url=profile_url
            ))

        return SimilarCandidatesResponse(
            query_candidate_id=candidate_id,
            recommendations=recommendations,
            algorithm_used=algorithm,
            total_candidates_analyzed=len(self.candidate_database)
        )

    def recommend_for_role(
        self,
        required_skills: List[str],
        nice_to_have_skills: List[str] = [],
        top_n: int = 10
    ) -> List[CandidateRecommendation]:
        """
        Recommend candidates for a specific role

        Args:
            required_skills: Must-have skills
            nice_to_have_skills: Optional skills
            top_n: Number of candidates to return

        Returns:
            Recommended candidates
        """

        candidate_scores = []

        for candidate in self.candidate_database:
            candidate_id = candidate.get("github_username") or candidate.get("candidate_id")
            candidate_skills = self._extract_skills(candidate)

            # Calculate match score
            required_matches = len(set(required_skills).intersection(set(candidate_skills)))
            nice_matches = len(set(nice_to_have_skills).intersection(set(candidate_skills)))

            # Score: required skills are mandatory
            required_coverage = required_matches / len(required_skills) if required_skills else 0.0
            nice_coverage = nice_matches / len(nice_to_have_skills) if nice_to_have_skills else 0.0

            # Weighted score
            score = (required_coverage * 0.8) + (nice_coverage * 0.2)

            # Minimum required coverage
            if required_coverage < 0.5:  # Must have at least 50% of required skills
                continue

            matching_skills = list(set(required_skills + nice_to_have_skills).intersection(set(candidate_skills)))
            reasons = [
                f"{int(required_coverage * 100)}% match on required skills",
                f"Has {len(matching_skills)} matching skills"
            ]

            candidate_scores.append((
                candidate_id,
                score,
                matching_skills,
                reasons,
                candidate
            ))

        # Sort by score
        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        # Build recommendations
        recommendations = []
        for cid, score, matching_skills, reasons, candidate in candidate_scores[:top_n]:
            github_username = candidate.get("github_username")
            profile_url = f"https://github.com/{github_username}" if github_username else None

            recommendations.append(CandidateRecommendation(
                candidate_id=cid,
                similarity_score=round(score, 3),
                matching_skills=matching_skills[:10],
                matching_reasons=reasons,
                profile_url=profile_url
            ))

        return recommendations

    def _extract_skills(self, candidate: Dict) -> List[str]:
        """Extract all skills from candidate data"""
        skills = set()

        # From skill scores
        skill_scores = candidate.get("skill_scores", [])
        for entry in skill_scores:
            skill = entry.get("skill")
            if skill:
                skills.add(skill.lower())

        # From top languages
        top_languages = candidate.get("top_languages", [])
        for lang in top_languages:
            skills.add(lang.lower())

        # From matched skills
        matched_skills = candidate.get("matched_skills", [])
        for skill in matched_skills:
            skills.add(skill.lower())

        # From technical skills
        technical_skills = candidate.get("technical_skills", [])
        for skill in technical_skills:
            skills.add(skill.lower())

        return list(skills)

    def _content_based_similarity(self, candidate1: Dict, candidate2: Dict) -> float:
        """Calculate similarity based on skills and profile content"""

        skills1 = set(self._extract_skills(candidate1))
        skills2 = set(self._extract_skills(candidate2))

        # Jaccard similarity on skills
        skill_similarity = jaccard_similarity(skills1, skills2)

        # Score similarity
        score1 = candidate1.get("score", 0)
        score2 = candidate2.get("score", 0)

        # Normalized score difference (0 = very different, 1 = identical)
        score_diff = abs(score1 - score2)
        score_similarity = 1.0 - min(score_diff / 100.0, 1.0)

        # Combined similarity (weighted)
        combined = (skill_similarity * 0.8) + (score_similarity * 0.2)

        return combined

    def _collaborative_similarity(self, candidate1: Dict, candidate2: Dict) -> float:
        """
        Calculate collaborative similarity
        Based on: candidates with similar skills often get hired for similar roles
        """

        # Get activity patterns
        activity1 = candidate1.get("activity_metrics", {})
        activity2 = candidate2.get("activity_metrics", {})

        # Compare activity levels
        stars1 = activity1.get("total_stars", 0)
        stars2 = activity2.get("total_stars", 0)

        # Normalize stars (log scale)
        norm_stars1 = math.log1p(stars1)
        norm_stars2 = math.log1p(stars2)

        stars_similarity = 1.0 - min(abs(norm_stars1 - norm_stars2) / 10.0, 1.0)

        # Compare repo counts
        repos1 = candidate1.get("repos_analyzed", 0)
        repos2 = candidate2.get("repos_analyzed", 0)

        repos_similarity = 1.0 - min(abs(repos1 - repos2) / 20.0, 1.0)

        # Combined
        combined = (stars_similarity * 0.6) + (repos_similarity * 0.4)

        return combined

    def _find_matching_skills(self, candidate1: Dict, candidate2: Dict) -> List[str]:
        """Find skills that both candidates have"""
        skills1 = set(self._extract_skills(candidate1))
        skills2 = set(self._extract_skills(candidate2))

        return list(skills1.intersection(skills2))[:10]  # Top 10

    def _explain_similarity(self, candidate1: Dict, candidate2: Dict, similarity: float) -> List[str]:
        """Generate human-readable reasons for similarity"""
        reasons = []

        matching_skills = self._find_matching_skills(candidate1, candidate2)
        if matching_skills:
            reasons.append(f"Shares {len(matching_skills)} skills: {', '.join(matching_skills[:3])}")

        score1 = candidate1.get("score", 0)
        score2 = candidate2.get("score", 0)
        if abs(score1 - score2) < 10:
            reasons.append(f"Similar overall scores ({score1} vs {score2})")

        activity1 = candidate1.get("activity_metrics", {})
        activity2 = candidate2.get("activity_metrics", {})

        stars1 = activity1.get("total_stars", 0)
        stars2 = activity2.get("total_stars", 0)

        if stars1 > 50 and stars2 > 50:
            reasons.append("Both have popular repositories")

        if similarity > 0.8:
            reasons.append("Highly similar profiles")
        elif similarity > 0.6:
            reasons.append("Good profile match")

        return reasons[:5]


# Global recommendation engine
recommendation_engine = CandidateRecommendationEngine()


def find_similar_candidates(
    candidate_id: str,
    candidates_pool: List[Dict],
    top_n: int = 10
) -> List[Dict]:
    """
    Convenience function to find similar candidates

    Args:
        candidate_id: Source candidate ID
        candidates_pool: Pool of candidates to search
        top_n: Number of recommendations

    Returns:
        List of similar candidates
    """

    engine = CandidateRecommendationEngine()
    engine.bulk_add_candidates(candidates_pool)

    result = engine.find_similar_candidates(candidate_id, top_n=top_n)
    return [r.model_dump() for r in result.recommendations]


def recommend_candidates_for_role(
    required_skills: List[str],
    candidates_pool: List[Dict],
    nice_to_have_skills: List[str] = [],
    top_n: int = 10
) -> List[Dict]:
    """
    Recommend candidates for a role

    Args:
        required_skills: Required skills
        candidates_pool: Pool of candidates
        nice_to_have_skills: Optional skills
        top_n: Number of recommendations

    Returns:
        Recommended candidates
    """

    engine = CandidateRecommendationEngine()
    engine.bulk_add_candidates(candidates_pool)

    recommendations = engine.recommend_for_role(
        required_skills=required_skills,
        nice_to_have_skills=nice_to_have_skills,
        top_n=top_n
    )

    return [r.model_dump() for r in recommendations]
