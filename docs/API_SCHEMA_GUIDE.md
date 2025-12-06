# HR API Schema Guide

## HRRunRequest - Полная спецификация вакансии

### Core Position Info
```json
{
  "role": "Senior Backend Python Developer",
  "job_description": "Полное описание вакансии для контекстного анализа"
}
```

### Location & Format
```json
{
  "location": "1",  // HH.ru area ID или название города
  "work_format": "hybrid",  // remote | office | hybrid
  "relocation_provided": true
}
```

### Skills & Requirements
```json
{
  "skills": ["python", "fastapi", "postgresql"],  // Обязательные
  "nice_to_have_skills": ["graphql", "kafka"],    // Желательные (не блокирующие)
  "seniority_level": "senior",  // junior | middle | senior | lead
  "min_years_experience": 5
}
```

### Compensation & Benefits
```json
{
  "salary_from": 250000,
  "salary_to": 400000,
  "salary_currency": "RUB",
  "benefits": [
    "ДМС для сотрудника и семьи",
    "Оплата обучения и конференций"
  ]
}
```

### Company Info
```json
{
  "company_name": "TechCorp",
  "company_size": "medium",  // startup | small | medium | large | enterprise
  "company_industry": "FinTech",
  "team_size": 12
}
```

### Employment Details
```json
{
  "employment_type": "full_time",  // full_time | part_time | contract | internship
  "project_type": "product"         // product | outsource | consulting
}
```

### Languages & Certifications
```json
{
  "required_languages": [
    {"language": "russian", "level": "native"},
    {"language": "english", "level": "B2"}
  ],
  "required_certifications": ["AWS Certified"]
}
```

### Process Info
```json
{
  "interview_stages": 4,
  "decision_deadline": "2025-01-15",
  "vacancy_priority": "urgent",  // urgent | normal | low
  "hiring_manager": "Иван Петров"
}
```

### Market Analysis Settings
```json
{
  "per_page": 20,
  "mandatory_threshold": 0.7,  // >70% частоты = mandatory
  "preferred_threshold": 0.3   // 30-70% = preferred
}
```

## CandidateInput - Полная информация о кандидате

### Identity & Contacts
```json
{
  "github_username": "donnemartin",
  "full_name": "Donne Martin",
  "email": "donne@example.com",
  "phone": "+7 999 345-67-89",
  "linkedin_url": "https://linkedin.com/in/donnemartin",
  "portfolio_url": "https://donnemartin.com"
}
```

### Resume & Skills
```json
{
  "resume_text": "Полный текст резюме для keyword matching и анализа",
  "current_position": "Senior Backend Engineer at Meta",
  "years_of_experience": 8
}
```

### Technical Analysis
```json
{
  "lookback_days": 90,     // Анализ активности за последние N дней
  "repos_limit": 20        // Сколько репозиториев анализировать
}
```

### Expectations & Availability
```json
{
  "expected_salary_from": 280000,
  "expected_salary_to": 380000,
  "current_location": "Москва",
  "relocation_willing": true,
  "remote_willing": true,
  "availability_date": "2025-01-20",
  "notice_period_days": 14
}
```

### Languages & Certifications
```json
{
  "english_level": "C1",  // A1 | A2 | B1 | B2 | C1 | C2 | native
  "other_languages": ["russian"],
  "certifications": [
    "AWS Certified Solutions Architect",
    "Kubernetes Administrator (CKA)"
  ]
}
```

### Background
```json
{
  "education": "BS Computer Science, Stanford University",
  "previous_companies": ["Facebook", "Amazon", "Startup.io"]
}
```

### Source & Status
```json
{
  "source": "job_board",  // referral | job_board | linkedin | headhunt | etc
  "current_status": "new",  // new | screening | interview | offer | rejected
  "notes": "Strong technical profile with modern stack"
}
```

## Как это влияет на скоринг

### 1. Salary Match
Если `expected_salary_to < salary_from` вакансии:
- **Risk flag**: "salary_expectations_mismatch"
- **Recommendation**: "Adjust offer or discuss compensation"

### 2. Experience Match
Если `years_of_experience < min_years_experience`:
- **Penalty**: -15 points
- **Decision**: Downgrade to "hold" or "no"

### 3. Location Match
Если `current_location != location` и `relocation_willing = false` и `remote_willing = false`:
- **Auto reject**: "Location mismatch, not willing to relocate or work remote"

### 4. Language Requirements
Если кандидат не соответствует `required_languages`:
- **Risk flag**: "language_requirements_not_met"
- **Blocking** если указан mandatory

### 5. Availability
Если `availability_date > decision_deadline`:
- **Risk flag**: "availability_conflict"
- **Note**: "Candidate available after deadline"

### 6. Certifications
Если missing `required_certifications`:
- **Risk flag**: "missing_certifications"
- **Blocking** если critical для роли

## Пример использования

### Минимальный запрос (как раньше)
```json
{
  "role": "Python Developer",
  "skills": ["python", "fastapi"],
  "candidates": [
    {
      "github_username": "torvalds"
    }
  ]
}
```

### Полный enterprise запрос
```json
{
  "role": "Senior Backend Python Developer",
  "job_description": "...",
  "location": "1",
  "work_format": "hybrid",
  "skills": ["python", "fastapi", "postgresql", "docker"],
  "nice_to_have_skills": ["kafka", "graphql"],
  "seniority_level": "senior",
  "min_years_experience": 5,
  "salary_from": 250000,
  "salary_to": 400000,
  "company_name": "TechCorp",
  "company_size": "medium",
  "required_languages": [
    {"language": "english", "level": "B2"}
  ],
  "interview_stages": 4,
  "vacancy_priority": "urgent",
  "candidates": [
    {
      "github_username": "donnemartin",
      "full_name": "Donne Martin",
      "email": "donne@example.com",
      "resume_text": "...",
      "years_of_experience": 8,
      "expected_salary_from": 280000,
      "expected_salary_to": 380000,
      "current_location": "Москва",
      "english_level": "C1",
      "certifications": ["AWS Certified"]
    }
  ]
}
```

## Тест с полными данными

```bash
# Запустить с полным JSON
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | jq . > result_full.json

# Проверить что учитывается все
jq '.report.candidate_scores[0]' result_full.json
```

Теперь система может:
- ✅ Полностью заменить HR специалиста
- ✅ Учитывать все факторы принятия решения
- ✅ Давать обоснованные рекомендации
- ✅ Автоматически фильтровать по множеству критериев
