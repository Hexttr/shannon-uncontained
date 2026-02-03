# Веб-интерфейс Shannon-Uncontained

## ✅ Веб-интерфейс создан и запущен!

**Доступ:** http://72.56.79.153:3000

## Возможности

### 1. Запуск тестов
- Введите URL цели
- Выберите фреймворк (Express.js или FastAPI)
- Нажмите "Запустить тест"
- Следите за прогрессом в реальном времени

### 2. Просмотр результатов
- Автоматический список всех workspace
- Прямые ссылки на World Model
- Обновление списка по требованию

### 3. Визуализация графа
- Выберите workspace
- Выберите режим визуализации:
  - **Topology** - Инфраструктурная сеть
  - **Evidence** - Provenance агентов
  - **Provenance** - EBSL-native граф
- Экспортируйте интерактивный HTML граф

## Запуск веб-интерфейса

### На сервере:
```bash
ssh root@72.56.79.153
cd /root/shannon-uncontained

# Запустить интерфейс
node web-interface.js

# Или в фоне
nohup node web-interface.js > web-interface.log 2>&1 &
```

### Остановка:
```bash
pkill -f 'web-interface.js'
```

### Просмотр логов:
```bash
tail -f web-interface.log
```

## API Endpoints

### POST /api/run-test
Запуск теста на цель
```json
{
  "target": "https://target.com",
  "framework": "express"
}
```

### GET /api/workspaces
Получить список всех workspace

### POST /api/export-graph
Экспорт графа
```json
{
  "workspace": "target.com",
  "viewMode": "provenance"
}
```

### GET /workspace/:name
Получить World Model для workspace

### GET /public/graph-*.html
Просмотр экспортированного графа

## Использование

1. Откройте http://72.56.79.153:3000 в браузере
2. Введите URL цели (например, https://tcell.tj)
3. Выберите фреймворк
4. Нажмите "Запустить тест"
5. Дождитесь завершения
6. Просмотрите результаты или экспортируйте граф

## Примечания

- Веб-интерфейс работает на порту 3000
- Убедитесь что порт открыт в firewall
- Тесты могут занимать несколько минут
- Графы экспортируются в директорию `public/`

