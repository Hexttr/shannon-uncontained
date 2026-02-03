#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для выполнения на сервере: синхронизация файлов и проверка тестов
"""

import os
import sys
import subprocess
import json
import tarfile
import shutil

PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(cmd):
    """Выполнить команду"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def sync_files_from_local():
    """Синхронизировать файлы (будет вызвано через другой механизм)"""
    print("=" * 60)
    print("Синхронизация файлов")
    print("=" * 60)
    
    # Проверить наличие архива
    archive_path = f"{PROJECT_PATH}.sync.tar.gz"
    if os.path.exists(archive_path):
        print(f"[INFO] Найден архив: {archive_path}")
        
        # Распаковать
        exit_code, output, error = execute_command(
            f"cd {PROJECT_PATH} && tar -xzf {archive_path} --exclude='node_modules' --exclude='.git' --exclude='shannon-results' 2>&1"
        )
        
        if exit_code == 0:
            print("[OK] Архив распакован")
            # Удалить архив
            os.remove(archive_path)
        else:
            print(f"[ERROR] Ошибка распаковки: {error}")
    else:
        print("[INFO] Архив не найден, пропуск синхронизации")

def check_test_issue():
    """Проверить почему тесты завершаются мгновенно"""
    print("\n" + "=" * 60)
    print("Проверка проблемы с тестами")
    print("=" * 60)
    
    # Проверить логи веб-интерфейса
    print("\n[INFO] Проверка логов веб-интерфейса...")
    log_path = f"{PROJECT_PATH}/web-interface.log"
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("[LOG] Последние 30 строк:")
            for line in lines[-30:]:
                print(line.rstrip())
    else:
        print("[WARN] Лог файл не найден")
    
    # Найти последний workspace
    results_dir = f"{PROJECT_PATH}/shannon-results/repos"
    if os.path.exists(results_dir):
        workspaces = [d for d in os.listdir(results_dir) if os.path.isdir(os.path.join(results_dir, d))]
        if workspaces:
            latest = sorted(workspaces, key=lambda x: os.path.getmtime(os.path.join(results_dir, x)), reverse=True)[0]
            latest_path = os.path.join(results_dir, latest)
            print(f"\n[INFO] Последний workspace: {latest}")
            
            # Проверить world-model.json
            world_model_path = os.path.join(latest_path, 'world-model.json')
            if os.path.exists(world_model_path):
                try:
                    with open(world_model_path, 'r') as f:
                        data = json.load(f)
                    events = len(data.get('evidence_graph', {}).get('events', []))
                    claims = len(data.get('ledger', {}).get('claims', []))
                    entities = len(data.get('target_model', {}).get('entities', []))
                    print(f"[INFO] World Model статистика:")
                    print(f"  Events: {events}")
                    print(f"  Claims: {claims}")
                    print(f"  Entities: {entities}")
                except Exception as e:
                    print(f"[ERROR] Ошибка чтения world-model: {e}")
            
            # Проверить execution-log.json
            exec_log_path = os.path.join(latest_path, 'execution-log.json')
            if os.path.exists(exec_log_path):
                try:
                    with open(exec_log_path, 'r') as f:
                        log_data = json.load(f)
                    print(f"\n[INFO] Execution log найден")
                    if isinstance(log_data, list) and log_data:
                        print(f"  Записей: {len(log_data)}")
                        print(f"  Последняя запись: {json.dumps(log_data[-1], indent=2)[:200]}")
                except Exception as e:
                    print(f"[ERROR] Ошибка чтения execution-log: {e}")
    
    # Попробовать запустить тест для диагностики
    print("\n[INFO] Попытка запуска теста для диагностики...")
    exit_code, output, error = execute_command(
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && timeout 15 node shannon.mjs generate https://test.example.com --no-ai 2>&1 | head -100"
    )
    
    print("\n[INFO] Вывод команды:")
    print(output)
    if error:
        print("\n[ERROR]:")
        print(error[:1000])

def check_web_interface():
    """Проверить веб-интерфейс"""
    print("\n" + "=" * 60)
    print("Проверка веб-интерфейса")
    print("=" * 60)
    
    # Проверить процесс
    exit_code, output, error = execute_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    if output.strip():
        print("[OK] Веб-интерфейс запущен")
        print(output)
    else:
        print("[WARN] Веб-интерфейс не запущен")
    
    # Проверить порт
    exit_code, output, error = execute_command("ss -tlnp | grep ':3000' || netstat -tlnp | grep ':3000'")
    if output.strip():
        print("[OK] Порт 3000 слушается")
    else:
        print("[WARN] Порт 3000 не слушается")

def main():
    print("=" * 60)
    print("Синхронизация и проверка на сервере")
    print("=" * 60)
    
    # Синхронизация (если архив есть)
    sync_files_from_local()
    
    # Проверка проблемы с тестами
    check_test_issue()
    
    # Проверка веб-интерфейса
    check_web_interface()
    
    print("\n" + "=" * 60)
    print("[OK] Проверка завершена")
    print("=" * 60)

if __name__ == "__main__":
    main()

