from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CandidateInput(BaseModel):
    # Identity & Contacts
    github_username: str = Field(..., description="GitHub логин кандидата")
    full_name: Optional[str] = Field(None, description="Полное имя кандидата")
    email: Optional[str] = Field(None, description="Email для связи")
    phone: Optional[str] = Field(None, description="Телефон")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn профиль")
    portfolio_url: Optional[str] = Field(None, description="Портфолио/личный сайт")

    # Resume & Skills
    resume_text: Optional[str] = Field(None, description="Полный текст резюме")
    current_position: Optional[str] = Field(None, description="Текущая должность")
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="Общий опыт работы в годах")

    # Technical Analysis
    lookback_days: Optional[int] = Field(
        None, ge=1, description="Фильтр по последней активности в репозиториях за N дней"
    )
    repos_limit: int = Field(5, ge=1, le=30, description="Сколько репозиториев анализировать")

    # Expectations & Availability
    expected_salary_from: Optional[int] = Field(None, ge=0, description="Ожидаемая зарплата от, ₽")
    expected_salary_to: Optional[int] = Field(None, ge=0, description="Ожидаемая зарплата до, ₽")
    current_location: Optional[str] = Field(None, description="Текущее местоположение")
    relocation_willing: Optional[bool] = Field(None, description="Готовность к релокации")
    remote_willing: Optional[bool] = Field(True, description="Готовность к удаленке")
    availability_date: Optional[str] = Field(None, description="Дата готовности начать (YYYY-MM-DD)")
    notice_period_days: Optional[int] = Field(None, ge=0, description="Срок уведомления на текущей работе (дни)")

    # Languages & Certifications
    english_level: Optional[str] = Field(None, description="Уровень английского: A1/A2/B1/B2/C1/C2/native")
    other_languages: Optional[List[str]] = Field(default_factory=list, description="Другие языки")
    certifications: Optional[List[str]] = Field(default_factory=list, description="Сертификаты")

    # Background
    education: Optional[str] = Field(None, description="Образование")
    previous_companies: Optional[List[str]] = Field(default_factory=list, description="Предыдущие компании")

    # Source & Status
    source: Optional[str] = Field(None, description="Источник кандидата: referral/job_board/linkedin/etc")
    current_status: Optional[str] = Field("new", description="Статус: new/screening/interview/offer/rejected")
    notes: Optional[str] = Field(None, description="Дополнительные заметки")


class HRRunRequest(BaseModel):
    # Core Position Info
    role: str = Field(..., description="Название роли/позиции")
    job_description: Optional[str] = Field(None, description="Полное описание вакансии")

    # Location & Format
    location: Optional[str] = Field(None, description="Регион/город или HH area id")
    work_format: Optional[str] = Field("hybrid", description="Формат работы: remote/office/hybrid")
    relocation_provided: Optional[bool] = Field(False, description="Предоставляется релокация")

    # Skills & Requirements
    skills: List[str] = Field(default_factory=list, description="Обязательные навыки/стек")
    nice_to_have_skills: Optional[List[str]] = Field(default_factory=list, description="Желательные навыки")
    seniority_level: Optional[str] = Field(None, description="Уровень: junior/middle/senior/lead")
    min_years_experience: Optional[int] = Field(None, ge=0, description="Минимальный опыт в годах")

    # Compensation & Benefits
    salary_from: Optional[int] = Field(None, ge=0, description="Минимальная зарплата, ₽")
    salary_to: Optional[int] = Field(None, ge=0, description="Максимальная зарплата, ₽")
    salary_currency: Optional[str] = Field("RUB", description="Валюта зарплаты")
    benefits: Optional[List[str]] = Field(default_factory=list, description="Бенефиты: ДМС, обучение, etc")

    # Company Info
    company_name: Optional[str] = Field(None, description="Название компании")
    company_size: Optional[str] = Field(None, description="Размер: startup/small/medium/large/enterprise")
    company_industry: Optional[str] = Field(None, description="Индустрия компании")
    team_size: Optional[int] = Field(None, ge=1, description="Размер команды")

    # Employment Details
    employment_type: Optional[str] = Field("full_time", description="Тип: full_time/part_time/contract/internship")
    project_type: Optional[str] = Field(None, description="Тип проектов: product/outsource/consulting")

    # Languages & Certifications
    required_languages: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="Требования к языкам: [{'language': 'english', 'level': 'B2'}]"
    )
    required_certifications: Optional[List[str]] = Field(default_factory=list, description="Обязательные сертификаты")

    # Process Info
    interview_stages: Optional[int] = Field(3, ge=1, le=10, description="Количество этапов интервью")
    decision_deadline: Optional[str] = Field(None, description="Дедлайн принятия решения (YYYY-MM-DD)")
    vacancy_priority: Optional[str] = Field("normal", description="Приоритет: urgent/normal/low")
    hiring_manager: Optional[str] = Field(None, description="Имя hiring manager")

    # Market Analysis Settings
    per_page: int = Field(10, ge=1, le=50, description="Количество вакансий в выдаче для анализа рынка")
    mandatory_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Порог для mandatory skills (0-1)")
    preferred_threshold: Optional[float] = Field(0.3, ge=0.0, le=1.0, description="Порог для preferred skills (0-1)")

    # Candidates
    candidates: List[CandidateInput] = Field(default_factory=list, description="Список кандидатов")


class MarketResult(BaseModel):
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CandidateResult(BaseModel):
    github_username: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SalaryStats(BaseModel):
    count: int
    minimum: Optional[float]
    maximum: Optional[float]
    median: Optional[float]
    p25: Optional[float]
    p75: Optional[float]
    currency: Optional[str] = None


class TopSkill(BaseModel):
    skill: str
    count: int


class MarketSummary(BaseModel):
    total_found: int
    salary_stats: Optional[SalaryStats] = None
    top_skills: List[TopSkill] = Field(default_factory=list)
    source: str = "hh.ru"


class ActivityMetrics(BaseModel):
    days_since_last_push: Optional[int] = None
    commit_frequency_score: int = Field(0, ge=0, le=100)
    total_stars: int = 0
    total_forks: int = 0
    repo_diversity_score: int = Field(0, ge=0, le=100)
    one_commit_repos_count: int = 0


class RequirementMatch(BaseModel):
    mandatory_coverage: float = Field(0, description="% coverage of mandatory skills")
    preferred_coverage: float = Field(0, description="% coverage of preferred skills")
    overall_coverage: float = Field(0, description="Weighted overall coverage")
    mandatory_matched: List[str] = Field(default_factory=list)
    mandatory_missing: List[str] = Field(default_factory=list)
    preferred_matched: List[str] = Field(default_factory=list)
    preferred_missing: List[str] = Field(default_factory=list)


class CandidateScore(BaseModel):
    github_username: str
    score: int = Field(..., ge=0, le=100)
    decision: str = Field(..., description="go | hold | no")
    decision_reasons: List[str] = Field(default_factory=list, description="Top 3 reasons for decision")
    match_score: int = Field(..., ge=0, le=100, description="Скор по навыкам и соответствию требованиям")
    activity_score: int = Field(..., ge=0, le=100, description="Активность и свежесть репозиториев")
    risk_penalty: int = Field(..., ge=0, le=100, description="Штрафы за риски/отсутствие данных")
    skill_gaps: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    repos_analyzed: int = 0
    top_languages: List[str] = Field(default_factory=list)
    evidence: Dict[str, str] = Field(default_factory=dict)
    activity_metrics: Optional[ActivityMetrics] = None
    resume_match_score: Optional[float] = None
    linkedin_data: Optional[Dict[str, Any]] = None
    requirement_match: Optional[RequirementMatch] = None


class ShortlistCandidate(BaseModel):
    github_username: str
    score: int
    decision: str
    top_reasons: List[str] = Field(default_factory=list)


class InterviewSupport(BaseModel):
    questions: Dict[str, List[str]] = Field(default_factory=dict)
    checklist: List[Dict[str, str]] = Field(default_factory=list)
    coding_tasks: List[Dict[str, str]] = Field(default_factory=list)


class HRRecommendations(BaseModel):
    shortlist: List[ShortlistCandidate] = Field(default_factory=list)
    interview_next: List[str] = Field(default_factory=list, description="Кого звать на интервью")
    skills_to_train: List[str] = Field(default_factory=list, description="Навыки, которые можно доучить")
    risks: List[str] = Field(default_factory=list)
    competitive_offer_range: Optional[Dict[str, float]] = None


class MarketInsights(BaseModel):
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)
    top_locations: List[Dict[str, Any]] = Field(default_factory=list)
    supply_demand: Optional[Dict[str, Any]] = None
    salary_ranges_by_skill: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class SkillClassificationReport(BaseModel):
    mandatory_skills: List[Dict[str, Any]] = Field(default_factory=list)
    preferred_skills: List[Dict[str, Any]] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    methodology: Dict[str, Any] = Field(default_factory=dict)


class HRReport(BaseModel):
    role: str
    skills: List[str]
    market_summary: Optional[MarketSummary] = None
    market_insights: Optional[MarketInsights] = None
    candidate_scores: List[CandidateScore] = Field(default_factory=list)
    recommendations: Optional[HRRecommendations] = None
    skill_classification_report: Optional[SkillClassificationReport] = None
    summary: Optional[str] = Field(default=None, description="Человекочитаемая выжимка отчёта")


class HRRunResponse(BaseModel):
    market: MarketResult
    candidates: List[CandidateResult]
    report: Optional[HRReport] = None
    processing_time_ms: int = Field(0, description="Время обработки запроса в миллисекундах")
    cache_stats: Optional[Dict[str, int]] = Field(default=None, description="Статистика кэша (hits/misses)")
