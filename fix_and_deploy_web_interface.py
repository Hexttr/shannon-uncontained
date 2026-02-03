#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление и развертывание веб-интерфейса
"""

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
    """Загрузить файл на сервер"""
    sftp = client.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("=" * 60)
    print("Исправление и развертывание веб-интерфейса")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Остановить все процессы
        print("[INFO] Остановка процессов...")
        execute_command(client, "pkill -9 -f 'web-interface' || fuser -k 3000/tcp 2>/dev/null || true")
        time.sleep(1)
        
        # Загрузить исправленный файл как .cjs
        print("[INFO] Загрузка web-interface.cjs...")
        if upload_file(client, 'web-interface.cjs', f'{PROJECT_PATH}/web-interface.cjs'):
            print("[OK] Файл загружен")
        else:
            print("[ERROR] Не удалось загрузить файл")
            return
        
        # Установить права
        execute_command(client, f"chmod +x {PROJECT_PATH}/web-interface.cjs")
        
        # Проверить синтаксис
        print("[INFO] Проверка синтаксиса...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -c web-interface.cjs 2>&1"
        )
        
        if exit_status == 0:
            print("[OK] Синтаксис корректен")
        else:
            print(f"[ERROR] Ошибка синтаксиса:")
            print(error)
            return
        
        # Запустить веб-интерфейс
        print("[INFO] Запуск веб-интерфейса...")
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 & echo $!"
        )
        
        if exit_status == 0:
            pid = output.strip()
            print(f"[OK] Процесс запущен (PID: {pid})")
            
            time.sleep(2)
            
            # Проверить процесс
            exit_status, output, error = execute_command(
                client,
                f"ps -p {pid} 2>/dev/null || ps aux | grep 'web-interface.cjs' | grep -v grep"
            )
            print(f"\n[INFO] Процесс:")
            print(output if output.strip() else "Не найден")
            
            # Проверить логи
            exit_status, output, error = execute_command(
                client,
                f"tail -30 {PROJECT_PATH}/web-interface.log 2>&1"
            )
            print(f"\n[INFO] Логи:")
            print(output)
            
            # Проверить порт
            exit_status, output, error = execute_command(
                client,
                "netstat -tlnp | grep ':3000' || ss -tlnp | grep ':3000'"
            )
            print(f"\n[INFO] Порт:")
            if output.strip():
                print(output)
                print("\n" + "=" * 60)
                print("[OK] Веб-интерфейс запущен!")
                print(f"Доступ: http://{HOST}:3000")
                print("=" * 60)
            else:
                print("Не слушается")
                print("\n[ERROR] Веб-интерфейс не запустился")
        else:
            print(f"[ERROR] Ошибка запуска")
            print(f"Output: {output}")
            print(f"Error: {error}")
            
            # Показать логи
            exit_status, output, error = execute_command(
                client,
                f"cat {PROJECT_PATH}/web-interface.log 2>&1 || echo 'Лог не найден'"
            )
            print("\n[LOG]:")
            print(output)
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

