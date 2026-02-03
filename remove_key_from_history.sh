#!/bin/bash
# Скрипт для удаления API ключа из истории git

# Используем git filter-branch для замены ключа во всех коммитах
git filter-branch --force --index-filter \
  "git update-index --remove setup_claude_api.py 2>/dev/null || true" \
  --prune-empty --tag-name-filter cat -- --all

# Или заменяем ключ на placeholder
git filter-branch --force --tree-filter \
  "if [ -f setup_claude_api.py ]; then sed -i 's/sk-ant-api03-[A-Za-z0-9_-]*/ANTHROPIC_API_KEY_FROM_ENV/g' setup_claude_api.py; fi" \
  --prune-empty --tag-name-filter cat -- --all

