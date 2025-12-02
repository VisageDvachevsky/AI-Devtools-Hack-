# AI Devtools Hack - MCP Business AI Transformation

Бизнес-ориентированный MCP сервер с мультиагентной системой для автоматизации бизнес-процессов.

**Первый раз здесь? Читай [FIRST_RUN.md](FIRST_RUN.md) для инструкций по запуску.**

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
- Backend API: http://localhost:8000
- MCP Server: http://localhost:8001
- API Docs: http://localhost:8000/docs

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
REDIS_PORT=6379
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

- `docs/MCP_BASICS.md` - Основы MCP протокола
- `docs/ML_INTEGRATION_GUIDE.md` - Гайд по ML интеграции
- `docs/QUICKSTART_ML.md` - Быстрый старт для ML
- `docs/TROUBLESHOOTING.md` - Решение проблем
- API Docs: http://localhost:8000/docs

## Лицензия

Смотри LICENSE файл.
