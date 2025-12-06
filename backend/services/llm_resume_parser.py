"""
LLM-Based Resume Parser
Uses large language models to extract structured data from resumes
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from pydantic import BaseModel, Field


class ExperienceEntry(BaseModel):
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    issuer: str
    date_obtained: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    role: Optional[str] = None


class SkillAssessment(BaseModel):
    skill: str
    proficiency_level: str = Field(
        default="unknown",
        description="beginner/intermediate/advanced/expert/unknown"
    )
    years_of_experience: Optional[float] = None
    evidence: List[str] = Field(default_factory=list)


class ParsedResume(BaseModel):
    # Personal info
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    # Professional summary
    summary: Optional[str] = None
    current_role: Optional[str] = None
    total_years_experience: Optional[float] = None

    # Experience
    experience: List[ExperienceEntry] = Field(default_factory=list)

    # Education
    education: List[EducationEntry] = Field(default_factory=list)

    # Skills
    skills: List[SkillAssessment] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)

    # Certifications
    certifications: List[CertificationEntry] = Field(default_factory=list)

    # Projects
    projects: List[ProjectEntry] = Field(default_factory=list)

    # Languages
    languages: List[Dict[str, str]] = Field(default_factory=list)

    # Metadata
    parsing_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    parsing_method: str = "llm"
    parsed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class LLMResumeParser:
    """
    Advanced resume parser using LLM for structured data extraction
    """

    def __init__(self, api_key: Optional[str] = None, api_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("EVOLUTION_API_KEY")
        self.api_url = api_url or os.getenv("EVOLUTION_API_URL", "https://api.cloud.ru/v1")
        self.model = os.getenv("EVOLUTION_MODEL", "claude-3-5-sonnet-20241022")

    def _create_extraction_prompt(self, resume_text: str, required_skills: Optional[List[str]] = None) -> str:
        """Create prompt for LLM to extract structured data"""

        skills_context = ""
        if required_skills:
            skills_context = f"\nPay special attention to these required skills: {', '.join(required_skills)}\n"

        prompt = f"""Extract structured information from the following resume. Return ONLY valid JSON with no additional text.

{skills_context}
Resume text:
{resume_text}

Extract the following information in JSON format:

{{
    "full_name": "candidate's full name",
    "email": "email address",
    "phone": "phone number",
    "location": "location/city",
    "linkedin_url": "LinkedIn profile URL",
    "github_url": "GitHub profile URL",
    "summary": "professional summary or objective",
    "current_role": "current job title",
    "total_years_experience": number of years,
    "experience": [
        {{
            "company": "company name",
            "position": "job title",
            "start_date": "start date",
            "end_date": "end date or 'present'",
            "duration_months": estimated months,
            "responsibilities": ["responsibility 1", "responsibility 2"],
            "technologies": ["tech1", "tech2"],
            "achievements": ["achievement 1"]
        }}
    ],
    "education": [
        {{
            "institution": "school/university name",
            "degree": "degree name",
            "field_of_study": "field",
            "graduation_year": year,
            "gpa": "GPA if mentioned"
        }}
    ],
    "skills": [
        {{
            "skill": "skill name",
            "proficiency_level": "beginner/intermediate/advanced/expert",
            "years_of_experience": estimated years,
            "evidence": ["where mentioned in resume"]
        }}
    ],
    "technical_skills": ["skill1", "skill2"],
    "soft_skills": ["skill1", "skill2"],
    "certifications": [
        {{
            "name": "certification name",
            "issuer": "issuing organization",
            "date_obtained": "date",
            "credential_id": "ID if available"
        }}
    ],
    "projects": [
        {{
            "name": "project name",
            "description": "description",
            "technologies": ["tech1"],
            "url": "project URL",
            "role": "your role"
        }}
    ],
    "languages": [
        {{"language": "English", "proficiency": "Native"}},
        {{"language": "Russian", "proficiency": "Fluent"}}
    ]
}}

Important:
- Extract all information accurately from the resume
- For years of experience, estimate based on job history
- For skill proficiency, infer from context (job titles, responsibilities, years)
- Include only information explicitly stated or strongly implied
- Return ONLY the JSON object, no markdown, no explanations
"""
        return prompt

    async def parse_resume(
        self,
        resume_text: str,
        required_skills: Optional[List[str]] = None,
        fallback_to_regex: bool = True
    ) -> ParsedResume:
        """
        Parse resume using LLM

        Args:
            resume_text: Raw resume text
            required_skills: List of skills to pay attention to
            fallback_to_regex: Use regex extraction if LLM fails

        Returns:
            ParsedResume object
        """

        if not resume_text or not resume_text.strip():
            return ParsedResume(parsing_confidence=0.0)

        # Try LLM parsing first
        try:
            parsed_data = await self._parse_with_llm(resume_text, required_skills)
            if parsed_data:
                parsed_data["parsing_method"] = "llm"
                parsed_data["parsing_confidence"] = 0.9
                return ParsedResume(**parsed_data)
        except Exception as e:
            print(f"LLM parsing failed: {e}")

        # Fallback to regex-based extraction
        if fallback_to_regex:
            return self._parse_with_regex(resume_text, required_skills)

        return ParsedResume(parsing_confidence=0.0)

    async def _parse_with_llm(self, resume_text: str, required_skills: Optional[List[str]]) -> Optional[Dict]:
        """Use LLM API to parse resume"""

        if not self.api_key:
            raise ValueError("No API key configured")

        prompt = self._create_extraction_prompt(resume_text, required_skills)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000
                }

                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]

                    # Extract JSON from response (handle markdown code blocks)
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)

                    # Parse JSON
                    data = json.loads(content)
                    return data
                else:
                    raise Exception(f"API error: {response.status_code}")

        except Exception as e:
            print(f"LLM API call failed: {e}")
            return None

    def _parse_with_regex(self, resume_text: str, required_skills: Optional[List[str]]) -> ParsedResume:
        """Fallback regex-based parsing"""

        parsed = ParsedResume(parsing_method="regex_fallback", parsing_confidence=0.6)

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, resume_text)
        if email_match:
            parsed.email = email_match.group(0)

        # Extract phone
        phone_patterns = [
            r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',
            r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}'
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, resume_text)
            if phone_match:
                parsed.phone = phone_match.group(0)
                break

        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w\-]+'
        linkedin_match = re.search(linkedin_pattern, resume_text, re.IGNORECASE)
        if linkedin_match:
            parsed.linkedin_url = f"https://{linkedin_match.group(0)}"

        # Extract GitHub
        github_pattern = r'github\.com/[\w\-]+'
        github_match = re.search(github_pattern, resume_text, re.IGNORECASE)
        if github_match:
            parsed.github_url = f"https://{github_match.group(0)}"

        # Extract years of experience
        exp_patterns = [
            r'(\d+)\+?\s*(?:years?|лет|года|год)\s*(?:of\s*)?(?:experience|опыта)',
            r'опыт[:\s]*(\d+)\+?\s*(?:лет|года|год)',
        ]
        for pattern in exp_patterns:
            exp_match = re.search(pattern, resume_text, re.IGNORECASE)
            if exp_match:
                parsed.total_years_experience = float(exp_match.group(1))
                break

        # Extract skills from text if required_skills provided
        if required_skills:
            text_lower = resume_text.lower()
            for skill in required_skills:
                if skill.lower() in text_lower:
                    # Count mentions
                    mentions = len(re.findall(r'\b' + re.escape(skill.lower()) + r'\b', text_lower))
                    proficiency = "intermediate"
                    if mentions >= 5:
                        proficiency = "advanced"
                    elif mentions <= 2:
                        proficiency = "beginner"

                    parsed.skills.append(SkillAssessment(
                        skill=skill,
                        proficiency_level=proficiency,
                        evidence=[f"Mentioned {mentions} times in resume"]
                    ))

        return parsed


async def parse_resume_with_llm(
    resume_text: str,
    required_skills: Optional[List[str]] = None
) -> Dict:
    """
    Convenience function to parse resume with LLM

    Args:
        resume_text: Raw resume text
        required_skills: List of skills to focus on

    Returns:
        Parsed resume as dictionary
    """
    parser = LLMResumeParser()
    result = await parser.parse_resume(resume_text, required_skills)
    return result.model_dump()


async def batch_parse_resumes(
    resumes: List[Dict[str, str]],
    required_skills: Optional[List[str]] = None
) -> List[Dict]:
    """
    Parse multiple resumes in parallel

    Args:
        resumes: List of dicts with 'text' and optional 'id'
        required_skills: Skills to focus on

    Returns:
        List of parsed resumes
    """
    parser = LLMResumeParser()

    async def parse_one(resume_data: Dict) -> Dict:
        resume_text = resume_data.get("text", "")
        result = await parser.parse_resume(resume_text, required_skills)
        parsed = result.model_dump()
        parsed["resume_id"] = resume_data.get("id", "unknown")
        return parsed

    import asyncio
    tasks = [parse_one(resume) for resume in resumes]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return [r for r in results if not isinstance(r, Exception)]
