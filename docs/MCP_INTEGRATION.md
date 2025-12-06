# Архитектура интеграции с MCP

## Обзор

HR система рекрутинга интегрируется с MCP (Model Context Protocol) сервером для анализа GitHub профилей и получения данных о рынке труда через HH.ru API.

## Текущая архитектура MCP сервера

### Расположение файлов
```
ml/mcp_server/
├── main.py              # Точка входа MCP сервера
├── tools/
│   ├── github_tools.py  # Инструменты анализа GitHub
│   └── hh_tools_multi.py # Инструменты для HH.ru
```

### Запуск MCP сервера
```bash
docker-compose up ml
```

MCP сервер работает через stdio transport и доступен для backend через MLClient.

## Реализованные MCP инструменты

### 1. analyze_github

**Назначение:** Анализ репозиториев пользователя GitHub для извлечения навыков и метрик активности.

**Входные данные:**
```python
{
    "username": str,           # GitHub username
    "required_skills": List[str],  # Навыки для поиска
    "repos_limit": int,        # Макс. кол-во репозиториев (по умолчанию: 5)
    "lookback_days": Optional[int]  # Фильтр по последней активности
}
```

**Выходные данные:**
```python
{
    "skill_scores": [
        {
            "skill": str,
            "score": float,      # 0.0 до 1.0
            "evidence": str      # Названия репозиториев с языками
        }
    ],
    "top_languages": List[str],
    "repos_analyzed": int,
    "risk_flags": List[str],
    "activity_metrics": {
        "days_since_last_push": int,
        "commit_frequency_score": int,  # 0-100
        "total_stars": int,
        "total_forks": int,
        "repo_diversity_score": int,
        "one_commit_repos_count": int
    }
}
```

**Реализация:** `ml/mcp_server/tools/github_tools.py`

**Алгоритм скоринга:**
- Проверяет, встречается ли навык в имени репозитория, description, topics или languages
- Нормализует навыки (python, py, python3 -> python)
- Score = (кол-во совпадающих репо / общее кол-во проанализированных репо)
- Evidence включает имена репозиториев и обнаруженные языки

**Известные ограничения:**
- Консервативный скоринг: даже очевидные совпадения получают низкие баллы
- Пример: Tiangolo (создатель FastAPI) получает fastapi_score=0.1 несмотря на множество FastAPI репозиториев
- Рекомендация: улучшить скоринг, проверяя:
  - Зависимости пакетов (requirements.txt, package.json)
  - Анализ кода файлов (imports, используемые фреймворки)
  - Содержимое коммитов, а не только метаданные

### 2. search_jobs_multi_page

**Назначение:** Получение нескольких страниц вакансий с HH.ru API для анализа рынка.

**Входные данные:**
```python
{
    "query": str,              # Роль/название должности
    "location": Optional[str], # ID региона HH.ru или название города
    "skills": List[str],       # Требуемые навыки
    "salary_from": Optional[int],
    "salary_to": Optional[int],
    "per_page": int,           # Результатов на странице (по умолчанию: 10)
    "pages": int               # Кол-во страниц для загрузки (по умолчанию: 3)
}
```

**Выходные данные:**
```python
{
    "items": [
        {
            "title": str,
            "salary_from": Optional[int],
            "salary_to": Optional[int],
            "currency": str,
            "skills": List[str],
            "employer": str,
            "area": str,
            "url": str
        }
    ],
    "total_found": int,
    "pages_fetched": int
}
```

**Реализация:** `ml/mcp_server/tools/hh_tools_multi.py`

**Возможности:**
- Параллельная загрузка страниц с asyncio.gather
- Rate limiting (обработка 429)
- Нормализация валют
- Извлечение навыков из данных вакансий

## Интеграция с Backend

### Архитектура MLClient

**Расположение:** `backend/ml_integration/client.py`

**Ключевые возможности:**
- Асинхронные вызовы MCP инструментов через httpx
- Логика повторных попыток с экспоненциальной задержкой
- Обработка ошибок (401, 404, 429, 500+)
- Отслеживание метрик (успех/неудача)

**Пример использования:**
```python
from backend.ml_integration.client import MLClient

ml_client = MLClient()

# Вызов MCP инструмента
result = await ml_client.call_mcp_tool(
    "analyze_github",
    {"username": "torvalds", "required_skills": ["python", "c"]}
)
```

**Конфигурация повторных попыток:**
```python
max_retries = 3
retry_delay = 1.0  # секунды
backoff_multiplier = 2  # экспоненциальный: 1s, 2s, 4s
```

### Слой кеширования

**Расположение:** `backend/services/cache.py`

**Реализация:**
- Кеширование на основе Redis
- TTL: 1800 секунд (30 минут)
- Ключи кеша: `hr:market_multi:<hash>`, `hr:candidate:<hash>`
- Отслеживание статистики попаданий/промахов

**Преимущества:**
- Снижает нагрузку на MCP сервер
- Быстрое время отклика
- Защита от лимитов GitHub API

## Интеграция с HR сервисом

### Диаграмма потока

```
1. HR API запрос
   ↓
2. Backend (hr.py)
   ↓
3. Проверка Redis кеша
   ↓ (промах)
4. MLClient.call_mcp_tool()
   ↓
5. MCP Server (stdio)
   ↓
6. Внешние API (GitHub, HH.ru)
   ↓
7. Возврат результата
   ↓
8. Кеширование результата
   ↓
9. Скоринг кандидата
   ↓
10. Применение mandatory фильтра
   ↓
11. Возврат отчета
```

### Критические точки интеграции

**1. Нормализация навыков**
```python
# Backend нормализует навыки перед отправкой в MCP
from backend.services.normalization import normalize_skills_batch

normalized_skills = normalize_skills_batch(["Python", "FastAPI", "docker"])
# -> ["python", "fastapi", "docker"]
```

**2. Порог скоринга навыков**
```python
# HR система требует score >= 0.5 для обязательных навыков
min_score = 0.5  # Требуется реальное подтверждение
min_coverage = 0.8  # Должно покрывать 80%+ обязательных навыков
```

**3. Переопределение классификации**
```python
# Требования работодателя переопределяют рыночный анализ
classification_result = smart_classify_skills(
    role=request.role,
    required_skills=all_skills,
    market_data=market_data,
    employer_mandatory=request.skills,      # Всегда обязательные
    employer_preferred=request.nice_to_have_skills  # Всегда желательные
)
```

## Рекомендации для разработчиков MCP

### Улучшения высокого приоритета

**1. Улучшенное определение навыков GitHub**

Текущий алгоритм слишком консервативен. Улучшить:

```python
# Проверка зависимостей пакетов
- requirements.txt -> python пакеты
- package.json -> npm пакеты
- go.mod -> go модули

# Анализ реального кода
- Подсчет import statements (Python: "import fastapi", "from fastapi")
- Проверка паттернов использования фреймворков
- Определение ORM, баз данных, testing фреймворков

# Взвешивание характеристик репозитория
- Stars/forks указывают на популярность/важность
- Свежие коммиты указывают на текущую экспертизу
- Статус контрибьютора (владелец vs контрибьютор)
```

**2. Инструмент парсинга резюме**

Добавить MCP инструмент для продвинутого парсинга резюме:

```python
@mcp_tool
async def parse_resume_advanced(
    resume_text: str,
    required_skills: List[str]
) -> Dict:
    """
    Использовать LLM для извлечения:
    - Лет опыта по каждому навыку
    - Описания проектов
    - Сертификаты
    - Образование
    - Предыдущие роли и обязанности
    """
```

**3. Инструмент LinkedIn**

Добавить реальную интеграцию с LinkedIn (сейчас заглушка):

```python
@mcp_tool
async def analyze_linkedin_profile(
    linkedin_url: str
) -> Dict:
    """
    Извлечь:
    - История работы
    - Endorsements навыков
    - Рекомендации
    - Сертификаты
    - Образование
    """
```

**4. Инструмент конкурентной аналитики**

```python
@mcp_tool
async def analyze_market_competition(
    role: str,
    location: str,
    salary_range: Tuple[int, int]
) -> Dict:
    """
    Анализ:
    - Соотношение спроса/предложения
    - Перцентили зарплат по навыкам
    - Топ нанимающих компаний
    - Трендовые навыки
    - Метрики времени найма
    """
```

### Улучшения среднего приоритета

**5. Пакетная обработка**

Поддержка анализа нескольких кандидатов:

```python
@mcp_tool
async def analyze_github_batch(
    usernames: List[str],
    required_skills: List[str]
) -> Dict[str, Any]:
    """Обработка нескольких кандидатов параллельно"""
```

**6. Восстановление после ошибок**

Лучшая обработка частичных сбоев:

```python
# Если GitHub API падает для некоторых репозиториев, продолжать с доступными данными
# Возвращать частичные результаты с флагами ошибок
{
    "partial_data": True,
    "repos_analyzed": 3,
    "repos_failed": 2,
    "skill_scores": [...],
    "warnings": ["Не удалось загрузить репозитории: repo1, repo2"]
}
```

**7. Сервис таксономии навыков**

Централизованное управление навыками:

```python
@mcp_tool
async def get_skill_taxonomy() -> Dict:
    """
    Возврат канонических имен навыков и синонимов:
    {
        "python": ["python", "py", "python3", "питон"],
        "fastapi": ["fastapi", "fast-api", "фастапи"]
    }
    """
```

### Улучшения низкого приоритета

**8. Поиск по коду GitHub**

Глубокий анализ кода:

```python
@mcp_tool
async def search_github_code(
    username: str,
    code_patterns: List[str]
) -> Dict:
    """
    Поиск в коде паттернов:
    - "from fastapi import FastAPI"
    - "class.*SQLAlchemy"
    - "docker-compose"
    """
```

**9. Метрики качества вклада**

```python
@mcp_tool
async def analyze_contribution_quality(
    username: str
) -> Dict:
    """
    Метрики:
    - Участие в code review
    - Время решения issue
    - PR acceptance rate
    - Вовлеченность в сообщество
    """
```

**10. Определение технологического стека**

```python
@mcp_tool
async def detect_tech_stack(
    repo_url: str
) -> Dict:
    """
    Автоопределение полного стека:
    - Backend фреймворк
    - База данных
    - Frontend фреймворк
    - DevOps инструменты
    - Testing фреймворки
    """
```

## Конфигурация MCP сервера

### Переменные окружения

```bash
# MCP Server
MCP_LOG_LEVEL=INFO
GITHUB_TOKEN=your_github_token  # Опционально, увеличивает rate limits

# HH.ru API
HH_API_BASE_URL=https://api.hh.ru
HH_USER_AGENT=YourApp/1.0
```

### Настройка производительности

**GitHub API Rate Limits:**
- Без аутентификации: 60 запросов/час
- С аутентификацией: 5000 запросов/час
- Рекомендация: используйте GITHUB_TOKEN для production

**Concurrent запросы:**
```python
# Текущий: последовательная загрузка репозиториев
# Рекомендация: параллельная с семафором
async with asyncio.Semaphore(5):
    tasks = [fetch_repo(repo) for repo in repos]
    results = await asyncio.gather(*tasks)
```

**Кеширование ответов:**
- Кеш данных пользователя GitHub: 1 час
- Кеш данных репозитория: 30 минут
- Кеш рыночных данных HH.ru: 30 минут

## Тестирование MCP инструментов

### Ручное тестирование

```bash
# Тест analyze_github
echo '{"method":"analyze_github","params":{"username":"torvalds","required_skills":["c","python"],"repos_limit":10}}' | \
docker-compose exec -T ml python -m ml.mcp_server.main

# Тест search_jobs_multi_page
echo '{"method":"search_jobs_multi_page","params":{"query":"Python Developer","pages":2}}' | \
docker-compose exec -T ml python -m ml.mcp_server.main
```

### Интеграционное тестирование

```bash
# Полный тест HR workflow
./test_hr.sh
```

## Соображения по развертыванию

**Docker Compose сервисы:**
```yaml
ml:
  build: ./ml
  environment:
    - GITHUB_TOKEN=${GITHUB_TOKEN}
  volumes:
    - ./ml:/app/ml
  restart: unless-stopped
```

**Масштабирование:**
- MCP сервер stateless, можно запускать несколько инстансов
- Использовать load balancer для нескольких MCP серверов
- Redis кеш общий для всех инстансов

**Мониторинг:**
- Отслеживать success/failure rate вызовов MCP
- Мониторить использование GitHub API rate limit
- Алерты при высоком проценте ошибок

## Безопасность

**GitHub Token:**
- Никогда не коммитить токены в git
- Использовать переменные окружения или secrets manager
- Периодически ротировать токены

**HH.ru API:**
- Соблюдать rate limits (избегать 429 ошибок)
- Использовать User-Agent header
- Кешировать результаты для минимизации запросов

**Валидация входных данных:**
- Валидировать GitHub usernames (alphanumeric + дефисы)
- Санитизировать имена навыков
- Ограничивать repos_limit разумными значениями (макс 50)

## Дополнительная документация

- MCP Protocol: docs/MCP_BASICS.md
- ML Integration: docs/ML_INTEGRATION_GUIDE.md
- API Schema: docs/API_SCHEMA_GUIDE.md
- Testing Guide: docs/TESTING_GUIDE.md
