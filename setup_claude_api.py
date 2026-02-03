#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Настройка Claude API вместо Ollama на сервере
"""
import paramiko
import os
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

# Claude API ключ (НЕ коммитить в git!)
# Установите ключ через переменную окружения или .env файл
CLAUDE_API_KEY = process.env.ANTHROPIC_API_KEY || ""
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def update_env_file(ssh):
    """Обновление .env файла на сервере"""
    env_content = f"""# ============================================
# Shannon-Uncontained LLM Configuration
# ============================================

# LLM Provider - Claude (Anthropic) вместо Ollama
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY={CLAUDE_API_KEY}
LLM_MODEL={CLAUDE_MODEL}

# Альтернативные провайдеры (закомментированы)
# LLM_PROVIDER=ollama
# LLM_MODEL=codellama:7b

# OpenAI (альтернатива)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your_key_here
# LLM_MODEL=gpt-4o

# GitHub Models (бесплатный)
# LLM_PROVIDER=github
# GITHUB_TOKEN=ghp_your_token_here
"""
    
    try:
        sftp = ssh.open_sftp()
        # Создаем резервную копию
        try:
            sftp.stat('shannon-uncontained/.env.backup')
        except:
            stdin, stdout, stderr = ssh.exec_command('cp shannon-uncontained/.env shannon-uncontained/.env.backup 2>/dev/null || true')
            stdout.read()
        
        # Записываем новый .env
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        
        sftp.close()
        print("[OK] .env файл обновлен на сервере")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при обновлении .env: {e}")
        return False

def check_anthropic_sdk(ssh):
    """Проверка наличия @anthropic-ai/sdk в package.json"""
    try:
        stdin, stdout, stderr = ssh.exec_command('grep -q "@anthropic-ai/sdk" shannon-uncontained/package.json && echo "found" || echo "not_found"')
        result = stdout.read().decode('utf-8').strip()
        return result == "found"
    except Exception as e:
        print(f"[ERROR] Ошибка при проверке package.json: {e}")
        return False

def install_anthropic_sdk(ssh):
    """Установка @anthropic-ai/sdk"""
    print("\n--- Установка @anthropic-ai/sdk ---")
    commands = [
        ("Переход в директорию проекта", "cd shannon-uncontained && pwd"),
        ("Установка пакета", "cd shannon-uncontained && npm install @anthropic-ai/sdk --save"),
    ]
    
    for description, command in commands:
        print(f"\n{description}...")
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output)
        if error and "npm WARN" not in error:
            print(f"Ошибка: {error}")
    
    # Проверяем установку
    if check_anthropic_sdk(ssh):
        print("[OK] @anthropic-ai/sdk установлен")
        return True
    else:
        print("[WARNING] Не удалось подтвердить установку @anthropic-ai/sdk")
        return False

def update_llm_client(ssh):
    """Обновление llm-client.js для поддержки Anthropic"""
    print("\n--- Обновление llm-client.js ---")
    
    # Читаем текущий файл
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Проверяем, есть ли уже импорт Anthropic
        if "import Anthropic" in content or "from '@anthropic-ai/sdk'" in content:
            print("[INFO] Anthropic SDK уже импортирован")
        else:
            # Добавляем импорт после других импортов
            import_line = "import Anthropic from '@anthropic-ai/sdk';\n"
            # Ищем место после импортов OpenAI
            if "import OpenAI from 'openai';" in content:
                content = content.replace(
                    "import OpenAI from 'openai';",
                    "import OpenAI from 'openai';\n" + import_line
                )
                print("[OK] Добавлен импорт Anthropic SDK")
        
        # Обновляем case 'anthropic'
        old_anthropic_case = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                throw new Error('Anthropic provider requires @anthropic-ai/sdk - use Claude Code or set LLM_PROVIDER=github/openai/ollama/openrouter');"""
        
        new_anthropic_case = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-3-5-sonnet-20241022'
                };"""
        
        if old_anthropic_case in content:
            content = content.replace(old_anthropic_case, new_anthropic_case)
            print("[OK] Обновлен case 'anthropic' для использования Anthropic SDK")
        else:
            print("[WARNING] Не найден старый case 'anthropic', возможно уже обновлен")
        
        # Сохраняем обновленный файл
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        print("[OK] llm-client.js обновлен")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при обновлении llm-client.js: {e}")
        return False

def main():
    print("=== Настройка Claude API вместо Ollama ===\n")
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # 1. Проверяем наличие Anthropic SDK
        print("1. Проверка @anthropic-ai/sdk...")
        if not check_anthropic_sdk(ssh):
            print("   [INFO] @anthropic-ai/sdk не найден, устанавливаем...")
            install_anthropic_sdk(ssh)
        else:
            print("   [OK] @anthropic-ai/sdk уже установлен")
        
        # 2. Обновляем .env файл
        print("\n2. Обновление .env файла...")
        update_env_file(ssh)
        
        # 3. Обновляем llm-client.js
        print("\n3. Обновление llm-client.js...")
        update_llm_client(ssh)
        
        print("\n=== Настройка завершена! ===")
        print("\nТеперь проект будет использовать Claude 3.5 Sonnet вместо Ollama")
        print(f"Модель: {CLAUDE_MODEL}")
        print("\nДля применения изменений перезапустите приложение на сервере")
        
    finally:
        ssh.close()
        print("\n[OK] Соединение закрыто")

if __name__ == "__main__":
    main()

