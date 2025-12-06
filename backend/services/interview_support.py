from typing import Dict, List
from backend.services.normalization import categorize_skill, normalize_skill


SKILL_QUESTIONS = {
    "python": [
        "Explain the difference between list and tuple in Python",
        "What are decorators and how do you use them?",
        "Describe GIL and its impact on multithreading",
        "How do you handle memory management in Python?"
    ],
    "javascript": [
        "Explain event loop and asynchronous programming",
        "What is closure and when would you use it?",
        "Difference between var, let, and const",
        "How does prototypal inheritance work?"
    ],
    "react": [
        "Explain Virtual DOM and reconciliation",
        "What are hooks and why were they introduced?",
        "Difference between controlled and uncontrolled components",
        "How would you optimize performance in React app?"
    ],
    "docker": [
        "Explain difference between image and container",
        "How do you optimize Docker image size?",
        "What is multi-stage build?",
        "How do you handle secrets in containers?"
    ],
    "kubernetes": [
        "Explain pods, deployments, and services",
        "How does Kubernetes handle scaling?",
        "What is Ingress controller?",
        "How do you debug a failing pod?"
    ],
    "postgresql": [
        "Explain ACID properties",
        "What are indexes and when to use them?",
        "Difference between JOIN types",
        "How do you optimize slow queries?"
    ]
}

SYSTEM_DESIGN_TOPICS = {
    "backend": [
        "Design a URL shortener service",
        "How would you design a rate limiter?",
        "Design a caching strategy for high-traffic API",
        "Explain your approach to microservices communication"
    ],
    "frontend": [
        "Design state management for large SPA",
        "How would you implement real-time updates?",
        "Explain your approach to code splitting",
        "Design a component library architecture"
    ],
    "database": [
        "Design database schema for e-commerce platform",
        "How would you handle database migrations?",
        "Explain sharding vs partitioning",
        "Design a backup and disaster recovery strategy"
    ],
    "devops": [
        "Design CI/CD pipeline for microservices",
        "How would you implement zero-downtime deployment?",
        "Explain monitoring and alerting strategy",
        "Design infrastructure for high availability"
    ]
}


def generate_interview_questions(
    skill_gaps: List[str],
    matched_skills: List[str],
    candidate_level: str = "unknown"
) -> Dict[str, List[str]]:
    """Generate interview questions based on skills"""

    questions = {
        "skill_verification": [],
        "skill_gaps_exploration": [],
        "system_design": [],
        "behavioral": []
    }

    # Questions to verify matched skills
    for skill in matched_skills[:5]:
        norm = normalize_skill(skill)
        if norm in SKILL_QUESTIONS:
            questions["skill_verification"].extend(SKILL_QUESTIONS[norm][:2])

    # Questions to explore skill gaps
    for skill in skill_gaps[:5]:
        norm = normalize_skill(skill)
        questions["skill_gaps_exploration"].append(
            f"Do you have experience with {skill}? If yes, describe a project where you used it."
        )

    # System design questions based on category
    categories = set(categorize_skill(normalize_skill(s)) for s in matched_skills)
    for category in categories:
        if category in SYSTEM_DESIGN_TOPICS:
            questions["system_design"].extend(SYSTEM_DESIGN_TOPICS[category][:2])

    # Behavioral questions based on level
    if candidate_level == "senior":
        questions["behavioral"] = [
            "Describe a time when you led a technical project",
            "How do you mentor junior developers?",
            "Tell me about a architectural decision you made and its outcome"
        ]
    else:
        questions["behavioral"] = [
            "Describe a challenging bug you fixed recently",
            "How do you approach learning new technologies?",
            "Tell me about a time you worked in a team"
        ]

    return questions


def generate_interview_checklist(
    skill_gaps: List[str],
    risk_flags: List[str],
    activity_metrics: Dict[str, any] = None
) -> List[Dict[str, str]]:
    """Generate interview checklist with items to verify"""

    checklist = []

    # Verify skill gaps
    if skill_gaps:
        checklist.append({
            "category": "Skills",
            "item": f"Verify proficiency in: {', '.join(skill_gaps[:3])}",
            "priority": "high"
        })

    # Check risk flags
    if "no_repos" in risk_flags or "no_languages_detected" in risk_flags:
        checklist.append({
            "category": "Experience",
            "item": "Ask for code samples or portfolio (limited GitHub activity)",
            "priority": "high"
        })

    if activity_metrics:
        days_inactive = activity_metrics.get("days_since_last_push", 0)
        if days_inactive > 90:
            checklist.append({
                "category": "Activity",
                "item": f"Clarify recent work ({days_inactive} days since last GitHub activity)",
                "priority": "medium"
            })

    # General items
    checklist.append({
        "category": "Team Fit",
        "item": "Assess communication skills and cultural fit",
        "priority": "medium"
    })

    checklist.append({
        "category": "Motivation",
        "item": "Understand why candidate is interested in the role",
        "priority": "medium"
    })

    return checklist


def generate_coding_tasks(
    primary_skills: List[str],
    difficulty: str = "medium"
) -> List[Dict[str, str]]:
    """Generate coding task suggestions based on stack"""

    tasks = []

    for skill in primary_skills[:3]:
        norm = normalize_skill(skill)
        category = categorize_skill(norm)

        if category == "backend":
            if difficulty == "senior":
                tasks.append({
                    "skill": skill,
                    "task": f"Implement rate limiter middleware using {skill}",
                    "duration": "45-60 min"
                })
            else:
                tasks.append({
                    "skill": skill,
                    "task": f"Build REST API for todo list using {skill}",
                    "duration": "30-45 min"
                })

        elif category == "frontend":
            if difficulty == "senior":
                tasks.append({
                    "skill": skill,
                    "task": f"Implement infinite scroll with {skill}",
                    "duration": "45-60 min"
                })
            else:
                tasks.append({
                    "skill": skill,
                    "task": f"Build searchable list component with {skill}",
                    "duration": "30-45 min"
                })

        elif category == "database":
            tasks.append({
                "skill": skill,
                "task": f"Write optimized query for data aggregation in {skill}",
                "duration": "20-30 min"
            })

    return tasks


def prepare_interview_script(
    candidate_username: str,
    matched_skills: List[str],
    skill_gaps: List[str],
    risk_flags: List[str],
    activity_metrics: Dict[str, any] = None,
    seniority: str = "unknown"
) -> Dict[str, any]:
    """Prepare complete interview script"""

    questions = generate_interview_questions(skill_gaps, matched_skills, seniority)
    checklist = generate_interview_checklist(skill_gaps, risk_flags, activity_metrics)
    coding_tasks = generate_coding_tasks(matched_skills, difficulty=seniority)

    return {
        "candidate": candidate_username,
        "seniority": seniority,
        "questions": questions,
        "checklist": checklist,
        "coding_tasks": coding_tasks,
        "estimated_duration": "60-90 min"
    }
