#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Анализ выполнения теста - детально"""

import paramiko
import sys
import io
import json
from datetime import datetime

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
    print("АНАЛИЗ РЕАЛЬНОГО ВЫПОЛНЕНИЯ ТЕСТА")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        
        # Найти последний workspace
        exit_status, output, error = execute_command(
            client,
            f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1"
        )
        latest_workspace = output.strip().rstrip('/')
        
        if not latest_workspace:
            print("[ERROR] Workspace не найден")
            return
        
        domain = latest_workspace.split('/')[-1]
        print(f"\n[INFO] Анализ workspace: {domain}\n")
        
        # Скачать execution-log.json для анализа
        sftp = client.open_sftp()
        try:
            with sftp.file(f"{latest_workspace}/execution-log.json", 'r') as f:
                exec_log_content = f.read().decode('utf-8')
            exec_log = json.loads(exec_log_content)
        finally:
            sftp.close()
        
        print("=" * 60)
        print("АНАЛИЗ EXECUTION LOG")
        print("=" * 60)
        
        print(f"\nВсего записей: {len(exec_log)}")
        
        # Время выполнения
        if exec_log:
            first_time = datetime.fromisoformat(exec_log[0]['timestamp'].replace('Z', '+00:00'))
            last_time = datetime.fromisoformat(exec_log[-1]['timestamp'].replace('Z', '+00:00'))
            duration = last_time - first_time
            
            print(f"\nВремя выполнения:")
            print(f"  Начало: {first_time}")
            print(f"  Конец: {last_time}")
            print(f"  Длительность: {duration}")
            print(f"  Секунд: {duration.total_seconds():.2f}")
            
            if duration.total_seconds() < 60:
                print("\n⚠️ ВНИМАНИЕ: Тест завершился слишком быстро!")
                print("  Это может означать что агенты пропускаются или не выполняют реальную работу")
        
        # Анализ агентов
        agents = {}
        for entry in exec_log:
            agent = entry.get('agent', 'unknown')
            agents[agent] = agents.get(agent, 0) + 1
        
        print(f"\nВыполненные агенты ({len(agents)}):")
        for agent, count in sorted(agents.items()):
            success_count = sum(1 for e in exec_log if e.get('agent') == agent and e.get('success'))
            failed_count = count - success_count
            status = "✅" if failed_count == 0 else "⚠️"
            print(f"  {status} {agent}: {count} раз (успешно: {success_count}, ошибок: {failed_count})")
        
        # Проверить есть ли реальные действия
        print(f"\n" + "=" * 60)
        print("ПРОВЕРКА РЕАЛЬНЫХ ДЕЙСТВИЙ")
        print("=" * 60)
        
        # Проверить summary/duration в логах
        has_duration = sum(1 for e in exec_log if 'duration' in e or 'time' in str(e.get('summary', '')))
        print(f"\nЗаписей с информацией о времени выполнения: {has_duration}")
        
        # Показать несколько записей детально
        print(f"\nДетали первых 5 записей:")
        for i, entry in enumerate(exec_log[:5]):
            print(f"\n{i+1}. {entry.get('agent', 'unknown')}:")
            print(f"   Время: {entry.get('timestamp', 'unknown')}")
            print(f"   Успех: {entry.get('success', 'unknown')}")
            if 'summary' in entry:
                summary = str(entry['summary'])[:200]
                print(f"   Summary: {summary}")
            if 'error' in entry:
                print(f"   Ошибка: {entry['error'][:200]}")
        
        # Проверить Evidence Graph
        print(f"\n" + "=" * 60)
        print("АНАЛИЗ EVIDENCE GRAPH")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            f"python3 -c \"import json; data=json.load(open('{latest_workspace}/world-model.json')); events = data.get('evidence_graph', {{}}).get('events', []); print(f'Всего событий: {{len(events)}}'); print('\\nТипы событий:'); types = {{}}; [types.update({{e.get('event_type', 'unknown'): types.get(e.get('event_type', 'unknown'), 0) + 1}}) for e in events]; [print(f'  {{k}}: {{v}}') for k, v in sorted(types.items())]; print('\\nИсточники:'); sources = {{}}; [sources.update({{e.get('source', 'unknown'): sources.get(e.get('source', 'unknown'), 0) + 1}}) for e in events]; [print(f'  {{k}}: {{v}}') for k, v in sorted(sources.items())]\" 2>&1"
        )
        print(output)
        
        # Проверить реальное время выполнения команды
        print(f"\n" + "=" * 60)
        print("ТЕСТ НА НОВОМ ДОМЕНЕ (для проверки времени)")
        print("=" * 60)
        
        import time
        test_domain = f"test-{int(time.time())}.example.com"
        print(f"\n[INFO] Запуск теста на: https://{test_domain}")
        print("[INFO] Это займет несколько минут...\n")
        
        start_time = time.time()
        
        stdin, stdout, stderr = client.exec_command(
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && timeout 600 node shannon.mjs generate https://{test_domain} --no-ai 2>&1",
            get_pty=True
        )
        
        # Читать вывод в реальном времени
        output_lines = []
        while True:
            if stdout.channel.exit_status_ready():
                break
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
                if data:
                    print(data, end='', flush=True)
                    output_lines.append(data)
            time.sleep(0.1)
        
        elapsed_time = time.time() - start_time
        exit_status = stdout.channel.recv_exit_status()
        remaining = stdout.read().decode('utf-8', errors='ignore')
        if remaining:
            print(remaining, end='', flush=True)
        
        print(f"\n\n[INFO] Время выполнения: {elapsed_time:.2f} секунд ({elapsed_time/60:.2f} минут)")
        print(f"[INFO] Код выхода: {exit_status}")
        
        if elapsed_time < 30:
            print("\n⚠️ ВНИМАНИЕ: Тест завершился слишком быстро!")
            print("Возможные причины:")
            print("  1. Домен не существует - агенты быстро завершаются")
            print("  2. Агенты пропускаются из-за ошибок")
            print("  3. Resume функциональность пропускает уже выполненные агенты")
        else:
            print("\n✅ Тест выполняется нормальное время")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

