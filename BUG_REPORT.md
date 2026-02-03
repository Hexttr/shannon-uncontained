# Отчет об ошибке в оригинальном коде

## Проблема

В оригинальном репозитории Steake/shannon-uncontained обнаружена ошибка несоответствия API.

### Детали

**Файл:** `local-source-generator.mjs` (строка 71)

**Проблемный код:**
```javascript
const orchestrator = createLSGv2({
    mode: 'live',
    maxParallel: options.parallel || 4,
    enableCaching: true,
    streamDeltas: true,
});
```

**Ошибка выполнения:**
```
❌ Generation failed: orchestrator.on is not a function
```

### Причина

В файле `src/local-source-generator/v2/index.js` функция `createLSGv2()` возвращает объект:
```javascript
return { orchestrator };
```

Но в `local-source-generator.mjs` используется как прямой объект:
```javascript
const orchestrator = createLSGv2({...});  // ❌ Неправильно
```

Должно быть:
```javascript
const { orchestrator } = createLSGv2({...});  // ✅ Правильно
```

### Где используется правильно

- ✅ `src/cli/commands/RunCommand.js` (строка 52): `const { orchestrator } = createLSGv2({`
- ✅ `src/local-source-generator/v2/test-suite.mjs`: использует деструктуризацию

### Где используется неправильно

- ❌ `local-source-generator.mjs` (строка 71): `const orchestrator = createLSGv2({`
- ❌ `shannon.mjs` (строка 187): `const orchestrator = createLSGv2({`

### Комментарий в коде

В `src/local-source-generator/v2/index.js` есть комментарий:
```javascript
/**
 * @returns {object} Object containing { orchestrator } - BREAKING CHANGE: Previously returned orchestrator directly
 * 
 * @example
 * // New usage (v2):
 * const { orchestrator } = createLSGv2();
 * 
 * // Old usage (v1 - DEPRECATED):
 * // const orchestrator = createLSGv2();
 */
```

Это указывает на то, что API был изменен, но не все места использования были обновлены.

## Решение

Нужно исправить два файла:

1. `local-source-generator.mjs` (строка 71)
2. `shannon.mjs` (строка 187)

Заменить:
```javascript
const orchestrator = createLSGv2({...});
```

На:
```javascript
const { orchestrator } = createLSGv2({...});
```

## Статус

Это баг в оригинальном репозитории, который мешает работе приложения. Без исправления код не будет работать.

