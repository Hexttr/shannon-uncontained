#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Развертывание исправлений и запуск теста
"""

import paramiko
import sys
import io
import time
import tarfile
import os

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"
TARGET = "https://tcell.tj"

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def deploy_fixes(client):
    """Развернуть исправленные файлы"""
    print("\n[INFO] Развертывание исправлений...")
    
    # Создать архив только с исправленными файлами
    files_to_deploy = ['local-source-generator.mjs', 'shannon.mjs']
    
    archive_name = "fixes.tar.gz"
    with tarfile.open(archive_name, "w:gz") as tar:
        for file in files_to_deploy:
            if os.path.exists(file):
                tar.add(file)
                print(f"  [OK] Добавлен: {file}")
    
    # Загрузить на сервер
    sftp = client.open_sftp()
    try:
        sftp.put(archive_name, f"{PROJECT_PATH}.fixes.tar.gz")
        print("[OK] Архив загружен")
    finally:
        sftp.close()
    
    # Распаковать на сервере
    commands = [
        f"cd {PROJECT_PATH} && tar -xzf {PROJECT_PATH}.fixes.tar.gz",
        f"rm -f {PROJECT_PATH}.fixes.tar.gz",
    ]
    
    for cmd in commands:
        exit_status, output, error = execute_command(client, cmd)
        if exit_status == 0:
            print(f"  [OK] {cmd[:60]}...")
        else:
            print(f"  [WARN] {cmd[:60]}... - {error[:100]}")
    
    # Удалить локальный архив
    if os.path.exists(archive_name):
        os.remove(archive_name)

def run_test(client):
    """Запустить тест"""
    print("\n" + "=" * 60)
    print("Запуск тестового прогона")
    print("=" * 60)
    print(f"Цель: {TARGET}\n")
    
    command = f"""cd {PROJECT_PATH} && export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && node shannon.mjs generate {TARGET} 2>&1"""
    
    print("[INFO] Выполнение команды...\n")
    print("-" * 60)
    
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    
    output_lines = []
    error_lines = []
    
    # Читаем вывод в реальном времени
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
    return exit_status, ''.join(output_lines), ''.join(error_lines)

def check_results(client):
    """Проверить результаты"""
    print("\n" + "=" * 60)
    print("Проверка результатов")
    print("=" * 60)
    
    domain = TARGET.replace('https://', '').replace('http://', '').split('/')[0]
    workspace_path = f"{PROJECT_PATH}/shannon-results/repos/{domain}"
    
    # Проверка workspace
    exit_status, output, error = execute_command(
        client,
        f"test -d {workspace_path} && echo 'exists' || echo 'not exists'"
    )
    
    if output.strip() == 'exists':
        print(f"[OK] Workspace создан: {workspace_path}")
        
        # Размер
        exit_status, output, error = execute_command(
            client,
            f"du -sh {workspace_path} 2>/dev/null | awk '{{print $1}}'"
        )
        if output.strip():
            print(f"  Размер: {output.strip()}")
        
        # Количество файлов
        exit_status, output, error = execute_command(
            client,
            f"find {workspace_path} -type f | wc -l"
        )
        if output.strip():
            print(f"  Файлов: {output.strip()}")
        
        # Список файлов
        exit_status, output, error = execute_command(
            client,
            f"find {workspace_path} -type f | head -20"
        )
        if output.strip():
            files = [f for f in output.strip().split('\n') if f]
            print(f"\n  Созданные файлы ({len(files)}):")
            for f in files[:15]:
                print(f"    - {f}")
            if len(files) > 15:
                print(f"    ... и еще {len(files) - 15} файлов")
        
        # Проверка world-model
        exit_status, output, error = execute_command(
            client,
            f"test -f {workspace_path}/world-model.json && echo 'exists' || echo 'not exists'"
        )
        if output.strip() == 'exists':
            print("\n[OK] World model создан")
            
            # Размер
            exit_status, output, error = execute_command(
                client,
                f"ls -lh {workspace_path}/world-model.json | awk '{{print $5}}'"
            )
            if output.strip():
                print(f"  Размер: {output.strip()}")
        else:
            print("\n[WARN] World model не найден")
        
        # Проверка evidence
        exit_status, output, error = execute_command(
            client,
            f"test -d {workspace_path}/evidence && echo 'exists' || echo 'not exists'"
        )
        if output.strip() == 'exists':
            print("[OK] Evidence директория создана")
            
            # Количество событий
            exit_status, output, error = execute_command(
                client,
                f"find {workspace_path}/evidence -name '*.jsonl' -exec wc -l {{}} + 2>/dev/null | tail -1 | awk '{{print $1}}'"
            )
            if output.strip():
                print(f"  Событий: {output.strip()}")
    else:
        print(f"[WARN] Workspace не найден: {workspace_path}")

def main():
    print("=" * 60)
    print("Развертывание исправлений и запуск теста")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Развернуть исправления
        deploy_fixes(client)
        
        # Запустить тест
        exit_status, output, error = run_test(client)
        
        print(f"\n[INFO] Код выхода: {exit_status}")
        
        # Проверить результаты
        check_results(client)
        
        print("\n" + "=" * 60)
        if exit_status == 0:
            print("[OK] Тестовый прогон завершен успешно!")
        else:
            print(f"[WARN] Тестовый прогон завершен с кодом {exit_status}")
            if error:
                print(f"\nОшибки:\n{error[-500:]}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

