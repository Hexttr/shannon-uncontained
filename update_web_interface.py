#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обновить веб-интерфейс с потоковым выводом"""

import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def upload_file(client, local_path, remote_path):
    sftp = client.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"[ERROR] {e}")
        return False
    finally:
        sftp.close()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
print(f"[OK] Подключено к {HOST}\n")

# Загрузить обновленный веб-интерфейс
print("[INFO] Загрузка web-interface.cjs...")
if upload_file(client, 'web-interface.cjs', f'{PROJECT_PATH}/web-interface.cjs'):
    print("[OK] Файл загружен")

# Перезапустить
print("[INFO] Перезапуск веб-интерфейса...")
execute_command(client, "pkill -9 -f 'web-interface.cjs' || true")
time.sleep(1)

exit_status, output, error = execute_command(
    client,
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 & echo $!"
)

if exit_status == 0:
    print(f"[OK] Веб-интерфейс обновлен и перезапущен")
    print(f"[INFO] Теперь CLI вывод отображается в реальном времени!")
    print(f"[INFO] Доступ: http://{HOST}:3000")

client.close()

