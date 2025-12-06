
## Новые файлы

### MCP Tools (ml/mcp_server/tools/)
```
github_tools_advanced.py - Advanced GitHub analysis
linkedin_tools.py - LinkedIn integration
stackoverflow_tools.py - StackOverflow analysis
```

### Backend Services (backend/services/)
```
advanced_resume_parser.py - Resume parsing БЕЗ LLM
batch_processor.py - Batch processing engine
advanced_market_analytics.py - Trends & forecasting
job_description_generator.py - JD generation
predictive_analytics.py - Predictions
ab_testing.py - A/B testing framework
candidate_recommendations.py - Recommendation system
metrics.py - Prometheus metrics
 feedback_loop.py - Feedback system
```

### API Endpoints (backend/api/v1/)
```
 batch.py - Batch processing API
```

---

## 🔧 Установка

### 1. Опциональные API ключи (для максимальной функциональности)

```bash
# .env file
GITHUB_TOKEN=your_github_token  # Увеличивает rate limit до 5000 req/hour
PROXYCURL_API_KEY=your_key  # Для real LinkedIn API (опционально)
```

### 2. Запуск

```bash
# Запустить все сервисы
docker-compose up

# Или локально
poetry install
poetry run uvicorn backend.main:app --reload --port 8005
```

---

## Быстрые примеры

### 1. Advanced GitHub Analysis

```bash
curl -X POST http://localhost:8005/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_github_advanced",
    "parameters": {
      "username": "torvalds",
      "required_skills": ["c", "python", "linux"],
      "repos_limit": 20,
      "analyze_code": true,
      "analyze_dependencies": true
    }
  }'
```

**Результат включает:**
- Dependency analysis (requirements.txt, package.json, etc)
- Import statements detection
- Framework detection
- Weighted confidence scores
- Code analysis metrics

### 2. Batch Processing

```bash
curl -X POST http://localhost:8005/api/v1/batch/submit \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Senior Backend Developer",
    "skills": ["python", "fastapi", "postgresql", "docker"],
    "nice_to_have_skills": ["kubernetes", "redis"],
    "candidates": [
      {"github_username": "donnemartin", "repos_limit": 20},
      {"github_username": "gvanrossum", "repos_limit": 15},
      {"github_username": "torvalds", "repos_limit": 10}
    ],
    "concurrency": 5,
    "timeout_per_candidate": 120
  }'

# Response:
{
  "job_id": "abc123",
  "status": "processing",
  "message": "Batch job submitted successfully",
  "total_candidates": 3
}

# Check progress:
curl http://localhost:8005/api/v1/batch/status/abc123

# Get results:
curl http://localhost:8005/api/v1/batch/results/abc123
```

### 3. LinkedIn Analysis

```bash
curl -X POST http://localhost:8005/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_linkedin",
    "parameters": {
      "linkedin_url": "https://linkedin.com/in/username",
      "extract_skills": true,
      "extract_experience": true,
      "extract_education": true
    }
  }'
```

### 4. StackOverflow Analysis

```bash
curl -X POST http://localhost:8005/api/v1/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "analyze_stackoverflow",
    "parameters": {
      "user_id": 22656,
      "include_posts": true,
      "include_tags": true
    }
  }'
```

### 5. Resume Parsing 

```python
from backend.services.advanced_resume_parser import parse_resume_advanced

resume_text = """
John Doe
john@example.com
+7 (999) 123-45-67

Senior Python Developer with 8 years of experience...
"""

result = parse_resume_advanced(
    resume_text,
    required_skills=["python", "fastapi", "postgresql"]
)

print(result.email)  # john@example.com
print(result.total_years_experience)  # 8.0
print(result.skills)  # List[SkillAssessment]
```

### 6. Market Analytics с трендами

```python
from backend.services.advanced_market_analytics import AdvancedMarketAnalytics

analytics = AdvancedMarketAnalytics()

# Analyze trends
trends = analytics.analyze_trends(current_market_data, historical_data, skills)

# Forecast salaries
forecasts = analytics.forecast_salaries(market_data, "Backend Developer", skills)

# Competition analysis
competition = analytics.analyze_competition(market_data, "Backend Developer", 10)

# Skill demand forecast
demand = analytics.forecast_skill_demand(market_data, skills)
```

### 7. Predictive Analytics

```python
from backend.services.predictive_analytics import PredictiveAnalytics

analytics = PredictiveAnalytics()

# Predict offer acceptance
prediction = analytics.predict_offer_acceptance(
    candidate_id="user1",
    candidate_score=85,
    salary_offered=250000,
    market_median_salary=200000,
    has_competing_offers=True,
    days_in_process=20
)

print(prediction.probability_accept)  # 0.75
print(prediction.recommendation)  # "Strong probability..."
print(prediction.key_factors)  # List of reasons
```

### 8. Job Description Generator

```python
from backend.services.job_description_generator import (
    generate_job_description,
    JobDescriptionRequest,
    format_job_description_markdown
)

jd = generate_job_description(JobDescriptionRequest(
    role="Senior Backend Developer",
    company_name="TechCorp",
    location="Remote",
    required_skills=["python", "fastapi", "postgresql", "docker"],
    nice_to_have_skills=["kubernetes", "redis"],
    experience_level="senior",
    salary_range={"from": 200000, "to": 300000, "currency": "RUB"},
    benefits=["Stock options", "Flexible hours"]
))

# Export to Markdown
markdown = format_job_description_markdown(jd)
print(markdown)
```

### 9. A/B Testing

```python
from backend.services.ab_testing import ab_testing_framework

# Create experiment
exp_id = ab_testing_framework.create_experiment(
    name="New Scoring Algorithm",
    description="Test dependency analysis weight",
    variants=["baseline", "variant_a"],
    traffic_split={"baseline": 0.5, "variant_a": 0.5}
)

# Register scoring functions
ab_testing_framework.register_variant("baseline", baseline_scoring)
ab_testing_framework.register_variant("variant_a", new_scoring)

# Start experiment
ab_testing_framework.start_experiment(exp_id)

# Score candidates (automatic assignment to variants)
variant, score = ab_testing_framework.score_candidate_with_variant(
    exp_id, "candidate1", candidate_data
)

# Analyze results
results = ab_testing_framework.analyze_experiment(exp_id)
print(f"Winner: {results.winner}")
print(f"Statistical significance: {results.statistical_significance}")
```

### 10. Candidate Recommendations

```python
from backend.services.candidate_recommendations import recommendation_engine

# Add candidates to pool
recommendation_engine.bulk_add_candidates(all_candidates)

# Find similar candidates
similar = recommendation_engine.find_similar_candidates(
    candidate_id="user1",
    top_n=10,
    algorithm="hybrid"  # content / collaborative / hybrid
)

# Recommend for role
recommended = recommendation_engine.recommend_for_role(
    required_skills=["python", "docker", "postgresql"],
    nice_to_have_skills=["kubernetes"],
    top_n=10
)
```

### 11. Prometheus Metrics

```bash
# Metrics endpoint (for Prometheus scraping)
curl http://localhost:8005/metrics

# Summary stats
curl http://localhost:8005/api/v1/metrics/stats

# Response:
{
  "cache_hit_rate": 78.5,
  "average_candidate_score": 72.3,
  "total_candidates_analyzed": 1523,
  "candidates_accepted": 536,
  "candidates_rejected": 987,
  "acceptance_rate": 35.2
}
```

### 12. Feedback Loop

```python
from backend.services.feedback_loop import feedback_loop

# Submit feedback
feedback_loop.submit_feedback(
    candidate_id="user1",
    original_score=75,
    original_decision="go",
    feedback_type=FeedbackType.HIRE_OUTCOME,
    actual_outcome=HireOutcome.HIRED,
    interview_score=4.5,
    role="Backend Developer"
)

# Auto-analysis (every 50 entries)
analytics = feedback_loop.analyze_feedback()

print(f"Accuracy: {analytics.scoring_accuracy_rate}")
print(f"False positive rate: {analytics.false_positive_rate}")
print(f"Recommendations: {analytics.recommended_adjustments}")

# Apply adjustments
for adj in feedback_loop.get_pending_adjustments():
    feedback_loop.apply_adjustment(adj.adjustment_id)
```

---

## Prometheus + Grafana Setup

### prometheus.yml
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'hr-system'
    static_configs:
      - targets: ['backend:8005']
    metrics_path: '/metrics'
```

### docker-compose.yml
```yaml
services:
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
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## API Endpoints

### Existing
- `POST /api/v1/hr/run` - Main HR analysis
- `GET /api/v1/hr/interview/{username}` - Interview support
- `GET /api/v1/hr/outreach/{username}` - Outreach template

### NEW!
- `POST /api/v1/batch/submit` - Submit batch job
- `GET /api/v1/batch/status/{job_id}` - Job status
- `GET /api/v1/batch/results/{job_id}` - Job results
- `DELETE /api/v1/batch/cancel/{job_id}` - Cancel job
- `GET /api/v1/batch/jobs` - List all jobs
- `GET /api/v1/batch/stats` - Batch stats
- `GET /metrics` - Prometheus metrics

---

## Документация

- **ENTERPRISE_FEATURES.md** - Полная документация всех фич
- **README.md** - Общее описание проекта
- **docs/MCP_INTEGRATION.md** - MCP архитектура
- **docs/TESTING_GUIDE.md** - Тестирование
