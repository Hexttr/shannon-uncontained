#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Загрузить скрипт и выполнить на сервере"""

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
    with open(script_file, 'r', encoding='utf-8') as f:
        script_content = f.read()
    
    remote_path = f"{PROJECT_PATH}/{script_file}"
    sftp = client.open_sftp()
    try:
        with sftp.file(remote_path, 'w') as f:
            f.write(script_content)
        sftp.chmod(remote_path, 0o755)
        print(f"[OK] Загружен: {script_file}")
    finally:
        sftp.close()
    
    print(f"[INFO] Выполнение {script_file}...")
    stdin, stdout, stderr = client.exec_command(f"cd {PROJECT_PATH} && python3 {script_file}")
    
    output_lines = []
    while True:
        if stdout.channel.exit_status_ready():
            break
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            if data:
                print(data, end='', flush=True)
                output_lines.append(data)
    
    exit_status = stdout.channel.recv_exit_status()
    remaining = stdout.read().decode('utf-8', errors='ignore')
    if remaining:
        print(remaining, end='', flush=True)
    
    return exit_status

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
print(f"[OK] Подключено к {HOST}\n")

# Загрузить и выполнить скрипт анализа
with open('analyze_execution.py', 'r', encoding='utf-8') as f:
    script_content = f.read()

remote_path = f"{PROJECT_PATH}/analyze_execution.py"
sftp = client.open_sftp()
try:
    with sftp.file(remote_path, 'w') as f:
        f.write(script_content)
    sftp.chmod(remote_path, 0o755)
    print(f"[OK] Загружен: analyze_execution.py")
finally:
    sftp.close()

print(f"[INFO] Выполнение analyze_execution.py...")
stdin, stdout, stderr = client.exec_command(f"cd {PROJECT_PATH} && python3 analyze_execution.py", get_pty=True)

import time
output_lines = []
while True:
    if stdout.channel.exit_status_ready():
        break
    if stdout.channel.recv_ready():
        data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
    time.sleep(0.1)

exit_status = stdout.channel.recv_exit_status()
remaining = stdout.read().decode('utf-8', errors='ignore')
if remaining:
    print(remaining, end='', flush=True)

client.close()

