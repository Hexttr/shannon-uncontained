#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка правильных имен моделей Anthropic
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

def test_correct_models(ssh):
    """Тест правильных имен моделей"""
    print("=" * 70)
    print("ПРОВЕРКА ПРАВИЛЬНЫХ ИМЕН МОДЕЛЕЙ ANTHROPIC")
    print("=" * 70)
    
    # Правильные имена моделей согласно документации Anthropic
    correct_models = [
        "claude-3-5-sonnet-20241022",  # Стандартный формат
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet",  # Без даты (может работать)
    ]
    
    print("\nТестируем стандартные имена моделей...\n")
    
    for model in correct_models:
        print(f"Тест: {model}")
        test_script = f"""
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({{ apiKey: process.env.ANTHROPIC_API_KEY }});
client.messages.create({{
    model: '{model}',
    max_tokens: 10,
    messages: [{{ role: 'user', content: 'Hi' }}]
}}).then(r => {{
    console.log('✅ SUCCESS');
    process.exit(0);
}}).catch(e => {{
    if (e.status === 404) {{
        console.log('❌ 404 - модель не найдена');
    }} else {{
        console.log('❌ ERROR:', e.message.substring(0, 100));
    }}
    process.exit(1);
}});
"
"""
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode('utf-8', errors='ignore')
        result = "✅" if "SUCCESS" in output else "❌"
        print(f"  {result} {output.strip()}")
        
        if "SUCCESS" in output:
            print(f"\n🎉 НАЙДЕНА РАБОТАЮЩАЯ МОДЕЛЬ: {model}")
            return model
    
    return None

def check_api_key_validity(ssh):
    """Проверка валидности API ключа"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ВАЛИДНОСТИ API КЛЮЧА")
    print("=" * 70)
    
    # Проверяем формат ключа
    stdin, stdout, stderr = ssh.exec_command("grep 'ANTHROPIC_API_KEY=' shannon-uncontained/.env | cut -d'=' -f2")
    api_key = stdout.read().decode('utf-8').strip()
    
    print(f"API ключ начинается с: {api_key[:20]}...")
    print(f"Длина ключа: {len(api_key)} символов")
    
    if not api_key.startswith('sk-ant-api03-'):
        print("⚠️ ВНИМАНИЕ: Ключ должен начинаться с 'sk-ant-api03-'")
        return False
    
    # Тест с простым запросом к известной модели
    print("\nТест API ключа с моделью claude-3-haiku-20240307...")
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
client.messages.create({
    model: 'claude-3-haiku-20240307',
    max_tokens: 10,
    messages: [{ role: 'user', content: 'Hi' }]
}).then(r => {
    console.log('✅ API ключ валиден, модель работает');
    process.exit(0);
}).catch(e => {
    if (e.status === 401) {
        console.log('❌ 401 - неверный API ключ');
    } else if (e.status === 404) {
        console.log('❌ 404 - модель не найдена');
    } else {
        console.log('❌ ERROR:', e.message);
    }
    process.exit(1);
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output)
    
    return "валиден" in output.lower()

def fix_with_working_model(ssh, working_model):
    """Исправление с рабочей моделью"""
    if not working_model:
        return False
    
    print("\n" + "=" * 70)
    print(f"ИСПРАВЛЕНИЕ С МОДЕЛЬЮ: {working_model}")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        
        # Обновляем .env
        with sftp.open('shannon-uncontained/.env', 'r') as f:
            env_content = f.read().decode('utf-8')
        
        import re
        env_content = re.sub(
            r'LLM_MODEL=.*',
            f'LLM_MODEL={working_model}',
            env_content
        )
        
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        
        print(f"[OK] .env обновлен")
        
        # Обновляем llm-client.js
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            llm_content = f.read().decode('utf-8')
        
        # Заменяем дефолтное имя модели
        llm_content = re.sub(
            r"model: modelOverride \|\| '[^']+'",
            f"model: modelOverride || '{working_model}'",
            llm_content
        )
        
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(llm_content)
        
        print(f"[OK] llm-client.js обновлен")
        
        sftp.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Проверяем API ключ
        if not check_api_key_validity(ssh):
            print("\n⚠️ Проблема с API ключом или доступом")
        
        # Тестируем модели
        working_model = test_correct_models(ssh)
        
        if working_model:
            # Исправляем с рабочей моделью
            if fix_with_working_model(ssh, working_model):
                print("\n✅ ИСПРАВЛЕНО! Используется модель:", working_model)
            else:
                print("\n❌ Ошибка при исправлении")
        else:
            print("\n❌ Не найдена рабочая модель. Возможные причины:")
            print("   1. Неверный API ключ")
            print("   2. Проблемы с доступом к API")
            print("   3. Неправильный формат запроса")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

