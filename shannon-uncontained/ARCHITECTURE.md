# Архитектура Shannon-Uncontained

## Обзор проекта

Shannon-Uncontained - это фреймворк для пентестинга с акцентом на эпистемическую систему учета неопределенности через EQBSL (Evidence-Quantified Bayesian Subjective Logic).

## Ключевые компоненты

### 1. Core System (src/core/)

#### WorldModel.js
- Центральный граф знаний
- Управление сущностями, утверждениями и связями
- Поддержка EQBSL тензоров для каждого утверждения
- Методы: addClaim(), addEvidence(), query(), propagate()

#### EpistemicLedger.js
- Управление EQBSL тензорами
- Формулы: b = r/(r+s+K), d = s/(r+s+K), u = K/(r+s+K)
- Декей (decay) доказательств во времени
- Транзитивное доверие с затуханием

#### BudgetManager.js
- Ограничения ресурсов: время, токены, сетевые запросы
- Предотвращение runaway агентов
- Профили: ci, recon-only, full

### 2. Local Source Generator (src/local-source-generator/)

#### Агенты LSGv2:
1. **Recon Agents:**
   - api-discovery.js - обнаружение API endpoints
   - fingerprinter.js - фингерпринтинг технологий
   - ghost-traffic.js - анализ скрытого трафика
   - dark-matter.js - обнаружение скрытых ресурсов
   - shadow-it.js - обнаружение shadow IT

2. **Exploitation Agents:**
   - exploit-auth.js - тестирование аутентификации
   - exploit-authz.js - тестирование авторизации
   - exploit-injection.js - SQL/NoSQL/XSS инъекции
   - exploit-ssrf.js - SSRF атаки
   - exploit-xss.js - XSS атаки

3. **Analysis Agents:**
   - llm-analyzer.js - LLM анализ кода/конфигов
   - misconfig-detector.js - обнаружение мисконфигураций
   - vuln-mapper.js - маппинг уязвимостей на OWASP ASVS

#### Crawlers:
- active-crawl.js - активный краулинг с Playwright
- js-analysis.js - анализ JavaScript кода
- network-recon.js - сетевой рекон

#### Generators:
- pseudo-source-builder.js - построение псевдо-исходников из черного ящика

### 3. Evidence Graph (src/local-source-generator/v2/worldmodel/)

#### evidence-graph.js
- Append-only event store
- Content-addressed события
- Provenance tracking
- Методы: append(), query(), getProvenance()

### 4. CLI System (src/cli/)

#### Commands:
- RunCommand.js - полный пайплайн пентестинга
- ModelCommand.js - интроспекция модели (show, graph, export-html, why)
- EvidenceCommand.js - управление доказательствами (stats)

#### Execution:
- execution-runner.js - оркестрация выполнения
- input-validator.js - валидация входных данных
- prompts.js - интерактивные промпты
- ui.js - CLI интерфейс

### 5. AI Integration (src/ai/)

#### llm-client.js
- Поддержка множественных провайдеров:
  - OpenAI (GPT-4, GPT-4o)
  - Anthropic (Claude 3.5 Sonnet, Opus)
  - GitHub Models (бесплатный tier)
  - Ollama (локальный)
  - llama.cpp (локальный)

#### claude-executor.js
- Интеграция с Claude Agent SDK
- Выполнение кода агентами

### 6. Analyzers (src/analyzers/)

- ErrorPatternAnalyzer.js - анализ паттернов ошибок
- HTTPMethodAnalyzer.js - анализ HTTP методов
- SecurityHeaderAnalyzer.js - анализ security headers

### 7. Reporting (src/local-source-generator/reporting/)

- report-generator.js - генерация отчетов
- cvss-calculator.js - расчет CVSS scores
- webhook-reporter.js - отправка в webhook

### 8. MCP Server (mcp-server/)

- Интеграция с Model Context Protocol
- Tools: generate-totp, save-deliverable
- Валидация очередей и TOTP

## Структура данных

### EQBSL Tensor
```javascript
{
  b: 0.7,  // Belief (уверенность в истинности)
  d: 0.1,  // Disbelief (уверенность в ложности)
  u: 0.2,  // Uncertainty (неопределенность)
  a: 0.5   // Base rate (базовая вероятность)
}
// b + d + u = 1
// Expectation E = b + a*u
```

### Claim Structure
```javascript
{
  id: "claim:port:443:open",
  subject: "port:443",
  predicate: "is_open",
  value: true,
  evidence: ["evidence:nmap:scan:123"],
  tensor: { b: 0.8, d: 0.1, u: 0.1, a: 0.5 },
  timestamp: "2025-01-XX...",
  agent: "NmapAgent"
}
```

### Evidence Structure
```javascript
{
  id: "evidence:nmap:scan:123",
  type: "port_scan",
  source: "nmap",
  target: "example.com",
  observations: [
    { port: 443, state: "open", service: "https" }
  ],
  tensor: { b: 0.9, d: 0.05, u: 0.05, a: 0.5 },
  timestamp: "2025-01-XX...",
  metadata: { tool_version: "7.94" }
}
```

## Пайплайн выполнения

1. **Phase 0: Initialization**
   - Загрузка конфигурации
   - Инициализация WorldModel, EpistemicLedger, BudgetManager
   - Создание workspace

2. **Phase 1: Black-box Reconnaissance**
   - Запуск LSGv2 агентов:
     - Subdomain discovery (subfinder, amass)
     - Port scanning (nmap)
     - Web crawling (katana, active-crawl)
     - Technology fingerprinting
     - API discovery
   - Сбор доказательств в Evidence Graph
   - Построение WorldModel

3. **Phase 2: Analysis**
   - LLM анализ собранных данных
   - Обнаружение мисконфигураций
   - Маппинг на OWASP ASVS
   - Построение псевдо-исходников

4. **Phase 3: Exploitation**
   - Запуск exploitation агентов
   - Тестирование уязвимостей
   - Валидация через ground-truth проверки

5. **Phase 4: Reporting**
   - Генерация отчета с EQBSL confidence scores
   - Экспорт HTML графа знаний
   - CVSS расчеты

## Конфигурация

### configs/example-config.yaml
```yaml
target: "https://example.com"
budget:
  max_time_ms: 3600000
  max_tokens: 100000
  max_network_requests: 1000
agents:
  enabled:
    - NmapAgent
    - SubfinderAgent
    - ActiveCrawlAgent
  disabled:
    - ExploitAgent  # для recon-only режима
llm:
  provider: "openai"
  model: "gpt-4"
```

## Workspace Structure

```
workspaces/
└── shannon-results/
    └── repos/
        └── example.com/
            ├── evidence/
            │   └── evidence-graph.jsonl
            ├── world-model/
            │   ├── entities.json
            │   ├── claims.json
            │   └── relations.json
            ├── reports/
            │   └── shannon-report.md
            └── checkpoints/
                └── checkpoint-*.json
```

## Зависимости

### Основные:
- Node.js 18+
- TensorFlow.js (для ML компонентов)
- Playwright (для браузерного краулинга)
- Commander.js (CLI)
- Axios (HTTP клиент)

### Инструменты пентестинга:
- nmap
- subfinder
- amass
- katana
- whatweb
- nuclei (опционально)

## Интеграция с сервером

### Модуль server-connection.js
- Подключение через paramiko (SSH)
- Выполнение команд на удаленном сервере
- Установка зависимостей
- Запуск агентов
- Мониторинг выполнения

## Расширяемость

### Добавление нового агента:
1. Создать файл в `src/local-source-generator/agents/`
2. Реализовать интерфейс Agent:
   - `async run(context)` - основной метод
   - `getBudgetRequirements()` - требования к ресурсам
   - `getName()` - имя агента
3. Зарегистрировать в `src/local-source-generator/index.js`

### Добавление нового LLM провайдера:
1. Расширить `src/ai/llm-client.js`
2. Добавить конфигурацию в `.env.example`
3. Обновить документацию

