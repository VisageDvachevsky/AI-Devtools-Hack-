"""
Predictive Analytics System
Predicts hiring outcomes using statistical models (no ML APIs!)
"""
import hashlib
import math
import statistics
from collections import defaultdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class HiringOutcome(str, Enum):
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    CANDIDATE_WITHDREW = "candidate_withdrew"
    NOT_SELECTED = "not_selected"


class OfferAcceptancePrediction(BaseModel):
    candidate_id: str
    probability_accept: float = Field(ge=0.0, le=1.0)
    probability_reject: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    key_factors: List[str] = Field(default_factory=list)
    recommendation: str
    risk_level: str  # "low", "medium", "high"


class TimeToHirePrediction(BaseModel):
    role: str
    estimated_days: int
    confidence_interval: Tuple[int, int]  # (min_days, max_days)
    factors_affecting: List[str]
    similar_roles_avg: Optional[int] = None


class CandidateAttritionRiskPrediction(BaseModel):
    candidate_id: str
    attrition_risk_score: float = Field(ge=0.0, le=1.0, description="0=low risk, 1=high risk")
    risk_level: str  # "low", "medium", "high"
    risk_factors: List[str]
    retention_recommendations: List[str]


class SalaryNegotiationPrediction(BaseModel):
    candidate_id: str
    likely_counter_offer: Optional[int] = None
    negotiation_probability: float = Field(ge=0.0, le=1.0)
    acceptable_range: Tuple[int, int]
    market_position: str  # "below_market", "at_market", "above_market"
    negotiation_strategy: str


class PredictiveAnalytics:
    """
    Predictive analytics using statistical models and heuristics
    No ML APIs required - pure math!
    """

    def __init__(self):
        # Historical data cache (in production, load from database)
        self.historical_outcomes: List[Dict] = []

    def predict_offer_acceptance(
        self,
        candidate_id: str,
        candidate_score: int,
        salary_offered: int,
        market_median_salary: int,
        candidate_experience_years: float,
        has_competing_offers: bool = False,
        interview_feedback_score: Optional[float] = None,
        days_in_process: int = 0,
        historical_data: Optional[List[Dict]] = None
    ) -> OfferAcceptancePrediction:
        """
        Predict probability of candidate accepting offer

        Factors considered:
        - Salary competitiveness
        - Candidate engagement
        - Market conditions
        - Process duration
        """

        # Base probability: 60%
        prob_accept = 0.60

        key_factors = []

        # Factor 1: Salary competitiveness (weight: 0.3)
        if market_median_salary > 0:
            salary_ratio = salary_offered / market_median_salary

            if salary_ratio >= 1.15:
                salary_factor = 0.25
                key_factors.append("Salary 15%+ above market (+25%)")
            elif salary_ratio >= 1.05:
                salary_factor = 0.15
                key_factors.append("Salary 5-15% above market (+15%)")
            elif salary_ratio >= 0.95:
                salary_factor = 0.0
                key_factors.append("Salary at market rate (0%)")
            elif salary_ratio >= 0.85:
                salary_factor = -0.15
                key_factors.append("Salary 5-15% below market (-15%)")
            else:
                salary_factor = -0.30
                key_factors.append("Salary 15%+ below market (-30%)")

            prob_accept += salary_factor

        # Factor 2: Candidate quality and engagement (weight: 0.2)
        if candidate_score >= 85:
            engagement_factor = 0.10
            key_factors.append("Top candidate (score 85+) (+10%)")
        elif candidate_score >= 70:
            engagement_factor = 0.05
        elif candidate_score < 50:
            engagement_factor = -0.10
            key_factors.append("Lower engagement (score <50) (-10%)")
        else:
            engagement_factor = 0.0

        prob_accept += engagement_factor

        # Factor 3: Interview feedback (weight: 0.15)
        if interview_feedback_score:
            if interview_feedback_score >= 4.5:
                feedback_factor = 0.15
                key_factors.append("Excellent interview performance (+15%)")
            elif interview_feedback_score >= 3.5:
                feedback_factor = 0.05
            else:
                feedback_factor = -0.10
                key_factors.append("Mixed interview feedback (-10%)")

            prob_accept += feedback_factor

        # Factor 4: Competing offers (weight: 0.2)
        if has_competing_offers:
            competing_factor = -0.20
            key_factors.append("Has competing offers (-20%)")
            prob_accept += competing_factor

        # Factor 5: Process duration (weight: 0.1)
        if days_in_process > 45:
            duration_factor = -0.15
            key_factors.append(f"Long process ({days_in_process} days) (-15%)")
            prob_accept += duration_factor
        elif days_in_process > 30:
            duration_factor = -0.05
            prob_accept += duration_factor

        # Cap probability between 0 and 1
        prob_accept = max(0.0, min(1.0, prob_accept))
        prob_reject = 1.0 - prob_accept

        # Calculate confidence based on number of factors
        confidence = min(1.0, 0.5 + (len(key_factors) * 0.1))

        # Determine risk level
        if prob_accept >= 0.75:
            risk_level = "low"
            recommendation = "Strong probability of acceptance. Proceed with standard offer."
        elif prob_accept >= 0.50:
            risk_level = "medium"
            recommendation = "Moderate acceptance probability. Consider sweetening the offer or highlighting unique benefits."
        else:
            risk_level = "high"
            recommendation = "Low acceptance probability. Improve compensation or address candidate concerns before extending offer."

        return OfferAcceptancePrediction(
            candidate_id=candidate_id,
            probability_accept=round(prob_accept, 2),
            probability_reject=round(prob_reject, 2),
            confidence=round(confidence, 2),
            key_factors=key_factors,
            recommendation=recommendation,
            risk_level=risk_level
        )

    def predict_time_to_hire(
        self,
        role: str,
        required_skills: List[str],
        market_competition_level: str = "medium",
        historical_data: Optional[List[Dict]] = None
    ) -> TimeToHirePrediction:
        """
        Predict time to hire for a role

        Factors:
        - Role seniority
        - Skill rarity
        - Market competition
        - Historical data
        """

        # Base time: 30 days
        base_days = 30

        factors_affecting = []

        # Factor 1: Role seniority
        role_lower = role.lower()
        if "senior" in role_lower or "lead" in role_lower or "principal" in role_lower:
            base_days += 15
            factors_affecting.append("Senior role requires extended search (+15 days)")
        elif "junior" in role_lower:
            base_days -= 5
            factors_affecting.append("Junior role faster to fill (-5 days)")

        # Factor 2: Skill rarity
        rare_skills = ["rust", "haskell", "scala", "kubernetes", "blockchain", "ml", "ai"]
        has_rare_skills = any(skill.lower() in rare_skills for skill in required_skills)

        if has_rare_skills:
            base_days += 10
            factors_affecting.append("Rare skills increase search time (+10 days)")

        # Factor 3: Market competition
        if market_competition_level == "high":
            base_days += 12
            factors_affecting.append("High market competition (+12 days)")
        elif market_competition_level == "low":
            base_days -= 7
            factors_affecting.append("Low market competition (-7 days)")

        # Calculate confidence interval (±20%)
        margin = int(base_days * 0.2)
        confidence_interval = (base_days - margin, base_days + margin)

        # Get average from historical data if available
        similar_roles_avg = None
        if historical_data:
            similar_times = [
                h.get("time_to_hire", 0)
                for h in historical_data
                if h.get("role", "").lower() in role_lower
            ]
            if similar_times:
                similar_roles_avg = int(statistics.mean(similar_times))

        return TimeToHirePrediction(
            role=role,
            estimated_days=base_days,
            confidence_interval=confidence_interval,
            factors_affecting=factors_affecting,
            similar_roles_avg=similar_roles_avg
        )

    def predict_attrition_risk(
        self,
        candidate_id: str,
        tenure_at_previous_company_months: List[int],
        total_jobs_count: int,
        current_job_satisfaction_score: Optional[float] = None,
        salary_vs_market: float = 1.0  # 1.0 = at market, 0.9 = 10% below
    ) -> CandidateAttritionRiskPrediction:
        """
        Predict risk of candidate leaving within first year
        """

        risk_score = 0.0
        risk_factors = []

        # Factor 1: Job hopping pattern
        if total_jobs_count >= 5 and len(tenure_at_previous_company_months) >= 2:
            avg_tenure = statistics.mean(tenure_at_previous_company_months)

            if avg_tenure < 12:
                risk_score += 0.35
                risk_factors.append("Very short average tenure (<1 year)")
            elif avg_tenure < 24:
                risk_score += 0.20
                risk_factors.append("Short average tenure (<2 years)")
            elif avg_tenure > 48:
                risk_score -= 0.10  # Loyalty bonus
                risk_factors.append("Stable employment history (4+ years average)")

        # Factor 2: Frequency of job changes
        if total_jobs_count > 6:
            risk_score += 0.15
            risk_factors.append("Frequent job changes (6+ jobs)")

        # Factor 3: Salary competitiveness
        if salary_vs_market < 0.90:
            risk_score += 0.25
            risk_factors.append("Below-market salary increases flight risk")
        elif salary_vs_market > 1.10:
            risk_score -= 0.10
            risk_factors.append("Above-market salary improves retention")

        # Factor 4: Current satisfaction (if available)
        if current_job_satisfaction_score:
            if current_job_satisfaction_score < 3.0:
                risk_score += 0.20
                risk_factors.append("Low reported job satisfaction")
            elif current_job_satisfaction_score > 4.0:
                risk_score -= 0.15

        # Cap risk score
        risk_score = max(0.0, min(1.0, risk_score))

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Recommendations
        recommendations = []
        if risk_score > 0.5:
            recommendations.extend([
                "Consider offering equity vesting schedule",
                "Implement strong onboarding and mentorship program",
                "Schedule regular check-ins during first 6 months",
                "Ensure competitive compensation package"
            ])
        else:
            recommendations.append("Standard retention practices should suffice")

        return CandidateAttritionRiskPrediction(
            candidate_id=candidate_id,
            attrition_risk_score=round(risk_score, 2),
            risk_level=risk_level,
            risk_factors=risk_factors,
            retention_recommendations=recommendations
        )

    def predict_salary_negotiation(
        self,
        candidate_id: str,
        initial_offer: int,
        market_median: int,
        candidate_current_salary: Optional[int] = None,
        candidate_experience_years: float = 3.0
    ) -> SalaryNegotiationPrediction:
        """
        Predict salary negotiation behavior
        """

        negotiation_probability = 0.5  # Base: 50% negotiate

        # Factor 1: Offer vs market
        offer_vs_market = initial_offer / market_median if market_median > 0 else 1.0

        if offer_vs_market < 0.90:
            negotiation_probability = 0.85
            market_position = "below_market"
        elif offer_vs_market < 1.0:
            negotiation_probability = 0.65
            market_position = "slightly_below_market"
        elif offer_vs_market >= 1.10:
            negotiation_probability = 0.20
            market_position = "above_market"
        else:
            market_position = "at_market"

        # Factor 2: Experience level (seniors negotiate more)
        if candidate_experience_years >= 7:
            negotiation_probability = min(1.0, negotiation_probability + 0.15)
        elif candidate_experience_years < 2:
            negotiation_probability = max(0.0, negotiation_probability - 0.10)

        # Predict likely counter offer
        likely_counter = None
        if negotiation_probability > 0.5:
            # Typically ask for 10-20% more
            increase_pct = 0.15  # 15% average
            likely_counter = int(initial_offer * (1 + increase_pct))

        # Acceptable range (what company should be willing to go to)
        acceptable_min = initial_offer
        acceptable_max = int(market_median * 1.10)  # Up to 10% above market

        # Strategy
        if market_position == "below_market":
            strategy = "Expect negotiation. Be prepared to increase offer to market rate or highlight non-monetary benefits."
        elif market_position == "above_market":
            strategy = "Offer is strong. Minimal negotiation expected. Stand firm on compensation."
        else:
            strategy = "Moderate negotiation likely. Have 5-10% buffer ready or emphasize total compensation package."

        return SalaryNegotiationPrediction(
            candidate_id=candidate_id,
            likely_counter_offer=likely_counter,
            negotiation_probability=round(negotiation_probability, 2),
            acceptable_range=(acceptable_min, acceptable_max),
            market_position=market_position,
            negotiation_strategy=strategy
        )


def predict_hiring_outcomes(
    candidate_id: str,
    candidate_data: Dict,
    market_data: Dict,
    offer_details: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to run all predictions

    Args:
        candidate_id: Candidate identifier
        candidate_data: Candidate information
        market_data: Market insights
        offer_details: Offer details if available

    Returns:
        All predictions as dict
    """

    analytics = PredictiveAnalytics()

    predictions = {}

    # Offer acceptance prediction
    if offer_details:
        predictions["offer_acceptance"] = analytics.predict_offer_acceptance(
            candidate_id=candidate_id,
            candidate_score=candidate_data.get("score", 70),
            salary_offered=offer_details.get("salary", 0),
            market_median_salary=market_data.get("median_salary", 0),
            candidate_experience_years=candidate_data.get("experience_years", 3.0),
            has_competing_offers=candidate_data.get("has_competing_offers", False),
            interview_feedback_score=candidate_data.get("interview_score"),
            days_in_process=candidate_data.get("days_in_process", 20)
        ).model_dump()

        # Salary negotiation prediction
        predictions["salary_negotiation"] = analytics.predict_salary_negotiation(
            candidate_id=candidate_id,
            initial_offer=offer_details.get("salary", 0),
            market_median=market_data.get("median_salary", 0),
            candidate_current_salary=candidate_data.get("current_salary"),
            candidate_experience_years=candidate_data.get("experience_years", 3.0)
        ).model_dump()

    # Time to hire prediction
    predictions["time_to_hire"] = analytics.predict_time_to_hire(
        role=market_data.get("role", "Software Engineer"),
        required_skills=market_data.get("required_skills", []),
        market_competition_level=market_data.get("competition_level", "medium")
    ).model_dump()

    # Attrition risk
    if candidate_data.get("previous_tenures"):
        predictions["attrition_risk"] = analytics.predict_attrition_risk(
            candidate_id=candidate_id,
            tenure_at_previous_company_months=candidate_data.get("previous_tenures", []),
            total_jobs_count=candidate_data.get("total_jobs", 3),
            salary_vs_market=candidate_data.get("salary_vs_market", 1.0)
        ).model_dump()

    return predictions
