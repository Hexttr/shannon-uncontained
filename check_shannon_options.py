#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка опций команды shannon.mjs
"""
import paramiko
import sys
import os

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def connect_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    return ssh

def execute_command(ssh, command, timeout=300):
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("CHECKING SHANNON.MJS OPTIONS")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Проверяем help
    print("\n1. HELP OUTPUT:")
    print("-" * 80)
    cmd = f"cd {PROJECT_PATH} && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin && export GOPATH=$HOME/go && ./shannon.mjs --help"
    success, output, error = execute_command(ssh, cmd)
    print(output)
    if error:
        print("ERROR:", error)
    
    # Проверяем команду generate
    print("\n2. GENERATE COMMAND HELP:")
    print("-" * 80)
    cmd = f"cd {PROJECT_PATH} && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin && export GOPATH=$HOME/go && ./shannon.mjs generate --help"
    success, output, error = execute_command(ssh, cmd)
    print(output)
    if error:
        print("ERROR:", error)
    
    ssh.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

