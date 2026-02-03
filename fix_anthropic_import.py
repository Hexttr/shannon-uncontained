#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление импорта Anthropic
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

def check_imports(ssh):
    """Проверка импортов"""
    print("=" * 70)
    print("ПРОВЕРКА ИМПОРТОВ")
    print("=" * 70)
    
    # Проверяем импорты в начале файла
    print("\n1. Импорты в начале файла:")
    stdin, stdout, stderr = ssh.exec_command("head -10 shannon-uncontained/src/ai/llm-client.js")
    imports = stdout.read().decode('utf-8', errors='ignore')
    print(imports)
    
    # Проверяем есть ли импорт Anthropic
    stdin, stdout, stderr = ssh.exec_command("grep -n 'import.*Anthropic\\|require.*Anthropic' shannon-uncontained/src/ai/llm-client.js")
    anthropic_import = stdout.read().decode('utf-8', errors='ignore')
    print("\n2. Импорт Anthropic:")
    print(anthropic_import if anthropic_import else "❌ НЕ НАЙДЕН!")

def fix_imports(ssh):
    """Исправление импортов"""
    print("\n" + "=" * 70)
    print("ИСПРАВЛЕНИЕ ИМПОРТОВ")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Проверяем есть ли импорт Anthropic
        if "import Anthropic" not in content and "require('@anthropic-ai/sdk')" not in content:
            print("\n[ПРОБЛЕМА] Импорт Anthropic отсутствует!")
            
            # Находим место после импорта OpenAI
            openai_import_pos = content.find("import OpenAI from 'openai';")
            if openai_import_pos != -1:
                # Вставляем импорт Anthropic после OpenAI
                import_line = "import Anthropic from '@anthropic-ai/sdk';\n"
                content = content[:openai_import_pos + len("import OpenAI from 'openai';")] + "\n" + import_line + content[openai_import_pos + len("import OpenAI from 'openai';"):]
                print("[OK] Добавлен импорт Anthropic")
            else:
                # Ищем любое место в начале файла
                first_import = content.find("import ")
                if first_import != -1:
                    # Находим конец первой строки импорта
                    first_line_end = content.find("\n", first_import)
                    import_line = "import Anthropic from '@anthropic-ai/sdk';\n"
                    content = content[:first_line_end + 1] + import_line + content[first_line_end + 1:]
                    print("[OK] Добавлен импорт Anthropic (альтернативное место)")
                else:
                    print("[ERROR] Не найдено место для импорта")
                    sftp.close()
                    return False
        else:
            print("[OK] Импорт Anthropic уже есть")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c src/ai/llm-client.js 2>&1")
        syntax_check = stdout.read().decode('utf-8', errors='ignore')
        error_check = stderr.read().decode('utf-8', errors='ignore')
        
        if syntax_check or error_check:
            print("Ошибки:")
            print(syntax_check)
            print(error_check)
            return False
        else:
            print("[OK] Синтаксис корректен")
            
            # Тестируем что импорт работает
            print("\nТест импорта...")
            test_import = """
cd shannon-uncontained && node -e "
import('./src/ai/llm-client.js').then(m => {
    if (m.Anthropic || typeof Anthropic !== 'undefined') {
        console.log('✅ Anthropic доступен');
    } else {
        console.log('❌ Anthropic не доступен');
    }
    // Проверяем через require
    const Anthropic = require('@anthropic-ai/sdk');
    console.log('✅ Anthropic через require:', typeof Anthropic);
});
"
"""
            stdin, stdout, stderr = ssh.exec_command(test_import)
            import_test = stdout.read().decode('utf-8', errors='ignore')
            print(import_test)
            
            return True
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_query_after_fix(ssh):
    """Тест query после исправления"""
    print("\n" + "=" * 70)
    print("ТЕСТ QUERY ПОСЛЕ ИСПРАВЛЕНИЯ")
    print("=" * 70)
    
    test_query = """
cd shannon-uncontained && timeout 10 node -e "
require('dotenv').config();
import('./src/ai/llm-client.js').then(async m => {
    try {
        const gen = m.query({ 
            prompt: 'Say hello in one word', 
            options: { cwd: '/tmp', maxTurns: 1 } 
        });
        const first = await gen.next();
        console.log('✅ Первый результат получен');
        console.log('Тип:', first.value?.type);
        if (first.value?.message) {
            console.log('Сообщение:', first.value.message.content?.substring(0, 50));
        }
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack?.substring(0, 500));
    }
});
" 2>&1
"""
    stdin, stdout, stderr = ssh.exec_command(test_query)
    query_test = stdout.read().decode('utf-8', errors='ignore')
    print(query_test)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_imports(ssh)
        
        if fix_imports(ssh):
            test_query_after_fix(ssh)
            print("\n✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
            print("\nТеперь Anthropic импортирован и должен работать в функции query")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

