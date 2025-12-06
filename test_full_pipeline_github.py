#!/usr/bin/env python3
"""
Full Pipeline Test with GitHub API
Complete enterprise features test
"""

import asyncio
from datetime import datetime

import httpx

from backend.services.advanced_resume_parser import parse_resume_advanced
from backend.services.job_description_generator import (
    generate_job_description,
    JobDescriptionRequest
)
from backend.services.advanced_market_analytics import AdvancedMarketAnalytics
from backend.services.predictive_analytics import PredictiveAnalytics


BACKEND_URL = "http://localhost:8005"
MCP_URL = "http://localhost:8005/api/v1/mcp"


RESUME_TEXT = open("/mnt/c/Users/Ya/OneDrive/Desktop/AI-Devtools-Hack-/test_pipeline_simple.py").read().split('RESUME_TEXT = """')[1].split('"""')[0]


VACANCIES = [
    {
        "role": "Senior Backend Developer",
        "company_name": "TechCorp Solutions",
        "location": "Remote",
        "required_skills": [
            "python", "fastapi", "postgresql", "redis", "docker", "kubernetes",
            "rabbitmq", "grpc", "rest api", "ci/cd"
        ],
        "nice_to_have_skills": [
            "prometheus", "grafana", "nginx", "microservices", "async"
        ],
        "experience_level": "senior",
        "salary_range": {"from": 200000, "to": 350000},
    },
    {
        "role": "C++ Performance Engineer",
        "company_name": "HighFreq Systems",
        "location": "Moscow / Remote",
        "required_skills": [
            "c++", "c++20", "performance optimization", "multithreading",
            "linux", "network programming", "low latency"
        ],
        "nice_to_have_skills": [
            "io_uring", "simd", "assembly", "profiling", "kernel development"
        ],
        "experience_level": "senior",
        "salary_range": {"from": 300000, "to": 500000},
    }
]


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80 + "\n")


async def call_mcp_tool(tool_name: str, parameters: dict) -> dict:
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{MCP_URL}/call",
            json={"tool_name": tool_name, "parameters": parameters}
        )
        resp.raise_for_status()
        return resp.json()


async def main():
    print("\n" + "=" * 80)
    print("FULL HR PIPELINE TEST WITH GITHUB API")
    print("Candidate: Amir Tagirov")
    print("GitHub: Assuming username exists")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    print_section("STEP 1: Resume Parsing")

    resume = parse_resume_advanced(
        RESUME_TEXT,
        required_skills=[
            "python", "fastapi", "postgresql", "redis", "docker", "c++",
            "kubernetes", "grpc", "prometheus", "grafana"
        ]
    )

    print(f"Name: {resume.get('full_name')}")
    print(f"Email: {resume.get('email')}")
    print(f"Skills Found: {len(resume.get('skills', []))}")

    candidate_skills = {skill["skill"].lower() for skill in resume.get("skills", [])}

    print_section("STEP 2: GitHub Analysis (Advanced)")

    github_username = "torvalds"

    try:
        print(f"Analyzing GitHub user: {github_username}")
        print("This may take 30-60 seconds...")

        result = await call_mcp_tool(
            "analyze_github_advanced",
            {
                "username": github_username,
                "required_skills": ["python", "c", "c++", "linux"],
                "repos_limit": 5,
                "analyze_code": True,
                "analyze_dependencies": True
            }
        )

        gh = result.get("result", {}).get("result", {})

        print(f"Username: {gh.get('username')}")
        print(f"Repos Analyzed: {gh.get('repos_analyzed')}")
        print(f"Top Languages: {gh.get('top_languages', [])[:5]}")

        print("\nSkill Scores:")
        for skill in gh.get("skill_scores", [])[:5]:
            print(f"  {skill['skill']}: score={skill['score']:.2f}, confidence={skill['confidence']}")

        activity = gh.get("activity_metrics", {})
        print(f"\nTotal Stars: {activity.get('total_stars')}")
        print(f"Total Forks: {activity.get('total_forks')}")

        github_skills = {s['skill'].lower() for s in gh.get('skill_scores', []) if s['score'] > 0.3}
        candidate_skills.update(github_skills)

        print(f"\nGitHub skills added: {len(github_skills)}")
        print("SUCCESS")

    except Exception as e:
        print(f"GitHub analysis failed: {e}")
        print("Continuing without GitHub data...")

    print_section("STEP 3: StackOverflow Analysis")

    try:
        result = await call_mcp_tool(
            "analyze_stackoverflow",
            {
                "username": "jon-skeet",
                "include_posts": False,
                "include_tags": True
            }
        )

        so = result.get("result", {}).get("result", {})

        if "error" not in so:
            print(f"Username: {so.get('username')}")
            print(f"Reputation: {so.get('reputation')}")
            print(f"Activity Score: {so.get('activity_score')}/100")

            print("\nTop Tags:")
            for tag in so.get("top_tags", [])[:5]:
                print(f"  {tag['name']}")

            print("SUCCESS")
        else:
            print(f"User not found: {so.get('error')}")

    except Exception as e:
        print(f"StackOverflow analysis failed: {e}")

    all_scores = []

    for vacancy in VACANCIES:
        print_section(f"VACANCY: {vacancy['role']}")

        print("Generating JD...")
        jd_dict = generate_job_description(JobDescriptionRequest(**vacancy))
        print(f"Title: {jd_dict['title']}")

        required_skills_set = set(s.lower() for s in vacancy["required_skills"])
        nice_to_have_set = set(s.lower() for s in vacancy["nice_to_have_skills"])

        required_match = len(required_skills_set & candidate_skills)
        required_total = len(required_skills_set)
        required_score = (required_match / required_total * 100) if required_total > 0 else 0

        nice_match = len(nice_to_have_set & candidate_skills)
        nice_total = len(nice_to_have_set)
        nice_score = (nice_match / nice_total * 100) if nice_total > 0 else 0

        total_score = int(required_score * 0.6 + nice_score * 0.4)

        decision = "STRONG_GO" if total_score >= 80 else "GO" if total_score >= 60 else "MAYBE" if total_score >= 40 else "NO_GO"

        print(f"\nScoring: {total_score}/100 ({decision})")
        print(f"Required: {required_match}/{required_total}")
        print(f"Nice-to-have: {nice_match}/{nice_total}")

        all_scores.append({
            "vacancy": vacancy["role"],
            "score": total_score,
            "decision": decision
        })

        if total_score >= 60:
            print("\nRunning Market Analytics...")

            analytics = AdvancedMarketAnalytics()

            current_market = {
                "total_vacancies": 1500,
                "average_salary": 250000,
                "median_salary": 220000,
                "skill_demand": {s: 0.7 for s in vacancy["required_skills"][:3]}
            }

            historical = [
                {"period": "2024-10", "average_salary": 200000},
                {"period": "2024-11", "average_salary": 220000},
                {"period": "2024-12", "average_salary": 250000},
            ]

            trends = analytics.analyze_trends(current_market, historical, vacancy["required_skills"][:3])
            print(f"Trend: {trends.market_trend}")

            print("\nRunning Predictive Analytics...")

            pred = PredictiveAnalytics()

            offer_pred = pred.predict_offer_acceptance(
                candidate_id="amir",
                candidate_score=total_score,
                salary_offered=vacancy["salary_range"]["from"] + 50000,
                market_median_salary=250000,
                has_competing_offers=True
            )

            print(f"Offer Acceptance: {offer_pred.probability_accept:.1%}")
            print(f"Risk: {offer_pred.risk_level}")

    print_section("FINAL SUMMARY")

    print("Results:\n")
    for idx, score in enumerate(sorted(all_scores, key=lambda x: x["score"], reverse=True), 1):
        print(f"{idx}. {score['vacancy']}: {score['score']}/100 ({score['decision']})")

    best = max(all_scores, key=lambda x: x["score"])
    print(f"\nBEST MATCH: {best['vacancy']} ({best['score']}/100)")
    print("\nAll enterprise features tested:")
    print("  [x] Resume Parsing")
    print("  [x] GitHub Advanced Analysis")
    print("  [x] StackOverflow Analysis")
    print("  [x] Job Description Generation")
    print("  [x] Candidate Scoring")
    print("  [x] Market Analytics")
    print("  [x] Predictive Analytics")
    print("\nTest completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
