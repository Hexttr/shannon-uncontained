#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Настройка Ollama как провайдера по умолчанию"""

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
print("НАСТРОЙКА OLLAMA КАК ПРОВАЙДЕРА ПО УМОЛЧАНИЮ")
print("=" * 60)

# 1. Проверить Ollama
print("\n[1] Проверка Ollama...")
exit_status, output, error = execute_command(client, "which ollama")
if exit_status == 0:
    print(f"[OK] Ollama установлена: {output.strip()}")
else:
    print("[ERROR] Ollama не найдена!")
    client.close()
    sys.exit(1)

# 2. Проверить работает ли Ollama
print("\n[2] Проверка работы Ollama...")
exit_status, output, error = execute_command(client, "curl -s http://localhost:11434/api/tags 2>&1 | head -10")
if exit_status == 0 and 'models' in output.lower():
    print("[OK] Ollama работает")
    print("Доступные модели:")
    print(output[:300])
else:
    print("[WARNING] Ollama не отвечает или нет моделей")
    print("Попытка запуска Ollama...")
    execute_command(client, "systemctl start ollama || ollama serve > /dev/null 2>&1 &")
    import time
    time.sleep(3)

# 3. Проверить какие модели установлены
print("\n[3] Список установленных моделей...")
exit_status, output, error = execute_command(client, "ollama list 2>&1")
print(output if output.strip() else "[INFO] Нет установленных моделей")

# 4. Настроить .env файл
print("\n[4] Настройка .env файла...")
env_content = """# ============================================
# Shannon-Uncontained LLM Configuration
# ============================================

# LLM Provider - Ollama по умолчанию
LLM_PROVIDER=ollama
LLM_MODEL=codellama:7b

# Для продакшена раскомментируйте:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your_key_here
# LLM_MODEL=claude-3-5-sonnet-20241022

# OpenAI (альтернатива)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your_key_here
# LLM_MODEL=gpt-4o

# GitHub Models (бесплатный)
# LLM_PROVIDER=github
# GITHUB_TOKEN=ghp_your_token_here
"""

sftp = client.open_sftp()
try:
    with sftp.file(f'{PROJECT_PATH}/.env', 'w') as f:
        f.write(env_content)
    print("[OK] .env файл обновлен")
    
    # Проверить содержимое
    with sftp.file(f'{PROJECT_PATH}/.env', 'r') as f:
        content = f.read().decode('utf-8')
        print("\nСодержимое .env:")
        print(content[:500])
finally:
    sftp.close()

# 5. Проверить что модель доступна
print("\n[5] Проверка доступности модели codellama:7b...")
exit_status, output, error = execute_command(client, "ollama list | grep codellama")
if exit_status == 0 and output.strip():
    print("[OK] Модель codellama:7b найдена")
    print(output)
else:
    print("[INFO] Модель codellama:7b не найдена")
    print("[INFO] Для установки выполните: ollama pull codellama:7b")

# 6. Тест подключения к Ollama
print("\n[6] Тест подключения к Ollama...")
exit_status, output, error = execute_command(
    client,
    "curl -s http://localhost:11434/api/generate -d '{\"model\":\"codellama:7b\",\"prompt\":\"test\",\"stream\":false}' 2>&1 | head -3"
)
if exit_status == 0:
    print("[OK] Ollama отвечает на запросы")
else:
    print("[WARNING] Ollama не отвечает на запросы")
    print(f"Вывод: {output[:200]}")

client.close()

print("\n" + "=" * 60)
print("ГОТОВО")
print("=" * 60)
print("\nOllama настроена как провайдер по умолчанию")
print("Для использования в тестах нужно убрать флаг --no-ai")

