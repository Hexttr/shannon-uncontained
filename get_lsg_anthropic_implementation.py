#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Получение полной реализации Anthropic из LSGv2
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

def get_anthropic_implementation(ssh):
    """Получение реализации Anthropic из LSGv2"""
    print("=" * 70)
    print("РЕАЛИЗАЦИЯ ANTHROPIC В LSGv2")
    print("=" * 70)
    
    # Получаем метод callAnthropic
    print("\n1. Метод callAnthropic:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 50 'callAnthropic' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -60")
    call_anthropic = stdout.read().decode('utf-8', errors='ignore')
    print(call_anthropic)
    
    # Проверяем как определяется модель
    print("\n2. Определение модели Claude 4.5:")
    stdin, stdout, stderr = ssh.exec_command("grep -B 5 -A 10 'claude-4.5\\|claude.*4.*5' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js")
    model_config = stdout.read().decode('utf-8', errors='ignore')
    print(model_config)
    
    # Проверяем как используется в RunCommand
    print("\n3. Использование в RunCommand:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'getLLMClient' shannon-uncontained/src/cli/commands/RunCommand.js | head -30")
    runcommand_usage = stdout.read().decode('utf-8', errors='ignore')
    print(runcommand_usage)

def download_lsg_llm_client(ssh):
    """Скачивание LSGv2 LLM клиента для анализа"""
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Сохраняем локально
        with open('lsg-llm-client.js', 'w', encoding='utf-8') as f:
            f.write(content)
        
        sftp.close()
        print("\n[OK] LSGv2 LLM клиент скачан как lsg-llm-client.js")
        return content
    except Exception as e:
        print(f"[ERROR] Ошибка при скачивании: {e}")
        return None

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        get_anthropic_implementation(ssh)
        content = download_lsg_llm_client(ssh)
        
        if content and 'callAnthropic' in content:
            print("\n✅ НАЙДЕНА ГОТОВАЯ РЕАЛИЗАЦИЯ ANTHROPIC!")
            print("LSGv2 LLM клиент имеет метод callAnthropic с полной поддержкой Anthropic API")
            print("\nМожно использовать эту реализацию или адаптировать её для основного llm-client.js")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

