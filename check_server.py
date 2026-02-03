#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка состояния сервера"""

import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
    print("[OK] Подключено к серверу\n")
    
    commands = [
        ("Проверка директории", "ls -la /root/ | grep shannon"),
        ("Содержимое /root", "ls -la /root/"),
        ("Node.js версия", "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node --version"),
        ("npm версия", "export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && npm --version"),
    ]
    
    for desc, cmd in commands:
        print(f"[INFO] {desc}...")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        if output.strip():
            print(f"  {output.strip()}")
        if error.strip() and exit_status != 0:
            print(f"  [WARN] {error.strip()}")
        print()
        
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    client.close()

