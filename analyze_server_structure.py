#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ структуры проекта на сервере
"""
import paramiko
import os
import sys

# Настройка кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Данные для подключения
SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    """Подключение к серверу через SSH"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Подключение к серверу {SERVER_HOST}...")
        ssh.connect(
            hostname=SERVER_HOST,
            port=SERVER_PORT,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            timeout=10
        )
        print("[OK] Успешное подключение к серверу")
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def analyze_shannon_project(ssh):
    """Анализ проекта shannon-uncontained"""
    if not ssh:
        return
    
    print("\n=== Анализ проекта shannon-uncontained ===\n")
    
    commands = [
        ("Структура shannon-uncontained", "ls -la shannon-uncontained/"),
        ("README проекта", "head -50 shannon-uncontained/README.md 2>/dev/null || echo 'README не найден'"),
        ("Основные файлы проекта", "find shannon-uncontained -maxdepth 2 -type f -name '*.mjs' -o -name '*.js' -o -name '*.py' -o -name '*.json' -o -name 'package.json' | head -20"),
        ("Структура src", "ls -la shannon-uncontained/src/ 2>/dev/null || echo 'src не найден'"),
        ("Конфигурационные файлы", "find shannon-uncontained -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name 'config*' | head -20"),
        ("package.json", "cat shannon-uncontained/package.json 2>/dev/null || echo 'package.json не найден'"),
    ]
    
    results = {}
    
    for description, command in commands:
        print(f"\n--- {description} ---")
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output)
            results[description] = output
        if error and "Permission denied" not in error and "No such file" not in error:
            print(f"Ошибка: {error}")
    
    return results

def main():
    """Основная функция"""
    ssh = connect_to_server()
    
    if not ssh:
        return
    
    try:
        # Анализ проекта
        results = analyze_shannon_project(ssh)
        
        print("\n\n=== Анализ завершен ===")
        print("Структура проекта сохранена для дальнейшей работы")
        
    finally:
        ssh.close()
        print("\n[OK] Соединение закрыто")

if __name__ == "__main__":
    main()

