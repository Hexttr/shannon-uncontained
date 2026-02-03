#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная настройка и тестирование всех возможностей Shannon-Uncontained
"""

import paramiko
import sys
import io
import time
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"
TARGET = "https://tcell.tj"
WORKSPACE = f"{PROJECT_PATH}/shannon-results/repos/tcell.tj"

def execute_command(client, command, timeout=300):
    """Выполнить команду с таймаутом"""
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    
    output_lines = []
    error_lines = []
    start_time = time.time()
    
    while True:
        if time.time() - start_time > timeout:
            break
        
        if stdout.channel.exit_status_ready():
            break
        
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
            if data:
                output_lines.append(data)
        
        if stderr.channel.recv_stderr_ready():
            data = stderr.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            if data:
                error_lines.append(data)
        
        time.sleep(0.1)
    
    exit_status = stdout.channel.recv_exit_status()
    remaining_output = stdout.read().decode('utf-8', errors='ignore')
    remaining_error = stderr.read().decode('utf-8', errors='ignore')
    
    return exit_status, ''.join(output_lines) + remaining_output, ''.join(error_lines) + remaining_error

def test_cli_commands(client):
    """Тестирование всех CLI команд"""
    print("\n" + "=" * 60)
    print("Тестирование CLI команд")
    print("=" * 60)
    
    results = {}
    
    # 1. Проверка help
    print("\n[TEST] Проверка help...")
    exit_status, output, error = execute_command(
        client,
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs --help",
        timeout=30
    )
    results['help'] = exit_status == 0
    if exit_status == 0:
        print("  [OK] Help работает")
    else:
        print(f"  [FAIL] Help не работает: {error[:200]}")
    
    # 2. Model show
    print("\n[TEST] Команда: model show...")
    exit_status, output, error = execute_command(
        client,
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs model show --workspace {WORKSPACE}",
        timeout=60
    )
    results['model_show'] = exit_status == 0
    if exit_status == 0:
        print("  [OK] model show работает")
        if 'World Model' in output or 'Entities' in output or 'Claims' in output:
            print("  [OK] Вывод содержит данные модели")
    else:
        print(f"  [FAIL] model show не работает: {error[:200]}")
    
    # 3. Model graph
    print("\n[TEST] Команда: model graph...")
    exit_status, output, error = execute_command(
        client,
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs model graph --workspace {WORKSPACE}",
        timeout=60
    )
    results['model_graph'] = exit_status == 0
    if exit_status == 0:
        print("  [OK] model graph работает")
    else:
        print(f"  [WARN] model graph: {error[:200]}")
    
    # 4. Model export-html (все три режима)
    print("\n[TEST] Команда: model export-html...")
    for view_mode in ['topology', 'evidence', 'provenance']:
        print(f"  Тестирование режима: {view_mode}...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs model export-html --workspace {WORKSPACE} --view {view_mode} -o /tmp/shannon-graph-{view_mode}.html",
            timeout=120
        )
        if exit_status == 0:
            print(f"    [OK] {view_mode} режим работает")
            # Проверить что файл создан
            exit_status_check, output_check, error_check = execute_command(
                client,
                f"test -f /tmp/shannon-graph-{view_mode}.html && echo 'exists' || echo 'not exists'",
                timeout=10
            )
            if 'exists' in output_check:
                print(f"    [OK] HTML файл создан: /tmp/shannon-graph-{view_mode}.html")
        else:
            print(f"    [WARN] {view_mode} режим: {error[:200]}")
    
    # 5. Evidence stats
    print("\n[TEST] Команда: evidence stats...")
    exit_status, output, error = execute_command(
        client,
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs evidence stats {WORKSPACE}",
        timeout=60
    )
    results['evidence_stats'] = exit_status == 0
    if exit_status == 0:
        print("  [OK] evidence stats работает")
    else:
        print(f"  [WARN] evidence stats: {error[:200]}")
    
    return results

def check_world_model_structure(client):
    """Проверка структуры World Model"""
    print("\n" + "=" * 60)
    print("Проверка структуры World Model")
    print("=" * 60)
    
    world_model_path = f"{WORKSPACE}/world-model.json"
    
    # Проверка существования
    exit_status, output, error = execute_command(
        client,
        f"test -f {world_model_path} && echo 'exists' || echo 'not exists'",
        timeout=10
    )
    
    if output.strip() != 'exists':
        print(f"[WARN] World model не найден: {world_model_path}")
        return
    
    print(f"[OK] World model найден: {world_model_path}")
    
    # Чтение и анализ структуры
    exit_status, output, error = execute_command(
        client,
        f"cat {world_model_path} | python3 -m json.tool | head -100",
        timeout=30
    )
    
    if exit_status == 0:
        print("\n[INFO] Структура World Model (первые 100 строк):")
        print(output[:2000])
    
    # Проверка наличия ключевых полей
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; data=json.load(open('{world_model_path}')); print('entities:', len(data.get('entities', []))); print('claims:', len(data.get('claims', []))); print('evidence:', len(data.get('evidence', []))); print('keys:', list(data.keys())[:10])\"",
        timeout=30
    )
    
    if exit_status == 0:
        print("\n[INFO] Статистика World Model:")
        print(output)

def check_evidence_graph(client):
    """Проверка Evidence Graph"""
    print("\n" + "=" * 60)
    print("Проверка Evidence Graph")
    print("=" * 60)
    
    evidence_dir = f"{WORKSPACE}/evidence"
    
    exit_status, output, error = execute_command(
        client,
        f"test -d {evidence_dir} && echo 'exists' || echo 'not exists'",
        timeout=10
    )
    
    if output.strip() == 'exists':
        print(f"[OK] Evidence директория найдена: {evidence_dir}")
        
        # Количество файлов
        exit_status, output, error = execute_command(
            client,
            f"find {evidence_dir} -type f | wc -l",
            timeout=10
        )
        if output.strip():
            print(f"  Файлов: {output.strip()}")
        
        # Список файлов
        exit_status, output, error = execute_command(
            client,
            f"find {evidence_dir} -type f | head -10",
            timeout=10
        )
        if output.strip():
            files = [f for f in output.strip().split('\n') if f]
            print(f"\n  Файлы ({len(files)}):")
            for f in files[:10]:
                print(f"    - {f}")
    else:
        print(f"[WARN] Evidence директория не найдена")

def check_generated_artifacts(client):
    """Проверка сгенерированных артефактов"""
    print("\n" + "=" * 60)
    print("Проверка сгенерированных артефактов")
    print("=" * 60)
    
    # Проверка различных типов артефактов
    artifacts_to_check = [
        ('API документация', 'API.md'),
        ('Архитектура', 'ARCHITECTURE.md'),
        ('Evidence', 'EVIDENCE.md'),
        ('README', 'README.md'),
        ('Код приложения', 'app.js'),
        ('Тесты API', 'api.test.js'),
        ('Тесты безопасности', 'security.test.js'),
        ('Конфигурация', 'config/index.js'),
        ('Модели', 'models/index.js'),
        ('Middleware', 'middleware/auth.js'),
        ('Package.json', 'package.json'),
    ]
    
    found = 0
    for name, file_path in artifacts_to_check:
        full_path = f"{WORKSPACE}/{file_path}"
        exit_status, output, error = execute_command(
            client,
            f"test -f '{full_path}' && echo 'exists' || echo 'not exists'",
            timeout=10
        )
        if output.strip() == 'exists':
            print(f"  [OK] {name}: {file_path}")
            found += 1
        else:
            print(f"  [WARN] {name}: не найден")
    
    print(f"\n[INFO] Найдено артефактов: {found}/{len(artifacts_to_check)}")

def test_osint_feature(client):
    """Тестирование OSINT функций"""
    print("\n" + "=" * 60)
    print("Тестирование OSINT функций")
    print("=" * 60)
    
    # Тест email OSINT (на тестовом email)
    test_email = "test@example.com"
    print(f"\n[TEST] OSINT для email: {test_email}...")
    
    exit_status, output, error = execute_command(
        client,
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs osint email {test_email} --no-breaches --no-social",
        timeout=60
    )
    
    if exit_status == 0:
        print("  [OK] OSINT команда работает")
        if 'Email:' in output or 'Domain:' in output:
            print("  [OK] OSINT возвращает данные")
    else:
        print(f"  [WARN] OSINT команда: {error[:200]}")

def create_comprehensive_config(client):
    """Создание полной конфигурации"""
    print("\n" + "=" * 60)
    print("Создание полной конфигурации")
    print("=" * 60)
    
    config_content = """# ============================================
# Shannon-Uncontained Full Configuration
# ============================================

# LLM Provider (текущая настройка для тестов)
LLM_PROVIDER=ollama
LLM_MODEL=codellama:7b

# Для продакшена раскомментируйте:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your_key_here
# LLM_MODEL=claude-3-5-sonnet-20241022

# Advanced Model Configuration
# Разные модели для разных задач (раскомментируйте при использовании облачных провайдеров):
# LLM_FAST_MODEL=gpt-3.5-turbo        # Для быстрых задач
# LLM_SMART_MODEL=gpt-4o              # Для сложных задач
# LLM_CODE_MODEL=claude-3-5-sonnet-20241022  # Для генерации кода

# Budget Configuration (опционально)
# MAX_TIME_MS=3600000                 # 1 час максимум
# MAX_TOKENS=100000                   # Максимум токенов
# MAX_NETWORK_REQUESTS=1000           # Максимум сетевых запросов

# Tool Configuration
# SKIP_NMAP=false                     # Пропустить nmap сканирование
# SKIP_CRAWL=false                    # Пропустить краулинг

# Framework Configuration
# FRAMEWORK=express                   # express или fastapi

# Metasploit Configuration (опционально)
# MSF_HOST=127.0.0.1
# MSF_PORT=55553
# MSF_USER=msf
# MSF_PASS=msf

# Output Configuration
# OUTPUT_DIR=./shannon-results        # Директория для результатов
# VERBOSE=false                       # Подробный вывод
# QUIET=false                         # Тихий режим
"""
    
    config_path = f"{PROJECT_PATH}/.env.full"
    
    # Записать конфигурацию
    command = f"""cat > {config_path} << 'ENVEOF'
{config_content}
ENVEOF
"""
    exit_status, output, error = execute_command(client, command, timeout=10)
    
    if exit_status == 0:
        print(f"[OK] Полная конфигурация создана: {config_path}")
    else:
        print(f"[WARN] Ошибка создания конфигурации: {error[:200]}")

def main():
    print("=" * 60)
    print("Полная настройка и тестирование Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # 1. Проверка workspace
        print("[INFO] Проверка workspace...")
        exit_status, output, error = execute_command(
            client,
            f"test -d {WORKSPACE} && echo 'exists' || echo 'not exists'",
            timeout=10
        )
        
        if output.strip() != 'exists':
            print(f"[WARN] Workspace не найден: {WORKSPACE}")
            print("  Запустите сначала: shannon.mjs generate https://tcell.tj")
            return
        
        print(f"[OK] Workspace найден: {WORKSPACE}")
        
        # 2. Проверка структуры World Model
        check_world_model_structure(client)
        
        # 3. Проверка Evidence Graph
        check_evidence_graph(client)
        
        # 4. Проверка артефактов
        check_generated_artifacts(client)
        
        # 5. Тестирование CLI команд
        cli_results = test_cli_commands(client)
        
        # 6. Тестирование OSINT
        test_osint_feature(client)
        
        # 7. Создание полной конфигурации
        create_comprehensive_config(client)
        
        # Итоговый отчет
        print("\n" + "=" * 60)
        print("Итоговый отчет")
        print("=" * 60)
        
        print("\n[OK] CLI команды:")
        for cmd, result in cli_results.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {cmd}")
        
        print("\n[OK] Все проверки завершены!")
        print("\nДоступные команды:")
        print("  - shannon.mjs generate <target>     - Полный пайплайн")
        print("  - shannon.mjs model show           - Показать модель")
        print("  - shannon.mjs model graph          - ASCII граф")
        print("  - shannon.mjs model export-html   - HTML визуализация")
        print("  - shannon.mjs model why <claim>   - Объяснение claim")
        print("  - shannon.mjs evidence stats       - Статистика evidence")
        print("  - shannon.mjs osint email <email>  - OSINT по email")
        print("  - shannon.mjs synthesize <ws>     - Повторный синтез")
        
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

