"""
Advanced Resume Parser (No LLM required)
Uses NLP libraries, regex, and heuristics for intelligent resume parsing
FREE and FAST - no API costs!
"""
import re
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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


class SkillAssessment(BaseModel):
    skill: str
    proficiency_level: str = "intermediate"
    years_of_experience: Optional[float] = None
    evidence: List[str] = Field(default_factory=list)
    mention_count: int = 0


class ParsedResume(BaseModel):
    # Personal info
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Professional
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

    # Metadata
    parsing_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    parsing_method: str = "advanced_nlp"
    parsed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Common job titles for role detection
JOB_TITLES = [
    "senior", "junior", "lead", "principal", "staff", "architect",
    "developer", "engineer", "programmer", "analyst", "scientist",
    "manager", "director", "head", "chief", "cto", "ceo",
    "backend", "frontend", "fullstack", "full stack", "devops",
    "data", "ml", "ai", "qa", "test",
]

# Degree keywords
DEGREE_KEYWORDS = [
    "bachelor", "master", "phd", "doctorate", "mba",
    "бакалавр", "магистр", "кандидат наук", "доктор",
    "b.s.", "m.s.", "b.a.", "m.a.", "ph.d."
]

# Soft skills keywords
SOFT_SKILLS = [
    "leadership", "communication", "teamwork", "problem solving",
    "analytical", "critical thinking", "creativity", "adaptability",
    "time management", "collaboration", "negotiation", "presentation",
    "лидерство", "командная работа", "коммуникация", "аналитика"
]

# Common tech skill keywords (expand this significantly)
TECH_SKILLS = [
    "python", "javascript", "java", "c++", "cpp", "c#", "csharp", "go", "golang", "rust", "php", "ruby",
    "react", "vue", "angular", "node.js", "nodejs", "django", "flask", "fastapi",
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch", "rabbitmq", "kafka",
    "docker", "kubernetes", "k8s", "aws", "azure", "gcp", "terraform", "ansible",
    "git", "ci/cd", "jenkins", "gitlab", "github actions", "grpc", "rest", "rest api",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "linux", "unix", "windows", "bash", "shell", "nginx", "apache",
    "prometheus", "grafana", "loki", "elk", "microservices", "async", "asyncio",
    "io_uring", "simd", "avx", "sse", "assembly", "network programming", "multithreading",
    "performance optimization", "low latency", "c++20", "c++17", "profiling",
    "helm", "argocd", "istio", "service mesh"
]

# Special skill mappings for variations
SKILL_ALIASES = {
    "c++": ["cpp", "c plus plus", "cplusplus"],
    "c#": ["csharp", "c sharp"],
    "node.js": ["nodejs", "node"],
    "postgresql": ["postgres", "psql"],
    "kubernetes": ["k8s"],
    "golang": ["go"],
}


class AdvancedResumeParser:
    """
    Advanced resume parser using pattern matching and NLP heuristics
    No expensive LLM API calls required!
    """

    def __init__(self):
        self.tech_skills_pattern = self._compile_skills_pattern(TECH_SKILLS)
        self.soft_skills_pattern = self._compile_skills_pattern(SOFT_SKILLS)

    def _compile_skills_pattern(self, skills: List[str]) -> re.Pattern:
        """Create optimized regex pattern for skill matching"""
        # Escape and join skills with word boundaries
        pattern = r'\b(' + '|'.join(re.escape(s) for s in skills) + r')\b'
        return re.compile(pattern, re.IGNORECASE)

    def parse_resume(self, resume_text: str, required_skills: Optional[List[str]] = None) -> ParsedResume:
        """
        Parse resume using intelligent pattern matching

        Args:
            resume_text: Raw resume text
            required_skills: Skills to specifically look for

        Returns:
            ParsedResume object
        """

        if not resume_text or not resume_text.strip():
            return ParsedResume(parsing_confidence=0.0)

        resume = ParsedResume()

        # Extract personal information
        resume.email = self._extract_email(resume_text)
        resume.phone = self._extract_phone(resume_text)
        resume.linkedin_url = self._extract_linkedin(resume_text)
        resume.github_url = self._extract_github(resume_text)
        resume.full_name = self._extract_name(resume_text)
        resume.location = self._extract_location(resume_text)

        # Extract professional summary
        resume.summary = self._extract_summary(resume_text)
        resume.current_role = self._extract_current_role(resume_text)

        # Extract years of experience
        resume.total_years_experience = self._extract_years_of_experience(resume_text)

        # Extract sections
        sections = self._split_into_sections(resume_text)

        # Parse experience
        if "experience" in sections or "work" in sections:
            exp_text = sections.get("experience", sections.get("work", ""))
            resume.experience = self._parse_experience_section(exp_text)

        # Parse education
        if "education" in sections:
            resume.education = self._parse_education_section(sections["education"])

        # Parse certifications
        if "certifications" in sections or "certificates" in sections:
            cert_text = sections.get("certifications", sections.get("certificates", ""))
            resume.certifications = self._parse_certifications_section(cert_text)

        # Extract skills
        resume.technical_skills = self._extract_technical_skills(resume_text)
        resume.soft_skills = self._extract_soft_skills(resume_text)

        # Detailed skill assessment for required skills
        if required_skills:
            resume.skills = self._assess_skills(resume_text, required_skills)

        # Calculate parsing confidence
        resume.parsing_confidence = self._calculate_confidence(resume)

        return resume

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number (multiple formats)"""
        patterns = [
            r'(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}',  # Russian
            r'\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}',  # International
            r'\(\d{3}\)[\s\-]?\d{3}[\s\-]?\d{4}',  # US format
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL"""
        pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return None

    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub URL"""
        pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return None

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract full name (heuristic: first 2-3 capitalized words at top)"""
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and len(line) < 50:
                # Look for capitalized words
                words = line.split()
                if 2 <= len(words) <= 4:
                    if all(w[0].isupper() for w in words if w):
                        return line
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location (city, country)"""
        # Common location patterns
        patterns = [
            r'(?:Location|Адрес|City)[:\s]+([A-Za-zА-Яа-я\s,]+)',
            r'\b([A-Z][a-z]+,\s*[A-Z]{2,})\b',  # City, STATE
            r'\b(Moscow|Saint Petersburg|New York|London|Berlin|Paris)\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary"""
        patterns = [
            r'(?:Summary|Objective|Profile|О себе)[:\s]+([^\n]+(?:\n[^\n]+){0,3})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:500]  # Limit to 500 chars
        return None

    def _extract_current_role(self, text: str) -> Optional[str]:
        """Extract current job title"""
        for title in JOB_TITLES:
            pattern = rf'\b({title}\s+\w+(?:\s+\w+)?)\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_years_of_experience(self, text: str) -> Optional[float]:
        """Extract total years of experience"""
        patterns = [
            r'(\d+(?:\.\d+)?)\+?\s*(?:years?|лет|года|год)\s*(?:of\s*)?(?:experience|опыта)',
            r'(?:experience|опыт|опыт работы)[:\s—–-]*(\d+(?:\.\d+)?)\+?\s*(?:years?|лет|года|год)',
            r'(?:самозанятый|самозанятость).*?(\d{4})\s*[-—–]\s*(?:настоящее время|present)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years_str = match.group(1)
                # Handle year format (e.g. "2020 - present")
                if len(years_str) == 4:
                    start_year = int(years_str)
                    current_year = datetime.now().year
                    return float(current_year - start_year)
                return float(years_str)

        # Fallback: try to parse date ranges
        date_ranges = re.findall(
            r'(?:январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\s*[-—–]\s*(?:настоящее время|present|\d{4})',
            text,
            re.IGNORECASE
        )

        if date_ranges:
            # Find earliest year
            earliest_year = min(int(y) for y in date_ranges)
            current_year = datetime.now().year
            return float(current_year - earliest_year)

        return None

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume into logical sections"""
        sections = {}

        # Common section headers
        section_markers = {
            "experience": r"(?:work\s+)?experience|employment|work\s+history|опыт\s+работы",
            "education": r"education|academic|обучение|образование",
            "skills": r"(?:technical\s+)?skills|competencies|навыки",
            "certifications": r"certifications?|certificates|сертификаты",
            "projects": r"projects|portfolio|проекты",
            "languages": r"languages|языки",
        }

        lines = text.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Check if line is a section header
            is_header = False
            for section_key, pattern in section_markers.items():
                if re.match(rf'^{pattern}\s*:?\s*$', line_lower):
                    # Save previous section
                    if current_section:
                        sections[current_section] = '\n'.join(current_content)

                    # Start new section
                    current_section = section_key
                    current_content = []
                    is_header = True
                    break

            if not is_header and current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _parse_experience_section(self, text: str) -> List[ExperienceEntry]:
        """Parse work experience entries"""
        experiences = []

        # Split by job entries - look for patterns like company name followed by dates
        # Pattern: Company name, then date range on next line
        entries = re.split(
            r'\n(?=[A-ZА-Я][A-Za-zА-Яа-я0-9\s\.\-]{3,}(?:\s+\([^)]+\))?\s*\n(?:январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь|\d{4}|january|february|march|april|may|june|july|august|september|october|november|december))',
            text,
            flags=re.IGNORECASE
        )

        for entry in entries:
            if len(entry.strip()) < 20:
                continue

            exp = ExperienceEntry(company="Unknown", position="Unknown")

            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if not lines:
                continue

            # First line is usually company name
            exp.company = lines[0]

            # Extract dates (month year format)
            month_date_pattern = r'(?:январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\s*[-—–]\s*(?:настоящее время|настоящее|present|(?:январь|февраль|март|апрель|май|июнь|июль|август|сентябрь|октябрь|ноябрь|декабрь|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4}))'
            date_match = re.search(month_date_pattern, entry, re.IGNORECASE)

            if date_match:
                exp.start_date = date_match.group(1)
                if date_match.group(2):
                    exp.end_date = date_match.group(2)
                else:
                    exp.end_date = "present"

                # Calculate duration
                try:
                    start_year = int(exp.start_date)
                    if exp.end_date == "present":
                        end_year = datetime.now().year
                    else:
                        end_year = int(exp.end_date)
                    exp.duration_months = (end_year - start_year) * 12
                except:
                    pass

            # Extract position title (usually after date line)
            if len(lines) >= 3:
                # Position is typically on 3rd line or after dates
                for i, line in enumerate(lines[1:], 1):
                    # Skip date line
                    if re.search(month_date_pattern, line, re.IGNORECASE):
                        continue
                    # Position is next non-date line
                    if len(line) > 3 and not line.isdigit():
                        exp.position = line
                        break

            # Extract technologies mentioned
            tech_matches = self.tech_skills_pattern.findall(entry)
            exp.technologies = list(set(tech_matches))

            # Extract responsibilities (lines starting with bullet points, dashes, or key achievements)
            responsibilities = []
            for line in lines:
                # Match bullet points or achievement-like lines
                if re.match(r'^[-•●▪—–]\s*', line) or any(kw in line.lower() for kw in ['улучшил', 'ускорил', 'создал', 'разработал', 'реализовал', 'настроил']):
                    clean_line = line.lstrip('-•●▪—– ').strip()
                    if len(clean_line) > 10:
                        responsibilities.append(clean_line)

            exp.responsibilities = responsibilities[:10]

            if exp.company != "Unknown" or exp.position != "Unknown":
                experiences.append(exp)

        return experiences[:15]

    def _parse_education_section(self, text: str) -> List[EducationEntry]:
        """Parse education entries"""
        education = []

        entries = re.split(r'\n(?=\d{4}|\w+\s+University|University\s+of|Университет)', text)

        for entry in entries:
            if len(entry.strip()) < 15:
                continue

            edu = EducationEntry(institution="Unknown")

            # Extract degree
            for degree_kw in DEGREE_KEYWORDS:
                if degree_kw.lower() in entry.lower():
                    edu.degree = degree_kw.title()
                    break

            # Extract graduation year
            year_match = re.search(r'\b(19\d{2}|20\d{2})\b', entry)
            if year_match:
                edu.graduation_year = int(year_match.group(1))

            # Extract institution (first meaningful line)
            lines = [l.strip() for l in entry.split('\n') if l.strip()]
            if lines:
                edu.institution = lines[0]

            # Extract field of study
            field_pattern = r'(?:in|major|специальность)[:\s]+([A-Za-zА-Яа-я\s]+)'
            field_match = re.search(field_pattern, entry, re.IGNORECASE)
            if field_match:
                edu.field_of_study = field_match.group(1).strip()

            education.append(edu)

        return education[:5]  # Limit to 5 degrees

    def _parse_certifications_section(self, text: str) -> List[CertificationEntry]:
        """Parse certifications"""
        certifications = []

        lines = [l.strip() for l in text.split('\n') if l.strip()]

        for line in lines:
            if len(line) < 10:
                continue

            cert = CertificationEntry(name=line, issuer="Unknown")

            # Extract issuer
            issuer_pattern = r'(?:by|from|issued by)\s+([A-Za-z\s]+)'
            issuer_match = re.search(issuer_pattern, line, re.IGNORECASE)
            if issuer_match:
                cert.issuer = issuer_match.group(1).strip()
                cert.name = line.replace(issuer_match.group(0), '').strip()

            # Extract date
            date_pattern = r'\b(\d{4})\b'
            date_match = re.search(date_pattern, line)
            if date_match:
                cert.date_obtained = date_match.group(1)

            certifications.append(cert)

        return certifications[:10]

    def _extract_technical_skills(self, text: str) -> List[str]:
        """Extract technical skills from entire resume"""
        matches = self.tech_skills_pattern.findall(text)
        skill_counts = Counter(m.lower() for m in matches)
        # Return skills mentioned at least twice, sorted by frequency
        return [skill for skill, count in skill_counts.most_common(30) if count >= 2]

    def _extract_soft_skills(self, text: str) -> List[str]:
        """Extract soft skills"""
        matches = self.soft_skills_pattern.findall(text)
        skill_counts = Counter(m.lower() for m in matches)
        return [skill for skill, count in skill_counts.most_common(15) if count >= 1]

    def _assess_skills(self, text: str, required_skills: List[str]) -> List[SkillAssessment]:
        """Detailed assessment of specific skills"""
        assessments = []
        text_lower = text.lower()

        for skill in required_skills:
            skill_lower = skill.lower()

            # Count mentions (including aliases)
            mentions = 0
            search_terms = [skill_lower]

            # Add aliases if available
            if skill_lower in SKILL_ALIASES:
                search_terms.extend(SKILL_ALIASES[skill_lower])

            for term in search_terms:
                # Special handling for c++, c#, etc
                if '+' in term or '#' in term:
                    mentions += len(re.findall(re.escape(term), text_lower))
                else:
                    mentions += len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))

            if mentions == 0:
                continue

            # Determine proficiency based on context
            proficiency = "intermediate"
            evidence = []

            # Check for experience indicators
            exp_patterns = [
                (rf'\b(\d+)\+?\s*(?:years?|лет)\s*(?:of\s*)?(?:experience\s+)?(?:with\s+)?{re.escape(skill_lower)}',
                 "expert"),
                (rf'{re.escape(skill_lower)}\s*(?:expert|advanced|proficient|master)', "advanced"),
                (rf'(?:senior|lead|principal).*{re.escape(skill_lower)}', "advanced"),
                (rf'{re.escape(skill_lower)}\s*(?:beginner|learning|basic)', "beginner"),
            ]

            for pattern, level in exp_patterns:
                if re.search(pattern, text_lower):
                    proficiency = level
                    evidence.append(f"Context indicates {level} level")
                    break

            # Fallback: use mention count
            if not evidence:
                if mentions >= 8:
                    proficiency = "advanced"
                    evidence.append(f"Mentioned {mentions} times")
                elif mentions >= 4:
                    proficiency = "intermediate"
                    evidence.append(f"Mentioned {mentions} times")
                else:
                    proficiency = "beginner"
                    evidence.append(f"Mentioned {mentions} times")

            # Extract years if mentioned
            years_pattern = rf'{re.escape(skill_lower)}.*?(\d+)\+?\s*(?:years?|лет)'
            years_match = re.search(years_pattern, text_lower)
            years_exp = float(years_match.group(1)) if years_match else None

            assessments.append(SkillAssessment(
                skill=skill,
                proficiency_level=proficiency,
                years_of_experience=years_exp,
                evidence=evidence,
                mention_count=mentions
            ))

        return assessments

    def _calculate_confidence(self, resume: ParsedResume) -> float:
        """Calculate parsing confidence score"""
        confidence = 0.0

        # Check completeness
        if resume.email:
            confidence += 0.15
        if resume.phone:
            confidence += 0.1
        if resume.full_name:
            confidence += 0.1

        if len(resume.experience) > 0:
            confidence += 0.25
        if len(resume.education) > 0:
            confidence += 0.15

        if len(resume.skills) > 0:
            confidence += 0.15
        if len(resume.technical_skills) > 0:
            confidence += 0.1

        return min(1.0, confidence)


def parse_resume_advanced(resume_text: str, required_skills: Optional[List[str]] = None) -> Dict:
    """
    Convenience function to parse resume

    Args:
        resume_text: Raw resume text
        required_skills: Skills to analyze

    Returns:
        Parsed resume as dict
    """
    parser = AdvancedResumeParser()
    result = parser.parse_resume(resume_text, required_skills)
    return result.model_dump()


def batch_parse_resumes_advanced(
    resumes: List[Dict[str, str]],
    required_skills: Optional[List[str]] = None
) -> List[Dict]:
    """
    Parse multiple resumes (synchronous, no API calls needed!)

    Args:
        resumes: List of dicts with 'text' and optional 'id'
        required_skills: Skills to analyze

    Returns:
        List of parsed resumes
    """
    parser = AdvancedResumeParser()
    results = []

    for resume_data in resumes:
        resume_text = resume_data.get("text", "")
        parsed = parser.parse_resume(resume_text, required_skills)
        result_dict = parsed.model_dump()
        result_dict["resume_id"] = resume_data.get("id", "unknown")
        results.append(result_dict)

    return results
