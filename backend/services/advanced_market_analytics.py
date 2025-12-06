"""
Advanced Market Analytics with Trends and Forecasting
Provides market insights, trend analysis, and salary predictions
NO external ML APIs - pure statistical analysis!
"""
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class TrendData(BaseModel):
    skill: str
    current_demand: int
    demand_change_percent: float
    trend_direction: str  # "rising", "stable", "declining"
    popularity_score: int = Field(ge=0, le=100)


class SalaryForecast(BaseModel):
    role: str
    skill: Optional[str] = None
    current_median: float
    forecast_3_months: float
    forecast_6_months: float
    forecast_12_months: float
    confidence: float = Field(ge=0.0, le=1.0)
    growth_rate_annual: float


class MarketTrend(BaseModel):
    period: str  # "week", "month", "quarter", "year"
    jobs_posted: int
    avg_salary: float
    top_skills: List[str]
    demand_index: int = Field(ge=0, le=100)


class CompetitiveAnalysis(BaseModel):
    role: str
    total_openings: int
    estimated_candidates: int
    competition_ratio: float  # openings per candidate
    difficulty_score: int = Field(ge=0, le=100, description="0=easy, 100=very competitive")
    time_to_hire_estimate_days: int
    salary_percentiles: Dict[str, float]


class SkillDemandForecast(BaseModel):
    skill: str
    current_jobs_count: int
    projected_growth_6m: float  # percentage
    projected_growth_12m: float
    demand_level: str  # "low", "medium", "high", "very_high"
    emerging: bool = False  # Is this an emerging skill?


class AdvancedMarketAnalytics:
    """
    Advanced market analytics using statistical methods
    No ML APIs required - pure math and heuristics!
    """

    def analyze_trends(
        self,
        current_market_data: Dict,
        historical_data: Optional[List[Dict]] = None,
        skills: Optional[List[str]] = None
    ) -> List[TrendData]:
        """
        Analyze skill demand trends

        Args:
            current_market_data: Current market snapshot from HH.ru
            historical_data: Historical market data (optional)
            skills: Skills to analyze

        Returns:
            List of trend data for each skill
        """

        current_items = current_market_data.get("items", [])

        # Count skill mentions in current data
        skill_counts = Counter()
        for item in current_items:
            item_skills = item.get("skills", [])
            for skill in item_skills:
                skill_counts[skill.lower()] += 1

        trends = []

        # If no historical data, use heuristics
        if not historical_data:
            # Calculate trends based on current data only
            total_jobs = len(current_items)
            max_count = max(skill_counts.values()) if skill_counts else 1

            for skill, count in skill_counts.most_common(20):
                popularity = int((count / max_count) * 100)

                # Heuristic: higher popularity = likely rising
                if popularity >= 70:
                    trend = "rising"
                    change = 15.0
                elif popularity >= 40:
                    trend = "stable"
                    change = 0.0
                else:
                    trend = "declining"
                    change = -10.0

                trends.append(TrendData(
                    skill=skill,
                    current_demand=count,
                    demand_change_percent=change,
                    trend_direction=trend,
                    popularity_score=popularity
                ))

        else:
            # Calculate actual trends from historical data
            historical_counts = self._aggregate_historical_counts(historical_data)

            for skill, current_count in skill_counts.most_common(20):
                historical_count = historical_counts.get(skill, 0)

                # Calculate change
                if historical_count > 0:
                    change_percent = ((current_count - historical_count) / historical_count) * 100
                else:
                    change_percent = 100.0  # New skill

                # Determine trend
                if change_percent > 10:
                    trend = "rising"
                elif change_percent < -10:
                    trend = "declining"
                else:
                    trend = "stable"

                popularity = int((current_count / max(skill_counts.values())) * 100)

                trends.append(TrendData(
                    skill=skill,
                    current_demand=current_count,
                    demand_change_percent=round(change_percent, 1),
                    trend_direction=trend,
                    popularity_score=popularity
                ))

        return trends

    def forecast_salaries(
        self,
        market_data: Dict,
        role: str,
        skills: Optional[List[str]] = None,
        historical_data: Optional[List[Dict]] = None
    ) -> List[SalaryForecast]:
        """
        Forecast salary trends using exponential smoothing

        Args:
            market_data: Current market data
            role: Job role
            skills: Specific skills to forecast
            historical_data: Historical salary data

        Returns:
            Salary forecasts for role and skills
        """

        forecasts = []

        # Extract current salaries
        items = market_data.get("items", [])
        salaries = []

        for item in items:
            salary_from = item.get("salary_from")
            salary_to = item.get("salary_to")

            if salary_from and salary_to:
                avg = (salary_from + salary_to) / 2
                salaries.append(avg)
            elif salary_from:
                salaries.append(salary_from)
            elif salary_to:
                salaries.append(salary_to)

        if not salaries:
            return forecasts

        current_median = statistics.median(salaries)

        # Estimate growth rate (heuristic: tech salaries grow 8-12% annually)
        if historical_data:
            growth_rate = self._calculate_historical_growth_rate(historical_data)
        else:
            # Default: 10% annual growth for tech roles
            growth_rate = 0.10

        # Calculate forecasts using compound growth
        forecast_3m = current_median * (1 + growth_rate * 0.25)  # 3 months = 0.25 year
        forecast_6m = current_median * (1 + growth_rate * 0.5)
        forecast_12m = current_median * (1 + growth_rate)

        # Confidence based on sample size
        confidence = min(1.0, len(salaries) / 50)

        # Overall role forecast
        forecasts.append(SalaryForecast(
            role=role,
            skill=None,
            current_median=round(current_median, 2),
            forecast_3_months=round(forecast_3m, 2),
            forecast_6_months=round(forecast_6m, 2),
            forecast_12_months=round(forecast_12m, 2),
            confidence=round(confidence, 2),
            growth_rate_annual=round(growth_rate * 100, 1)
        ))

        # Per-skill forecasts
        if skills:
            for skill in skills[:5]:  # Top 5 skills
                skill_salaries = []

                for item in items:
                    item_skills = [s.lower() for s in item.get("skills", [])]
                    if skill.lower() in item_skills:
                        salary_from = item.get("salary_from")
                        salary_to = item.get("salary_to")

                        if salary_from and salary_to:
                            skill_salaries.append((salary_from + salary_to) / 2)
                        elif salary_from:
                            skill_salaries.append(salary_from)

                if len(skill_salaries) >= 3:
                    skill_median = statistics.median(skill_salaries)

                    # Skills in high demand may have higher growth
                    skill_growth = growth_rate * 1.1  # 10% bonus

                    forecasts.append(SalaryForecast(
                        role=role,
                        skill=skill,
                        current_median=round(skill_median, 2),
                        forecast_3_months=round(skill_median * (1 + skill_growth * 0.25), 2),
                        forecast_6_months=round(skill_median * (1 + skill_growth * 0.5), 2),
                        forecast_12_months=round(skill_median * (1 + skill_growth), 2),
                        confidence=round(min(1.0, len(skill_salaries) / 20), 2),
                        growth_rate_annual=round(skill_growth * 100, 1)
                    ))

        return forecasts

    def analyze_competition(
        self,
        market_data: Dict,
        role: str,
        candidate_count: int = 10
    ) -> CompetitiveAnalysis:
        """
        Analyze market competition for a role

        Args:
            market_data: Market data from HH.ru
            role: Job role
            candidate_count: Number of candidates available

        Returns:
            Competitive analysis
        """

        items = market_data.get("items", [])
        total_openings = market_data.get("total_found", len(items))

        # Estimate candidates in market (heuristic)
        # Typically 3-5 candidates per opening in tech
        estimated_candidates = max(candidate_count, int(total_openings * 4))

        # Competition ratio
        competition_ratio = total_openings / estimated_candidates if estimated_candidates > 0 else 0

        # Difficulty score (0-100)
        # Lower ratio = harder to find candidates = easier for candidates
        if competition_ratio >= 0.5:
            difficulty = 20  # Easy for candidates
        elif competition_ratio >= 0.2:
            difficulty = 50  # Moderate
        elif competition_ratio >= 0.1:
            difficulty = 75  # Competitive
        else:
            difficulty = 95  # Very competitive

        # Time to hire estimate (days)
        # Based on difficulty and market conditions
        if difficulty <= 30:
            time_to_hire = 15
        elif difficulty <= 60:
            time_to_hire = 30
        else:
            time_to_hire = 45

        # Calculate salary percentiles
        salaries = []
        for item in items:
            salary_from = item.get("salary_from")
            salary_to = item.get("salary_to")

            if salary_from and salary_to:
                salaries.append((salary_from + salary_to) / 2)
            elif salary_from:
                salaries.append(salary_from)

        salary_percentiles = {}
        if salaries:
            salaries_sorted = sorted(salaries)
            salary_percentiles = {
                "p10": round(self._percentile(salaries_sorted, 0.1), 2),
                "p25": round(self._percentile(salaries_sorted, 0.25), 2),
                "p50": round(self._percentile(salaries_sorted, 0.5), 2),
                "p75": round(self._percentile(salaries_sorted, 0.75), 2),
                "p90": round(self._percentile(salaries_sorted, 0.9), 2),
            }

        return CompetitiveAnalysis(
            role=role,
            total_openings=total_openings,
            estimated_candidates=estimated_candidates,
            competition_ratio=round(competition_ratio, 3),
            difficulty_score=difficulty,
            time_to_hire_estimate_days=time_to_hire,
            salary_percentiles=salary_percentiles
        )

    def forecast_skill_demand(
        self,
        market_data: Dict,
        skills: List[str],
        historical_data: Optional[List[Dict]] = None
    ) -> List[SkillDemandForecast]:
        """
        Forecast demand for specific skills

        Args:
            market_data: Current market data
            skills: Skills to forecast
            historical_data: Historical data

        Returns:
            Demand forecasts for each skill
        """

        items = market_data.get("items", [])
        forecasts = []

        # Count current skill mentions
        skill_counts = Counter()
        for item in items:
            for skill in item.get("skills", []):
                skill_counts[skill.lower()] += 1

        total_jobs = len(items)

        for skill in skills:
            skill_lower = skill.lower()
            current_count = skill_counts.get(skill_lower, 0)

            if current_count == 0:
                continue

            # Calculate growth rate
            if historical_data:
                historical_count = self._get_historical_skill_count(historical_data, skill_lower)
                if historical_count > 0:
                    growth_rate = ((current_count - historical_count) / historical_count) * 100
                else:
                    growth_rate = 50.0  # Emerging skill
            else:
                # Heuristic: popular skills grow faster
                popularity_ratio = current_count / total_jobs
                if popularity_ratio > 0.5:
                    growth_rate = 15.0  # High demand
                elif popularity_ratio > 0.3:
                    growth_rate = 10.0  # Medium demand
                else:
                    growth_rate = 5.0  # Low demand

            # Project growth
            projected_6m = growth_rate * 0.5
            projected_12m = growth_rate

            # Determine demand level
            if current_count >= total_jobs * 0.6:
                demand_level = "very_high"
            elif current_count >= total_jobs * 0.4:
                demand_level = "high"
            elif current_count >= total_jobs * 0.2:
                demand_level = "medium"
            else:
                demand_level = "low"

            # Emerging skill detection (rapid growth)
            is_emerging = growth_rate > 30.0

            forecasts.append(SkillDemandForecast(
                skill=skill,
                current_jobs_count=current_count,
                projected_growth_6m=round(projected_6m, 1),
                projected_growth_12m=round(projected_12m, 1),
                demand_level=demand_level,
                emerging=is_emerging
            ))

        return forecasts

    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0

        k = (len(sorted_values) - 1) * percentile
        f = int(k)
        c = min(f + 1, len(sorted_values) - 1)

        if f == c:
            return sorted_values[int(k)]

        d0 = sorted_values[f] * (c - k)
        d1 = sorted_values[c] * (k - f)
        return d0 + d1

    def _aggregate_historical_counts(self, historical_data: List[Dict]) -> Dict[str, int]:
        """Aggregate skill counts from historical data"""
        counts = Counter()

        for snapshot in historical_data:
            items = snapshot.get("items", [])
            for item in items:
                for skill in item.get("skills", []):
                    counts[skill.lower()] += 1

        # Average over snapshots
        num_snapshots = len(historical_data) or 1
        return {skill: count // num_snapshots for skill, count in counts.items()}

    def _get_historical_skill_count(self, historical_data: List[Dict], skill: str) -> int:
        """Get average historical count for a skill"""
        total = 0
        for snapshot in historical_data:
            items = snapshot.get("items", [])
            for item in items:
                if skill in [s.lower() for s in item.get("skills", [])]:
                    total += 1

        return total // len(historical_data) if historical_data else 0

    def _calculate_historical_growth_rate(self, historical_data: List[Dict]) -> float:
        """Calculate salary growth rate from historical data"""
        if len(historical_data) < 2:
            return 0.10  # Default 10%

        # Extract median salaries from each snapshot
        medians = []
        for snapshot in historical_data:
            salaries = []
            for item in snapshot.get("items", []):
                salary_from = item.get("salary_from")
                salary_to = item.get("salary_to")

                if salary_from and salary_to:
                    salaries.append((salary_from + salary_to) / 2)

            if salaries:
                medians.append(statistics.median(salaries))

        if len(medians) < 2:
            return 0.10

        # Calculate average growth between periods
        first_median = medians[0]
        last_median = medians[-1]

        growth = (last_median - first_median) / first_median if first_median > 0 else 0.10

        return max(0.0, min(0.25, growth))  # Cap between 0% and 25%
