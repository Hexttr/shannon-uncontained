#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка скрипта на сервер и выполнение там
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

def upload_and_execute(client, script_file):
    """Загрузить скрипт и выполнить на сервере"""
    print(f"[INFO] Загрузка {script_file}...")
    
    # Прочитать скрипт
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    remote_path = f"{PROJECT_PATH}/{script_file}"
    
    # Загрузить
    sftp = client.open_sftp()
    try:
        with sftp.file(remote_path, 'w') as f:
            f.write(script_content)
        sftp.chmod(remote_path, 0o755)
        print(f"[OK] Файл загружен: {remote_path}")
    finally:
        sftp.close()
    
    # Выполнить
    print(f"[INFO] Выполнение {script_file} на сервере...")
    stdin, stdout, stderr = client.exec_command(f"cd {PROJECT_PATH} && python3 {script_file}")
    
    # Читать вывод
    output_lines = []
    error_lines = []
    
    while True:
        if stdout.channel.exit_status_ready():
            break
        
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            if data:
                print(data, end='', flush=True)
                output_lines.append(data)
        
        if stderr.channel.recv_stderr_ready():
            data = stderr.channel.recv_stderr(4096).decode('utf-8', errors='ignore')
            if data:
                print(data, end='', flush=True, file=sys.stderr)
                error_lines.append(data)
    
    exit_status = stdout.channel.recv_exit_status()
    remaining_output = stdout.read().decode('utf-8', errors='ignore')
    remaining_error = stderr.read().decode('utf-8', errors='ignore')
    
    if remaining_output:
        print(remaining_output, end='', flush=True)
    if remaining_error:
        print(remaining_error, end='', flush=True, file=sys.stderr)
    
    return exit_status

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Загрузить и выполнить скрипт проверки
        exit_status = upload_and_execute(client, 'server_sync_and_check.py')
        
        if exit_status == 0:
            print("\n[OK] Скрипт выполнен успешно")
        else:
            print(f"\n[WARN] Скрипт завершился с кодом {exit_status}")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

