# План реализации Shannon-Uncontained

## Этап 1: Подготовка инфраструктуры ✅

### 1.1 Анализ репозитория
- [x] Изучить структуру Steake/shannon-uncontained
- [x] Определить ключевые компоненты
- [x] Составить архитектурный план

### 1.2 Настройка сервера
- [ ] Создать модуль подключения через paramiko
- [ ] Подключиться к серверу 72.56.79.153
- [ ] Очистить существующие данные
- [ ] Установить Node.js 18+
- [ ] Установить системные зависимости (nmap, subfinder, etc.)

### 1.3 Клонирование репозитория
- [ ] Скачать все файлы из Steake/shannon-uncontained
- [ ] Исправить проблемы с путями файлов (Windows compatibility)
- [ ] Проверить целостность структуры

## Этап 2: Core System (src/core/)

### 2.1 EpistemicLedger.js
- [ ] Реализовать EQBSL тензор структуру
- [ ] Реализовать формулы: b, d, u, a
- [ ] Реализовать decay механизм
- [ ] Реализовать транзитивное доверие
- [ ] Написать тесты

### 2.2 WorldModel.js
- [ ] Реализовать граф знаний
- [ ] Методы добавления сущностей и утверждений
- [ ] Интеграция с EpistemicLedger
- [ ] Методы запросов и поиска
- [ ] Propagate механизм
- [ ] Написать тесты

### 2.3 BudgetManager.js
- [ ] Реализовать отслеживание ресурсов
- [ ] Профили: ci, recon-only, full
- [ ] Проверка лимитов перед выполнением агентов
- [ ] Написать тесты

## Этап 3: Evidence Graph System

### 3.1 evidence-graph.js
- [ ] Реализовать append-only event store
- [ ] Content-addressed события
- [ ] Provenance tracking
- [ ] Методы query и getProvenance
- [ ] Интеграция с WorldModel

## Этап 4: Local Source Generator v2

### 4.1 Recon Agents
- [ ] api-discovery.js - обнаружение API endpoints
- [ ] fingerprinter.js - фингерпринтинг технологий
- [ ] ghost-traffic.js - анализ скрытого трафика
- [ ] dark-matter.js - обнаружение скрытых ресурсов
- [ ] shadow-it.js - обнаружение shadow IT

### 4.2 Crawlers
- [ ] active-crawl.js - активный краулинг с Playwright
- [ ] js-analysis.js - анализ JavaScript кода
- [ ] network-recon.js - сетевой рекон

### 4.3 Generators
- [ ] pseudo-source-builder.js - построение псевдо-исходников

### 4.4 Analyzers
- [ ] llm-analyzer.js - LLM анализ
- [ ] misconfig-detector.js - обнаружение мисконфигураций
- [ ] vuln-mapper.js - маппинг уязвимостей

## Этап 5: Exploitation Agents

### 5.1 Реализация агентов
- [ ] exploit-auth.js - тестирование аутентификации
- [ ] exploit-authz.js - тестирование авторизации
- [ ] exploit-injection.js - SQL/NoSQL/XSS инъекции
- [ ] exploit-ssrf.js - SSRF атаки
- [ ] exploit-xss.js - XSS атаки

### 5.2 Ground-truth валидация
- [ ] Механизм проверки результатов эксплуатации
- [ ] Интеграция с WorldModel

## Этап 6: AI Integration

### 6.1 LLM Client
- [ ] Поддержка OpenAI
- [ ] Поддержка Anthropic Claude
- [ ] Поддержка GitHub Models
- [ ] Поддержка Ollama
- [ ] Поддержка llama.cpp
- [ ] Единый интерфейс для всех провайдеров

### 6.2 Claude Executor
- [ ] Интеграция с Claude Agent SDK
- [ ] Выполнение кода агентами
- [ ] Безопасное выполнение

## Этап 7: CLI System

### 7.1 Основные команды
- [ ] shannon.mjs - главная точка входа
- [ ] RunCommand.js - команда `run`
- [ ] ModelCommand.js - команды `model show/graph/export-html/why`
- [ ] EvidenceCommand.js - команда `evidence stats`

### 7.2 Execution Runner
- [ ] Оркестрация выполнения агентов
- [ ] Управление фазами пайплайна
- [ ] Checkpoint механизм
- [ ] Resume функциональность

### 7.3 UI Components
- [ ] Прогресс бары
- [ ] Цветной вывод
- [ ] Интерактивные промпты
- [ ] Форматирование таблиц

## Этап 8: Reporting System

### 8.1 Report Generator
- [ ] Генерация markdown отчетов
- [ ] Интеграция EQBSL confidence scores
- [ ] OWASP ASVS маппинг
- [ ] CVSS расчеты

### 8.2 Visualization
- [ ] ASCII граф знаний
- [ ] HTML экспорт с D3.js
- [ ] Три режима: topology, evidence, provenance
- [ ] Интерактивная навигация

## Этап 9: Configuration & Setup

### 9.1 Configuration System
- [ ] Парсинг YAML конфигов
- [ ] Валидация схемы (ajv)
- [ ] Переменные окружения (.env)
- [ ] Профили конфигурации

### 9.2 Setup Scripts
- [ ] setup.sh для Linux/Mac
- [ ] setup.ps1 для Windows
- [ ] Проверка зависимостей
- [ ] Установка инструментов

## Этап 10: Testing & Validation

### 10.1 Unit Tests
- [ ] Тесты для всех core компонентов
- [ ] Тесты для агентов
- [ ] Тесты для CLI команд
- [ ] Покрытие > 80%

### 10.2 Integration Tests
- [ ] Полный пайплайн на тестовом таргете
- [ ] Проверка всех агентов
- [ ] Проверка отчетов
- [ ] Проверка визуализации

### 10.3 End-to-End Tests
- [ ] Тест на реальном таргете
- [ ] Проверка всех функций
- [ ] Производительность
- [ ] Стабильность

## Этап 11: Deployment на сервер

### 11.1 Server Setup
- [ ] Установка Node.js через nvm
- [ ] Установка системных пакетов
- [ ] Настройка переменных окружения
- [ ] Настройка LLM провайдера

### 11.2 Service Configuration
- [ ] Systemd service (опционально)
- [ ] Логирование
- [ ] Мониторинг
- [ ] Backup механизм

## Этап 12: Documentation

### 12.1 User Documentation
- [ ] README.md с примерами
- [ ] Quick Start Guide
- [ ] Configuration Guide
- [ ] Troubleshooting Guide

### 12.2 Developer Documentation
- [ ] Architecture документация
- [ ] API Reference
- [ ] Contributing Guide
- [ ] EQBSL Primer

## Приоритеты реализации

### Критический путь (Must Have):
1. Core System (WorldModel, EpistemicLedger, BudgetManager)
2. Evidence Graph
3. Базовые Recon агенты (nmap, subfinder, crawl)
4. CLI команды (run, generate, model show)
5. LLM интеграция (минимум один провайдер)

### Важно (Should Have):
6. Все LSGv2 агенты
7. Exploitation агенты
8. Reporting система
9. Визуализация графа

### Желательно (Nice to Have):
10. MCP Server интеграция
11. ML Training компоненты
12. Расширенные аналитики
13. Webhook интеграции

## Метрики успеха

- [ ] Все core компоненты реализованы и протестированы
- [ ] Все агенты из оригинального репозитория реализованы
- [ ] Полный пайплайн работает end-to-end
- [ ] Документация полная и актуальная
- [ ] Производительность соответствует требованиям
- [ ] Код соответствует стандартам качества

## Риски и митигация

### Риск 1: Проблемы с путями файлов на Windows
**Митигация:** Использовать path.join(), нормализация путей

### Риск 2: Зависимости от внешних инструментов
**Митигация:** Проверка наличия инструментов, fallback механизмы

### Риск 3: LLM API лимиты и costs
**Митигация:** BudgetManager, кэширование, локальные провайдеры

### Риск 4: Производительность на больших таргетах
**Митигация:** Оптимизация запросов, инкрементальная обработка

