#!/bin/bash

echo "Устанавливаем git hooks..."

# Копируем pre-commit hook
cp scripts/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✓ Pre-commit hook установлен"
echo ""
echo "Что он делает:"
echo "  - Проверяет кто делает коммит"
echo "  - Если ML-щик пытается изменить backend/frontend - предупреждает"
echo "  - Дает возможность отменить коммит"
echo ""
echo "Готово!"
