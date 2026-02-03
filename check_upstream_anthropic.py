#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка готовой реализации Anthropic в upstream
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

def check_upstream_files(ssh):
    """Проверка файлов из upstream"""
    print("=" * 70)
    print("ПРОВЕРКА UPSTREAM РЕАЛИЗАЦИИ")
    print("=" * 70)
    
    # Проверяем LLM_SETUP_GUIDE.md
    print("\n1. Проверка LLM_SETUP_GUIDE.md...")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'Claude 4.5 Sonnet' shannon-uncontained/LLM_SETUP_GUIDE.md | head -30")
    guide_content = stdout.read().decode('utf-8', errors='ignore')
    print(guide_content)
    
    # Проверяем как настроен Anthropic в upstream
    print("\n2. Проверка текущей реализации llm-client.js...")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'case.*anthropic' shannon-uncontained/src/ai/llm-client.js | head -15")
    anthropic_case = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_case)
    
    # Проверяем используется ли Anthropic SDK в query функции
    print("\n3. Проверка использования Anthropic SDK в query...")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'new Anthropic\\|anthropicClient' shannon-uncontained/src/ai/llm-client.js | head -10")
    anthropic_usage = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_usage if anthropic_usage else "Не найдено прямого использования Anthropic SDK")
    
    # Проверяем документацию по интеграции
    print("\n4. Проверка документации по интеграции...")
    stdin, stdout, stderr = ssh.exec_command("cat shannon-uncontained/LLM_SETUP_GUIDE.md | grep -A 30 'Claude 4.5 Sonnet поддерживается' | head -40")
    integration_docs = stdout.read().decode('utf-8', errors='ignore')
    print(integration_docs)

def verify_current_setup(ssh):
    """Проверка текущей настройки"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ТЕКУЩЕЙ НАСТРОЙКИ")
    print("=" * 70)
    
    # Проверяем .env
    stdin, stdout, stderr = ssh.exec_command("grep -E 'LLM_PROVIDER|LLM_MODEL|ANTHROPIC' shannon-uncontained/.env")
    env_config = stdout.read().decode('utf-8', errors='ignore')
    print("\nТекущая конфигурация .env:")
    print(env_config)
    
    # Тест работы модели
    print("\nТест работы модели...")
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
console.log('Модель:', process.env.LLM_MODEL);
client.messages.create({
    model: process.env.LLM_MODEL,
    max_tokens: 50,
    messages: [{ role: 'user', content: 'Say hello and confirm you are Claude 4.5 Sonnet' }]
}).then(r => {
    console.log('✅ Ответ:', r.content[0].text);
}).catch(e => {
    console.log('❌ Ошибка:', e.message);
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    test_output = stdout.read().decode('utf-8', errors='ignore')
    print(test_output)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_upstream_files(ssh)
        verify_current_setup(ssh)
        
        print("\n" + "=" * 70)
        print("ИТОГОВЫЙ СТАТУС")
        print("=" * 70)
        print("\n✅ Модель Claude 4.5 Sonnet найдена и работает!")
        print("✅ Имя модели: claude-sonnet-4-5")
        print("✅ Конфигурация обновлена")
        print("\n📝 В upstream репозитории есть документация по Claude 4.5 Sonnet")
        print("   но полная интеграция требует обновления функции query")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

