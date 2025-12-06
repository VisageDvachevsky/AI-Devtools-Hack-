"""
Job Description Generator
Automatically generates professional job descriptions based on market data
NO LLM required - template-based with smart customization!
"""
import random
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class JobDescriptionRequest(BaseModel):
    role: str
    company_name: str
    location: str = "Remote"
    required_skills: List[str] = Field(default_factory=list)
    nice_to_have_skills: List[str] = Field(default_factory=list)
    experience_level: str = "middle"  # junior, middle, senior, lead
    salary_range: Optional[Dict[str, int]] = None  # {"from": 100000, "to": 200000, "currency": "RUB"}
    benefits: List[str] = Field(default_factory=list)
    market_data: Optional[Dict] = None  # Market insights for better generation


class GeneratedJobDescription(BaseModel):
    title: str
    company: str
    location: str
    employment_type: str = "Full-time"

    # Main sections
    overview: str
    responsibilities: List[str]
    requirements: List[str]
    nice_to_have: List[str]
    benefits: List[str]

    # Additional info
    salary_range: Optional[str] = None
    application_process: str

    # Metadata
    seo_keywords: List[str] = Field(default_factory=list)
    generated_at: str


# Template components for different experience levels
EXPERIENCE_MODIFIERS = {
    "junior": {
        "years": "0-2",
        "level_description": "Entry-level",
        "responsibility_prefix": "Assist with",
        "autonomy": "under supervision"
    },
    "middle": {
        "years": "2-5",
        "level_description": "Mid-level",
        "responsibility_prefix": "Develop and maintain",
        "autonomy": "with minimal supervision"
    },
    "senior": {
        "years": "5+",
        "level_description": "Senior",
        "responsibility_prefix": "Lead and architect",
        "autonomy": "independently"
    },
    "lead": {
        "years": "7+",
        "level_description": "Lead",
        "responsibility_prefix": "Drive strategy and mentor",
        "autonomy": "with full ownership"
    }
}

# Common responsibilities by role type
ROLE_RESPONSIBILITIES = {
    "backend": [
        "Design and implement scalable backend services and APIs",
        "Optimize database queries and improve application performance",
        "Write clean, maintainable, and well-tested code",
        "Collaborate with frontend developers and product team",
        "Participate in code reviews and technical discussions",
        "Debug and resolve production issues",
        "Contribute to technical documentation and best practices"
    ],
    "frontend": [
        "Build responsive and intuitive user interfaces",
        "Implement pixel-perfect designs from mockups",
        "Optimize frontend performance and bundle size",
        "Collaborate with designers and backend developers",
        "Write reusable and modular component code",
        "Ensure cross-browser compatibility",
        "Participate in UX/UI discussions"
    ],
    "fullstack": [
        "Develop end-to-end features across the full stack",
        "Design and implement both frontend and backend solutions",
        "Integrate third-party services and APIs",
        "Optimize application performance at all layers",
        "Collaborate with cross-functional teams",
        "Maintain and improve existing codebase",
        "Participate in architecture decisions"
    ],
    "devops": [
        "Design and maintain CI/CD pipelines",
        "Manage cloud infrastructure and deployments",
        "Implement monitoring, logging, and alerting solutions",
        "Automate operational tasks and improve reliability",
        "Optimize infrastructure costs and performance",
        "Ensure security and compliance requirements",
        "Provide support for development teams"
    ],
    "data": [
        "Design and build data pipelines and ETL processes",
        "Develop and maintain data models and schemas",
        "Optimize query performance and data storage",
        "Collaborate with analysts and stakeholders",
        "Implement data quality checks and monitoring",
        "Create and maintain data documentation",
        "Support analytics and reporting requirements"
    ],
    "ml": [
        "Design and implement machine learning models",
        "Conduct experiments and evaluate model performance",
        "Deploy models to production environments",
        "Monitor and improve model accuracy over time",
        "Collaborate with data engineers and product teams",
        "Research and implement state-of-the-art techniques",
        "Create technical documentation for ML systems"
    ]
}

# Common benefits
STANDARD_BENEFITS = [
    "Competitive salary and equity packages",
    "Flexible working hours and remote work options",
    "Professional development and learning budget",
    "Modern tech stack and tools",
    "Health insurance and wellness programs",
    "Paid time off and vacation days",
    "Collaborative and inclusive work environment",
    "Regular team events and activities",
    "Career growth opportunities",
    "Latest hardware and equipment"
]


class JobDescriptionGenerator:
    """
    Intelligent job description generator
    Uses templates, market data, and heuristics to create compelling JDs
    """

    def __init__(self):
        pass

    def generate(self, request: JobDescriptionRequest) -> GeneratedJobDescription:
        """
        Generate a complete job description

        Args:
            request: Job description parameters

        Returns:
            Generated job description
        """

        # Determine role type
        role_type = self._classify_role(request.role)

        # Determine experience level
        exp_level = request.experience_level.lower()
        exp_info = EXPERIENCE_MODIFIERS.get(exp_level, EXPERIENCE_MODIFIERS["middle"])

        # Generate title
        title = self._generate_title(request.role, exp_level)

        # Generate overview
        overview = self._generate_overview(
            request.company_name,
            request.role,
            exp_info,
            request.market_data
        )

        # Generate responsibilities
        responsibilities = self._generate_responsibilities(
            role_type,
            exp_level,
            request.required_skills
        )

        # Generate requirements
        requirements = self._generate_requirements(
            request.required_skills,
            exp_info,
            request.market_data
        )

        # Generate nice-to-have
        nice_to_have = self._generate_nice_to_have(request.nice_to_have_skills)

        # Generate benefits
        benefits = self._generate_benefits(request.benefits, request.market_data)

        # Format salary range
        salary_str = None
        if request.salary_range:
            salary_from = request.salary_range.get("from", 0)
            salary_to = request.salary_range.get("to", 0)
            currency = request.salary_range.get("currency", "RUB")

            if salary_from and salary_to:
                salary_str = f"{salary_from:,} - {salary_to:,} {currency} per year"
            elif salary_from:
                salary_str = f"From {salary_from:,} {currency} per year"

        # Generate application process
        application_process = self._generate_application_process(exp_level)

        # Generate SEO keywords
        seo_keywords = self._generate_seo_keywords(
            request.role,
            request.required_skills,
            request.location
        )

        from datetime import datetime
        return GeneratedJobDescription(
            title=title,
            company=request.company_name,
            location=request.location,
            employment_type="Full-time",
            overview=overview,
            responsibilities=responsibilities,
            requirements=requirements,
            nice_to_have=nice_to_have,
            benefits=benefits,
            salary_range=salary_str,
            application_process=application_process,
            seo_keywords=seo_keywords,
            generated_at=datetime.utcnow().isoformat()
        )

    def _classify_role(self, role: str) -> str:
        """Classify role into category"""
        role_lower = role.lower()

        if any(kw in role_lower for kw in ["backend", "api", "server"]):
            return "backend"
        elif any(kw in role_lower for kw in ["frontend", "react", "vue", "ui"]):
            return "frontend"
        elif any(kw in role_lower for kw in ["fullstack", "full stack", "full-stack"]):
            return "fullstack"
        elif any(kw in role_lower for kw in ["devops", "sre", "infrastructure"]):
            return "devops"
        elif any(kw in role_lower for kw in ["data engineer", "data pipeline", "etl"]):
            return "data"
        elif any(kw in role_lower for kw in ["ml", "machine learning", "ai", "data scientist"]):
            return "ml"
        else:
            return "backend"  # Default

    def _generate_title(self, role: str, exp_level: str) -> str:
        """Generate job title"""
        exp_info = EXPERIENCE_MODIFIERS.get(exp_level, EXPERIENCE_MODIFIERS["middle"])
        level_prefix = exp_info["level_description"]

        # Clean up role
        role_clean = role.strip()

        if exp_level in ["junior", "senior", "lead"]:
            if not any(prefix in role_clean.lower() for prefix in ["junior", "senior", "lead"]):
                return f"{level_prefix} {role_clean}"

        return role_clean

    def _generate_overview(
        self,
        company_name: str,
        role: str,
        exp_info: Dict,
        market_data: Optional[Dict]
    ) -> str:
        """Generate company and role overview"""

        overview_templates = [
            f"{company_name} is seeking a talented {role} to join our growing team. "
            f"As a {exp_info['level_description']} engineer, you will play a key role in building and scaling our products. "
            f"This is an exciting opportunity to work with modern technologies and make a real impact.",

            f"We're looking for an experienced {role} to help {company_name} deliver innovative solutions to our customers. "
            f"You'll work {exp_info['autonomy']} on challenging problems and collaborate with a talented team of engineers. "
            f"Join us in building the future of our platform.",

            f"At {company_name}, we're on a mission to revolutionize our industry. We're searching for a passionate {role} "
            f"who thrives in a fast-paced environment. With {exp_info['years']} years of experience, you'll contribute to "
            f"critical projects and help shape our technical direction."
        ]

        # Add market insights if available
        base_overview = random.choice(overview_templates)

        if market_data:
            total_jobs = market_data.get("total_found", 0)
            if total_jobs > 100:
                base_overview += f" This role is in high demand with {total_jobs}+ open positions in the market."

        return base_overview

    def _generate_responsibilities(
        self,
        role_type: str,
        exp_level: str,
        skills: List[str]
    ) -> List[str]:
        """Generate role responsibilities"""

        base_responsibilities = ROLE_RESPONSIBILITIES.get(role_type, ROLE_RESPONSIBILITIES["backend"])

        # Customize based on exp level
        exp_info = EXPERIENCE_MODIFIERS.get(exp_level, EXPERIENCE_MODIFIERS["middle"])

        responsibilities = []

        # Select 5-7 responsibilities
        for resp in base_responsibilities[:7]:
            # Adjust language based on exp level
            if exp_level == "junior":
                if resp.startswith("Design") or resp.startswith("Lead"):
                    resp = resp.replace("Design", "Assist in designing")
                    resp = resp.replace("Lead", "Support")
            elif exp_level == "lead":
                if not any(word in resp for word in ["Lead", "Drive", "Mentor"]):
                    resp = "Lead initiatives to " + resp.lower()

            responsibilities.append(resp)

        # Add skill-specific responsibilities
        if "kubernetes" in [s.lower() for s in skills]:
            responsibilities.append("Manage and optimize Kubernetes clusters")
        if "react" in [s.lower() for s in skills]:
            responsibilities.append("Build responsive React components and features")

        return responsibilities[:7]

    def _generate_requirements(
        self,
        skills: List[str],
        exp_info: Dict,
        market_data: Optional[Dict]
    ) -> List[str]:
        """Generate job requirements"""

        requirements = []

        # Experience requirement
        requirements.append(f"{exp_info['years']} years of professional software development experience")

        # Technical skills
        if skills:
            # Group by type
            languages = [s for s in skills if s.lower() in ["python", "javascript", "java", "go", "rust", "typescript"]]
            frameworks = [s for s in skills if s.lower() in ["react", "vue", "angular", "django", "flask", "fastapi"]]
            tools = [s for s in skills if s.lower() in ["docker", "kubernetes", "aws", "postgresql", "redis"]]

            if languages:
                requirements.append(f"Strong proficiency in {', '.join(languages[:2])}")

            if frameworks:
                requirements.append(f"Hands-on experience with {', '.join(frameworks[:2])}")

            if tools:
                requirements.append(f"Familiarity with {', '.join(tools[:3])}")

        # Soft skills
        requirements.extend([
            "Excellent problem-solving and analytical skills",
            "Strong communication and collaboration abilities",
            "Self-motivated with ability to work independently",
            "Passion for writing clean, efficient code"
        ])

        # Education
        requirements.append("Bachelor's degree in Computer Science or equivalent experience")

        return requirements

    def _generate_nice_to_have(self, skills: List[str]) -> List[str]:
        """Generate nice-to-have qualifications"""

        nice_to_have = []

        if skills:
            for skill in skills[:5]:
                nice_to_have.append(f"Experience with {skill}")

        # Add generic nice-to-haves
        nice_to_have.extend([
            "Contributions to open-source projects",
            "Experience with agile/scrum methodologies",
            "Previous startup or fast-paced environment experience",
            "Technical blog or speaking experience"
        ])

        return nice_to_have[:6]

    def _generate_benefits(self, custom_benefits: List[str], market_data: Optional[Dict]) -> List[str]:
        """Generate benefits list"""

        benefits = []

        # Add custom benefits first
        if custom_benefits:
            benefits.extend(custom_benefits)

        # Add standard benefits
        benefits.extend(STANDARD_BENEFITS)

        # Add competitive benefits based on market
        if market_data:
            total_jobs = market_data.get("total_found", 0)
            if total_jobs > 500:  # Highly competitive market
                benefits.insert(0, "Sign-on bonus and relocation assistance")
                benefits.insert(1, "Stock options with accelerated vesting")

        # Return unique benefits
        seen = set()
        unique_benefits = []
        for b in benefits:
            if b.lower() not in seen:
                seen.add(b.lower())
                unique_benefits.append(b)

        return unique_benefits[:10]

    def _generate_application_process(self, exp_level: str) -> str:
        """Generate application process description"""

        if exp_level in ["senior", "lead"]:
            return (
                "Our hiring process includes:\n"
                "1. Initial screening call (30 min)\n"
                "2. Technical interview (1 hour)\n"
                "3. System design discussion (1 hour)\n"
                "4. Team fit and culture interview (45 min)\n"
                "5. Offer and negotiation\n\n"
                "Typical timeline: 2-3 weeks. We value your time and provide feedback at each stage."
            )
        else:
            return (
                "Our hiring process includes:\n"
                "1. Initial screening call (30 min)\n"
                "2. Technical assessment (take-home or live coding)\n"
                "3. Technical interview (1 hour)\n"
                "4. Team fit interview (30 min)\n"
                "5. Offer\n\n"
                "Timeline: 1-2 weeks. We'll keep you informed throughout the process."
            )

    def _generate_seo_keywords(self, role: str, skills: List[str], location: str) -> List[str]:
        """Generate SEO keywords for job posting"""

        keywords = []

        # Add role variations
        role_lower = role.lower()
        keywords.append(role)
        keywords.append(f"{role} job")
        keywords.append(f"{role} position")

        # Add skills
        keywords.extend(skills[:10])

        # Add location
        keywords.append(location)
        keywords.append(f"{role} {location}")

        # Add generic tech keywords
        keywords.extend([
            "software engineer",
            "tech jobs",
            "developer position",
            "remote work",
            "startup jobs"
        ])

        return list(set(keywords))[:20]  # Unique, max 20


def generate_job_description(request: JobDescriptionRequest) -> Dict:
    """
    Convenience function to generate job description

    Args:
        request: Job description parameters

    Returns:
        Generated job description as dict
    """
    generator = JobDescriptionGenerator()
    result = generator.generate(request)
    return result.model_dump()


def format_job_description_markdown(jd: GeneratedJobDescription) -> str:
    """Format job description as Markdown"""

    md = f"""# {jd.title}

**{jd.company}** | {jd.location} | {jd.employment_type}

{f"**Salary:** {jd.salary_range}" if jd.salary_range else ""}

## About the Role

{jd.overview}

## Responsibilities

{chr(10).join(f"- {r}" for r in jd.responsibilities)}

## Requirements

{chr(10).join(f"- {r}" for r in jd.requirements)}

## Nice to Have

{chr(10).join(f"- {n}" for n in jd.nice_to_have)}

## What We Offer

{chr(10).join(f"- {b}" for b in jd.benefits)}

## Application Process

{jd.application_process}

---
*Generated on {jd.generated_at}*
"""

    return md
