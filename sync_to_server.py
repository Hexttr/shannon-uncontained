#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Синхронизация всех файлов из оригинала на сервер
"""

import paramiko
import os
import tarfile
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def create_archive():
    """Создать архив проекта исключая мои файлы"""
    exclude_dirs = {'.git', 'node_modules', 'temp_repo', '__pycache__', '.pytest_cache'}
    exclude_files = {
        '.DS_Store', '*.pyc', '*.pyo',
        # Мои файлы которые нужно исключить
        'ARCHITECTURE.md', 'DEPLOYMENT_STATUS.md', 'FINAL_REPORT.md',
        'IMPLEMENTATION_PLAN.md', 'LLM_SETUP_GUIDE.md', 'SETUP_COMPLETE.md',
        'SETUP_SUMMARY.md', 'TEST_RUN_REPORT.md',
        'check_results.py', 'check_server.py', 'deploy_fix.py', 'deploy_to_server.py',
        'download_missing_files.py', 'download_repo.py', 'fix_and_run.py',
        'run_test.py', 'server_setup.py', 'setup_complete.py', 'setup_ollama.py',
        'sync_to_server.py', 'verify_repo_completeness.py', 'verify_setup.py',
    }
    
    archive_name = "shannon-original.tar.gz"
    
    with tarfile.open(archive_name, "w:gz") as tar:
        for root, dirs, files in os.walk('.'):
            # Фильтруем директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, '.')
                
                # Пропускаем архив и исключенные файлы
                if file_path == archive_name:
                    continue
                
                # Пропускаем мои скрипты и документацию
                skip = False
                for excluded in exclude_files:
                    if excluded in rel_path or rel_path.endswith(excluded.replace('*', '')):
                        skip = True
                        break
                
                if skip:
                    continue
                
                # Пропускаем файлы в исключенных директориях
                if any(excluded in file_path for excluded in exclude_dirs):
                    continue
                
                tar.add(file_path, arcname=rel_path)
    
    print(f"[OK] Архив создан: {archive_name}")
    return archive_name

def main():
    print("=" * 60)
    print("Синхронизация оригинального кода на сервер")
    print("=" * 60)
    
    # Создать архив
    archive_name = create_archive()
    
    # Подключение к серверу
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Загрузка архива
        print("[INFO] Загрузка архива на сервер...")
        sftp = client.open_sftp()
        remote_archive = f"{PROJECT_PATH}.tar.gz"
        
        try:
            sftp.put(archive_name, remote_archive)
            print(f"[OK] Архив загружен: {remote_archive}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки: {e}")
            return
        finally:
            sftp.close()
        
        # Распаковка на сервере
        print("\n[INFO] Распаковка на сервере...")
        commands = [
            f"cd /root && rm -rf {PROJECT_PATH}",
            f"cd /root && mkdir -p {PROJECT_PATH}",
            f"cd /root && tar -xzf {PROJECT_PATH}.tar.gz -C {PROJECT_PATH} --strip-components=0",
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && npm install",
            f"rm -f {PROJECT_PATH}.tar.gz",
        ]
        
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print(f"  [OK] {cmd[:60]}...")
            else:
                error = stderr.read().decode('utf-8')
                print(f"  [WARN] {cmd[:60]}... - {error[:100]}")
        
        print("\n" + "=" * 60)
        print("[OK] Синхронизация завершена!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        # Удалить локальный архив
        if os.path.exists(archive_name):
            os.remove(archive_name)

if __name__ == "__main__":
    main()

