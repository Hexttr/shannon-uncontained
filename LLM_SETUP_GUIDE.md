# Руководство по настройке LLM провайдеров

## Поддерживаемые провайдеры

Shannon-Uncontained поддерживает следующие LLM провайдеры:

### Локальные (бесплатные для тестов)
- ✅ **Ollama** - полностью поддерживается
- ✅ **llama.cpp** - поддерживается
- ✅ **LM Studio** - поддерживается

### Облачные (для продакшена)
- ✅ **OpenAI** (GPT-4, GPT-4o)
- ✅ **Anthropic Claude** (Claude 3.5 Sonnet, Claude 4.5 Sonnet)
- ✅ **GitHub Models** (бесплатный tier)
- ✅ **OpenRouter** (доступ к множеству моделей)

## Рекомендуемая конфигурация

### Для тестов: Ollama (бесплатно)

Ollama полностью поддерживается и идеально подходит для локального тестирования.

#### 1. Установка Ollama

**На Linux (сервер):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**На Windows/Mac:**
Скачайте с [ollama.com](https://ollama.com)

#### 2. Загрузка модели

```bash
# Рекомендуемые модели для пентестинга:
ollama pull llama3.2        # Быстрая, хорошая для тестов
ollama pull llama3.1:70b    # Более мощная, требует больше RAM
ollama pull codellama       # Специализированная для кода
ollama pull mistral         # Альтернатива Llama
```

#### 3. Настройка .env для тестов

```bash
# .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
# Или для более мощной модели:
# LLM_MODEL=llama3.1:70b
```

#### 4. Проверка работы Ollama

```bash
# Проверить что Ollama запущен
curl http://localhost:11434/api/tags

# Протестировать модель
ollama run llama3.2 "Hello, test"
```

### Для продакшена: Claude 4.5 Sonnet

Claude 4.5 Sonnet поддерживается через два механизма:

#### Вариант 1: Через LSGv2 Orchestrator (рекомендуется)

LSGv2 использует собственный LLM клиент который поддерживает Anthropic напрямую:

```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
# Или для Claude 4.5 Sonnet (когда доступен):
# LLM_MODEL=claude-4-5-sonnet-20250101
```

#### Вариант 2: Через Claude Executor

Claude Executor использует `@anthropic-ai/claude-agent-sdk`:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your_key_here
# Claude Executor автоматически использует Claude SDK
```

#### Получение API ключа

1. Зарегистрируйтесь на [console.anthropic.com](https://console.anthropic.com/)
2. Создайте API ключ
3. Добавьте в `.env` файл

**Стоимость:** ~$0.003 за 1K входных токенов, ~$0.015 за 1K выходных токенов

## Переключение между тестами и продакшеном

### Быстрое переключение через переменные окружения

**Для тестов (Ollama):**
```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
```

**Для продакшена (Claude 4.5 Sonnet):**
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your_key_here
export LLM_MODEL=claude-3-5-sonnet-20241022
```

### Использование разных .env файлов

**Создайте два файла:**

`.env.test` (для тестов):
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

`.env.production` (для продакшена):
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
```

**Использование:**
```bash
# Для тестов
cp .env.test .env
./shannon.mjs generate https://example.com

# Для продакшена
cp .env.production .env
./shannon.mjs generate https://example.com
```

## Настройка на сервере

### 1. Установка Ollama на сервере

```bash
ssh root@72.56.79.153
curl -fsSL https://ollama.com/install.sh | sh

# Запуск Ollama в фоне
ollama serve &

# Загрузка модели
ollama pull llama3.2
```

### 2. Настройка .env на сервере

```bash
cd /root/shannon-uncontained
nano .env
```

**Для тестов:**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
```

**Для продакшена:**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
```

### 3. Проверка настройки

```bash
# Проверить Ollama
curl http://localhost:11434/api/tags

# Проверить Anthropic (если настроен)
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

## Продвинутая конфигурация

### Использование разных моделей для разных задач

```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Базовые модели
LLM_MODEL=claude-3-5-sonnet-20241022

# Для быстрых задач (классификация)
LLM_FAST_MODEL=claude-3-haiku-20240307

# Для сложных задач (архитектурный анализ)
LLM_SMART_MODEL=claude-3-5-sonnet-20241022

# Для генерации кода
LLM_CODE_MODEL=claude-3-5-sonnet-20241022
```

### Кастомный endpoint для Claude

Если используете прокси или кастомный endpoint:

```bash
# .env
LLM_PROVIDER=custom
LLM_BASE_URL=https://your-claude-proxy.com/v1
ANTHROPIC_API_KEY=sk-ant-your_key_here
LLM_MODEL=claude-3-5-sonnet-20241022
```

## Troubleshooting

### Ollama не отвечает

```bash
# Проверить статус
ps aux | grep ollama

# Перезапустить
pkill ollama
ollama serve &

# Проверить порт
netstat -tlnp | grep 11434
```

### Claude API ошибки

```bash
# Проверить API ключ
echo $ANTHROPIC_API_KEY

# Проверить доступность API
curl -I https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Проблемы с моделями

Если модель не найдена, проверьте доступные модели:

**Для Ollama:**
```bash
ollama list
```

**Для Anthropic:**
Проверьте [документацию Anthropic](https://docs.anthropic.com/claude/docs/models-overview) для актуального списка моделей.

## Рекомендации

1. **Для разработки и тестов:** Используйте Ollama с llama3.2 - быстро, бесплатно, достаточно для большинства задач
2. **Для продакшена:** Используйте Claude 4.5 Sonnet через `LLM_PROVIDER=anthropic` - лучшее качество для критичных задач
3. **Для экономии:** Используйте Claude Haiku для простых задач, Sonnet для сложных
4. **Для максимальной производительности:** Используйте локальные модели (Ollama) когда скорость важнее качества

## Примеры использования

### Тестовый запуск с Ollama

```bash
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
./shannon.mjs generate https://test-target.com
```

### Продакшен запуск с Claude

```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-your_key_here
export LLM_MODEL=claude-3-5-sonnet-20241022
./shannon.mjs generate https://production-target.com
```

## Дополнительная информация

- [Ollama документация](https://ollama.com/docs)
- [Anthropic API документация](https://docs.anthropic.com/claude/reference)
- [Список моделей Anthropic](https://docs.anthropic.com/claude/docs/models-overview)

