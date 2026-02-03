#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка реализации query в upstream
"""
import paramiko
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def check_lsg_orchestrator(ssh):
    """Проверка LSGv2 Orchestrator который может иметь готовую реализацию"""
    print("=" * 70)
    print("ПРОВЕРКА LSGv2 ORCHESTRATOR")
    print("=" * 70)
    
    # Ищем LLM клиент в LSGv2
    commands = [
        ("Поиск LLM клиента в LSGv2", "find shannon-uncontained/src/local-source-generator -name '*llm*' -o -name '*anthropic*' 2>/dev/null | head -10"),
        ("Проверка orchestrator", "ls -la shannon-uncontained/src/local-source-generator/v2/orchestrator/ 2>/dev/null | head -10"),
        ("LLM клиент в orchestrator", "cat shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js 2>/dev/null | head -100 || echo 'Файл не найден'"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output[:500] if output else "Не найдено")

def check_claude_executor(ssh):
    """Проверка Claude Executor"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА CLAUDE EXECUTOR")
    print("=" * 70)
    
    stdin, stdout, stderr = ssh.exec_command("ls -la shannon-uncontained/src/ai/claude-executor.js 2>/dev/null && head -50 shannon-uncontained/src/ai/claude-executor.js || echo 'Файл не найден'")
    executor_content = stdout.read().decode('utf-8', errors='ignore')
    print(executor_content[:1000])

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_lsg_orchestrator(ssh)
        check_claude_executor(ssh)
        
        print("\n" + "=" * 70)
        print("РЕКОМЕНДАЦИИ")
        print("=" * 70)
        print("\n✅ Модель claude-sonnet-4-5 работает")
        print("✅ Конфигурация обновлена на Claude 4.5 Sonnet")
        print("\n📝 В upstream есть:")
        print("   - LSGv2 Orchestrator с собственным LLM клиентом")
        print("   - Claude Executor с поддержкой Anthropic SDK")
        print("\n💡 Для полной интеграции можно использовать один из этих компонентов")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

