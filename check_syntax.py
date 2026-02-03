#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка синтаксиса файла на сервере"""

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

# Проверить какой файл используется
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && ls -la web-interface*.cjs 2>&1"
)
output = stdout.read().decode('utf-8', errors='ignore')
print("Файлы на сервере:")
print(output)

# Проверить синтаксис Node.js файла
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1"
)
exit_status = stdout.channel.recv_exit_status()
output = stdout.read().decode('utf-8', errors='ignore')
error = stderr.read().decode('utf-8', errors='ignore')

print("\nПроверка синтаксиса:")
print(f"Exit code: {exit_status}")
if output:
    print(f"Output: {output}")
if error:
    print(f"Error: {error}")

# Проверить строки 119-125
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && sed -n '119,125p' web-interface.cjs | cat -A"
)
output = stdout.read().decode('utf-8', errors='ignore')
print("\nСтроки 119-125 (с невидимыми символами):")
print(repr(output))

# Проверить строки 240-250
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && sed -n '240,250p' web-interface.cjs | cat -A"
)
output = stdout.read().decode('utf-8', errors='ignore')
print("\nСтроки 240-250 (с невидимыми символами):")
print(repr(output))

client.close()
