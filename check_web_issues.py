#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка проблем веб-интерфейса"""

import paramiko
import sys
import io

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
print("ПРОВЕРКА ВЕБ-ИНТЕРФЕЙСА")
print("=" * 60)

# 1. Проверить активные процессы пентестов
print("\n[1] Проверка активных процессов пентестов...")
exit_status, output, error = execute_command(client, "ps aux | grep -E '(shannon|node.*shannon)' | grep -v grep")
if output.strip():
    print("Найдены активные процессы:")
    print(output)
    print("\n[INFO] Завершение процессов...")
    execute_command(client, "pkill -9 -f 'shannon.mjs' || true")
    execute_command(client, "pkill -9 -f 'node.*shannon' || true")
    print("[OK] Процессы завершены")
else:
    print("[OK] Активных процессов пентестов нет")

# 2. Проверить логи веб-интерфейса
print("\n[2] Проверка логов веб-интерфейса...")
exit_status, output, error = execute_command(client, f"tail -50 {PROJECT_PATH}/web-interface.log 2>&1")
if output.strip():
    print("Последние 50 строк логов:")
    print(output)
else:
    print("[INFO] Логи пусты или файл не существует")

# 3. Проверить статус веб-интерфейса
print("\n[3] Проверка статуса веб-интерфейса...")
exit_status, output, error = execute_command(client, "ps aux | grep 'web-interface.cjs' | grep -v grep")
if output.strip():
    print("[OK] Веб-интерфейс запущен")
    print(output)
else:
    print("[ERROR] Веб-интерфейс не запущен!")

# 4. Проверить порт 3000
print("\n[4] Проверка порта 3000...")
exit_status, output, error = execute_command(client, "netstat -tlnp | grep ':3000' || ss -tlnp | grep ':3000'")
if output.strip():
    print("[OK] Порт 3000 слушается")
    print(output)
else:
    print("[ERROR] Порт 3000 не слушается!")

# 5. Проверить синтаксис web-interface.cjs
print("\n[5] Проверка синтаксиса web-interface.cjs...")
exit_status, output, error = execute_command(
    client,
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -c web-interface.cjs 2>&1"
)
if exit_status == 0:
    print("[OK] Синтаксис корректен")
else:
    print("[ERROR] Ошибка синтаксиса:")
    print(error if error else output)

# 6. Проверить файл на наличие проблем
print("\n[6] Проверка содержимого web-interface.cjs...")
exit_status, output, error = execute_command(client, f"grep -n 'runTest' {PROJECT_PATH}/web-interface.cjs | head -5")
print("Найдено упоминаний runTest:")
print(output if output.strip() else "Не найдено")

client.close()

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)

