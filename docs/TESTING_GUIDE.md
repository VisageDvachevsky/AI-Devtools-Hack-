# Руководство по проверке HR системы

## Быстрый тест

Просто запустите:
```bash
./test_hr.sh
```

## Что проверяет система

### Test 1: Простой случай (только Python обязателен)
- GVanRossum (создатель Python): должен получить GO
- Torvalds (C-разработчик): должен получить NO

Ожидаемый результат:
```
gvanrossum: score=100, decision=go, mandatory_coverage=100%
torvalds: score=30, decision=no, mandatory_coverage=0%
```

### Test 2: Сложный случай (6 обязательных навыков)
Требования: Python, FastAPI, PostgreSQL, Docker, Redis, Kubernetes

Все 5 кандидатов должны быть отклонены, так как:
- У всех есть только Python (score=1.0)
- Остальные навыки (FastAPI, Docker, etc) имеют score < 0.5
- Mandatory coverage = 16.7% (только 1 из 6 навыков)
- Требуется >= 80% coverage

Ожидаемый результат:
```
Все: score=30, decision=no, mandatory_coverage=16.7%
```

### Test 3: Классификация навыков
Проверяет, что:
- 6 mandatory (из request.skills)
- 4 preferred (из request.nice_to_have_skills)
- 0 optional

### Test 4: Причины отклонения
Проверяет детальные причины блокировки:
- "BLOCKING: Missing mandatory skills (5/6): docker, fastapi, kubernetes"
- "Mandatory coverage only 17% (required 80%+)"
- "Cannot proceed without: docker, fastapi"

## Ручная проверка

### 1. Проверить, что mandatory требования работают

```bash
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Python Developer",
    "skills": ["python"],
    "candidates": [{"github_username": "gvanrossum", "repos_limit": 10}]
  }' | jq '.report.candidate_scores[0] | {score, decision, mandatory_coverage: .requirement_match.mandatory_coverage}'
```

Ожидание: `decision: "go"`, `mandatory_coverage: 100`

### 2. Проверить, что отклонение работает

```bash
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Python Developer",
    "skills": ["python"],
    "candidates": [{"github_username": "torvalds", "repos_limit": 10}]
  }' | jq '.report.candidate_scores[0] | {score, decision, mandatory_coverage: .requirement_match.mandatory_coverage}'
```

Ожидание: `decision: "no"`, `mandatory_coverage: 0`, `score: 30`

### 3. Проверить различие mandatory vs preferred

```bash
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Backend Developer",
    "skills": ["python", "fastapi"],
    "nice_to_have_skills": ["docker", "kubernetes"],
    "candidates": [{"github_username": "tiangolo", "repos_limit": 15}]
  }' | jq '.report.skill_classification_report.summary'
```

Ожидание:
```json
{
  "mandatory_count": 2,  // python, fastapi
  "preferred_count": 2,  // docker, kubernetes
  "optional_count": 0
}
```

### 4. Проверить блокирующие причины

```bash
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | \
  jq '.report.candidate_scores[0].decision_reasons'
```

Ожидание: Должны содержать:
- "BLOCKING: Missing mandatory skills"
- "Mandatory coverage only X% (required 80%+)"
- "Cannot proceed without: ..."

## Критерии успешной проверки

Mandatory filtering работает:
- Кандидаты без обязательных навыков отклоняются (decision="no")
- Score ограничен 30 для жесткого отказа
- Mandatory coverage < 80% -> автоматический reject

Классификация навыков корректна:
- `request.skills` -> mandatory
- `request.nice_to_have_skills` -> preferred
- Employer override применяется (не переопределяется рынком)

Причины отклонения понятны:
- "BLOCKING:" префикс для блокирующих причин
- Перечислены конкретные недостающие навыки
- Указан % покрытия и требуемый порог

Система работает в обе стороны:
- Принимает кандидатов с нужными навыками (GVanRossum для Python)
- Отклоняет кандидатов без нужных навыков (Torvalds для Python)

## Известные ограничения

GitHub skill scoring консервативный:
- MCP GitHub analysis tool дает низкие scores даже для очевидных совпадений
- Например: Tiangolo (создатель FastAPI) получает fastapi_score=0.1
- Это ограничение MCP tool, не HR системы
- HR система корректно применяет threshold 0.5

## Логирование

Проверить логи backend для деталей классификации:
```bash
docker-compose logs backend | grep "Smart skill classification"
```

Должно показать:
```
Mandatory: ['python', 'fastapi', 'postgresql', 'docker', 'redis', 'kubernetes']
Preferred: ['graphql', 'kafka', 'prometheus', 'terraform']
Optional: []
Employer override applied: True
```

## Структура тестовых данных

### test_hr_simple.json
Минимальный тест:
- Роль: Python Developer
- Обязательно: python
- Желательно: docker, fastapi
- Кандидаты: gvanrossum (проходит), torvalds (отклонен)

### test_hr_request_full.json
Полный enterprise тест:
- Роль: Senior Backend Python Developer
- Обязательно: python, fastapi, postgresql, docker, redis, kubernetes
- Желательно: graphql, kafka, prometheus, terraform
- Кандидаты: 5 известных разработчиков с полными профилями
- Все поля заполнены (зарплата, location, benefits, certifications, etc)

## Решение проблем

Если тесты не проходят:

1. Проверьте, что backend запущен:
```bash
docker-compose ps backend
```

2. Проверьте логи на ошибки:
```bash
docker-compose logs backend | tail -50
```

3. Перезапустите backend:
```bash
docker-compose restart backend
```

4. Очистите Redis кеш:
```bash
docker-compose exec redis redis-cli FLUSHALL
```

5. Проверьте, что MCP server доступен:
```bash
docker-compose ps ml
docker-compose logs ml | tail -20
```
