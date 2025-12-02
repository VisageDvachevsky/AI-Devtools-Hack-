# Чеклист для хакатона

## До хакатона (подготовка)

- [ ] Установить Docker и docker-compose
- [ ] Клонировать репозиторий
- [ ] Запустить `make dev` и убедиться что все работает
- [ ] Запустить `make check` для проверки
- [ ] Прочитать `docs/HACKATHON_GUIDE.md`
- [ ] Выбрать бизнес-кейс
- [ ] Выбрать 2-3 публичных API
- [ ] Зарегистрироваться и получить API ключи
- [ ] Добавить ключи в `.env`
- [ ] Протестировать примеры из `ml/examples/`

## В день хакатона

### Этап 1: Setup (30 минут)
- [ ] Запустить `make dev`
- [ ] Проверить что все сервисы работают
- [ ] Проверить API ключи в `.env`
- [ ] Открыть API docs: http://localhost:8000/docs

### Этап 2: MCP Tools (1-2 часа)
- [ ] Создать файл `ml/mcp_server/your_tools.py`
- [ ] Написать 2-3 tools для интеграции с API
- [ ] Использовать шаблоны из `ml/examples/templates.py`
- [ ] Зарегистрировать в `ml/mcp_server/__init__.py`
- [ ] Перезапустить: `docker-compose restart mcp_server`
- [ ] Проверить: `curl http://localhost:8001/tools/list`
- [ ] Протестировать каждый tool

### Этап 3: Agents (2-3 часа)
- [ ] Создать файл `ml/agents/your_agent.py`
- [ ] Написать основного агента
- [ ] Интегрировать с Evolution API
- [ ] Добавить логику использования tools
- [ ] Зарегистрировать в `ml/agents/__init__.py`
- [ ] Перезапустить: `docker-compose restart mcp_server`
- [ ] Проверить: `curl http://localhost:8001/agents/list`
- [ ] Протестировать агента

### Этап 4: Мультиагенты (опционально, 1-2 часа)
- [ ] Создать 2-3 специализированных агента
- [ ] Создать агента-координатора
- [ ] Настроить workflow между агентами
- [ ] Протестировать всю цепочку

### Этап 5: Тестирование (30-60 минут)
- [ ] Протестировать через API docs
- [ ] Протестировать через frontend
- [ ] Проверить обработку ошибок
- [ ] Подготовить примеры запросов
- [ ] Записать успешные сценарии

### Этап 6: Демо (30 минут)
- [ ] Подготовить презентацию кейса
- [ ] Записать demo сценарий
- [ ] Подготовить примеры запросов
- [ ] Проверить что все работает
- [ ] Продумать ответы на вопросы

## Файлы которые вы создаете/редактируете

### Создаете:
- `ml/mcp_server/your_tools.py` - ваши tools
- `ml/agents/your_agents.py` - ваши агенты
- `.env` - API ключи (НЕ коммитить!)

### Редактируете:
- `ml/mcp_server/__init__.py` - добавить импорты tools
- `ml/agents/__init__.py` - добавить импорты агентов

### НЕ трогаете:
- `backend/` - бэкенд (это моя зона)
- `frontend/` - фронтенд (это моя зона)
- `docker-compose.yml` - конфигурация
- `Makefile` - команды

## Быстрые команды

```bash
# Запустить все
make dev

# Проверить что работает
make check

# Перезапустить MCP сервер после изменений
docker-compose restart mcp_server

# Посмотреть логи
make logs

# Посмотреть логи MCP сервера
docker-compose logs -f mcp_server

# Остановить все
make down

# Очистить и перезапустить
make clean && make dev
```

## Тестирование

### Список tools
```bash
curl http://localhost:8001/tools/list
```

### Вызвать tool
```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "your_tool", "parameters": {...}}'
```

### Список агентов
```bash
curl http://localhost:8001/agents/list
```

### Выполнить агента
```bash
curl -X POST http://localhost:8001/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "your_agent", "input_data": {...}, "config": {}}'
```

## Решение проблем

### Ошибки импорта
```bash
docker-compose restart mcp_server
docker-compose logs mcp_server
```

### Tool не регистрируется
1. Проверь декоратор `@tool_registry.register()`
2. Проверь импорт в `__init__.py`
3. Перезапусти MCP сервер

### Агент не работает
1. Проверь логи: `docker-compose logs mcp_server`
2. Проверь API ключи в `.env`
3. Протестируй tools отдельно

### API ключи не работают
1. Проверь что ключ добавлен в `.env`
2. Перезапусти: `make down && make dev`
3. Проверь название переменной в коде

## Ресурсы

- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- `docs/HACKATHON_GUIDE.md` - детальный гайд
- `ml/examples/templates.py` - шаблоны кода
- `ml/examples/example_api_integration.py` - примеры API
- `ml/examples/example_multiagent.py` - примеры мультиагентов

## Критерии оценки (примерно)

- Работающий MCP сервер с публичными API
- Качество интеграции API
- Агент(ы) решают бизнес-задачу
- Демонстрация работы
- Код и архитектура
- Презентация и pitch

Удачи на хакатоне!
