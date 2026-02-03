#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка HTML вывода - детальный анализ"""

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

# Получить HTML через curl
stdin, stdout, stderr = client.exec_command(
    f"curl -s http://localhost:3000/ 2>&1"
)
output = stdout.read().decode('utf-8', errors='ignore')

# Найти скрипт
script_start = output.find('<script>')
script_end = output.find('</script>')
if script_start >= 0 and script_end >= 0:
    script_content = output[script_start + 8:script_end]
    lines = script_content.split('\n')
    
    # Проверить строку 121 (это будет строка 106 в HTML, но нужно найти правильную)
    # В браузере нумерация начинается с <script>, так что строка 121 = строка 121-105 = 16 в скрипте
    print("Строки скрипта (первые 30):")
    for i, line in enumerate(lines[:30], 1):
        if i == 16:  # Примерно строка 121 в браузере
            print(f">>> {i}: {repr(line)}")
        else:
            print(f"    {i}: {repr(line[:80])}")
    
    # Проверить строку 16 (которая будет строкой 121 в браузере)
    if len(lines) >= 16:
        line_16 = lines[15]  # Индекс 15 для строки 16
        print(f"\nСтрока 16 (позиция 64): {repr(line_16)}")
        if len(line_16) >= 64:
            print(f"Символ на позиции 64: {repr(line_16[63])}")
            print(f"Контекст: {repr(line_16[50:80])}")

client.close()
