#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка файла на сервере"""

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
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=15)

# Проверить строки вокруг 160
print("Строки 158-162:")
stdin, stdout, stderr = client.exec_command(
    f"sed -n '158,162p' {PROJECT_PATH}/web-interface.cjs"
)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# Проверить строку 135
print("\nСтрока 135:")
stdin, stdout, stderr = client.exec_command(
    f"sed -n '135p' {PROJECT_PATH}/web-interface.cjs"
)
output = stdout.read().decode('utf-8', errors='ignore')
print(repr(output))

# Проверить что функция runTest есть
print("\nПроверка функции runTest:")
stdin, stdout, stderr = client.exec_command(
    f"grep -n 'function runTest' {PROJECT_PATH}/web-interface.cjs"
)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

# Проверить HTML вывод
print("\nПроверка HTML (первые 150 строк):")
stdin, stdout, stderr = client.exec_command(
    f"curl -s http://localhost:3000/ 2>&1 | head -150 | tail -20"
)
output = stdout.read().decode('utf-8', errors='ignore')
print(output)

client.close()

