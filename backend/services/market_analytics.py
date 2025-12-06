from typing import Dict, List, Optional
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from backend.services.normalization import normalize_skill, convert_salary_to_rub


def analyze_market_trends(
    market_data_list: List[Dict[str, any]],
    timeframe_days: int = 30
) -> Dict[str, any]:
    """Analyze market trends across multiple data snapshots"""

    if not market_data_list:
        return {
            "trend": "no_data",
            "demand_change": 0,
            "salary_change": 0
        }

    total_vacancies = sum(data.get("total_found", 0) for data in market_data_list)
    avg_vacancies = total_vacancies / len(market_data_list) if market_data_list else 0

    # Simple trend detection
    if len(market_data_list) >= 2:
        recent = market_data_list[-1].get("total_found", 0)
        older = market_data_list[0].get("total_found", 0)
        demand_change = ((recent - older) / older * 100) if older > 0 else 0
    else:
        demand_change = 0

    trend = "growing" if demand_change > 10 else "declining" if demand_change < -10 else "stable"

    return {
        "trend": trend,
        "demand_change_percent": round(demand_change, 1),
        "avg_vacancies": int(avg_vacancies),
        "total_snapshots": len(market_data_list),
        "timeframe_days": timeframe_days
    }


def extract_top_companies(market_data: Dict[str, any], top_n: int = 10) -> List[Dict[str, any]]:
    """Extract top companies by vacancy count"""

    items = market_data.get("items", [])
    company_counter = Counter()

    for item in items:
        company = item.get("company")
        if company:
            company_counter[company] += 1

    top_companies = []
    for company, count in company_counter.most_common(top_n):
        top_companies.append({
            "company": company,
            "vacancy_count": count
        })

    return top_companies


def extract_top_locations(market_data: Dict[str, any], top_n: int = 10) -> List[Dict[str, any]]:
    """Extract top locations by vacancy count"""

    items = market_data.get("items", [])
    location_counter = Counter()

    for item in items:
        location = item.get("location")
        if location:
            location_counter[location] += 1

    top_locations = []
    for location, count in location_counter.most_common(top_n):
        top_locations.append({
            "location": location,
            "vacancy_count": count
        })

    return top_locations


def calculate_salary_ranges_by_skill(
    market_data: Dict[str, any],
    min_samples: int = 3
) -> Dict[str, Dict[str, float]]:
    """Calculate salary ranges grouped by skills"""

    items = market_data.get("items", [])
    skill_salaries = defaultdict(list)

    for item in items:
        salary_from = item.get("salary_from")
        salary_to = item.get("salary_to")
        currency = item.get("currency", "RUB")
        skills = item.get("skills", [])

        if not skills:
            continue

        # Calculate median salary for this vacancy
        salary = None
        if salary_from and salary_to:
            salary = (salary_from + salary_to) / 2
        elif salary_from:
            salary = salary_from
        elif salary_to:
            salary = salary_to

        if salary:
            # Convert to RUB
            salary_rub = convert_salary_to_rub(salary, currency)

            for skill in skills:
                norm_skill = normalize_skill(skill)
                if norm_skill:
                    skill_salaries[norm_skill].append(salary_rub)

    # Calculate ranges for skills with enough samples
    ranges = {}
    for skill, salaries in skill_salaries.items():
        if len(salaries) >= min_samples:
            salaries_sorted = sorted(salaries)
            ranges[skill] = {
                "min": round(min(salaries), 0),
                "max": round(max(salaries), 0),
                "median": round(salaries_sorted[len(salaries_sorted) // 2], 0),
                "samples": len(salaries)
            }

    return ranges


def calculate_supply_demand_ratio(
    vacancy_count: int,
    candidate_count: int
) -> Dict[str, any]:
    """Calculate supply/demand ratio"""

    if candidate_count == 0:
        ratio = float('inf')
        interpretation = "very_high_demand"
    elif vacancy_count == 0:
        ratio = 0.0
        interpretation = "no_demand"
    else:
        ratio = vacancy_count / candidate_count
        if ratio > 2:
            interpretation = "high_demand"
        elif ratio > 1:
            interpretation = "moderate_demand"
        elif ratio > 0.5:
            interpretation = "balanced"
        else:
            interpretation = "low_demand"

    return {
        "ratio": round(ratio, 2) if ratio != float('inf') else None,
        "interpretation": interpretation,
        "vacancies": vacancy_count,
        "candidates": candidate_count
    }


def generate_market_insights(
    market_data: Dict[str, any],
    required_skills: List[str],
    candidate_count: int = 0
) -> Dict[str, any]:
    """Generate comprehensive market insights"""

    total_found = market_data.get("total_found", 0)

    top_companies = extract_top_companies(market_data, top_n=5)
    top_locations = extract_top_locations(market_data, top_n=5)
    salary_ranges = calculate_salary_ranges_by_skill(market_data)

    supply_demand = calculate_supply_demand_ratio(total_found, candidate_count)

    # Find salary ranges for required skills
    relevant_salary_ranges = {}
    for skill in required_skills:
        norm = normalize_skill(skill)
        if norm in salary_ranges:
            relevant_salary_ranges[skill] = salary_ranges[norm]

    # Calculate competitive offer estimate
    if relevant_salary_ranges:
        all_medians = [r["median"] for r in relevant_salary_ranges.values()]
        competitive_offer = {
            "min": round(min(all_medians) * 0.9, 0),
            "median": round(sum(all_medians) / len(all_medians), 0),
            "max": round(max(all_medians) * 1.1, 0),
            "currency": "RUB"
        }
    else:
        competitive_offer = None

    return {
        "total_vacancies": total_found,
        "top_companies": top_companies,
        "top_locations": top_locations,
        "supply_demand": supply_demand,
        "salary_ranges_by_skill": relevant_salary_ranges,
        "competitive_offer_estimate": competitive_offer
    }
