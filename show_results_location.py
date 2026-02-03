#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Показать где находятся результаты"""

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
print("РЕЗУЛЬТАТЫ ПЕНТЕСТОВ")
print("=" * 60)

stdin, stdout, stderr = client.exec_command(
    f"ls -lh {PROJECT_PATH}/shannon-results/repos/ 2>/dev/null | head -20",
    timeout=10
)
output = stdout.read().decode('utf-8', errors='ignore')
print("\nДоступные workspace:")
print(output if output.strip() else "Нет результатов")

stdin, stdout, stderr = client.exec_command(
    f"find {PROJECT_PATH}/shannon-results/repos -name 'world-model.json' -o -name 'execution-log.json' -o -name 'README.md' | head -10",
    timeout=10
)
files = stdout.read().decode('utf-8', errors='ignore')
if files.strip():
    print("\nОсновные файлы результатов:")
    print(files)

print("\n" + "=" * 60)
print("ПУТЬ К РЕЗУЛЬТАТАМ:")
print("=" * 60)
print(f"SSH: ssh root@{HOST}")
print(f"Директория: {PROJECT_PATH}/shannon-results/repos/<domain>/")
print("\nОсновные файлы:")
print("  - world-model.json - World Model с данными")
print("  - execution-log.json - Лог выполнения агентов")
print("  - README.md - Документация")
print("  - API.md - API документация")
print("  - EVIDENCE.md - Собранные доказательства")

client.close()

