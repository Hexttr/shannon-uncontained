#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск веб-интерфейса на сервере
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

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def main():
    print("=" * 60)
    print("Запуск веб-интерфейса Shannon-Uncontained")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Проверить существует ли файл
        exit_status, output, error = execute_command(
            client,
            f"test -f {PROJECT_PATH}/web-interface.js && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() != 'exists':
            print("[INFO] Создание веб-интерфейса...")
            # Запустить создание интерфейса
            import subprocess
            result = subprocess.run(['python', 'create_web_interface.py'], capture_output=True, text=True)
            if result.returncode != 0:
                print("[WARN] Ошибка создания интерфейса, создаю упрощенную версию...")
                # Создать упрощенную версию напрямую
                pass
        
        # Остановить старый процесс если запущен
        print("[INFO] Остановка старого процесса...")
        execute_command(client, f"pkill -f 'web-interface.js' || true")
        
        # Запустить веб-интерфейс
        print("[INFO] Запуск веб-интерфейса...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.js > web-interface.log 2>&1 &"
        )
        
        if exit_status == 0:
            print("\n[OK] Веб-интерфейс запущен!")
            print("\n[INFO] Доступ:")
            print(f"  http://{HOST}:3000")
            print("\n[INFO] Логи:")
            print(f"  tail -f {PROJECT_PATH}/web-interface.log")
            print("\n[INFO] Остановка:")
            print(f"  pkill -f 'web-interface.js'")
        else:
            print(f"[WARN] Ошибка запуска: {error[:200]}")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

