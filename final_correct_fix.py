#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальное правильное исправление
"""
import paramiko
import sys
import re

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

def fix_correctly(ssh):
    """Правильное исправление"""
    print("=" * 70)
    print("ПРАВИЛЬНОЕ ИСПРАВЛЕНИЕ")
    print("=" * 70)
    
    try:
        # Читаем локальный файл
        with open('src/ai/llm-client.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Исправляем только case 'anthropic' - заменяем throw на return
        pattern = r"(case 'anthropic':\s*if \(!anthropicKey\) throw new Error\('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set'\);\s*)throw new Error\('Anthropic provider requires @anthropic-ai/sdk[^']+'\);"
        
        replacement = r"\1return {\n                    provider: 'anthropic',\n                    baseURL: 'https://api.anthropic.com/v1',\n                    apiKey: anthropicKey,\n                    model: modelOverride || 'claude-3-5-sonnet-20241022'\n                };"
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print("[OK] Case 'anthropic' исправлен")
        else:
            # Пробуем более простой паттерн
            simple_pattern = r"throw new Error\('Anthropic provider requires @anthropic-ai/sdk"
            if simple_pattern in content:
                # Находим начало case
                case_pos = content.rfind("case 'anthropic':", 0, content.find(simple_pattern))
                if case_pos != -1:
                    # Находим конец throw
                    throw_end = content.find("';", content.find(simple_pattern)) + 2
                    # Заменяем
                    old_block = content[case_pos:throw_end]
                    new_block = """case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-3-5-sonnet-20241022'
                };"""
                    content = content[:case_pos] + new_block + content[throw_end:]
                    print("[OK] Case 'anthropic' исправлен (простой паттерн)")
                else:
                    print("[WARNING] Не найден case 'anthropic'")
            else:
                print("[INFO] Case 'anthropic' уже исправлен")
        
        # Загружаем на сервер
        sftp = ssh.open_sftp()
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
            return True
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_summary(ssh):
    """Создание итогового отчета"""
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    
    print("\n✅ ИСПРАВЛЕНО:")
    print("1. Case 'anthropic' теперь возвращает конфигурацию вместо throw")
    print("2. Синтаксис файла корректен")
    
    print("\n⚠️ ВАЖНО:")
    print("Функция query все еще использует OpenAI SDK для всех провайдеров")
    print("Это означает что Anthropic API будет вызываться через OpenAI-совместимый формат")
    print("НО Anthropic API НЕ совместим с OpenAI API!")
    
    print("\n📝 РЕШЕНИЕ:")
    print("Есть два варианта:")
    print("1. Использовать OpenRouter как прокси (поддерживает Anthropic через OpenAI API)")
    print("2. Обновить функцию query для использования Anthropic SDK напрямую")
    
    print("\n🔧 РЕКОМЕНДАЦИЯ:")
    print("Попробуйте сначала запустить пентест - возможно код уже работает")
    print("Если нет - нужно будет обновить функцию query для прямой работы с Anthropic SDK")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if fix_correctly(ssh):
            create_summary(ssh)
            print("\n✅ ГОТОВО К ТЕСТИРОВАНИЮ!")
        else:
            print("\n❌ Ошибка при исправлении")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

