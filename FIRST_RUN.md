# Инструкции для первого запуска

## Автоматическая настройка

```bash
cp .env.example .env
make dev
```

Подожди 1-2 минуты пока все сервисы запустятся.

## Проверка настройки

```bash
./scripts/test_setup.sh
```

Должно показать:
- Все сервисы работают
- Примеры инструментов зарегистрированы
- Пример агента работает

## Сервисы

- Backend: http://localhost:8000
- Backend API Docs: http://localhost:8000/docs
- MCP Server: http://localhost:8001
- Frontend: http://localhost:3000

## Частые проблемы при первом запуске

### Порт уже занят
```bash
make down
make dev
```

### Poetry install не работает
Удали poetry.lock если существует:
```bash
rm poetry.lock 2>/dev/null
make dev
```

### Docker build не работает
```bash
make clean
make dev
```

### Frontend не запускается
Это нормально при первом запуске. Frontend перезапустится автоматически после установки node_modules.

## Следующие шаги

Для ML команды: Читай `docs/QUICKSTART_ML.md`

Для тестирования API: Открой http://localhost:8000/docs
