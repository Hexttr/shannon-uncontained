#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для загрузки всех файлов из репозитория Steake/shannon-uncontained
Использует GitHub API для получения структуры и raw файлов
"""

import os
import json
import requests
import time
import sys
from pathlib import Path
from urllib.parse import quote

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

REPO_OWNER = "Steake"
REPO_NAME = "shannon-uncontained"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"

def get_file_tree():
    """Получение дерева файлов из репозитория"""
    url = f"{BASE_URL}/git/trees/main?recursive=1"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[ERROR] Ошибка получения дерева файлов: {response.status_code}")
        return None
    
    data = response.json()
    return data.get('tree', [])

def download_file(file_path, output_dir="."):
    """Загрузка файла из репозитория"""
    # Пропускаем файлы с проблемными путями для Windows
    if file_path.endswith('.'):
        # Заменяем trailing dot на underscore
        file_path = file_path[:-1] + '_'
    
    url = f"{RAW_BASE_URL}/{file_path}"
    local_path = Path(output_dir) / file_path
    
    # Создаем директории если нужно
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Для бинарных файлов используем режим 'wb'
            if file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg')):
                local_path.write_bytes(response.content)
            else:
                # Для текстовых файлов пытаемся сохранить как текст
                try:
                    content = response.text
                    local_path.write_text(content, encoding='utf-8')
                except:
                    local_path.write_bytes(response.content)
            
            return True
        else:
            print(f"  [WARN] Не удалось загрузить {file_path}: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] Ошибка загрузки {file_path}: {e}")
        return False

def main():
    """Основная функция"""
    print("=" * 60)
    print("Загрузка репозитория Shannon-Uncontained")
    print("=" * 60)
    
    # Получаем список файлов
    print("\n[INFO] Получение списка файлов...")
    tree = get_file_tree()
    if not tree:
        print("[ERROR] Не удалось получить список файлов")
        return
    
    # Фильтруем только файлы (не директории)
    files = [item['path'] for item in tree if item['type'] == 'blob']
    print(f"[OK] Найдено {len(files)} файлов")
    
    # Загружаем файлы
    print("\n[INFO] Загрузка файлов...")
    downloaded = 0
    failed = 0
    
    for i, file_path in enumerate(files, 1):
        status = f"[{i}/{len(files)}] {file_path[:60]}... "
        print(status, end="", flush=True)
        
        if download_file(file_path):
            print("[OK]")
            downloaded += 1
        else:
            print("[FAIL]")
            failed += 1
        
        # Небольшая задержка чтобы не превысить rate limit
        if i % 10 == 0:
            time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"[OK] Загружено: {downloaded}")
    print(f"[FAIL] Ошибок: {failed}")
    print("=" * 60)
    
    # Исправляем проблемные файлы
    print("\n[INFO] Исправление проблемных путей...")
    fix_problematic_paths()

def fix_problematic_paths():
    """Исправление файлов с проблемными путями для Windows"""
    problematic_files = [
        "src/local-source-generator/crawlers/active-crawl.",
        "src/local-source-generator/crawlers/js-analysis.",
    ]
    
    for file_path in problematic_files:
        old_path = Path(file_path)
        new_path = Path(file_path[:-1] + "_")
        
        if old_path.exists():
            # Переименовываем
            old_path.rename(new_path)
            print(f"  [OK] Переименован: {file_path} -> {new_path}")
        elif new_path.exists():
            # Файл уже был переименован при загрузке
            print(f"  [OK] Уже исправлен: {new_path}")

if __name__ == "__main__":
    main()

