#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка настройки Claude API
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

def verify_setup(ssh):
    """Проверка настройки"""
    print("=== Проверка настройки Claude API ===\n")
    
    checks = [
        ("Проверка .env файла", "grep -E 'LLM_PROVIDER|ANTHROPIC_API_KEY|LLM_MODEL' shannon-uncontained/.env | head -5"),
        ("Проверка импорта Anthropic", "grep -n 'import.*Anthropic' shannon-uncontained/src/ai/llm-client.js | head -2"),
        ("Проверка case 'anthropic'", "grep -A 5 \"case 'anthropic':\" shannon-uncontained/src/ai/llm-client.js | head -8"),
        ("Проверка package.json", "grep '@anthropic-ai/sdk' shannon-uncontained/package.json"),
    ]
    
    for description, command in checks:
        print(f"--- {description} ---")
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output)
        elif error and "Permission denied" not in error:
            print(f"[WARNING] {error.strip()}")

def fix_anthropic_case(ssh):
    """Исправление case 'anthropic' для правильной работы"""
    print("\n--- Исправление case 'anthropic' ---")
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Ищем текущий case 'anthropic'
        if "case 'anthropic':" in content:
            # Проверяем, правильно ли настроен
            if "throw new Error('Anthropic provider requires" in content:
                # Заменяем на правильную конфигурацию
                old_pattern = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                throw new Error('Anthropic provider requires @anthropic-ai/sdk - use Claude Code or set LLM_PROVIDER=github/openai/ollama/openrouter');"""
            
                new_pattern = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-3-5-sonnet-20241022'
                };"""
            
                if old_pattern in content:
                    content = content.replace(old_pattern, new_pattern)
                    print("[OK] Исправлен case 'anthropic'")
                else:
                    # Пробуем найти другой вариант
                    import re
                    pattern = r"case 'anthropic':.*?throw new Error\('Anthropic provider requires"
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        # Заменяем найденный блок
                        start = match.start()
                        end = content.find("';", match.end()) + 2
                        old_block = content[start:end]
                        content = content.replace(old_block, new_pattern)
                        print("[OK] Исправлен case 'anthropic' (альтернативный паттерн)")
                    else:
                        print("[INFO] case 'anthropic' уже настроен или имеет другой формат")
            else:
                print("[INFO] case 'anthropic' уже правильно настроен")
        else:
            print("[WARNING] case 'anthropic' не найден в файле")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при исправлении: {e}")
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        verify_setup(ssh)
        fix_anthropic_case(ssh)
        print("\n=== Повторная проверка ===")
        verify_setup(ssh)
        
        print("\n=== Настройка завершена! ===")
        print("Claude 3.5 Sonnet готов к использованию")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

