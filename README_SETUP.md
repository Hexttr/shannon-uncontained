# Shannon-Uncontained - Полная настройка завершена ✅

## Статус: ГОТОВО К ИСПОЛЬЗОВАНИЮ

Система полностью настроена и протестирована. Все компоненты работают.

## Быстрый старт

### На сервере:
```bash
ssh root@72.56.79.153
cd /root/shannon-uncontained

# Запустить пентест на цель
./shannon.mjs generate https://target.com

# Просмотреть результаты
./shannon.mjs model show --workspace shannon-results/repos/target.com

# Экспортировать интерактивный граф
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view provenance
```

## Что настроено

- ✅ Node.js v20.20.0
- ✅ Все npm зависимости (412 пакетов)
- ✅ Ollama с моделью codellama:7b
- ✅ Все системные инструменты
- ✅ Все файлы из оригинала
- ✅ Все компоненты работают
- ✅ Все агенты доступны (37+)
- ✅ Все CLI команды работают

## Документация

- `USAGE_GUIDE.md` - Подробное руководство по использованию
- `COMPLETE_SETUP_STATUS.md` - Статус настройки
- `TEST_RESULTS_tcell_tj.md` - Результаты тестового прогона
- `.env` - Текущая конфигурация (Ollama)
- `.env.full` - Полная конфигурация со всеми опциями

## Переключение на продакшен

Отредактируйте `.env` на сервере:
```bash
nano /root/shannon-uncontained/.env
```

Раскомментируйте:
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
```

Закомментируйте Ollama строки.

## Все команды

См. `USAGE_GUIDE.md` для полного списка команд и опций.

## Репозиторий

Все изменения закоммичены и запушены в:
https://github.com/Hexttr/shannon-uncontained

