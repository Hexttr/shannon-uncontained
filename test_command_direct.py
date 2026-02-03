#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест команды напрямую"""

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

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

target = "https://tcell.tj"
command = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs generate {target} --no-ai 2>&1"

print("Команда:")
print(command)
print("\n" + "="*60)
print("Выполнение (первые 20 строк, 10 секунд):")
print("="*60 + "\n")

stdin, stdout, stderr = client.exec_command(command, get_pty=True)

start = time.time()
output_lines = []

while True:
    if stdout.channel.exit_status_ready():
        break
    if stdout.channel.recv_ready():
        data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
            if len(output_lines) > 20:
                break
    if time.time() - start > 10:
        print("\n[Timeout after 10 seconds]")
        break
    time.sleep(0.1)

exit_status = stdout.channel.recv_exit_status()
remaining = stdout.read().decode('utf-8', errors='ignore')
if remaining:
    print(remaining[:500], end='', flush=True)

print(f"\n\n[INFO] Exit code: {exit_status}")
print(f"[INFO] Output lines: {len(output_lines)}")
print(f"[INFO] Time: {time.time() - start:.2f} seconds")

client.close()

