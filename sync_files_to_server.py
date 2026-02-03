#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация всех файлов на сервер через tar архив
"""

import paramiko
import sys
import io
import os
import tarfile

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def main():
    print("=" * 60)
    print("Синхронизация файлов на сервер")
    print("=" * 60)
    
    # Создать архив
    print("\n[INFO] Создание архива...")
    archive_name = "shannon-sync.tar.gz"
    
    exclude_dirs = {'.git', 'node_modules', 'shannon-results', 'temp_repo', '__pycache__', '.pytest_cache'}
    exclude_patterns = ['.log', '.pyc', '.DS_Store', archive_name]
    
    with tarfile.open(archive_name, "w:gz") as tar:
        for root, dirs, files in os.walk('.'):
            # Исключить директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                # Пропустить исключенные файлы
                if any(file.endswith(ext) for ext in exclude_patterns):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                
                try:
                    tar.add(file_path, arcname=arcname)
                    if len([f for f in os.listdir('.') if f.endswith('.py')]) < 50:  # Показывать только если файлов немного
                        print(f"  [ADD] {arcname[:60]}")
                except Exception as e:
                    print(f"  [WARN] Пропущен {arcname}: {e}")
    
    print(f"\n[OK] Архив создан: {archive_name} ({os.path.getsize(archive_name) / 1024 / 1024:.2f} MB)")
    
    # Загрузить на сервер
    print("[INFO] Загрузка архива на сервер...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}")
        
        sftp = client.open_sftp()
        try:
            sftp.put(archive_name, f"{PROJECT_PATH}.sync.tar.gz")
            print("[OK] Архив загружен")
        finally:
            sftp.close()
        
        # Распаковать на сервере
        print("[INFO] Распаковка архива на сервере...")
        stdin, stdout, stderr = client.exec_command(
            f"cd {PROJECT_PATH} && tar -xzf {PROJECT_PATH}.sync.tar.gz --exclude='node_modules' --exclude='.git' --exclude='shannon-results' 2>&1 && rm -f {PROJECT_PATH}.sync.tar.gz && echo 'OK'"
        )
        
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if 'OK' in output:
            print("[OK] Архив распакован")
        else:
            print(f"[WARN] Вывод: {output[:200]}")
            if error:
                print(f"[ERROR]: {error[:200]}")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    # Удалить локальный архив
    if os.path.exists(archive_name):
        os.remove(archive_name)
        print(f"[OK] Локальный архив удален")
    
    print("\n" + "=" * 60)
    print("[OK] Синхронизация завершена")
    print("=" * 60)

if __name__ == "__main__":
    main()

