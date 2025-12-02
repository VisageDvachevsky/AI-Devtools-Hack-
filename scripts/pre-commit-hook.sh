#!/bin/bash

# Pre-commit hook для проверки зон ответственности

# Цвета для вывода
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Зона ответственности backend/devops
BACKEND_USER="VisageDvachevsky"
BACKEND_EMAIL="82640121+VisageDvachevsky@users.noreply.github.com"

# Получаем текущего пользователя
CURRENT_USER=$(git config user.name)
CURRENT_EMAIL=$(git config user.email)

# Файлы которые может менять только backend/devops
PROTECTED_PATHS=(
    "backend/"
    "frontend/"
    "docker-compose.yml"
    "Makefile"
    "pyproject.toml"
    ".gitignore"
    "scripts/"
)

# Получаем список измененных файлов
CHANGED_FILES=$(git diff --cached --name-only)

# Проверяем, является ли пользователь backend/devops
IS_BACKEND_USER=false
if [[ "$CURRENT_USER" == "$BACKEND_USER" ]] || [[ "$CURRENT_EMAIL" == "$BACKEND_EMAIL" ]]; then
    IS_BACKEND_USER=true
fi

# Если это backend/devops - разрешаем все
if [ "$IS_BACKEND_USER" = true ]; then
    exit 0
fi

# Проверяем, изменяет ли ML-щик защищенные файлы
PROTECTED_FILES_CHANGED=()
for file in $CHANGED_FILES; do
    for protected in "${PROTECTED_PATHS[@]}"; do
        if [[ $file == $protected* ]]; then
            PROTECTED_FILES_CHANGED+=("$file")
            break
        fi
    done
done

# Если ML-щик изменяет защищенные файлы - предупреждаем
if [ ${#PROTECTED_FILES_CHANGED[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}    ВНИМАНИЕ! ЗОНА ОТВЕТСТВЕННОСТИ!    ${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Вы (${CURRENT_USER}) пытаетесь закоммитить изменения в зоне backend/devops:${NC}"
    echo ""
    for file in "${PROTECTED_FILES_CHANGED[@]}"; do
        echo -e "  ${RED}✗${NC} $file"
    done
    echo ""
    echo -e "${YELLOW}Эти файлы должен менять только:${NC}"
    echo -e "  ${GREEN}✓${NC} $BACKEND_USER"
    echo -e "  ${GREEN}✓${NC} $BACKEND_EMAIL"
    echo ""
    echo -e "${YELLOW}Ваша зона ответственности:${NC}"
    echo -e "  ${GREEN}✓${NC} ml/agents/       - Ваши агенты"
    echo -e "  ${GREEN}✓${NC} ml/mcp_server/   - Ваши tools"
    echo -e "  ${GREEN}✓${NC} ml/examples/     - Примеры"
    echo -e "  ${GREEN}✓${NC} .env             - API ключи"
    echo ""
    echo -e "${RED}Что делать:${NC}"
    echo "  1. Отменить этот коммит (нажми Ctrl+C сейчас)"
    echo "  2. Убрать файлы из staged: git reset HEAD <файл>"
    echo "  3. Коммитить только ml/ файлы"
    echo ""
    echo -e "${YELLOW}Или нажми Enter чтобы продолжить (НЕ РЕКОМЕНДУЕТСЯ)${NC}"
    read -p ""

    # Даем возможность отменить
    echo ""
    echo -e "${RED}Вы уверены что хотите закоммитить изменения в чужой зоне?${NC}"
    echo "Введите 'yes' чтобы продолжить, или любой другой текст чтобы отменить:"
    read -p "> " CONFIRM

    if [[ "$CONFIRM" != "yes" ]]; then
        echo ""
        echo -e "${GREEN}Коммит отменен. Хорошее решение!${NC}"
        echo ""
        exit 1
    else
        echo ""
        echo -e "${YELLOW}Коммит продолжается... Убедись что знаешь что делаешь!${NC}"
        echo ""
    fi
fi

exit 0
