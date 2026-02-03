#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск тестового прогона Shannon на целевом домене
"""

import paramiko
import sys
import io
import time
import select

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"
TARGET = "https://tcell.tj"

def execute_command_streaming(client, command, timeout=3600):
    """Выполнить команду с потоковым выводом"""
    print(f"[INFO] Выполнение: {command}")
    print("=" * 60)
    
    stdin, stdout, stderr = client.exec_command(command)
    
    # Настройка неблокирующего режима
    channel = stdout.channel
    channel.setblocking(0)
    
    output_lines = []
    error_lines = []
    
    start_time = time.time()
    
    while True:
        # Проверка таймаута
        if time.time() - start_time > timeout:
            print(f"\n[WARN] Превышен таймаут ({timeout} секунд)")
            break
        
        # Проверка завершения
        if channel.exit_status_ready():
            break
        
        # Чтение stdout
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8', errors='ignore')
            if data:
                print(data, end='', flush=True)
                output_lines.append(data)
        
        # Чтение stderr
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            if data:
                print(data, end='', flush=True, file=sys.stderr)
                error_lines.append(data)
        
        time.sleep(0.1)
    
    # Получить финальный статус
    exit_status = channel.recv_exit_status()
    
    # Прочитать оставшиеся данные
    while channel.recv_ready():
        data = channel.recv(1024).decode('utf-8', errors='ignore')
        if data:
            print(data, end='', flush=True)
            output_lines.append(data)
    
    return exit_status, ''.join(output_lines), ''.join(error_lines)

def check_results(client, target):
    """Проверка результатов выполнения"""
    print("\n" + "=" * 60)
    print("Проверка результатов")
    print("=" * 60)
    
    # Определить workspace директорию
    domain = target.replace('https://', '').replace('http://', '').split('/')[0]
    workspace_path = f"{PROJECT_PATH}/shannon-results/repos/{domain}"
    
    # Проверка существования workspace
    exit_status, output, error = client.exec_command(
        f"test -d {workspace_path} && echo 'exists' || echo 'not exists'"
    )
    exists = output.read().decode('utf-8').strip() == 'exists'
    
    if exists:
        print(f"[OK] Workspace найден: {workspace_path}")
        
        # Список файлов в workspace
        exit_status, output, error = client.exec_command(
            f"find {workspace_path} -type f | head -20"
        )
        if exit_status == 0:
            files = output.read().decode('utf-8').strip().split('\n')
            print(f"\n[INFO] Найдено файлов: {len([f for f in files if f])}")
            for f in files[:10]:
                if f:
                    print(f"  - {f}")
        
        # Проверка world-model
        exit_status, output, error = client.exec_command(
            f"test -f {workspace_path}/world-model.json && echo 'exists' || echo 'not exists'"
        )
        if output.read().decode('utf-8').strip() == 'exists':
            print("\n[OK] World model создан")
            
            # Размер файла
            exit_status, output, error = client.exec_command(
                f"ls -lh {workspace_path}/world-model.json | awk '{{print $5}}'"
            )
            size = output.read().decode('utf-8').strip()
            print(f"  Размер: {size}")
        
        # Проверка evidence graph
        exit_status, output, error = client.exec_command(
            f"test -d {workspace_path}/evidence && echo 'exists' || echo 'not exists'"
        )
        if output.read().decode('utf-8').strip() == 'exists':
            print("[OK] Evidence graph создан")
            
            # Количество событий
            exit_status, output, error = client.exec_command(
                f"find {workspace_path}/evidence -name '*.jsonl' -exec wc -l {{}} + 2>/dev/null | tail -1 | awk '{{print $1}}'"
            )
            count = output.read().decode('utf-8').strip()
            if count:
                print(f"  Событий: {count}")
        
        # Проверка отчетов
        exit_status, output, error = client.exec_command(
            f"find {workspace_path} -name '*.md' -o -name '*.html' | head -5"
        )
        reports = output.read().decode('utf-8').strip().split('\n')
        if reports and reports[0]:
            print("\n[OK] Отчеты созданы:")
            for r in reports[:5]:
                if r:
                    print(f"  - {r}")
    else:
        print(f"[WARN] Workspace не найден: {workspace_path}")
        print("  Возможно выполнение еще не завершено или произошла ошибка")

def main():
    print("=" * 60)
    print("Тестовый прогон Shannon-Uncontained")
    print("=" * 60)
    print(f"Цель: {TARGET}")
    print(f"Сервер: {HOST}")
    print()
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # Проверка готовности
        print("[INFO] Проверка готовности системы...")
        
        # Проверка Ollama
        exit_status, output, error = client.exec_command("curl -s http://localhost:11434/api/tags")
        if exit_status == 0:
            print("[OK] Ollama работает")
        else:
            print("[WARN] Ollama может быть не запущен")
        
        # Проверка .env
        exit_status, output, error = client.exec_command(
            f"grep -E '^LLM_PROVIDER=' {PROJECT_PATH}/.env"
        )
        if exit_status == 0:
            provider = output.read().decode('utf-8').strip()
            print(f"[OK] Конфигурация: {provider}")
        
        # Запуск теста
        print("\n" + "=" * 60)
        print("Запуск тестового прогона")
        print("=" * 60)
        print(f"Цель: {TARGET}")
        print("Это может занять несколько минут...")
        print()
        
        command = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && ./shannon.mjs generate {TARGET}"
        
        exit_status, output, error = execute_command_streaming(client, command, timeout=1800)  # 30 минут таймаут
        
        print("\n" + "=" * 60)
        print("Завершение выполнения")
        print("=" * 60)
        print(f"Код выхода: {exit_status}")
        
        if exit_status == 0:
            print("[OK] Выполнение завершено успешно")
        else:
            print(f"[WARN] Выполнение завершено с кодом {exit_status}")
            if error:
                print(f"\nОшибки:\n{error[:500]}")
        
        # Проверка результатов
        check_results(client, TARGET)
        
        print("\n" + "=" * 60)
        print("Тестовый прогон завершен")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

