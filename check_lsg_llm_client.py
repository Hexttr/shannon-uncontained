#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка LLM клиента в LSGv2 на поддержку Anthropic
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

def analyze_lsg_llm_client(ssh):
    """Анализ LLM клиента в LSGv2"""
    print("=" * 70)
    print("АНАЛИЗ LLM КЛИЕНТА В LSGv2")
    print("=" * 70)
    
    # Читаем файл полностью
    stdin, stdout, stderr = ssh.exec_command("cat shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js")
    llm_client_content = stdout.read().decode('utf-8', errors='ignore')
    
    # Ищем использование Anthropic
    print("\n1. Поиск использования Anthropic:")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'anthropic\\|Anthropic\\|claude' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -20")
    anthropic_usage = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_usage if anthropic_usage else "Не найдено")
    
    # Ищем getProviderConfig или аналогичную функцию
    print("\n2. Поиск функции конфигурации провайдера:")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'getProvider\\|provider.*config\\|LLM_PROVIDER' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -20")
    provider_config = stdout.read().decode('utf-8', errors='ignore')
    print(provider_config if provider_config else "Не найдено")
    
    # Показываем структуру файла
    print("\n3. Структура файла (первые 150 строк):")
    print(llm_client_content[:3000])
    
    return llm_client_content

def check_if_we_can_use_lsg(ssh):
    """Проверка можно ли использовать LSGv2 LLM клиент"""
    print("\n" + "=" * 70)
    print("ВОЗМОЖНОСТЬ ИСПОЛЬЗОВАНИЯ LSGv2 LLM КЛИЕНТА")
    print("=" * 70)
    
    # Проверяем как используется LLM клиент
    stdin, stdout, stderr = ssh.exec_command("grep -r 'from.*llm-client' shannon-uncontained/src/local-source-generator/v2/orchestrator/*.js | head -10")
    imports = stdout.read().decode('utf-8', errors='ignore')
    print("Импорты LLM клиента:")
    print(imports if imports else "Не найдено")
    
    # Проверяем используется ли он в основном коде
    stdin, stdout, stderr = ssh.exec_command("grep -r 'orchestrator/llm-client' shannon-uncontained/src shannon-uncontained/*.mjs 2>/dev/null | head -10")
    usage = stdout.read().decode('utf-8', errors='ignore')
    print("\nИспользование в основном коде:")
    print(usage if usage else "Не найдено")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        content = analyze_lsg_llm_client(ssh)
        check_if_we_can_use_lsg(ssh)
        
        # Проверяем есть ли поддержка Anthropic
        if 'anthropic' in content.lower() or 'Anthropic' in content:
            print("\n✅ В LSGv2 LLM клиенте ЕСТЬ поддержка Anthropic!")
        else:
            print("\n⚠️ В LSGv2 LLM клиенте НЕТ прямой поддержки Anthropic")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

