#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка настройки и тестирование системы
"""

import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command):
    """Выполнить команду"""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def main():
    print("=" * 60)
    print("Проверка настройки Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Проверка .env файла
        print("[INFO] Проверка .env файла...")
        exit_status, output, error = execute_command(
            client,
            f"cat {PROJECT_PATH}/.env | head -30"
        )
        if exit_status == 0:
            print("[OK] Содержимое .env (первые 30 строк):")
            print(output)
        
        # Проверка Ollama
        print("\n[INFO] Проверка Ollama...")
        exit_status, output, error = execute_command(client, "ollama list")
        if exit_status == 0:
            print("[OK] Загруженные модели:")
            print(output)
        
        # Проверка Node.js
        print("\n[INFO] Проверка Node.js...")
        exit_status, output, error = execute_command(
            client,
            "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node --version"
        )
        if exit_status == 0:
            print(f"[OK] Node.js: {output.strip()}")
        
        # Проверка npm зависимостей
        print("\n[INFO] Проверка npm зависимостей...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && test -d node_modules && echo 'installed' || echo 'not installed'"
        )
        if exit_status == 0:
            if 'installed' in output:
                print("[OK] npm зависимости установлены")
            else:
                print("[WARN] npm зависимости не установлены")
        
        # Проверка системных инструментов
        print("\n[INFO] Проверка системных инструментов...")
        tools = ['nmap', 'git', 'curl']
        for tool in tools:
            exit_status, output, error = execute_command(client, f"which {tool}")
            if exit_status == 0:
                print(f"  [OK] {tool}: {output.strip()}")
            else:
                print(f"  [WARN] {tool}: не найден")
        
        # Проверка структуры проекта
        print("\n[INFO] Проверка структуры проекта...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && ls -la | head -20"
        )
        if exit_status == 0:
            print("[OK] Структура проекта:")
            print(output)
        
        # Тест чтения .env через Node.js
        print("\n[INFO] Тест чтения конфигурации...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -e \"require('dotenv').config(); console.log('LLM_PROVIDER:', process.env.LLM_PROVIDER); console.log('LLM_MODEL:', process.env.LLM_MODEL);\""
        )
        if exit_status == 0:
            print("[OK] Конфигурация читается:")
            print(output)
        
        print("\n" + "=" * 60)
        print("[OK] Проверка завершена!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

