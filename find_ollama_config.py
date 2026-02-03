#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск конфигурации Ollama в проекте на сервере
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

def find_ollama_config(ssh):
    """Поиск конфигурации Ollama"""
    commands = [
        ("Поиск упоминаний Ollama в .env файлах", "find shannon-uncontained -name '.env*' -exec grep -l 'ollama\|OLLAMA' {} \\; 2>/dev/null"),
        ("Содержимое .env файлов", "cat shannon-uncontained/.env 2>/dev/null || echo 'Нет .env'"),
        ("Поиск Ollama в JS файлах", "grep -r 'ollama\|OLLAMA' shannon-uncontained/src --include='*.js' --include='*.mjs' 2>/dev/null | head -20"),
        ("Поиск в конфигурационных файлах", "grep -r 'ollama\|OLLAMA' shannon-uncontained --include='*.json' --include='*.yaml' --include='*.yml' 2>/dev/null | head -20"),
        ("LLM клиент файлы", "find shannon-uncontained/src -name '*llm*' -o -name '*ai*' 2>/dev/null"),
    ]
    
    for description, command in commands:
        print(f"\n--- {description} ---")
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode('utf-8', errors='ignore')
        error = stderr.read().decode('utf-8', errors='ignore')
        if output:
            print(output)
        if error and "Permission denied" not in error and "No such file" not in error:
            print(f"Ошибка: {error}")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    try:
        find_ollama_config(ssh)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

