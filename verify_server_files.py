#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка файлов на сервере и реального выполнения теста"""

import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command, timeout=10):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status, output, error

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

print("=" * 60)
print("ПРОВЕРКА ФАЙЛОВ И РЕАЛЬНОГО ВЫПОЛНЕНИЯ")
print("=" * 60)

# 1. Проверить версию web-interface.cjs
print("\n[1] Проверка web-interface.cjs...")
exit_status, output, error = execute_command(client, f"grep -c 'hasData' {PROJECT_PATH}/web-interface.cjs")
print(f"Найдено упоминаний 'hasData': {output.strip()}")

# 2. Проверить размер файла
exit_status, output, error = execute_command(client, f"wc -l {PROJECT_PATH}/web-interface.cjs")
print(f"Строк в файле: {output.strip()}")

# 3. Запустить реальный тест на НОВОМ домене и засечь время
print("\n[2] Запуск РЕАЛЬНОГО теста на НОВОМ домене...")
test_domain = f"real-test-{int(time.time())}.example.com"
print(f"Домен: https://{test_domain}")
print("Это займет несколько минут...\n")

start_time = time.time()

stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && timeout 600 node shannon.mjs generate https://{test_domain} --no-ai 2>&1",
    get_pty=True
)

# Читать вывод в реальном времени
output_lines = []
last_output_time = time.time()

while True:
    if stdout.channel.exit_status_ready():
        break
    
    if stdout.channel.recv_ready():
        data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
            last_output_time = time.time()
    
    # Таймаут если нет вывода 2 минуты
    if time.time() - last_output_time > 120:
        print("\n[WARNING] Нет вывода 2 минуты, продолжаем ожидание...")
        last_output_time = time.time()
    
    # Общий таймаут 10 минут
    if time.time() - start_time > 600:
        print("\n[WARNING] Достигнут таймаут 10 минут")
        break
    
    time.sleep(0.1)

elapsed_time = time.time() - start_time
exit_status = stdout.channel.recv_exit_status()
remaining = stdout.read().decode('utf-8', errors='ignore')
if remaining:
    print(remaining, end='', flush=True)

print(f"\n\n[INFO] Время выполнения: {elapsed_time:.2f} секунд ({elapsed_time/60:.2f} минут)")
print(f"[INFO] Код выхода: {exit_status}")
print(f"[INFO] Строк вывода: {len(output_lines)}")

# 4. Проверить созданный workspace
print("\n[3] Проверка созданного workspace...")
exit_status, output, error = execute_command(client, f"ls -td {PROJECT_PATH}/shannon-results/repos/{test_domain} 2>/dev/null | head -1")
if output.strip():
    workspace = output.strip()
    print(f"[OK] Workspace создан: {workspace}")
    
    # Проверить execution-log
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; data=json.load(open('{workspace}/execution-log.json')); print(f'Всего записей: {{len(data)}}'); agents=set([e.get('agent') for e in data]); print(f'Уникальных агентов: {{len(agents)}}'); print('Агенты:'); [print(f'  - {{a}}') for a in sorted(agents)]\" 2>&1"
    )
    print(output)
    
    # Проверить время выполнения из лога
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; from datetime import datetime; data=json.load(open('{workspace}/execution-log.json')); start=datetime.fromisoformat(data[0]['timestamp'].replace('Z','+00:00')); end=datetime.fromisoformat(data[-1]['timestamp'].replace('Z','+00:00')); dur=(end-start).total_seconds(); print(f'Время выполнения (из лога): {{dur:.2f}} секунд ({{dur/60:.2f}} минут)')\" 2>&1"
    )
    print(output)
else:
    print("[WARNING] Workspace не найден")

# 5. Проверить сколько агентов должно быть
print("\n[4] Проверка доступных агентов...")
exit_status, output, error = execute_command(
    client,
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -e \"const {{createLSGv2}}=require('./src/local-source-generator/v2/index.js'); const {{orchestrator}}=createLSGv2(); console.log('Agents:', orchestrator.agents ? orchestrator.agents.length : 'unknown')\" 2>&1 | head -5"
)
print(output)

client.close()

print("\n" + "=" * 60)
print("ВЫВОДЫ:")
print("=" * 60)
if elapsed_time < 60:
    print("⚠️ Тест завершился слишком быстро (< 1 минуты)")
    print("   Возможные причины:")
    print("   1. Домен не существует - агенты быстро завершаются")
    print("   2. Resume функциональность пропускает агенты")
    print("   3. Не все агенты выполняются")
elif elapsed_time < 300:
    print("✅ Тест выполнился за нормальное время (1-5 минут)")
    print("   Это нормально для простых целей или несуществующих доменов")
else:
    print("✅ Тест выполнился долго (> 5 минут)")
    print("   Это нормально для реальных целей с множеством агентов")

