# Гайд по хакатону для ML команды

## Что от вас требуется

По условиям трека нужно:
1. MCP-сервер с интеграцией публичного API
2. Агент или мультиагентная система
3. Бизнес-ориентированное решение

## Уже готово в проекте

- Базовая структура MCP сервера
- Система регистрации tools и agents
- Интеграция с бэкендом
- Docker и деплой
- Документация

## Что нужно сделать на хакатоне

### 1. Выбрать бизнес-кейс

Примеры:
- Автоматизация email рассылки
- Мониторинг новостей и аналитика
- Управление задачами и календарем
- Обработка обращений клиентов
- Аналитика продаж
- HR автоматизация

### 2. Выбрать публичные API

Примеры API:
- Email: Gmail API, SendGrid
- Календари: Google Calendar
- CRM: HubSpot, Salesforce
- Новости: NewsAPI
- Погода: OpenWeatherMap
- Соцсети: Twitter API, VK API
- Финансы: Alpha Vantage
- Документы: Google Docs API

### 3. Создать MCP tools для API

Каждый API endpoint = 1 tool

Пример структуры:
```python
from ml.mcp_server.tools import tool_registry
import httpx

@tool_registry.register(name="send_email", description="Send email via Gmail")
async def send_email(to: str, subject: str, body: str) -> dict:
    # Интеграция с Gmail API
    return {"status": "sent", "message_id": "..."}

@tool_registry.register(name="get_news", description="Get latest news")
async def get_news(query: str, limit: int = 5) -> dict:
    # Интеграция с NewsAPI
    return {"articles": [...]}
```

### 4. Создать агента

Простой агент (один агент использует tools):
```python
from ml.agents.registry import agent_registry
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI

@agent_registry.register(name="email_agent", description="Automate emails")
async def email_agent(input_data: dict, config: dict) -> dict:
    llm = ChatOpenAI(temperature=0.7)

    # Логика агента
    query = input_data["query"]

    # Используй tools через LangChain или напрямую
    result = await process_with_llm(query)

    return {"response": result}
```

Мультиагентная система (несколько агентов):
```python
@agent_registry.register(name="coordinator", description="Coordinates agents")
async def coordinator(input_data: dict, config: dict) -> dict:
    task = input_data["task"]

    # Разбить задачу на подзадачи
    subtasks = analyze_task(task)

    # Делегировать другим агентам
    results = []
    for subtask in subtasks:
        if subtask["type"] == "email":
            result = await call_agent("email_agent", subtask)
        elif subtask["type"] == "analytics":
            result = await call_agent("analytics_agent", subtask)
        results.append(result)

    # Объединить результаты
    return {"results": results}
```

### 5. Тестирование

```bash
# Запустить
make dev

# Проверить что tools зарегистрированы
curl http://localhost:8001/tools/list

# Проверить агентов
curl http://localhost:8001/agents/list

# Протестировать агента
curl -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "your_agent", "input_data": {...}, "config": {}}'
```

## Рекомендуемая структура работы

### День 1 (подготовка)
1. Выбрать бизнес-кейс
2. Выбрать 2-3 публичных API
3. Получить API ключи
4. Создать базовые tools для API
5. Протестировать tools

### День 2 (хакатон)
1. Создать агента с LangChain
2. Интегрировать с Evolution API
3. Добавить логику обработки
4. Протестировать end-to-end
5. Подготовить демо

## Примеры бизнес-кейсов

### Кейс 1: Email автоматизация
Tools:
- send_email
- get_unread_emails
- categorize_email
- draft_response

Agent:
- Читает новые письма
- Категоризирует по важности
- Генерирует черновики ответов
- Отправляет или сохраняет

### Кейс 2: Новостная аналитика
Tools:
- fetch_news
- analyze_sentiment
- extract_entities
- generate_summary

Agent:
- Собирает новости по теме
- Анализирует тональность
- Извлекает ключевые факты
- Создает итоговый отчет

### Кейс 3: HR помощник
Tools:
- parse_resume
- schedule_interview
- send_notification
- check_calendar

Agent:
- Обрабатывает резюме
- Находит свободные слоты
- Планирует интервью
- Отправляет уведомления

## Советы

### Используйте готовые библиотеки
- LangChain для агентов
- httpx для API запросов
- pydantic для валидации

### Храните API ключи в .env
```bash
GMAIL_API_KEY=...
NEWS_API_KEY=...
WEATHER_API_KEY=...
```

### Обрабатывайте ошибки
```python
@tool_registry.register(name="safe_tool", description="...")
async def safe_tool(param: str) -> dict:
    try:
        result = await external_api_call(param)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Логируйте
```python
import logging
logger = logging.getLogger(__name__)

@agent_registry.register(name="logged_agent", description="...")
async def logged_agent(input_data: dict, config: dict) -> dict:
    logger.info(f"Processing: {input_data}")
    result = await process(input_data)
    logger.info(f"Result: {result}")
    return result
```

## Чек-лист перед демо

- [ ] Все tools работают
- [ ] Агент отвечает корректно
- [ ] API ключи настроены
- [ ] Есть примеры запросов
- [ ] Подготовлен сценарий демо
- [ ] Проверена работа через frontend

## Файлы для редактирования

Вы работаете только в этих папках:
- `ml/mcp_server/` - ваши tools
- `ml/agents/` - ваши агенты
- `.env` - API ключи

НЕ трогайте:
- `backend/` - бэкенд
- `frontend/` - фронтенд
- `docker-compose.yml` - конфигурация

## Получение помощи

- Смотри примеры в `ml/examples/`
- Читай `docs/ML_INTEGRATION_GUIDE.md`
- Проверяй логи: `docker-compose logs mcp_server`
- Тестируй через API docs: http://localhost:8000/docs
