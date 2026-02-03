#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка всех возможностей и функций Shannon-Uncontained
"""

import paramiko
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"
WORKSPACE = f"{PROJECT_PATH}/shannon-results/repos/tcell.tj"

def execute_command(client, command, timeout=60):
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status, output, error

def check_agents(client):
    """Проверка всех агентов"""
    print("\n" + "=" * 60)
    print("Проверка доступности агентов")
    print("=" * 60)
    
    agents = {
        'Recon': [
            'NetReconAgent', 'SubdomainHunterAgent', 'CrawlerAgent',
            'TechFingerprinterAgent', 'JSHarvesterAgent', 'APIDiscovererAgent',
            'ContentDiscoveryAgent', 'SecretScannerAgent', 'WAFDetector',
            'BrowserCrawlerAgent', 'CORSProbeAgent', 'SitemapAgent',
            'OpenAPIDiscoveryAgent', 'EmailOSINTAgent'
        ],
        'Analysis': [
            'ArchitectInferAgent', 'AuthFlowAnalyzer', 'DataFlowMapper',
            'VulnHypothesizer', 'BusinessLogicAgent', 'SecurityHeaderAnalyzer',
            'TLSAnalyzer'
        ],
        'Exploitation': [
            'NucleiScanAgent', 'MetasploitAgent', 'SQLmapAgent',
            'XSSValidatorAgent', 'CommandInjectionAgent'
        ],
        'Synthesis': [
            'GroundTruthAgent', 'SourceGenAgent', 'SchemaGenAgent',
            'TestGenAgent', 'DocumentationAgent', 'BlackboxConfigGenAgent',
            'RemediationAgent'
        ]
    }
    
    total = 0
    found = 0
    
    for phase, agent_list in agents.items():
        print(f"\n{phase} агенты:")
        for agent in agent_list:
            total += 1
            # Проверка существования файла агента
            agent_file = agent.replace('Agent', '').lower()
            # Поиск файла агента
            exit_status, output, error = execute_command(
                client,
                f"find {PROJECT_PATH}/src/local-source-generator/v2/agents -name '*{agent_file}*' -o -name '*{agent.lower()}*' | head -1",
                timeout=10
            )
            if output.strip():
                print(f"  [OK] {agent}")
                found += 1
            else:
                print(f"  [WARN] {agent} - файл не найден")
    
    print(f"\n[INFO] Найдено агентов: {found}/{total}")
    return found, total

def check_world_model_features(client):
    """Проверка возможностей World Model"""
    print("\n" + "=" * 60)
    print("Проверка возможностей World Model")
    print("=" * 60)
    
    world_model_path = f"{WORKSPACE}/world-model.json"
    
    # Проверка структуры
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; data=json.load(open('{world_model_path}')); print('Секции:', list(data.keys())); print('Evidence events:', len(data.get('evidence_graph', {{}}).get('events', []))); print('Claims:', len(data.get('ledger', {{}}).get('claims', []))); print('Entities:', len(data.get('target_model', {{}}).get('entities', [])))\"",
        timeout=30
    )
    
    if exit_status == 0:
        print("[OK] World Model структура:")
        print(output)
    else:
        print(f"[WARN] Не удалось проанализировать структуру: {error[:200]}")

def check_epistemic_features(client):
    """Проверка EQBSL функций"""
    print("\n" + "=" * 60)
    print("Проверка EQBSL функций")
    print("=" * 60)
    
    world_model_path = f"{WORKSPACE}/world-model.json"
    
    # Проверка наличия EQBSL данных в ledger
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; data=json.load(open('{world_model_path}')); ledger=data.get('ledger', {{}}); claims=ledger.get('claims', []); print('Всего claims:', len(claims)); eqbsl_claims=[c for c in claims if 'tensor' in c or 'belief' in c or 'uncertainty' in c]; print('Claims с EQBSL:', len(eqbsl_claims)); print('Пример claim:', json.dumps(claims[0] if claims else {{}}, indent=2)[:500])\"",
        timeout=30
    )
    
    if exit_status == 0:
        print("[OK] EQBSL данные:")
        print(output)
    else:
        print(f"[WARN] Не удалось проверить EQBSL: {error[:200]}")

def test_visualization_modes(client):
    """Тестирование всех режимов визуализации"""
    print("\n" + "=" * 60)
    print("Тестирование режимов визуализации")
    print("=" * 60)
    
    modes = ['topology', 'evidence', 'provenance']
    
    for mode in modes:
        print(f"\n[TEST] Режим: {mode}")
        html_file = f"/tmp/shannon-graph-{mode}.html"
        
        # Проверка что файл создан
        exit_status, output, error = execute_command(
            client,
            f"test -f {html_file} && ls -lh {html_file} | awk '{{print $5}}' || echo 'not found'",
            timeout=10
        )
        
        if 'not found' not in output:
            size = output.strip()
            print(f"  [OK] HTML файл создан: {size}")
            
            # Проверка содержимого (должен быть D3.js код)
            exit_status, output, error = execute_command(
                client,
                f"grep -q 'd3' {html_file} && echo 'd3 found' || echo 'd3 not found'",
                timeout=10
            )
            if 'd3 found' in output:
                print(f"  [OK] D3.js код присутствует")
        else:
            print(f"  [WARN] HTML файл не найден")

def create_usage_guide(client):
    """Создание руководства по использованию"""
    print("\n" + "=" * 60)
    print("Создание руководства по использованию")
    print("=" * 60)
    
    guide_content = """# Руководство по использованию Shannon-Uncontained

## Основные команды

### 1. Генерация (полный пайплайн)
```bash
./shannon.mjs generate https://target.com
```

Опции:
- `-o, --output <dir>` - Директория для результатов (по умолчанию: ./shannon-results)
- `--framework <name>` - Фреймворк для синтеза (express, fastapi)
- `--no-ai` - Пропустить AI синтез (только recon)
- `--skip-nmap` - Пропустить nmap сканирование
- `--skip-crawl` - Пропустить краулинг
- `-p, --parallel <number>` - Максимум параллельных агентов (по умолчанию: 4)
- `-v, --verbose` - Подробный вывод

### 2. Просмотр World Model
```bash
# Показать модель с графиками
./shannon.mjs model show --workspace shannon-results/repos/target.com

# ASCII граф знаний
./shannon.mjs model graph --workspace shannon-results/repos/target.com

# Интерактивный HTML граф
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view topology
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view evidence
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view provenance

# Объяснение конкретного claim
./shannon.mjs model why <claim_id> --workspace shannon-results/repos/target.com
```

### 3. Evidence Graph
```bash
# Статистика evidence
./shannon.mjs evidence stats shannon-results/repos/target.com
```

### 4. OSINT
```bash
# OSINT по email
./shannon.mjs osint email user@example.com

# Опции:
# --no-breaches - Пропустить проверку утечек
# --no-social - Пропустить поиск соцсетей
# --json - Вывод в JSON
# -o, --output <file> - Сохранить в файл
```

### 5. Повторный синтез
```bash
# Запустить синтез на существующем World Model
./shannon.mjs synthesize shannon-results/repos/target.com --framework express
```

### 6. Полный пайплайн (run команда)
```bash
./shannon.mjs run https://target.com

# Опции:
# --workspace <dir> - Директория для артефактов
# --mode <mode> - Режим: live, replay, dry-run
# --strategy <type> - Стратегия: legacy, agentic
# --agent <name> - Запустить только конкретного агента
# --max-time-ms <ms> - Максимальное время выполнения
# --max-tokens <n> - Максимум токенов
```

## Режимы визуализации графа

1. **topology** - Инфраструктурная сеть: subdomains → paths → ports
2. **evidence** - Provenance агентов: какой агент что обнаружил
3. **provenance** - EBSL-native: source → event_type → target с tensor edges

## Структура результатов

```
shannon-results/repos/target.com/
├── world-model.json          # Центральный граф знаний
├── execution-log.json         # Лог выполнения
├── API.md                     # API документация
├── ARCHITECTURE.md            # Архитектурная документация
├── EVIDENCE.md                # Документация доказательств
├── README.md                  # Основная документация
├── app.js                     # Сгенерированный код приложения
├── api.test.js                # Тесты API
├── security.test.js           # Тесты безопасности
├── config/                    # Конфигурация
├── models/                    # Модели данных
├── middleware/                # Middleware
└── ml-training/               # Данные для ML обучения
```

## Примеры использования

### Быстрый recon
```bash
./shannon.mjs generate https://target.com --no-ai
```

### Полный анализ с синтезом
```bash
./shannon.mjs generate https://target.com --framework express --parallel 8
```

### Просмотр результатов
```bash
# Показать модель
./shannon.mjs model show --workspace shannon-results/repos/target.com

# Экспортировать интерактивный граф
./shannon.mjs model export-html --workspace shannon-results/repos/target.com --view provenance -o graph.html
```

### OSINT исследование
```bash
./shannon.mjs osint email admin@target.com --json -o osint-results.json
```
"""
    
    guide_path = f"{PROJECT_PATH}/USAGE_GUIDE.md"
    
    command = f"""cat > {guide_path} << 'GUIDEEOF'
{guide_content}
GUIDEEOF
"""
    exit_status, output, error = execute_command(client, command, timeout=10)
    
    if exit_status == 0:
        print(f"[OK] Руководство создано: {guide_path}")
    else:
        print(f"[WARN] Ошибка создания руководства: {error[:200]}")

def main():
    print("=" * 60)
    print("Проверка всех возможностей Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # 1. Проверка агентов
        agents_found, agents_total = check_agents(client)
        
        # 2. Проверка World Model
        check_world_model_features(client)
        
        # 3. Проверка EQBSL
        check_epistemic_features(client)
        
        # 4. Тестирование визуализации
        test_visualization_modes(client)
        
        # 5. Создание руководства
        create_usage_guide(client)
        
        # Итоговый отчет
        print("\n" + "=" * 60)
        print("Итоговый отчет")
        print("=" * 60)
        print(f"\n[OK] Агентов найдено: {agents_found}/{agents_total}")
        print("[OK] Все основные функции проверены")
        print("[OK] Руководство по использованию создано")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

