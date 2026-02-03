#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблем и запуск теста
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
TARGET = "https://tcell.tj"

def execute_command(client, command):
    """Выполнить команду"""
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def main():
    print("=" * 60)
    print("Исправление и запуск теста")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # 1. Проверка и запуск Ollama
        print("[INFO] Проверка Ollama...")
        exit_status, output, error = execute_command(client, "curl -s http://localhost:11434/api/tags")
        if exit_status != 0:
            print("[INFO] Запуск Ollama...")
            execute_command(client, "pkill ollama || true")
            time.sleep(2)
            execute_command(client, "nohup ollama serve > /tmp/ollama.log 2>&1 &")
            time.sleep(5)
            print("[OK] Ollama запущен")
        else:
            print("[OK] Ollama работает")
        
        # 2. Проверка прав на shannon.mjs
        print("\n[INFO] Проверка прав на shannon.mjs...")
        exit_status, output, error = execute_command(
            client,
            f"ls -la {PROJECT_PATH}/shannon.mjs"
        )
        print(output)
        
        # Установка прав на выполнение
        execute_command(client, f"chmod +x {PROJECT_PATH}/shannon.mjs")
        print("[OK] Права установлены")
        
        # 3. Проверка что файл существует и исполняемый
        exit_status, output, error = execute_command(
            client,
            f"test -x {PROJECT_PATH}/shannon.mjs && echo 'executable' || echo 'not executable'"
        )
        print(f"  Статус: {output.strip()}")
        
        # 4. Запуск через node напрямую
        print("\n" + "=" * 60)
        print("Запуск тестового прогона")
        print("=" * 60)
        print(f"Цель: {TARGET}\n")
        
        # Используем node напрямую вместо ./shannon.mjs
        command = f"""cd {PROJECT_PATH} && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs generate {TARGET} 2>&1"""
        
        print(f"[INFO] Выполнение команды...")
        print(f"Команда: {command[:100]}...\n")
        
        # Запуск в фоне и мониторинг
        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        
        # Читаем вывод в реальном времени
        print("Вывод выполнения:\n")
        print("-" * 60)
        
        output_lines = []
        error_lines = []
        
        # Читаем вывод построчно
        while True:
            if stdout.channel.exit_status_ready():
                break
            
            if stdout.channel.recv_ready():
                data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
                if data:
                    print(data, end='', flush=True)
                    output_lines.append(data)
            
            if stderr.channel.recv_stderr_ready():
                data = stderr.channel.recv_stderr(1024).decode('utf-8', errors='ignore')
                if data:
                    print(data, end='', flush=True, file=sys.stderr)
                    error_lines.append(data)
            
            time.sleep(0.1)
        
        exit_status = stdout.channel.recv_exit_status()
        remaining_output = stdout.read().decode('utf-8', errors='ignore')
        remaining_error = stderr.read().decode('utf-8', errors='ignore')
        
        if remaining_output:
            print(remaining_output, end='', flush=True)
            output_lines.append(remaining_output)
        if remaining_error:
            print(remaining_error, end='', flush=True, file=sys.stderr)
            error_lines.append(remaining_error)
        
        print("\n" + "-" * 60)
        print(f"\n[INFO] Код выхода: {exit_status}")
        
        # Проверка результатов
        print("\n" + "=" * 60)
        print("Проверка результатов")
        print("=" * 60)
        
        domain = TARGET.replace('https://', '').replace('http://', '').split('/')[0]
        workspace_path = f"{PROJECT_PATH}/shannon-results/repos/{domain}"
        
        exit_status_check, output_check, error_check = execute_command(
            client,
            f"test -d {workspace_path} && echo 'exists' || echo 'not exists'"
        )
        
        if output_check.strip() == 'exists':
            print(f"[OK] Workspace создан: {workspace_path}")
            
            # Список файлов
            exit_status_files, output_files, error_files = execute_command(
                client,
                f"find {workspace_path} -type f | head -20"
            )
            if output_files.strip():
                files = [f for f in output_files.strip().split('\n') if f]
                print(f"\n[INFO] Создано файлов: {len(files)}")
                for f in files[:10]:
                    print(f"  - {f}")
            
            # Размер workspace
            exit_status_size, output_size, error_size = execute_command(
                client,
                f"du -sh {workspace_path} 2>/dev/null | awk '{{print $1}}'"
            )
            if output_size.strip():
                print(f"\n[INFO] Размер workspace: {output_size.strip()}")
        else:
            print(f"[WARN] Workspace не найден: {workspace_path}")
            if error_lines:
                print("\n[ERROR] Ошибки выполнения:")
                print(''.join(error_lines[-500:]))
        
        print("\n" + "=" * 60)
        if exit_status == 0:
            print("[OK] Тестовый прогон завершен успешно")
        else:
            print(f"[WARN] Тестовый прогон завершен с кодом {exit_status}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

