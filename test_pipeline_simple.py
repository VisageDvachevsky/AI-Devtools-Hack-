#!/usr/bin/env python3
"""
Simplified Pipeline Test
Tests core features without external API dependencies
"""

import asyncio
from datetime import datetime

from backend.services.advanced_resume_parser import parse_resume_advanced
from backend.services.job_description_generator import (
    generate_job_description,
    JobDescriptionRequest,
    format_job_description_markdown
)
from backend.services.advanced_market_analytics import AdvancedMarketAnalytics
from backend.services.predictive_analytics import PredictiveAnalytics


RESUME_TEXT = """
Тагиров Амир Акбарович
Мужчина, 18 лет, родился 2 января 2007

+7 (920) 2585518
amitag152@icloud.com

Проживает: Нижний Новгород
Гражданство: Россия

Желаемая должность и зарплата
Backend-разработчик
180 000 руб на руки

Специализации: Программист, разработчик
Занятость: полная занятость
График работы: удаленная работа

Опыт работы 6 лет

wink.ai (open-source / ML-backend система)
Октябрь 2025 - настоящее время 3 месяца
Backend + DevOps

Backend (FastAPI, PostgreSQL, ARQ, Redis)
Ускорил обработку ML-запросов с 950-1100 мс до 320-410 мс (-65%).
Настроил production-ready connection pool: улучшил среднее время SELECT-запросов на 38%.
Устранил MissingGreenlet задержки.
Уменьшил latency ML-клиента с 210 -> 80 мс.
Оптимизировал endpoints: уменьшил cold-start payload с 2.1 сек -> 690 мс.

Реализовал healthchecks уровня L3: БД, Redis, ML.
Внедрил Request-ID tracing.
Убрал 100% hardcoded credentials.

Тестирование и качество
Создал 120+ тестов (backend + ML + pipelines).
Типизация: довёл mypy до 0 ошибок, покрытие type hints 100%.
Покрытие кода тестами увеличено с 24% -> 82% (backend) и с 18% -> 76% (ML service).

DevOps / CI / Мониторинг
Сократил время CI-пайплайна с 6 мин 12 сек -> 2 мин 10 сек (-65%).
Настроил Loki stack: сократил задержку поиска логов с 4-5 сек -> 0.8-1.2 сек.
Оптимизировал Docker-сборку: уменьшил размер на 41% (1.02 GB -> 598 MB).
Настроил Grafana дашборды.

AI-Tourist (R&D-проект)
Октябрь 2025 - настоящее время 3 месяца
Fullstack / AI / Backend Developer

Спроектировал микросервисную систему из 7 сервисов (FastAPI + gRPC).
Интегрировал 2GIS + OSRM.
Интегрировал Claude/OpenAI.
Подготовил production-ready Kubernetes деплой: Helm charts.
Полное время генерации путешествия уменьшено с 18 сек -> 4-6 сек.

KATANA Framework (личный проект / Open-source)
Октябрь 2025 - настоящее время 3 месяца
C++ Backend / Systems Developer

Разработал высокопроизводительный C++ фреймворк KATANA.
Реализовал backend на io_uring + batch submission.
Разработал кастомный arena allocator.
Оптимизировал HTTP/1.1 parser: SIMD (AVX2/SSE2).
Throughput увеличен в 15x: 3.2k -> 50k+ RPS.
Улучшение latency: p99 = 0.380ms -> <0.150ms (2.5x лучше).

MedAssist International
Сентябрь 2025 - настоящее время 4 месяца
Fullstack-разработчик (FastAPI, PostgreSQL, Redis, RabbitMQ, React)

Спроектировал архитектуру backend-ядра и микросервисов.
Реализовал интеграцию с 1С (OData).
Разработал систему подачи заявок.
Настроил мониторинг, метрики.
Подготовил CI/CD, Docker-окружение.

ITSC
Январь 2025 - настоящее время 1 год
Fullstack-разработчик

Спроектировал архитектуру онлайн-платформы DISC.
Разработал микросервис интерпретации DISC-профилей (FastAPI + gRPC).
Ускорил вычисление DISC-профиля с ~1.2 сек -> 280 мс.
Нагрузка: 50k+ ответов/час, SLA: p99 < 95 мс.

OcuVision
Февраль 2023 - настоящее время 2 года 11 месяцев
Frontend / VR Interface Developer (React)

Разработал React-интерфейс для управления VR-сессиями.
Выполнил масштабный рефакторинг.
Ускорил загрузку и отрисовку панели Settings ~в 1.6x.
Сократил количество лишних ререндеров на 35-45%.

Навыки
Python; FastAPI; PostgreSQL; Redis; RabbitMQ; gRPC; REST API; CI/CD; Docker; Kubernetes;
Prometheus; Grafana; Linux; React; TypeScript; DDD; Nginx; DevOps; C++; API Gateway; STL;
OpenGL; ECS; SIMD; io_uring; HTTP/1.1; Performance Optimization; Microservices; Async;
Testing; MyPy; Loki; Helm; 1C Integration; Machine Learning; NLP; Path Tracing; Shaders
"""


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
        "benefits": [
            "Stock options",
            "Flexible working hours",
            "Remote work",
            "Professional development budget",
            "Health insurance"
        ],
        "description": "Looking for experienced backend developer to lead microservices architecture"
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
        "benefits": [
            "Competitive salary",
            "Relocation support",
            "Latest hardware",
            "Conference attendance",
            "Bonuses based on performance"
        ],
        "description": "Seeking C++ expert for ultra-low latency trading systems"
    },
    {
        "role": "DevOps / SRE Engineer",
        "company_name": "CloudScale Inc",
        "location": "Remote",
        "required_skills": [
            "kubernetes", "docker", "ci/cd", "prometheus", "grafana",
            "linux", "python", "terraform", "ansible"
        ],
        "nice_to_have_skills": [
            "helm", "argocd", "loki", "elastic", "aws", "gcp"
        ],
        "experience_level": "middle",
        "salary_range": {"from": 180000, "to": 280000},
        "benefits": [
            "Remote work",
            "Flexible schedule",
            "Learning budget",
            "Modern tools",
            "International team"
        ],
        "description": "DevOps engineer to manage cloud infrastructure and CI/CD pipelines"
    }
]


def print_section(title: str):
    print("\n" + "=" * 80)
    print(f"{title}")
    print("=" * 80 + "\n")


async def main():
    print("\n" + "=" * 80)
    print("HR PIPELINE TEST - SIMPLIFIED VERSION")
    print("Candidate: Amir Tagirov")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    print_section("STEP 1: Resume Parsing (Advanced, No LLM)")

    resume = parse_resume_advanced(
        RESUME_TEXT,
        required_skills=[
            "python", "fastapi", "postgresql", "redis", "docker", "c++",
            "kubernetes", "grpc", "prometheus", "grafana"
        ]
    )

    print(f"Name: {resume.get('full_name')}")
    print(f"Email: {resume.get('email')}")
    print(f"Phone: {resume.get('phone')}")
    print(f"Location: {resume.get('location')}")

    exp_years = resume.get('total_years_experience') or 0
    confidence = resume.get('parsing_confidence') or 0

    print(f"Experience: {exp_years:.1f} years")
    print(f"Confidence: {confidence:.1f}%")

    print("\nTop Skills:")
    for skill in resume.get("skills", [])[:15]:
        print(f"  - {skill['skill']}: {skill['proficiency_level']} ({skill['mention_count']} mentions)")

    print("\nPositions:")
    for pos in resume.get("positions", [])[:5]:
        print(f"  - {pos['position']} at {pos['company']} ({pos.get('duration_months', 0)} months)")

    candidate_skills = {skill["skill"].lower() for skill in resume.get("skills", [])}

    all_scores = []

    for vacancy in VACANCIES:
        print_section(f"VACANCY: {vacancy['role']} at {vacancy['company_name']}")

        print("Generating Job Description...")
        jd_dict = generate_job_description(JobDescriptionRequest(**vacancy))
        print(f"Title: {jd_dict['title']}")
        print(f"Overview: {jd_dict['overview'][:200]}...")
        print(f"Salary: {jd_dict.get('salary_range', 'Not specified')}\n")

        print("Scoring Candidate...")

        required_skills_set = set(s.lower() for s in vacancy["required_skills"])
        nice_to_have_set = set(s.lower() for s in vacancy["nice_to_have_skills"])

        required_match = len(required_skills_set & candidate_skills)
        required_total = len(required_skills_set)
        required_score = (required_match / required_total * 100) if required_total > 0 else 0

        nice_match = len(nice_to_have_set & candidate_skills)
        nice_total = len(nice_to_have_set)
        nice_score = (nice_match / nice_total * 100) if nice_total > 0 else 0

        experience_years = resume.get("total_years_experience", 0) or 0
        required_exp = {"junior": 1, "middle": 3, "senior": 5, "lead": 7}.get(vacancy["experience_level"], 3)
        exp_score = min(100, (experience_years / required_exp) * 100) if experience_years > 0 else 0

        total_score = int(
            required_score * 0.5 +
            nice_score * 0.2 +
            exp_score * 0.3
        )

        decision = "STRONG_GO" if total_score >= 80 else "GO" if total_score >= 60 else "MAYBE" if total_score >= 40 else "NO_GO"

        print(f"Required Skills Match: {required_match}/{required_total} ({required_score:.1f}%)")
        print(f"Nice-to-Have Match: {nice_match}/{nice_total} ({nice_score:.1f}%)")
        print(f"Experience Score: {exp_score:.1f}%")
        print(f"TOTAL SCORE: {total_score}/100")
        print(f"DECISION: {decision}")

        print("\nMatched Required Skills:")
        for skill in sorted(required_skills_set & candidate_skills):
            print(f"  + {skill}")

        missing = required_skills_set - candidate_skills
        if missing:
            print("\nMissing Required Skills:")
            for skill in sorted(missing):
                print(f"  - {skill}")

        all_scores.append({
            "vacancy": vacancy["role"],
            "company": vacancy["company_name"],
            "score": total_score,
            "decision": decision,
            "required_match": required_match,
            "required_total": required_total
        })

        if total_score >= 60:
            print_section("Market Analytics & Forecasting")

            analytics = AdvancedMarketAnalytics()

            current_market = {
                "total_vacancies": 1247,
                "average_salary": 220000,
                "median_salary": 200000,
                "skill_demand": {skill: 0.65 + (hash(skill) % 30) / 100 for skill in vacancy["required_skills"][:5]}
            }

            historical_data = [
                {"period": "2024-09", "average_salary": 180000, "total_vacancies": 980},
                {"period": "2024-10", "average_salary": 190000, "total_vacancies": 1050},
                {"period": "2024-11", "average_salary": 205000, "total_vacancies": 1180},
                {"period": "2024-12", "average_salary": 220000, "total_vacancies": 1247},
            ]

            trends_list = analytics.analyze_trends(current_market, historical_data, vacancy["required_skills"][:5])

            print("Skill Trends:")
            for trend in trends_list[:5]:
                print(f"  - {trend.skill}: {trend.trend} (change: {trend.change_percentage:+.1f}%)")

            forecasts = analytics.forecast_salaries(current_market, vacancy["role"], vacancy["required_skills"][:5])

            print("\nSalary Forecasts:")
            for forecast in forecasts[:3]:
                print(f"  - {forecast.period}: {forecast.forecasted_salary:,.0f} RUB (confidence: {forecast.confidence_level})")

            competition = analytics.analyze_competition(current_market, vacancy["role"], 10)
            print(f"\nCompetition Ratio: {competition.competition_ratio:.2f}")
            print(f"Difficulty Score: {competition.difficulty_score}/100")
            print(f"Time to Hire Estimate: {competition.time_to_hire_estimate_days} days")

            print_section("Predictive Analytics")

            pred_analytics = PredictiveAnalytics()

            salary_offered = vacancy["salary_range"]["from"] + 30000
            market_median = (vacancy["salary_range"]["from"] + vacancy["salary_range"]["to"]) / 2

            offer_prediction = pred_analytics.predict_offer_acceptance(
                candidate_id="amir_tagirov",
                candidate_score=total_score,
                salary_offered=salary_offered,
                market_median_salary=int(market_median),
                candidate_experience_years=exp_years,
                has_competing_offers=True,
                days_in_process=15
            )

            print(f"Offer Acceptance Probability: {offer_prediction.probability_accept:.1%}")
            print(f"Risk Level: {offer_prediction.risk_level}")
            print(f"Recommendation: {offer_prediction.recommendation}")

            print("\nKey Factors:")
            for factor in offer_prediction.key_factors:
                print(f"  - {factor}")

            time_to_hire = pred_analytics.predict_time_to_hire(
                role=vacancy["role"],
                required_skills=vacancy["required_skills"][:3],
                market_competition_level="high"
            )

            print(f"\nEstimated Days to Hire: {time_to_hire.estimated_days}")
            print(f"Range: {time_to_hire.confidence_interval[0]}-{time_to_hire.confidence_interval[1]} days")

    print_section("FINAL SUMMARY")

    print("Candidate Match Results:\n")
    for idx, score in enumerate(sorted(all_scores, key=lambda x: x["score"], reverse=True), 1):
        print(f"{idx}. {score['vacancy']} at {score['company']}")
        print(f"   Score: {score['score']}/100")
        print(f"   Decision: {score['decision']}")
        print(f"   Required Skills: {score['required_match']}/{score['required_total']}")
        print("")

    best_match = max(all_scores, key=lambda x: x["score"])
    print(f"BEST MATCH: {best_match['vacancy']} at {best_match['company']}")
    print(f"Final Score: {best_match['score']}/100")
    print("")
    print("Pipeline test completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
