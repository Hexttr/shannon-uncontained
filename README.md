# Shannon-Uncontained Pentesting Framework

Пентест-фреймворк на основе [Shannon-Uncontained](https://github.com/Steake/shannon-uncontained) с расширенным функционалом.

## Описание

Shannon-Uncontained - это фреймворк для пентестинга, который использует AI для автоматизации процесса тестирования на проникновение. Проект использует эпистемический подход к безопасности, где каждое наблюдение кодируется с помощью EQBSL тензора (Evidence-Quantified Bayesian Subjective Logic).

## Структура проекта

- `server_analyzer.py` - Скрипт для подключения к серверу и анализа файлов
- `analyze_server_structure.py` - Детальный анализ структуры проекта на сервере
- `server_files/` - Файлы, скачанные с сервера
- `requirements.txt` - Python зависимости

## Доступ к серверу

Сервер: 72.56.79.153
Пользователь: root
Пароль: m8J@2_6whwza6U

## Установка

```bash
pip install -r requirements.txt
```

## Использование

### Анализ сервера

```bash
python server_analyzer.py
```

### Анализ структуры проекта

```bash
python analyze_server_structure.py
```

## Основные компоненты

- **shannon.mjs** - Основной скрипт пентестинга
- **local-source-generator.mjs** - Генератор локальных источников
- **src/** - Исходный код фреймворка
- **nuclei-templates/** - Шаблоны для Nuclei

## Зависимости

Проект требует установки следующих инструментов:
- Node.js 18+
- Nmap (с NSE)
- Go-based инструменты (subfinder, httpx, katana, nuclei, gau)
- Metasploit Framework (опционально)

## Лицензия

AGPL-3.0

