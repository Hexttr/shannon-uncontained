# Evidence Graph - Объяснение

## Что такое Evidence Graph?

**Evidence Graph** - это неизменяемое (immutable) хранилище всех наблюдений, собранных во время пентеста. Это центральный источник правды (source of truth) для всех агентов.

### Ключевые особенности:

- **Append-only**: События только добавляются, никогда не удаляются
- **Content-hashed IDs**: Одинаковое наблюдение = одинаковый ID
- **Индексирование**: По источнику, цели, типу события
- **Provenance**: Полная история откуда взялось каждое наблюдение

---

## Анализ событий из вашего пентеста

### Статистика:

- **Всего событий**: 273
- **Источников**: 11 различных инструментов/агентов

### Типы событий:

| Тип события | Количество | Описание |
|------------|-----------|----------|
| `endpoint_discovered` | 231 | Обнаруженные API endpoints |
| `validation_result` | 30 | Результаты валидации кода |
| `security_header_missing` | 3 | Отсутствующие security headers |
| `dns_record` | 2 | DNS записи (subdomain) |
| `waf_detected` | 1 | Обнаружен WAF |
| `tech_detection` | 1 | Обнаруженные технологии |
| `port_scan` | 1 | Результаты сканирования портов |
| `tool_timeout` | 1 | Таймаут инструмента |
| `cmdi_tested` | 1 | Тест на Command Injection |
| `sqli_tested` | 1 | Тест на SQL Injection |
| `xss_tested` | 1 | Тест на XSS |

### Источники событий:

| Источник | Событий | Что делает |
|---------|---------|------------|
| `gau` | 231 | Обнаружение endpoints из истории |
| `ValidationHarness` | 30 | Валидация сгенерированного кода |
| `SecurityHeaderAnalyzer` | 3 | Анализ security headers |
| `subfinder` | 2 | Поиск subdomain'ов |
| `WAFDetector` | 1 | Обнаружение WAF |
| `whatweb` | 1 | Определение технологий |
| `nmap` | 1 | Сканирование портов |
| `CrawlerAgent` | 1 | Кrawling (с таймаутом) |
| `CommandInjectionAgent` | 1 | Тест на Command Injection |
| `SQLmapAgent` | 1 | Тест на SQL Injection |
| `XSSValidatorAgent` | 1 | Тест на XSS |

### Категоризация:

- **Endpoint Discovery**: 231 событие (84.6%) - основная часть
- **Security Testing**: 31 событие (11.4%) - тесты безопасности
- **Network Recon**: 3 события (1.1%) - разведка сети
- **Technology Detection**: 2 события (0.7%) - определение технологий
- **Other**: 6 событий (2.2%) - прочее

---

## Примеры событий

### 1. DNS Record (subfinder)
```json
{
  "source": "subfinder",
  "event_type": "dns_record",
  "target": "tcell.tj",
  "payload": {
    "subdomain": "digital5.tcell.tj",
    "record_type": "subdomain"
  },
  "timestamp": "2026-02-03T14:14:44.304Z"
}
```

### 2. WAF Detected
```json
{
  "source": "WAFDetector",
  "type": "waf_detected",
  "data": {
    "waf": "nginx_waf",
    "confidence": 1,
    "blockedPayloads": 3
  }
}
```

### 3. Endpoint Discovered (gau)
```json
{
  "source": "gau",
  "event_type": "endpoint_discovered",
  "target": "https://tcell.tj",
  "payload": {
    "url": "http://www.tcell.tj:80/",
    "path": "/",
    "method": "GET"
  }
}
```

### 4. Port Scan (nmap)
```json
{
  "source": "nmap",
  "event_type": "port_scan",
  "target": "tcell.tj",
  "payload": {
    "port": 80,
    "protocol": "tcp",
    "state": "open",
    "service": "http nginx"
  }
}
```

---

## Что делает Shannon с событиями?

### 1. Evidence Graph
Собирает все события от агентов в единое хранилище

### 2. Target Model
Анализирует события и создает нормализованные сущности:
- **Endpoints** (API endpoints)
- **Components** (компоненты системы)
- **Data Models** (модели данных)
- **Auth Flows** (потоки аутентификации)
- **Workflows** (бизнес-логика)

### 3. Epistemic Ledger
Создает claims (утверждения) с оценкой уверенности:
- **b (belief)**: Степень уверенности что утверждение верно
- **d (disbelief)**: Степень уверенности что утверждение ложно
- **u (uncertainty)**: Степень неопределенности
- **a (base rate)**: Базовая вероятность

### 4. Artifact Manifest
Генерирует код на основе модели

---

## Преимущества подхода

✅ **Provenance**: Отслеживание откуда взялась информация  
✅ **Uncertainty Quantification**: Количественная оценка неопределенности  
✅ **Deterministic**: Воспроизводимые результаты  
✅ **Traceability**: Полная прослеживаемость данных  

---

## Где хранятся события?

Все события хранятся в файле:
```
pentest-results/repos/tcell.tj/world-model.json
```

В секции `evidence_graph.events` находится массив всех 273 событий.

---

## Итого

В вашем пентесте собрано **273 события** от **11 различных источников**.

**Основные находки:**
- 231 endpoint обнаружен через `gau`
- 30 результатов валидации кода
- 3 отсутствующих security header
- 1 WAF обнаружен (nginx_waf)
- Тесты на Command Injection, SQL Injection, XSS выполнены

Эти события используются для:
1. Построения модели цели (world-model.json)
2. Генерации кода приложения
3. Создания документации
4. Оценки уверенности в находках

