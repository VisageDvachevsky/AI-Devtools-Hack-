# Git настройка для команды

## Установка git hooks

После клонирования репозитория ОБЯЗАТЕЛЬНО установи git hooks:

```bash
make install-hooks
```

## Что делает pre-commit hook

Проверяет зоны ответственности перед каждым коммитом:

### Для backend/devops (VisageDvachevsky):
- Разрешает коммитить что угодно

### Для ML команды:
- Разрешает коммитить: `ml/`, `.env`, `docs/`
- Предупреждает если пытаешься изменить: `backend/`, `frontend/`, `docker-compose.yml` и т.д.

## Пример работы

### Сценарий 1: ML-щик коммитит свой код (OK)
```bash
git add ml/agents/my_agent.py
git commit -m "Add my agent"
# ✓ Коммит прошел без проблем
```

### Сценарий 2: ML-щик случайно изменил backend (Предупреждение)
```bash
git add backend/main.py
git commit -m "Fix something"

# Вывод:
========================================
    ВНИМАНИЕ! ЗОНА ОТВЕТСТВЕННОСТИ!
========================================

Вы (YourName) пытаетесь закоммитить изменения в зоне backend/devops:

  ✗ backend/main.py

Эти файлы должен менять только:
  ✓ VisageDvachevsky
  ✓ 82640121+VisageDvachevsky@users.noreply.github.com

Ваша зона ответственности:
  ✓ ml/agents/       - Ваши агенты
  ✓ ml/mcp_server/   - Ваши tools
  ✓ ml/examples/     - Примеры
  ✓ .env             - API ключи

Что делать:
  1. Отменить этот коммит (нажми Ctrl+C сейчас)
  2. Убрать файлы из staged: git reset HEAD <файл>
  3. Коммитить только ml/ файлы
```

## Настройка git config

Убедись что твой git config правильно настроен:

```bash
# Проверь текущие настройки
git config user.name
git config user.email

# Настрой если нужно
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Обход hook (только для backend/devops)

Если ДЕЙСТВИТЕЛЬНО нужно обойти hook:

```bash
git commit --no-verify -m "message"
```

**НЕ используй это без необходимости!**

## Зоны ответственности

### Backend/DevOps (VisageDvachevsky):
```
backend/           - FastAPI бэкенд
frontend/          - React фронтенд
docker-compose.yml - Docker конфигурация
Makefile           - Команды
pyproject.toml     - Python зависимости
scripts/           - Скрипты
.gitignore         - Git настройки
```

### ML команда:
```
ml/                - Весь ML код
  agents/          - Агенты
  mcp_server/      - MCP tools
  examples/        - Примеры
.env               - API ключи (не коммитить!)
docs/              - Документация (можно добавлять)
```

## Проблемы и решения

### Hook не работает
```bash
# Переустанови
make install-hooks

# Проверь права
ls -la .git/hooks/pre-commit
# Должно быть -rwxr-xr-x
```

### Hook блокирует нужный коммит
Свяжись с backend/devops (@VisageDvachevsky), обсудите изменения.

### Хочу отключить hook
```bash
# Временно
git commit --no-verify

# Полностью (НЕ рекомендуется)
rm .git/hooks/pre-commit
```

## Best practices

1. Всегда проверяй `git status` перед коммитом
2. Коммить маленькими порциями
3. Работай только в `ml/` папке
4. Не коммить `.env` файл
5. Пиши понятные commit messages

## Полезные команды

```bash
# Посмотреть что изменилось
git status

# Посмотреть diff
git diff

# Убрать файл из staged
git reset HEAD <file>

# Отменить изменения в файле
git checkout -- <file>

# Посмотреть историю
git log --oneline

# Посмотреть только свои коммиты
git log --author="Your Name"
```
