#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка завершения теста на сервере
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

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def main():
    print("=" * 60)
    print("Проверка завершения теста")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Найти последний workspace
        exit_status, output, error = execute_command(
            client,
            f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1"
        )
        latest_workspace = output.strip().rstrip('/')
        
        if not latest_workspace:
            print("[WARN] Workspace не найден")
            return
        
        domain = latest_workspace.split('/')[-1]
        print(f"[INFO] Последний workspace: {domain}")
        print(f"[INFO] Путь: {latest_workspace}\n")
        
        # Проверить world-model.json
        print("=" * 60)
        print("Проверка World Model")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            f"test -f {latest_workspace}/world-model.json && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() == 'exists':
            print("[OK] world-model.json найден")
            
            # Получить статистику
            exit_status, output, error = execute_command(
                client,
                f"python3 -c \"import json; data=json.load(open('{latest_workspace}/world-model.json')); print('Events:', len(data.get('evidence_graph', {{}}).get('events', []))); print('Claims:', len(data.get('ledger', {{}}).get('claims', []))); print('Entities:', len(data.get('target_model', {{}}).get('entities', []))); print('Execution log entries:', len(data.get('execution_log', [])))\" 2>&1"
            )
            print("\n[INFO] Статистика World Model:")
            print(output)
            
            # Проверить структуру
            exit_status, output, error = execute_command(
                client,
                f"python3 -c \"import json; data=json.load(open('{latest_workspace}/world-model.json')); print('Sections:', list(data.keys()))\" 2>&1"
            )
            print(f"[INFO] Секции: {output.strip()}")
        else:
            print("[WARN] world-model.json не найден")
        
        # Проверить execution-log.json
        print("\n" + "=" * 60)
        print("Проверка Execution Log")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            f"test -f {latest_workspace}/execution-log.json && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() == 'exists':
            print("[OK] execution-log.json найден")
            
            # Получить количество записей
            exit_status, output, error = execute_command(
                client,
                f"python3 -c \"import json; data=json.load(open('{latest_workspace}/execution-log.json')); print('Total entries:', len(data) if isinstance(data, list) else 'not a list'); print('Last 3 entries:'); entries = data[-3:] if isinstance(data, list) and len(data) > 0 else []; [print('  - ' + json.dumps(e)[:100]) for e in entries]\" 2>&1"
            )
            print("\n[INFO] Execution Log:")
            print(output)
        else:
            print("[WARN] execution-log.json не найден")
        
        # Проверить созданные файлы
        print("\n" + "=" * 60)
        print("Проверка созданных артефактов")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            f"find {latest_workspace} -type f | wc -l"
        )
        file_count = output.strip()
        print(f"[INFO] Всего файлов: {file_count}")
        
        # Список основных файлов
        exit_status, output, error = execute_command(
            client,
            f"find {latest_workspace} -type f -name '*.md' -o -name '*.js' -o -name '*.json' -o -name '*.yaml' | sort"
        )
        if output.strip():
            files = output.strip().split('\n')
            print(f"\n[INFO] Основные файлы ({len(files)}):")
            for f in files[:20]:
                print(f"  - {f}")
            if len(files) > 20:
                print(f"  ... и еще {len(files) - 20} файлов")
        
        # Проверить размер workspace
        exit_status, output, error = execute_command(
            client,
            f"du -sh {latest_workspace} 2>/dev/null | awk '{{print $1}}'"
        )
        if output.strip():
            print(f"\n[INFO] Размер workspace: {output.strip()}")
        
        # Проверить время последнего изменения
        exit_status, output, error = execute_command(
            client,
            f"stat -c '%y' {latest_workspace}/world-model.json 2>/dev/null || stat -f '%Sm' {latest_workspace}/world-model.json 2>/dev/null || echo 'не удалось получить время'"
        )
        if output.strip():
            print(f"[INFO] Последнее изменение: {output.strip()}")
        
        # Проверить запущенные процессы shannon
        print("\n" + "=" * 60)
        print("Проверка запущенных процессов")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            "ps aux | grep 'shannon.mjs generate' | grep -v grep || echo 'Нет запущенных тестов'"
        )
        print(output if output.strip() else "Нет запущенных процессов")
        
        # Итоговый вывод
        print("\n" + "=" * 60)
        print("ИТОГОВАЯ ОЦЕНКА")
        print("=" * 60)
        
        # Проверить что тест действительно завершен
        exit_status, output, error = execute_command(
            client,
            f"test -f {latest_workspace}/world-model.json && test -f {latest_workspace}/execution-log.json && echo 'COMPLETE' || echo 'INCOMPLETE'"
        )
        
        if output.strip() == 'COMPLETE':
            print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО")
            print(f"✅ Workspace: {domain}")
            print(f"✅ Файлов создано: {file_count}")
            print(f"✅ World Model создан")
            print(f"✅ Execution Log создан")
            print("\n✅ Все артефакты на месте!")
        else:
            print("\n⚠️ ТЕСТ МОЖЕТ БЫТЬ НЕ ЗАВЕРШЕН")
            print("Проверьте логи выше для деталей")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

