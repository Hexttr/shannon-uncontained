#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Быстрое обновление веб-интерфейса без зависаний"""

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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

print("[INFO] Загрузка web-interface.cjs...")

# Загрузить файл
sftp = client.open_sftp()
with open('web-interface.cjs', 'r', encoding='utf-8') as f:
    content = f.read()

with sftp.file(f'{PROJECT_PATH}/web-interface.cjs', 'w') as f:
    f.write(content)

sftp.chmod(f'{PROJECT_PATH}/web-interface.cjs', 0o755)
sftp.close()
print("[OK] Файл загружен")

# Остановить старый процесс (не ждем ответа)
print("[INFO] Остановка старого процесса...")
stdin, stdout, stderr = client.exec_command("pkill -9 -f 'web-interface.cjs' || true", timeout=5)
stdout.channel.close()

# Запустить новый процесс в фоне (не ждем ответа)
print("[INFO] Запуск нового процесса...")
cmd = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 &"
stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
stdout.channel.close()

client.close()
print("[OK] Веб-интерфейс обновлен!")
print(f"[INFO] Доступ: http://{HOST}:3000")

