#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Комплексная проверка всего"""

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

def execute_command(client, command, timeout=10):
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return exit_status, output, error

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=15)

print("=" * 60)
print("КОМПЛЕКСНАЯ ПРОВЕРКА СИСТЕМЫ")
print("=" * 60)

# 1. Проверить .env файл
print("\n[1] Проверка .env файла...")
exit_status, output, error = execute_command(client, f"cat {PROJECT_PATH}/.env")
print("Содержимое .env:")
print(output[:500])

# 2. Проверить web-interface.cjs на сервере
print("\n[2] Проверка web-interface.cjs на сервере...")
exit_status, output, error = execute_command(client, f"grep -n 'shannon.mjs generate' {PROJECT_PATH}/web-interface.cjs")
print("Команда запуска теста:")
print(output)

exit_status, output, error = execute_command(client, f"grep -c '--no-ai' {PROJECT_PATH}/web-interface.cjs")
no_ai_count = output.strip()
print(f"\nУпоминаний '--no-ai': {no_ai_count}")

# 3. Проверить оригинальные файлы из репозитория
print("\n[3] Проверка оригинальных файлов из репозитория...")
critical_files = [
    'shannon.mjs',
    'src/local-source-generator/v2/index.js',
    'src/core/WorldModel.js',
    'src/core/EpistemicLedger.js',
    'src/ai/llm-client.js'
]

for file_path in critical_files:
    exit_status, output, error = execute_command(client, f"test -f {PROJECT_PATH}/{file_path} && echo 'EXISTS' || echo 'MISSING'")
    status = output.strip()
    if status == 'EXISTS':
        # Проверить размер
        exit_status, size_output, error = execute_command(client, f"wc -c {PROJECT_PATH}/{file_path} | awk '{{print $1}}'")
        size = size_output.strip()
        print(f"  ✅ {file_path} ({size} bytes)")
    else:
        print(f"  ❌ {file_path} - ОТСУТСТВУЕТ!")

# 4. Проверить что мы не изменили оригинальные файлы
print("\n[4] Проверка изменений в оригинальных файлах...")
# Проверить shannon.mjs - должен быть оригинальным
exit_status, output, error = execute_command(client, f"grep -c 'createLSGv2' {PROJECT_PATH}/shannon.mjs")
if output.strip() == '0':
    print("  ⚠️ shannon.mjs не содержит createLSGv2 - возможно изменен")
else:
    print(f"  ✅ shannon.mjs содержит createLSGv2 ({output.strip()} раз)")

# Проверить что local-source-generator.mjs использует правильный API
exit_status, output, error = execute_command(client, f"grep -A 2 'createLSGv2' {PROJECT_PATH}/src/local-source-generator/v2/index.js | head -5")
print("\n  Проверка createLSGv2 в index.js:")
print(f"  {output[:200]}")

# 5. Проверить веб-интерфейс - отображение логов
print("\n[5] Проверка отображения логов в веб-интерфейсе...")
exit_status, output, error = execute_command(client, f"grep -A 5 'output.textContent' {PROJECT_PATH}/web-interface.cjs | head -10")
print("Код отображения вывода:")
print(output)

exit_status, output, error = execute_command(client, f"grep -c 'data.data' {PROJECT_PATH}/web-interface.cjs")
data_count = output.strip()
print(f"\nУпоминаний 'data.data' (отображение данных): {data_count}")

# 6. Проверить Ollama
print("\n[6] Проверка Ollama...")
exit_status, output, error = execute_command(client, "curl -s http://localhost:11434/api/tags 2>&1 | head -3")
if exit_status == 0 and 'models' in output.lower():
    print("[OK] Ollama работает")
    exit_status, output, error = execute_command(client, "ollama list | grep codellama")
    if output.strip():
        print(f"[OK] Модель codellama установлена:\n{output}")
else:
    print("[WARNING] Ollama не отвечает")

# 7. Проверить что команда запуска не использует --no-ai
print("\n[7] Проверка команды запуска...")
exit_status, output, error = execute_command(client, f"grep 'node shannon.mjs generate' {PROJECT_PATH}/web-interface.cjs")
print("Команда:")
print(output)

if '--no-ai' in output:
    print("\n❌ ОШИБКА: Команда все еще содержит --no-ai!")
else:
    print("\n✅ Команда не содержит --no-ai, будет использоваться Ollama")

# 8. Проверить логи веб-интерфейса
print("\n[8] Последние логи веб-интерфейса...")
exit_status, output, error = execute_command(client, f"tail -30 {PROJECT_PATH}/web-interface.log 2>&1")
if output.strip():
    print(output)
else:
    print("[INFO] Логи пусты")

client.close()

print("\n" + "=" * 60)
print("ПРОВЕРКА ЗАВЕРШЕНА")
print("=" * 60)

