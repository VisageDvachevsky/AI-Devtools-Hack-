# AI Devtools Hack - MCP HR Recruitment System

Enterprise-уровень система рекрутинга на базе MCP, автоматизирующая процесс подбора кандидатов через анализ GitHub профилей и рыночных данных.

## Архитектура

```
frontend/          - React + TypeScript UI
backend/           - FastAPI бэкенд API
ml/                - Рабочая зона ML команды
  mcp_server/      - Реализация MCP сервера
  agents/          - Реализации агентов
  examples/        - Примеры кода
docs/              - Документация
protos/            - gRPC определения
```

## Стек технологий

- Frontend: React + TypeScript
- Backend: Python + FastAPI
- MCP Server: Python + FastAPI
- Agents: LangChain / LlamaIndex
- LLM: Cloud.ru Evolution Foundation Model
- Контейнеризация: Docker, docker-compose

## Быстрый старт

### Требования

- Docker и docker-compose
- Python 3.11+
- Node.js 18+
- Poetry

### Настройка

1. Клонируй и настрой:

```bash
cp .env.example .env
# Добавь свои API ключи в .env
```

2. Запусти все сервисы:

```bash
make dev
```

Сервисы будут доступны по адресам:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8005
- MCP Server: http://localhost:8001
- API Docs: http://localhost:8005/docs

### HR Recruitment API

Основной эндпоинт для автоматизации рекрутинга с интеллектуальным скорингом кандидатов.

Возможности:
- Анализ рынка труда через HH.ru API (зарплаты, требуемые навыки, конкуренция)
- Глубокий анализ GitHub профилей (навыки, активность, качество кода)
- Строгая фильтрация по обязательным требованиям (mandatory skills)
- Автоматическая классификация навыков (mandatory/preferred/optional)
- Интеллектуальные рекомендации (кого звать на интервью, риски, пробелы в навыках)
- Кеширование результатов в Redis (30 минут TTL)

Пример запроса:

```bash
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d '{
        "role": "Senior Backend Python Developer",
        "skills": ["python", "fastapi", "postgresql", "docker"],
        "nice_to_have_skills": ["kubernetes", "redis"],
        "salary_from": 250000,
        "salary_to": 400000,
        "candidates": [
          {
            "github_username": "donnemartin",
            "repos_limit": 20,
            "resume_text": "8+ years Python backend experience..."
          }
        ]
      }'
```

Ответ содержит:
- `market` - рыночные данные HH.ru (вакансии, зарплаты, топ компании)
- `candidates` - анализ GitHub профилей кандидатов
- `report` - детальный отчет с рекомендациями:
  - Скоринг кандидатов (score 0-100, decision: go/hold/no)
  - Mandatory/preferred skills coverage
  - Риски и блокирующие причины
  - Skill gaps анализ
  - Рекомендации по интервью
  - Market insights (supply/demand, competitive salary)

Подробнее: `docs/API_SCHEMA_GUIDE.md`

### Команды для разработки

```bash
make install    # Установить зависимости
make dev        # Запустить dev окружение
make up         # Запустить сервисы в фоне
make down       # Остановить сервисы
make logs       # Посмотреть логи
make clean      # Очистить контейнеры
make test       # Запустить тесты
make check      # Проверить что все работает
make format     # Форматировать код
make lint       # Линтинг кода
make proto      # Сгенерировать gRPC код
```

## Структура проекта

### Backend (`backend/`)

FastAPI приложение, которое обрабатывает:
- API роутинг
- Валидацию запросов
- CORS конфигурацию
- Интеграцию с ML сервисами

Ключевые файлы:
- `backend/main.py` - Точка входа
- `backend/api/v1/` - API endpoints
- `backend/ml_integration/client.py` - Клиент для ML сервиса
- `backend/schemas/` - Pydantic модели

### ML рабочая зона (`ml/`)

ML команда реализует агентов и инструменты здесь:
- `ml/mcp_server/` - Реализация MCP сервера
- `ml/agents/` - Реализации агентов
- `ml/examples/` - Примеры реализаций

Смотри `docs/ML_INTEGRATION_GUIDE.md` для детальных инструкций.

### Frontend (`frontend/`)

React + TypeScript приложение:
- `frontend/src/` - Исходный код
- `frontend/src/api/` - API клиент

## Для ML команды

Прочитай эти доки первыми:
1. `docs/MCP_BASICS.md` - Концепты MCP
2. `docs/ML_INTEGRATION_GUIDE.md` - Как добавлять агентов/инструменты

Быстрый пример:

```python
from ml.agents.registry import agent_registry

@agent_registry.register(name="my_agent", description="Мой агент")
async def my_agent(input_data: dict, config: dict) -> dict:
    return {"response": "результат"}
```

Затем импортируй в `ml/agents/__init__.py` и перезапусти сервисы.

## API Endpoints

### Backend API (`/api/v1`)

Endpoints для агентов:
- `POST /agents/execute` - Выполнить агента
- `GET /agents/list` - Список агентов

MCP endpoints:
- `POST /mcp/call` - Вызвать MCP инструмент
- `GET /mcp/tools` - Список инструментов

### MCP Server (внутренний)

- `POST /agents/execute` - Выполнить агента
- `GET /agents/list` - Список агентов
- `POST /tools/call` - Вызвать инструмент
- `GET /tools/list` - Список инструментов

## Переменные окружения

Обязательные в `.env`:

```bash
EVOLUTION_API_KEY=твой_api_ключ
EVOLUTION_API_URL=https://api.cloud.ru/v1
```

Опциональные:

```bash
REDIS_HOST=redis
REDIS_PORT=6380
MCP_SERVER_URL=http://mcp_server:8001
```

## Деплой

### Локальная разработка

```bash
make dev
```

### Production

```bash
docker-compose up -d
```

### Cloud.ru Evolution AI Agents

Смотри деплой доки для конфигурации cloud.ru.

## Рабочий процесс команды

### Backend/DevOps
- Поддержка backend API
- Деплой
- Управление инфраструктурой
- Ревью ML интеграций

### ML команда
- Реализация агентов в `ml/agents/`
- Реализация инструментов в `ml/mcp_server/`
- Тестирование на примерах
- Документация возможностей агентов

## Тестирование

Запустить тесты:

```bash
make test
```

Тестировать конкретный компонент:

```bash
poetry run pytest backend/tests/
poetry run pytest ml/tests/
```

## Troubleshooting

### Сервисы не запускаются

```bash
make clean
make dev
```

### Ошибки импорта

```bash
poetry install
```

### Проблемы с подключением к API

Проверь конфигурацию в `.env` и URL сервисов.

### Посмотреть логи

```bash
make logs
# или конкретный сервис
docker-compose logs -f backend
```

Подробнее: `docs/TROUBLESHOOTING.md`

## Документация

### Для пользователей
- `docs/API_SCHEMA_GUIDE.md` - Полная спецификация API запросов
- `docs/TESTING_GUIDE.md` - Руководство по тестированию системы
- API Docs: http://localhost:8005/docs

### Для разработчиков
- `docs/MCP_INTEGRATION.md` - Архитектура MCP интеграции и рекомендации
- `docs/MCP_BASICS.md` - Основы MCP протокола
- `docs/ML_INTEGRATION_GUIDE.md` - Гайд по ML интеграции
- `docs/QUICKSTART_ML.md` - Быстрый старт для ML
- `docs/TROUBLESHOOTING.md` - Решение проблем

### Тестирование

Быстрая проверка системы:
```bash
./test_hr.sh
```

Ручное тестирование:
```bash
# Простой тест (только Python обязателен)
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_simple.json | jq .

# Полный тест (6 обязательных навыков)
curl -X POST http://localhost:8005/api/v1/hr/run \
  -H "Content-Type: application/json" \
  -d @test_hr_request_full.json | jq .
```

## Лицензия

Смотри LICENSE файл.
