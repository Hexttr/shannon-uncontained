#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка результатов тестового прогона
"""

import paramiko
import sys
import io
import json

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

def main():
    print("=" * 60)
    print("Проверка результатов тестового прогона")
    print("=" * 60)
    print(f"Цель: {TARGET}\n")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        domain = TARGET.replace('https://', '').replace('http://', '').split('/')[0]
        workspace_path = f"{PROJECT_PATH}/shannon-results/repos/{domain}"
        
        # Проверка workspace
        print(f"[INFO] Workspace: {workspace_path}\n")
        
        # Список всех файлов
        exit_status, output, error = execute_command(
            client,
            f"find {workspace_path} -type f 2>/dev/null | sort"
        )
        if exit_status == 0 and output.strip():
            files = [f for f in output.strip().split('\n') if f]
            print(f"[OK] Найдено файлов: {len(files)}\n")
            print("Структура файлов:")
            for f in files:
                # Получить размер
                exit_status_size, output_size, error_size = execute_command(
                    client,
                    f"ls -lh '{f}' 2>/dev/null | awk '{{print $5}}'"
                )
                size = output_size.strip() or "?"
                print(f"  [{size:>8}] {f}")
        
        # Проверка world-model
        print("\n" + "=" * 60)
        print("Проверка World Model")
        print("=" * 60)
        
        world_model_path = f"{workspace_path}/world-model.json"
        exit_status, output, error = execute_command(
            client,
            f"test -f {world_model_path} && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() == 'exists':
            print("[OK] World model найден")
            
            # Размер
            exit_status, output, error = execute_command(
                client,
                f"ls -lh {world_model_path} | awk '{{print $5}}'"
            )
            print(f"  Размер: {output.strip()}")
            
            # Попытка прочитать и показать структуру
            exit_status, output, error = execute_command(
                client,
                f"head -50 {world_model_path}"
            )
            if output.strip():
                print("\n  Первые строки:")
                print(output[:500])
        else:
            print("[WARN] World model не найден")
        
        # Проверка evidence
        print("\n" + "=" * 60)
        print("Проверка Evidence Graph")
        print("=" * 60)
        
        evidence_path = f"{workspace_path}/evidence"
        exit_status, output, error = execute_command(
            client,
            f"test -d {evidence_path} && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() == 'exists':
            print("[OK] Evidence директория найдена")
            
            # Количество файлов
            exit_status, output, error = execute_command(
                client,
                f"find {evidence_path} -type f | wc -l"
            )
            count = output.strip()
            print(f"  Файлов: {count}")
            
            # Список файлов
            exit_status, output, error = execute_command(
                client,
                f"find {evidence_path} -type f | head -10"
            )
            if output.strip():
                print("\n  Файлы:")
                for f in output.strip().split('\n'):
                    if f:
                        print(f"    - {f}")
        else:
            print("[WARN] Evidence директория не найдена")
        
        # Проверка логов
        print("\n" + "=" * 60)
        print("Проверка логов")
        print("=" * 60)
        
        log_path = f"{workspace_path}/execution-log.json"
        exit_status, output, error = execute_command(
            client,
            f"test -f {log_path} && echo 'exists' || echo 'not exists'"
        )
        
        if output.strip() == 'exists':
            print("[OK] Execution log найден")
            
            # Попытка прочитать лог
            exit_status, output, error = execute_command(
                client,
                f"cat {log_path} | head -100"
            )
            if output.strip():
                try:
                    log_data = json.loads(output)
                    print(f"  Статус: {log_data.get('status', 'unknown')}")
                    print(f"  Агентов выполнено: {len(log_data.get('agents', []))}")
                except:
                    print("  (не удалось распарсить JSON)")
        else:
            print("[WARN] Execution log не найден")
        
        # Общая статистика
        print("\n" + "=" * 60)
        print("Общая статистика")
        print("=" * 60)
        
        exit_status, output, error = execute_command(
            client,
            f"du -sh {workspace_path} 2>/dev/null | awk '{{print $1}}'"
        )
        if output.strip():
            print(f"Размер workspace: {output.strip()}")
        
        exit_status, output, error = execute_command(
            client,
            f"find {workspace_path} -type f | wc -l"
        )
        if output.strip():
            print(f"Всего файлов: {output.strip()}")
        
        print("\n" + "=" * 60)
        print("Проверка завершена")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

