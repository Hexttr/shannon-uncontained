#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка выполнения теста"""

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

def execute_command(client, command, timeout=5):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status, output, error

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

print("=" * 60)
print("ПРОВЕРКА ВЫПОЛНЕНИЯ ТЕСТА")
print("=" * 60)

# 1. Проверить активные процессы
print("\n[1] Активные процессы shannon...")
exit_status, output, error = execute_command(client, "ps aux | grep -E '(shannon|node.*shannon)' | grep -v grep")
if output.strip():
    print("Найдены процессы:")
    print(output)
else:
    print("[OK] Нет активных процессов")

# 2. Проверить логи веб-интерфейса
print("\n[2] Логи веб-интерфейса (последние 30 строк)...")
exit_status, output, error = execute_command(client, f"tail -30 {PROJECT_PATH}/web-interface.log 2>&1")
print(output)

# 3. Запустить тест напрямую и посмотреть вывод
print("\n[3] Запуск теста напрямую (первые 50 строк)...")
test_domain = f"test-{int(time.time())}.example.com"
print(f"Тест на: https://{test_domain}")

stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && timeout 30 node shannon.mjs generate https://{test_domain} --no-ai 2>&1 | head -50",
    timeout=35
)

# Читать вывод в реальном времени
import select
output_lines = []
start_time = time.time()

while True:
    if stdout.channel.exit_status_ready():
        break
    if stdout.channel.recv_ready():
        data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
    if time.time() - start_time > 30:
        break
    time.sleep(0.1)

exit_status = stdout.channel.recv_exit_status()
remaining = stdout.read().decode('utf-8', errors='ignore')
if remaining:
    print(remaining, end='', flush=True)

print(f"\n\n[INFO] Код выхода: {exit_status}")
print(f"[INFO] Время выполнения: {time.time() - start_time:.2f} секунд")

# 4. Проверить последний workspace
print("\n[4] Последний workspace...")
exit_status, output, error = execute_command(client, f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1")
if output.strip():
    latest = output.strip().rstrip('/')
    domain = latest.split('/')[-1]
    print(f"Последний: {domain}")
    
    # Проверить execution-log
    exit_status, output, error = execute_command(client, f"python3 -c \"import json; data=json.load(open('{latest}/execution-log.json')); print(f'Записей: {{len(data)}}'); print(f'Последняя: {{data[-1].get(\\\"agent\\\", \\\"unknown\\\")}} - {{data[-1].get(\\\"timestamp\\\", \\\"unknown\\\")}}')\" 2>&1")
    print(output)
else:
    print("[INFO] Workspace не найден")

client.close()

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)

