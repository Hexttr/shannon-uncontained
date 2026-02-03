#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка логов веб-интерфейса"""

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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

print("=" * 60)
print("ПРОВЕРКА ЛОГОВ ВЕБ-ИНТЕРФЕЙСА")
print("=" * 60)

# Проверить последние 100 строк логов
stdin, stdout, stderr = client.exec_command(f"tail -100 {PROJECT_PATH}/web-interface.log 2>&1", timeout=10)
output = stdout.read().decode('utf-8', errors='ignore')
print("\nПоследние 100 строк логов:")
print(output)

# Проверить есть ли ошибки
stdin, stdout, stderr = client.exec_command(f"grep -i 'error\\|warn\\|WEB' {PROJECT_PATH}/web-interface.log | tail -20", timeout=10)
errors = stdout.read().decode('utf-8', errors='ignore')
if errors.strip():
    print("\n" + "=" * 60)
    print("ОШИБКИ И ПРЕДУПРЕЖДЕНИЯ:")
    print("=" * 60)
    print(errors)

client.close()

