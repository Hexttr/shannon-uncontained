#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка использования Ollama"""

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
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=15)

print("=" * 60)
print("ПРОВЕРКА ИСПОЛЬЗОВАНИЯ OLLAMA")
print("=" * 60)

# 1. Проверить .env
print("\n[1] Проверка .env...")
exit_status, output, error = execute_command(client, f"cat {PROJECT_PATH}/.env | grep -E 'LLM_PROVIDER|LLM_MODEL'")
print(output)

# 2. Проверить что Ollama работает
print("\n[2] Проверка работы Ollama...")
exit_status, output, error = execute_command(client, "curl -s http://localhost:11434/api/tags 2>&1")
if exit_status == 0 and 'models' in output.lower():
    print("[OK] Ollama работает")
else:
    print("[ERROR] Ollama не отвечает!")
    print(f"Вывод: {output[:200]}")

# 3. Запустить тест и проверить использование LLM
print("\n[3] Запуск теста для проверки использования Ollama...")
test_domain = f"test-ollama-{int(time.time())}.example.com"
print(f"Домен: https://{test_domain}")

stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && timeout 120 node shannon.mjs generate https://{test_domain} 2>&1 | head -100",
    get_pty=True
)

start_time = time.time()
output_lines = []
has_llm_usage = False

while True:
    if stdout.channel.exit_status_ready():
        break
    if stdout.channel.recv_ready():
        data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
            # Проверить упоминания LLM/Ollama
            if any(keyword in data.lower() for keyword in ['ollama', 'llm', 'tokens', 'model', 'codellama']):
                has_llm_usage = True
    if time.time() - start_time > 30:
        print("\n[Timeout after 30 seconds]")
        break
    time.sleep(0.1)

elapsed = time.time() - start_time
exit_status = stdout.channel.recv_exit_status()
remaining = stdout.read().decode('utf-8', errors='ignore')
if remaining:
    print(remaining[:500], end='', flush=True)

print(f"\n\n[INFO] Время выполнения: {elapsed:.2f} секунд")
print(f"[INFO] Использование LLM обнаружено: {has_llm_usage}")

# 4. Проверить последний workspace
print("\n[4] Проверка последнего workspace...")
exit_status, output, error = execute_command(client, f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1")
if output.strip():
    latest = output.strip().rstrip('/')
    domain = latest.split('/')[-1]
    print(f"Последний: {domain}")
    
    # Проверить execution-log на использование LLM
    exit_status, output, error = execute_command(
        client,
        f"python3 -c \"import json; data=json.load(open('{latest}/execution-log.json')); llm_agents = [e for e in data if 'tokens_used' in e.get('summary', {{}}) and e.get('summary', {{}}).get('tokens_used', 0) > 0]; print(f'Агентов с использованием LLM: {{len(llm_agents)}}'); [print(f'  - {{e.get(\\\"agent\\\")}}: {{e.get(\\\"summary\\\", {{}}).get(\\\"tokens_used\\\", 0)}} токенов') for e in llm_agents[:5]]\" 2>&1"
    )
    print(output)

# 5. Проверить переменные окружения при запуске
print("\n[5] Проверка переменных окружения...")
exit_status, output, error = execute_command(
    client,
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -e \"require('dotenv').config(); console.log('LLM_PROVIDER:', process.env.LLM_PROVIDER); console.log('LLM_MODEL:', process.env.LLM_MODEL);\" 2>&1"
)
print(output)

# 6. Проверить логи веб-интерфейса
print("\n[6] Последние логи веб-интерфейса...")
exit_status, output, error = execute_command(client, f"tail -50 {PROJECT_PATH}/web-interface.log 2>&1")
if output.strip():
    print(output[-1000:])
else:
    print("[INFO] Логи пусты")

client.close()

print("\n" + "=" * 60)
print("ВЫВОДЫ:")
print("=" * 60)
if not has_llm_usage and elapsed < 60:
    print("⚠️ LLM не используется - тест выполняется без AI")
    print("Возможные причины:")
    print("  1. .env не загружается при запуске")
    print("  2. LLM_PROVIDER не установлен правильно")
    print("  3. Агенты пропускаются из-за resume")

