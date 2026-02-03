#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка структуры функции query
"""
import paramiko
import sys

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def check_structure(ssh):
    """Проверка структуры функции query"""
    commands = [
        ("Поиск функции query", "grep -n 'function.*query' shannon-uncontained/src/ai/llm-client.js | head -5"),
        ("Строки вокруг query", "grep -A 10 -B 5 'export.*query' shannon-uncontained/src/ai/llm-client.js | head -20"),
        ("Создание OpenAI client", "grep -n 'new OpenAI' shannon-uncontained/src/ai/llm-client.js"),
        ("Создание response", "grep -n 'client.chat.completions.create' shannon-uncontained/src/ai/llm-client.js | head -3"),
    ]
    
    for description, command in commands:
        print(f"\n--- {description} ---")
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        
        if output:
            print(output)
        if error and "Permission denied" not in error:
            print(f"Ошибка: {error}")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_structure(ssh)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

