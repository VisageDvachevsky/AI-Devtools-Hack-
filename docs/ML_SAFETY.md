# Безопасность для ML команды

## Что можно и что нельзя

### Можно трогать:
```
ml/
├── agents/        ← Создавай свои агенты
├── mcp_server/    ← Создавай свои tools
└── examples/      ← Смотри примеры
```

### НЕЛЬЗЯ трогать:
```
backend/           ← НЕ ТРОГАТЬ
frontend/          ← НЕ ТРОГАТЬ
docker-compose.yml ← НЕ ТРОГАТЬ
pyproject.toml     ← НЕ ТРОГАТЬ
Makefile           ← НЕ ТРОГАТЬ
```

### .env файл
- Можно добавлять свои API ключи
- НЕЛЬЗЯ коммитить в git (уже в .gitignore)
- Проверь что .env в .gitignore!

## Защита от поломок

### 1. Docker изоляция
Каждый сервис в своем контейнере:
- Если MCP сервер упадет → Backend работает
- Если твой код упадет → Frontend работает
- Автоматический перезапуск при падении

### 2. Timeout защита
Backend ждет ответ от MCP сервера только 30 секунд:
- Если твой агент зависнет → Backend не зависнет
- Пользователь получит ошибку, но система работает

### 3. Healthcheck
Docker проверяет здоровье сервисов каждые 30 секунд:
- Если сервис не отвечает → автоматический перезапуск
- Проверяется через `/health` endpoint

### 4. Git контроль
- Все изменения в git
- Можно откатить любые изменения
- Backend/Frontend защищены

## Что может сломаться

### Твой MCP сервер упадет если:
```python
# Бесконечный цикл
while True:
    pass

# Ошибка импорта
from nonexistent_module import something

# Некорректный код
@agent_registry.register(name="bad")
async def bad_agent():
    raise Exception("oops")
```

**Решение:**
- MCP сервер перезапустится автоматически
- Backend продолжит работать
- Просто исправь код и перезапусти: `docker-compose restart mcp_server`

### Твой код будет медленным если:
```python
@agent_registry.register(name="slow")
async def slow_agent(input_data, config):
    time.sleep(100)  # Долгая операция
    return {"result": "done"}
```

**Решение:**
- Backend получит timeout через 30 сек
- Используй async операции
- Добавь прогресс индикаторы

## Best Practices

### 1. Обработка ошибок
```python
@agent_registry.register(name="safe_agent")
async def safe_agent(input_data, config):
    try:
        result = await risky_operation()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 2. Валидация входных данных
```python
@agent_registry.register(name="validated_agent")
async def validated_agent(input_data, config):
    if "required_field" not in input_data:
        return {"error": "required_field is missing"}

    # Твой код
    return {"result": "ok"}
```

### 3. Timeout для внешних API
```python
import httpx

@tool_registry.register(name="api_tool")
async def api_tool(param: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://api.example.com/{param}")
            return response.json()
    except httpx.TimeoutException:
        return {"error": "API timeout"}
```

### 4. Логирование
```python
import logging
logger = logging.getLogger(__name__)

@agent_registry.register(name="logged_agent")
async def logged_agent(input_data, config):
    logger.info(f"Processing: {input_data}")
    try:
        result = await process(input_data)
        logger.info("Success")
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}
```

## Проверка перед коммитом

```bash
# 1. Проверь что все работает
make check

# 2. Проверь что .env не в git
git status | grep .env  # Не должно быть

# 3. Посмотри что изменилось
git status

# 4. Убедись что изменения только в ml/
git diff --name-only
```

## Если что-то сломалось

### MCP сервер не запускается
```bash
# Посмотри логи
docker-compose logs mcp_server

# Проверь синтаксис Python
python3 ml/agents/your_agent.py

# Перезапусти
docker-compose restart mcp_server
```

### Ошибки импорта
```bash
# Проверь что добавил импорт в __init__.py
cat ml/agents/__init__.py

# Перезапусти
docker-compose restart mcp_server
```

### Backend не видит твоих агентов
```bash
# Проверь что MCP сервер работает
curl http://localhost:8001/health

# Проверь список агентов
curl http://localhost:8001/agents/list

# Если агента нет - проверь регистрацию
```

## Помощь

- Логи: `make logs` или `docker-compose logs mcp_server`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Примеры: `ml/examples/`

Главное: **работай только в ml/ папке и всё будет хорошо!**
