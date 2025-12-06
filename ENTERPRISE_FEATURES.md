

## Реализованные улучшения
**Файл:** `ml/mcp_server/tools/github_tools_advanced.py`

**Что улучшили:**
- Анализ файлов зависимостей (requirements.txt, package.json, go.mod, Cargo.toml)
- Анализ импортов в коде (Python, JavaScript, Go и др.)
- Детекция фреймворков (FastAPI, Django, React, Vue, Angular, Docker, Kubernetes)
- Взвешенная оценка с учетом:
  - Dependency count (вес 0.3)
  - Import statements (вес 0.2)
  - Framework files (вес 0.15)
  - Popularity (stars, forks)
  - Recency (последняя активность)
- Confidence score для каждого навыка (low/medium/high/very_high)
- Подробные источники доказательств

**Пример использования:**
```python
# MCP tool
await ml_client.call_mcp_tool("analyze_github_advanced", {
    "username": "torvalds",
    "required_skills": ["c", "python", "linux"],
    "repos_limit": 20,
    "analyze_code": True,
    "analyze_dependencies": True
})
```

**Результат:**
```json
{
  "skill_scores": [
    {
      "skill": "python",
      "score": 0.85,
      "confidence": "very_high",
      "evidence": "5 dependency refs; 8 import statements; language match",
      "dependency_count": 5,
      "import_count": 8,
      "file_count": 3
    }
  ],
  "code_analysis": {
    "total_files_scanned": 45,
    "dependency_files_found": 12,
    "imports_analyzed": 23,
    "frameworks_detected": ["fastapi", "docker", "postgresql"],
    "confidence_score": 0.92
  }
}
```

---

**Файл:** `ml/mcp_server/tools/linkedin_tools.py`

**Возможности:**
- Real LinkedIn API через Proxycurl (если API key настроен)
- Fallback на web scraping (mock данные для демо)
- Batch analysis (до 20 профилей параллельно)

**Извлекаемые данные:**
- Skills и endorsements
- Work experience с duration
- Education background
- Certifications
- Recommendations count
- Activity metrics

**Пример:**
```python
await ml_client.call_mcp_tool("analyze_linkedin", {
    "linkedin_url": "https://linkedin.com/in/username",
    "extract_skills": True,
    "extract_experience": True
})
```

---

**Файл:** `backend/services/advanced_resume_parser.py`

**Использует:**
- Regex patterns
- NLP heuristics
- Section detection
- Entity extraction

**Извлекает:**
- Personal info (email, phone, LinkedIn, GitHub)
- Professional summary
- Work experience (company, position, dates, responsibilities)
- Education (institution, degree, year)
- Skills assessment (proficiency levels)
- Certifications
- Languages

**Parsing confidence: 60-95%** (зависит от формата резюме)

**Пример:**
```python
from backend.services.advanced_resume_parser import parse_resume_advanced

result = parse_resume_advanced(resume_text, required_skills=["python", "docker"])
# Returns ParsedResume object with all extracted data
```

---
**Файлы:**
- `backend/services/batch_processor.py`
- `backend/api/v1/batch.py`

**Возможности:**
- Массовая обработка кандидатов (до 100 за раз)
- Параллельное выполнение с контролем concurrency (1-20 потоков)
- Proress tracking в реальном времени
- Estimated time remaining
- Timeout per candidate
- Background processing
- Job cancellation

**API Endpoints:**
- `POST /api/v1/batch/submit` - Создать batch job
- `GET /api/v1/batch/status/{job_id}` - Статус job
- `GET /api/v1/batch/results/{job_id}` - Результаты
- `DELETE /api/v1/batch/cancel/{job_id}` - Отменить job
- `GET /api/v1/batch/stats` - Общая статистика

**Пример:**
```bash
curl -X POST http://localhost:8005/api/v1/batch/submit \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Backend Developer",
    "skills": ["python", "fastapi"],
    "candidates": [
      {"github_username": "user1"},
      {"github_username": "user2"}
    ],
    "concurrency": 10
  }'

# Response:
{
  "job_id": "abc123",
  "status": "processing",
  "total_candidates": 2
}

# Check progress:
curl http://localhost:8005/api/v1/batch/status/abc123

# Response:
{
  "job_id": "abc123",
  "status": "processing",
  "processed": 1,
  "total_candidates": 2,
  "progress_percent": 50.0,
  "estimated_time_remaining_seconds": 15.2
}
```

---
Файл:** `backend/services/advanced_market_analytics.py`

**Новые функции:**

#### Trend Analysis
```python
trends = analytics.analyze_trends(current_market_data, historical_data, skills)
# Returns:
# - Demand change % для каждого навыка
# - Trend direction (rising/stable/declining)
# - Popularity score (0-100)
```

#### Salary Forecasting
```python
forecasts = analytics.forecast_salaries(market_data, role, skills)
# Returns:
# - Current median
# - 3/6/12-month forecasts
# - Growth rate %
# - Confidence level
```

#### Competitive Analysis
```python
competition = analytics.analyze_competition(market_data, role, candidate_count)
# Returns:
# - Competition ratio (openings per candidate)
# - Difficulty score (0-100)
# - Estimated time to hire (days)
# - Salary percentiles (p10, p25, p50, p75, p90)
```

#### Skill Demand Forecasting
```python
demand_forecast = analytics.forecast_skill_demand(market_data, skills)
# Returns:
# - Projected growth 6/12 months
# - Demand level (low/medium/high/very_high)
# - Emerging skill flag
```

---

### 6. **StackOverflow Integration**
**Файл:** `ml/mcp_server/tools/stackoverflow_tools.py`

**Метрики:**
- Reputation и reputation level
- Answer/question counts
- Acceptance rate
- Activity score (0-100)
- Top tags (expertise areas)
- Badges (gold/silver/bronze)
- Recent answers и questions

**API:**
- `analyze_stackoverflow` - Один профиль
- `batch_analyze_stackoverflow` - До 20 профилей

**Пример:**
```python
result = await ml_client.call_mcp_tool("analyze_stackoverflow", {
    "user_id": 22656,  # Jon Skeet
    "include_posts": True
})
```

---

**Файл:** `backend/services/job_description_generator.py`

**Template-based с умной кастомизацией.**

**Генерирует:**
- Job title (с учетом seniority)
- Company overview
- Responsibilities (7-10 пунктов)
- Requirements (technical + soft skills)
- Nice-to-have qualifications
- Benefits (10+ пунктов)
- Application process
- SEO keywords

**Адаптируется под:**
- Experience level (junior/middle/senior/lead)
- Role type (backend/frontend/fullstack/devops/data/ml)
- Market data (competitive salary, high demand)

**Пример:**
```python
from backend.services.job_description_generator import generate_job_description

jd = generate_job_description(JobDescriptionRequest(
    role="Senior Backend Developer",
    company_name="TechCorp",
    location="Remote",
    required_skills=["python", "fastapi", "postgresql"],
    nice_to_have_skills=["kubernetes", "redis"],
    experience_level="senior",
    salary_range={"from": 200000, "to": 300000, "currency": "RUB"}
))

# Экспорт в Markdown
from backend.services.job_description_generator import format_job_description_markdown
markdown = format_job_description_markdown(jd)
```

---

**Файл:** `backend/services/predictive_analytics.py`

**Чистая статистика и heuristics.**

#### Offer Acceptance Prediction
```python
prediction = analytics.predict_offer_acceptance(
    candidate_score=85,
    salary_offered=250000,
    market_median_salary=200000,
    has_competing_offers=True
)
# Returns:
# - probability_accept: 0.75
# - probability_reject: 0.25
# - key_factors: ["Salary 25% above market", "Has competing offers"]
# - recommendation: "Strong probability..."
# - risk_level: "low"
```

#### Time to Hire Prediction
```python
prediction = analytics.predict_time_to_hire(
    role="Senior Python Developer",
    required_skills=["python", "kubernetes"],
    market_competition_level="high"
)
# Returns:
# - estimated_days: 45
# - confidence_interval: (36, 54)
# - factors_affecting: [...]
```

#### Attrition Risk Prediction
```python
risk = analytics.predict_attrition_risk(
    tenure_at_previous_company_months=[18, 24, 12],
    total_jobs_count=4,
    salary_vs_market=0.95
)
# Returns:
# - attrition_risk_score: 0.45 (0-1)
# - risk_level: "medium"
# - risk_factors: ["Short average tenure"]
# - retention_recommendations: [...]
```

#### Salary Negotiation Prediction
```python
negotiation = analytics.predict_salary_negotiation(
    initial_offer=200000,
    market_median=180000,
    candidate_experience_years=7
)
# Returns:
# - likely_counter_offer: 230000
# - negotiation_probability: 0.65
# - acceptable_range: (200000, 198000)
# - negotiation_strategy: "..."
```

---

**Файл:** `backend/services/ab_testing.py`

**Возможности:**
- Тестирование разных scoring алгоритмов
- Traffic splitting (consistent hashing)
- Real-time performance tracking
- Statistical significance calculation
- Automatic winner detection

**Метрики:**
- Average score
- Success rate (% "go" decisions)
- Score variance
- False positive/negative rates (если есть ground truth)

**Пример:**
```python
from backend.services.ab_testing import ab_testing_framework

# Создать эксперимент
experiment_id = ab_testing_framework.create_experiment(
    name="Scoring Model v2",
    description="Test new GitHub code analysis weight",
    variants=["baseline", "variant_a", "variant_b"],
    traffic_split={"baseline": 0.5, "variant_a": 0.25, "variant_b": 0.25}
)

# Зарегистрировать варианты
ab_testing_framework.register_variant("baseline", baseline_scoring_function)
ab_testing_framework.register_variant("variant_a", variant_a_scoring_function)

# Стартовать
ab_testing_framework.start_experiment(experiment_id)

# Скорить кандидата
variant, score = ab_testing_framework.score_candidate_with_variant(
    experiment_id, "candidate123", candidate_data
)

# Анализ результатов (после N кандидатов)
results = ab_testing_framework.analyze_experiment(experiment_id)
# Returns: Winner variant, statistical significance, metrics
```

---

**Файл:** `backend/services/candidate_recommendations.py`

**Алгоритмы:**
- Content-based filtering (по навыкам)
- Collaborative filtering (по активности)
- Hybrid approach (weighted combination)

**Similarity metrics:**
- Jaccard similarity (для skills)
- Cosine similarity (для векторов)
- Activity pattern matching

**API:**
```python
# Найти похожих кандидатов
similar = engine.find_similar_candidates(
    candidate_id="user1",
    top_n=10,
    algorithm="hybrid"  # content / collaborative / hybrid
)

# Рекомендовать для роли
recommendations = engine.recommend_for_role(
    required_skills=["python", "docker"],
    nice_to_have_skills=["kubernetes"],
    top_n=10
)
```

**Результат:**
```json
{
  "recommendations": [
    {
      "candidate_id": "user2",
      "similarity_score": 0.87,
      "matching_skills": ["python", "docker", "postgresql"],
      "matching_reasons": [
        "Shares 8 skills: python, docker, postgresql",
        "Similar overall scores (85 vs 82)",
        "Highly similar profiles"
      ],
      "profile_url": "https://github.com/user2"
    }
  ]
}
```

---

**Файл:** `backend/services/metrics.py`

**Metrics:**

#### API Metrics
- `hr_api_requests_total` - Total requests
- `hr_api_errors_total` - Total errors
- `hr_api_request_duration_seconds` - Request latency histogram

#### Candidate Metrics
- `hr_candidates_analyzed_total` - Total analyzed
- `hr_candidates_accepted_total` - "Go" decisions
- `hr_candidates_rejected_total` - "No" decisions
- `hr_candidate_scores` - Score distribution histogram
- `hr_average_candidate_score` - Average score gauge

#### GitHub Metrics
- `hr_github_api_calls_total` - API calls
- `hr_github_rate_limits_total` - Rate limit hits
- `hr_github_analysis_duration_seconds` - Analysis time

#### Cache Metrics
- `hr_cache_hits_total` - Cache hits
- `hr_cache_misses_total` - Cache misses
- `hr_cache_hit_rate` - Hit rate %

#### Batch Metrics
- `hr_batch_jobs_active` - Active jobs
- `hr_batch_jobs_completed_total` - Completed jobs
- `hr_batch_job_duration_seconds` - Job duration

**Endpoints:**
```bash
# Prometheus scrape endpoint
GET /metrics

# Summary stats
GET /api/v1/metrics/stats
```

**Example Prometheus config:**
```yaml
scrape_configs:
  - job_name: 'hr-system'
    static_configs:
      - targets: ['localhost:8005']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

**Performance monitoring decorator:**
```python
from backend.services.metrics import PerformanceMonitor

async def analyze_candidate(data):
    with PerformanceMonitor("hr_github_analysis_duration_seconds"):
        # ... analysis code
        pass
```

---
**Файл:** `backend/services/feedback_loop.py`

**Собирает feedback:**
- Scoring accuracy (правильно ли оценили?)
- Hire outcomes (наняли или нет?)
- Interview performance
- Model suggestions

**Анализирует:**
- Scoring accuracy rate
- False positive rate
- False negative rate
- Hire prediction accuracy
- Average score deviation

**Автоматически генерирует:**
- Recommendations для улучшения
- Model adjustments (изменения параметров)

**API:**
```python
from backend.services.feedback_loop import feedback_loop

# Submit feedback
feedback_loop.submit_feedback(
    candidate_id="user1",
    original_score=75,
    original_decision="go",
    feedback_type=FeedbackType.HIRE_OUTCOME,
    actual_outcome=HireOutcome.HIRED,
    role="Backend Developer"
)

# Analyze (автоматически каждые 50 feedback entries)
analytics = feedback_loop.analyze_feedback()
# Returns:
# - scoring_accuracy_rate: 0.82
# - false_positive_rate: 0.15
# - recommended_adjustments: ["Increase 'go' threshold by 5 points"]

# Apply adjustments
pending = feedback_loop.get_pending_adjustments()
for adj in pending:
    feedback_loop.apply_adjustment(adj.adjustment_id)
```

---

## Как использовать все фичи

### 1. Полный анализ кандидата
```python
# Advanced GitHub analysis
github_data = await ml_client.call_mcp_tool("analyze_github_advanced", {
    "username": "candidate",
    "required_skills": ["python", "fastapi", "postgresql"],
    "repos_limit": 20,
    "analyze_code": True,
    "analyze_dependencies": True
})

# LinkedIn analysis
linkedin_data = await ml_client.call_mcp_tool("analyze_linkedin", {
    "linkedin_url": "https://linkedin.com/in/candidate"
})

# StackOverflow analysis
so_data = await ml_client.call_mcp_tool("analyze_stackoverflow", {
    "username": "candidate"
})

# Resume parsing
from backend.services.advanced_resume_parser import parse_resume_advanced
resume_data = parse_resume_advanced(resume_text, required_skills)

# Combine все данные для comprehensive profile
```

### 2. Batch processing множества кандидатов
```bash
POST /api/v1/batch/submit
{
  "role": "Senior Backend Developer",
  "skills": ["python", "fastapi", "postgresql", "docker"],
  "nice_to_have_skills": ["kubernetes", "redis"],
  "candidates": [
    {"github_username": "user1", "linkedin_url": "...", "resume_text": "..."},
    {"github_username": "user2", ...},
    ...
  ],
  "concurrency": 10,
  "timeout_per_candidate": 120
}
```

### 3. Market analysis с прогнозами
```python
from backend.services.advanced_market_analytics import AdvancedMarketAnalytics

analytics = AdvancedMarketAnalytics()

# Trends
trends = analytics.analyze_trends(current_market, historical_data, skills)

# Salary forecasts
forecasts = analytics.forecast_salaries(market_data, role, skills)

# Competition
competition = analytics.analyze_competition(market_data, role, candidates)

# Skill demand
demand = analytics.forecast_skill_demand(market_data, skills)
```

### 4. Predictive analytics для hiring decisions
```python
from backend.services.predictive_analytics import predict_hiring_outcomes

predictions = predict_hiring_outcomes(
    candidate_id="user1",
    candidate_data={
        "score": 85,
        "experience_years": 7,
        "has_competing_offers": True
    },
    market_data={
        "median_salary": 200000,
        "role": "Senior Backend Developer"
    },
    offer_details={
        "salary": 250000
    }
)

# Returns:
# - offer_acceptance: probability, key factors, recommendation
# - salary_negotiation: likely counter, strategy
# - time_to_hire: estimated days
# - attrition_risk: risk score, retention tips
```

### 5. Job description generation
```python
from backend.services.job_description_generator import generate_job_description

jd = generate_job_description(JobDescriptionRequest(
    role="Senior Backend Developer",
    company_name="TechCorp",
    required_skills=["python", "fastapi", "postgresql"],
    experience_level="senior",
    market_data=market_insights  # Для competitive benefits
))
```

### 6. Мониторинг системы
```python
from backend.services.metrics import metrics

# Track metrics
metrics.inc_counter("hr_candidates_analyzed_total")
metrics.observe_histogram("hr_candidate_scores", score)
metrics.set_gauge("hr_batch_jobs_active", active_count)

# Get stats
stats = metrics.get_summary_stats()
# {
#   "total_candidates_analyzed": 1523,
#   "cache_hit_rate": 78.5,
#   "average_candidate_score": 72.3,
#   "acceptance_rate": 35.2
# }

# Prometheus export
prometheus_metrics = metrics.export_prometheus_format()
```

### 7. Continuous improvement с feedback
```python
from backend.services.feedback_loop import feedback_loop

# Submit hire outcome
feedback_loop.submit_feedback(
    candidate_id="user1",
    original_score=75,
    original_decision="go",
    actual_outcome=HireOutcome.HIRED,
    interview_score=4.5,
    role="Backend Developer"
)

# Auto-analysis и recommendations
analytics = feedback_loop.analyze_feedback()

# Apply improvements
for adjustment in feedback_loop.get_pending_adjustments():
    feedback_loop.apply_adjustment(adjustment.adjustment_id)
```

---

## Deployment

### Docker Compose
```yaml
services:
  backend:
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}  # Для GitHub API (5000 req/hour)
      - PROXYCURL_API_KEY=${PROXYCURL_API_KEY}  # Optional для LinkedIn
      - REDIS_HOST=redis

  redis:
    image: redis:7-alpine

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
```
