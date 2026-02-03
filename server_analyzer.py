#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для подключения к серверу и анализа файлов пентест-приложения
"""
import paramiko
import os
import sys
from pathlib import Path

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

def analyze_server_files(ssh):
    """Анализ файлов на сервере"""
    if not ssh:
        return
    
    print("\n=== Анализ структуры файлов на сервере ===\n")
    
    # Команды для анализа
    commands = [
        ("Текущая директория", "pwd"),
        ("Содержимое корневой директории", "ls -la"),
        ("Поиск Python файлов", "find . -name '*.py' -type f 2>/dev/null | head -20"),
        ("Поиск конфигурационных файлов", "find . -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.toml' -o -name '*.ini' -o -name '*.conf' 2>/dev/null | head -20"),
        ("Поиск README файлов", "find . -name 'README*' -o -name 'readme*' 2>/dev/null"),
        ("Процессы Python", "ps aux | grep python | grep -v grep"),
        ("Размер директорий", "du -sh */ 2>/dev/null | sort -h | tail -10"),
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
        if error and "Permission denied" not in error:
            print(f"Ошибка: {error}")
    
    return results

def download_files(ssh, remote_path, local_path):
    """Скачивание файлов с сервера"""
    if not ssh:
        return False
    
    try:
        sftp = ssh.open_sftp()
        
        # Создаем локальную директорию если нужно
        os.makedirs(local_path, exist_ok=True)
        
        # Рекурсивное скачивание
        def download_recursive(remote_dir, local_dir):
            try:
                items = sftp.listdir_attr(remote_dir)
                for item in items:
                    remote_item = f"{remote_dir}/{item.filename}"
                    local_item = os.path.join(local_dir, item.filename)
                    
                    if item.st_mode & 0o040000:  # Это директория
                        os.makedirs(local_item, exist_ok=True)
                        download_recursive(remote_item, local_item)
                    else:  # Это файл
                        print(f"Скачивание: {remote_item} -> {local_item}")
                        sftp.get(remote_item, local_item)
            except Exception as e:
                print(f"Ошибка при скачивании {remote_dir}: {e}")
        
        download_recursive(remote_path, local_path)
        sftp.close()
        return True
    except Exception as e:
        print(f"Ошибка при открытии SFTP: {e}")
        return False

def main():
    """Основная функция"""
    ssh = connect_to_server()
    
    if not ssh:
        return
    
    try:
        # Анализ файлов
        results = analyze_server_files(ssh)
        
        # Определяем рабочую директорию
        stdin, stdout, stderr = ssh.exec_command("pwd")
        work_dir = stdout.read().decode('utf-8').strip()
        print(f"\n\nРабочая директория на сервере: {work_dir}")
        
        # Спрашиваем о скачивании файлов
        print("\n=== Скачивание файлов ===")
        print("Скачиваю файлы с сервера...")
        
        # Скачиваем файлы в локальную директорию server_files
        if download_files(ssh, work_dir, "server_files"):
            print("[OK] Файлы успешно скачаны в директорию server_files/")
        else:
            print("[ERROR] Ошибка при скачивании файлов")
        
    finally:
        ssh.close()
        print("\n[OK] Соединение закрыто")

if __name__ == "__main__":
    main()

