#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание LLM клиента с сервера для анализа
"""
import paramiko
import os
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

def download_file(ssh, remote_path, local_path):
    """Скачивание файла с сервера"""
    try:
        sftp = ssh.open_sftp()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        sftp.get(remote_path, local_path)
        sftp.close()
        print(f"[OK] Скачан: {remote_path} -> {local_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка при скачивании {remote_path}: {e}")
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    files_to_download = [
        ("shannon-uncontained/src/ai/llm-client.js", "src/ai/llm-client.js"),
        ("shannon-uncontained/.env", "server_config/.env.example"),
        ("shannon-uncontained/.env.example", "server_config/.env.example.original"),
    ]
    
    try:
        for remote, local in files_to_download:
            download_file(ssh, remote, local)
    finally:
        ssh.close()
        print("\n[OK] Скачивание завершено")

if __name__ == "__main__":
    main()

