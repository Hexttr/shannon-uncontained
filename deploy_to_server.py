#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для копирования проекта на сервер и установки зависимостей
"""

import paramiko
import os
import sys
import tarfile
import io
from pathlib import Path

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
REMOTE_PATH = "/root/shannon-uncontained"

def create_archive():
    """Создание архива проекта"""
    print("[INFO] Создание архива проекта...")
    
    exclude_dirs = {'.git', 'node_modules', 'temp_repo', '__pycache__', '.pytest_cache'}
    exclude_files = {'.DS_Store', '*.pyc', '*.pyo'}
    
    archive_name = "shannon-uncontained.tar.gz"
    
    with tarfile.open(archive_name, "w:gz") as tar:
        for root, dirs, files in os.walk('.'):
            # Фильтруем директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                # Пропускаем архив и исключенные файлы
                if file_path == archive_name or any(file.endswith(ext) for ext in exclude_files):
                    continue
                
                # Пропускаем файлы в исключенных директориях
                if any(excluded in file_path for excluded in exclude_dirs):
                    continue
                
                tar.add(file_path, arcname=file_path)
    
    print(f"[OK] Архив создан: {archive_name}")
    return archive_name

def upload_file(sftp, local_path, remote_path):
    """Загрузка файла на сервер"""
    try:
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки {local_path}: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("Deploy Shannon-Uncontained to Server")
    print("=" * 60)
    
    # Создание архива
    archive_name = create_archive()
    
    # Подключение к серверу
    print("\n[INFO] Подключение к серверу...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=HOST,
            username=USERNAME,
            password=PASSWORD,
            timeout=30
        )
        print(f"[OK] Подключено к {HOST}")
        
        # Загрузка архива
        print(f"\n[INFO] Загрузка архива на сервер...")
        sftp = client.open_sftp()
        remote_archive = f"{REMOTE_PATH}.tar.gz"
        
        if upload_file(sftp, archive_name, remote_archive):
            print(f"[OK] Архив загружен: {remote_archive}")
        else:
            print("[ERROR] Не удалось загрузить архив")
            return
        
        sftp.close()
        
        # Распаковка и установка на сервере
        print("\n[INFO] Распаковка и установка на сервере...")
        commands = [
            f"cd /root && rm -rf {REMOTE_PATH}",
            f"cd /root && tar -xzf {REMOTE_PATH}.tar.gz",
            f"cd {REMOTE_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && npm install",
            f"cd {REMOTE_PATH} && cp .env.example .env || true",
            f"rm -f {REMOTE_PATH}.tar.gz",
        ]
        
        for cmd in commands:
            print(f"  Выполнение: {cmd[:80]}...")
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                output = stdout.read().decode('utf-8')
                if output.strip():
                    print(f"    [OK] {output[:100]}")
                else:
                    print(f"    [OK] Команда выполнена")
            else:
                error = stderr.read().decode('utf-8')
                print(f"    [WARN] Предупреждение: {error[:200]}")
        
        print("\n" + "=" * 60)
        print("[OK] Развертывание завершено!")
        print("=" * 60)
        print(f"\nСледующие шаги:")
        print(f"1. Подключитесь к серверу: ssh {USERNAME}@{HOST}")
        print(f"2. Перейдите в директорию: cd {REMOTE_PATH}")
        print(f"3. Настройте .env файл: nano .env")
        print(f"4. Запустите: ./shannon.mjs generate https://example.com")
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        # Удаление локального архива
        if os.path.exists(archive_name):
            os.remove(archive_name)
            print(f"\n[INFO] Локальный архив удален")

if __name__ == "__main__":
    main()

