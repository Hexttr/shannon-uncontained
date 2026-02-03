#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для выполнения на сервере: проверка почему тесты завершаются мгновенно
"""

import os
import sys
import subprocess
import json

PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(cmd, timeout=60):
    """Выполнить команду"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def main():
    print("=" * 60)
    print("Проверка проблемы с тестами")
    print("=" * 60)
    
    # Проверить последний workspace
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
                    print(f"\n[INFO] World Model статистика:")
                    print(f"  Events: {events}")
                    print(f"  Claims: {claims}")
                    print(f"  Entities: {entities}")
                    
                    if events == 0 and claims == 0:
                        print("\n[WARN] World Model пустой - тест не выполнил работу!")
                except Exception as e:
                    print(f"[ERROR] Ошибка чтения world-model: {e}")
    
    # Запустить тест с подробным выводом
    print("\n[INFO] Запуск теста для диагностики (с подробным выводом)...")
    exit_code, output, error = execute_command(
        f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node shannon.mjs generate https://test.example.com --no-ai -v 2>&1",
        timeout=120
    )
    
    print("\n[INFO] Полный вывод команды:")
    print(output)
    if error:
        print("\n[ERROR]:")
        print(error)
    
    print(f"\n[INFO] Код выхода: {exit_code}")
    
    # Проверить что создалось после теста
    print("\n[INFO] Проверка созданных файлов...")
    exit_code, output, error = execute_command(
        f"find {PROJECT_PATH}/shannon-results/repos/test.example.com -type f 2>/dev/null | head -20"
    )
    if output.strip():
        print("Созданные файлы:")
        print(output)
    else:
        print("Файлы не найдены")

if __name__ == "__main__":
    main()

