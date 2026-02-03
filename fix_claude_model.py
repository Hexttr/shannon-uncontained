#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление имени модели Claude
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

def test_model_names(ssh):
    """Тест различных имен моделей"""
    print("=" * 70)
    print("ТЕСТ РАЗЛИЧНЫХ ИМЕН МОДЕЛЕЙ CLAUDE")
    print("=" * 70)
    
    # Правильные имена моделей Anthropic
    model_names = [
        "claude-sonnet-3-5-20241022",  # Правильный формат
        "claude-3-5-sonnet-20241022",   # Текущий (неправильный)
        "claude-3-5-sonnet",            # Без даты
        "claude-sonnet-3.5-20241022",  # С точкой
    ]
    
    for model_name in model_names:
        print(f"\nТест модели: {model_name}")
        test_script = f"""
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({{ apiKey: process.env.ANTHROPIC_API_KEY }});
client.messages.create({{
    model: '{model_name}',
    max_tokens: 10,
    messages: [{{ role: 'user', content: 'Hi' }}]
}}).then(r => {{
    console.log('✅ SUCCESS:', r.content[0].text);
}}).catch(e => {{
    console.log('❌ ERROR:', e.message);
}});
"
"""
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output.strip())

def fix_model_name(ssh):
    """Исправление имени модели"""
    print("\n" + "=" * 70)
    print("ИСПРАВЛЕНИЕ ИМЕНИ МОДЕЛИ")
    print("=" * 70)
    
    # Правильное имя модели
    correct_model = "claude-sonnet-3-5-20241022"
    
    try:
        sftp = ssh.open_sftp()
        
        # Обновляем .env
        print("\n1. Обновление .env файла...")
        with sftp.open('shannon-uncontained/.env', 'r') as f:
            env_content = f.read().decode('utf-8')
        
        # Заменяем имя модели
        import re
        env_content = re.sub(
            r'LLM_MODEL=.*',
            f'LLM_MODEL={correct_model}',
            env_content
        )
        
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        
        print(f"[OK] .env обновлен: LLM_MODEL={correct_model}")
        
        # Обновляем llm-client.js
        print("\n2. Обновление llm-client.js...")
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            llm_content = f.read().decode('utf-8')
        
        # Заменяем дефолтное имя модели
        llm_content = llm_content.replace(
            "model: modelOverride || 'claude-3-5-sonnet-20241022'",
            f"model: modelOverride || '{correct_model}'"
        )
        
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(llm_content)
        
        print(f"[OK] llm-client.js обновлен")
        
        sftp.close()
        
        # Тестируем исправление
        print("\n3. Тест исправленной модели...")
        test_script = f"""
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({{ apiKey: process.env.ANTHROPIC_API_KEY }});
console.log('Модель из .env:', process.env.LLM_MODEL);
client.messages.create({{
    model: process.env.LLM_MODEL,
    max_tokens: 20,
    messages: [{{ role: 'user', content: 'Say hello in one word' }}]
}}).then(r => {{
    console.log('✅ SUCCESS:', r.content[0].text);
    process.exit(0);
}}).catch(e => {{
    console.log('❌ ERROR:', e.message);
    if (e.status) console.log('Status:', e.status);
    process.exit(1);
}});
"
"""
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        print(output)
        if error:
            print("Ошибки:", error)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при исправлении: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Сначала тестируем разные имена
        test_model_names(ssh)
        
        # Затем исправляем
        if fix_model_name(ssh):
            print("\n" + "=" * 70)
            print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
            print("=" * 70)
            print("\nТеперь можно перезапустить пентест через веб-интерфейс")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

