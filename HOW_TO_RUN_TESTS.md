# Как провести тест в Shannon-Uncontained

## 🎯 Быстрый старт

### 1. Подключиться к серверу
```bash
ssh root@72.56.79.153
cd /root/shannon-uncontained
```

### 2. Запустить тест на цель
```bash
# Полный пайплайн пентестинга
./shannon.mjs generate https://target.com

# Или с опциями
./shannon.mjs generate https://target.com --framework express --parallel 8
```

### 3. Просмотреть результаты

#### В терминале:
```bash
# Показать World Model с графиками
./shannon.mjs model show --workspace shannon-results/repos/target.com

# ASCII граф знаний
./shannon.mjs model graph --workspace shannon-results/repos/target.com

# Статистика Evidence
./shannon.mjs evidence stats shannon-results/repos/target.com
```

#### В браузере (интерактивная визуализация):
```bash
# Экспортировать интерактивный HTML граф
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view provenance -o graph.html

# Затем открыть в браузере
# Можно скопировать файл на локальную машину через scp:
scp root@72.56.79.153:/root/shannon-uncontained/graph.html ./
```

## 📊 Режимы визуализации

### 1. Topology (топология)
Инфраструктурная сеть: subdomains → paths → ports
```bash
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view topology -o topology.html
```

### 2. Evidence (доказательства)
Provenance агентов: какой агент что обнаружил
```bash
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view evidence -o evidence.html
```

### 3. Provenance (происхождение)
EBSL-native граф: source → event_type → target с tensor edges
```bash
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view provenance -o provenance.html
```

## 🔍 Примеры команд

### Быстрый recon (без AI синтеза)
```bash
./shannon.mjs generate https://target.com --no-ai
```

### Полный анализ с синтезом кода
```bash
./shannon.mjs generate https://target.com --framework express --parallel 8 -v
```

### OSINT по email
```bash
./shannon.mjs osint email user@target.com
```

### Повторный синтез на существующем World Model
```bash
./shannon.mjs synthesize shannon-results/repos/target.com --framework express
```

## 📁 Структура результатов

После выполнения теста результаты будут в:
```
shannon-results/repos/target.com/
├── world-model.json          # Центральный граф знаний
├── graph.html                # Интерактивная визуализация (если экспортировали)
├── API.md                    # API документация
├── ARCHITECTURE.md           # Архитектурная документация
├── EVIDENCE.md               # Документация доказательств
├── README.md                 # Основная документация
├── app.js                    # Сгенерированный код
├── api.test.js               # Тесты API
├── security.test.js          # Тесты безопасности
└── ...
```

## 🌐 Просмотр HTML визуализации

HTML файл содержит интерактивный граф с D3.js:
- **Zoom**: колесико мыши или pinch
- **Pan**: перетаскивание
- **Hover**: информация о узлах
- **Click**: детали узла
- **Фильтры**: по типу, уверенности, неопределенности

## 💡 Советы

1. **Для быстрого теста**: используйте `--no-ai` чтобы пропустить синтез кода
2. **Для полного анализа**: используйте `--framework express` или `fastapi`
3. **Для параллельности**: увеличьте `--parallel` до 8-16 для быстрых серверов
4. **Для отладки**: используйте `-v` для подробного вывода

## 🔧 Настройка для продакшена

Если хотите использовать Claude вместо Ollama:
```bash
nano .env
# Раскомментировать:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your_key_here
# LLM_MODEL=claude-3-5-sonnet-20241022
```

