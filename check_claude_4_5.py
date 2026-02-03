#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка Claude 4.5 Sonnet и поиск готовой реализации
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

def test_claude_4_5_models(ssh):
    """Тест различных имен Claude 4.5 моделей"""
    print("=" * 70)
    print("ТЕСТ МОДЕЛЕЙ CLAUDE 4.5")
    print("=" * 70)
    
    # Возможные имена моделей Claude 4.5
    models_to_test = [
        "claude-4-5-sonnet-20250101",  # С датой
        "claude-4-5-sonnet",            # Без даты
        "claude-sonnet-4-5",            # Альтернативный формат
        "claude-4.5-sonnet",            # С точкой
        "claude-opus-4-5",              # Opus вариант
        "claude-4-5-opus",              # Opus вариант 2
        "claude-3-5-sonnet-20241022",   # Текущая (для сравнения)
    ]
    
    print("\nТестируем различные варианты имен моделей...\n")
    
    working_model = None
    
    for model in models_to_test:
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
    console.log('✅ SUCCESS - модель работает!');
    process.exit(0);
}}).catch(e => {{
    if (e.status === 404) {{
        console.log('❌ 404 - модель не найдена');
    }} else if (e.status === 400) {{
        console.log('❌ 400 - неверный запрос');
    }} else {{
        console.log('❌ ERROR:', e.message.substring(0, 80));
    }}
    process.exit(1);
}});
"
"""
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode('utf-8', errors='ignore')
        result = "✅" if "SUCCESS" in output else "❌"
        print(f"  {result} {output.strip()[:100]}")
        
        if "SUCCESS" in output:
            working_model = model
            print(f"\n🎉 НАЙДЕНА РАБОТАЮЩАЯ МОДЕЛЬ: {model}")
            break
    
    return working_model

def check_upstream_implementation(ssh):
    """Проверка upstream репозитория на готовую реализацию"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА UPSTREAM РЕПОЗИТОРИЯ")
    print("=" * 70)
    
    # Проверяем есть ли информация о Claude 4.5 в документации
    commands = [
        ("Поиск упоминаний Claude 4.5", "grep -r 'claude.*4.*5\\|4.5' shannon-uncontained/docs shannon-uncontained/*.md 2>/dev/null | head -10"),
        ("Проверка README", "grep -i 'claude\\|anthropic\\|model' shannon-uncontained/README.md | head -10"),
        ("Проверка конфигурационных файлов", "find shannon-uncontained -name '*.example' -o -name '.env.example' | xargs grep -i 'claude\\|anthropic' 2>/dev/null | head -10"),
    ]
    
    for desc, cmd in commands:
        print(f"\n{desc}:")
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output if output.strip() else "Не найдено")

def update_to_claude_4_5(ssh, model_name):
    """Обновление на Claude 4.5 Sonnet"""
    if not model_name:
        print("\n⚠️ Рабочая модель не найдена, используем стандартное имя")
        model_name = "claude-4-5-sonnet"
    
    print("\n" + "=" * 70)
    print(f"ОБНОВЛЕНИЕ НА {model_name.upper()}")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        
        # Обновляем .env
        print("\n1. Обновление .env...")
        with sftp.open('shannon-uncontained/.env', 'r') as f:
            env_content = f.read().decode('utf-8')
        
        import re
        env_content = re.sub(
            r'LLM_MODEL=.*',
            f'LLM_MODEL={model_name}',
            env_content
        )
        
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        print(f"[OK] .env обновлен: LLM_MODEL={model_name}")
        
        # Обновляем llm-client.js
        print("\n2. Обновление llm-client.js...")
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            llm_content = f.read().decode('utf-8')
        
        # Заменяем дефолтное имя модели в case 'anthropic'
        llm_content = re.sub(
            r"model: modelOverride \|\| 'claude-[^']+'",
            f"model: modelOverride || '{model_name}'",
            llm_content
        )
        
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(llm_content)
        print(f"[OK] llm-client.js обновлен")
        
        sftp.close()
        
        # Тестируем
        print("\n3. Тест обновленной конфигурации...")
        test_script = f"""
cd shannon-uncontained && node -e "
require('dotenv').config();
console.log('LLM_MODEL из .env:', process.env.LLM_MODEL);
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({{ apiKey: process.env.ANTHROPIC_API_KEY }});
client.messages.create({{
    model: process.env.LLM_MODEL,
    max_tokens: 20,
    messages: [{{ role: 'user', content: 'Say hello' }}]
}}).then(r => {{
    console.log('✅ SUCCESS:', r.content[0].text);
}}).catch(e => {{
    console.log('❌ ERROR:', e.message);
    if (e.status) console.log('Status:', e.status);
}});
"
"""
        stdin, stdout, stderr = ssh.exec_command(test_script)
        output = stdout.read().decode('utf-8', errors='ignore')
        print(output)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Тестируем модели
        working_model = test_claude_4_5_models(ssh)
        
        # Проверяем upstream
        check_upstream_implementation(ssh)
        
        # Обновляем если найдена рабочая модель
        if working_model:
            if update_to_claude_4_5(ssh, working_model):
                print("\n✅ ОБНОВЛЕНО НА CLAUDE 4.5 SONNET!")
                print(f"Используется модель: {working_model}")
        else:
            print("\n⚠️ Рабочая модель не найдена автоматически")
            print("Попробуем обновить на стандартное имя claude-4-5-sonnet")
            update_to_claude_4_5(ssh, "claude-4-5-sonnet")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

