#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка полноты загрузки репозитория и сравнение с оригиналом
"""

import requests
import json
import os
from pathlib import Path

REPO_OWNER = "Steake"
REPO_NAME = "shannon-uncontained"

def get_github_files():
    """Получить список всех файлов из GitHub"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[ERROR] Не удалось получить список файлов: {response.status_code}")
        return []
    
    data = response.json()
    files = [item['path'] for item in data.get('tree', []) if item['type'] == 'blob']
    return files

def check_local_files():
    """Проверить какие файлы есть локально"""
    local_files = []
    for root, dirs, files in os.walk('.'):
        # Пропускаем служебные директории
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.pytest_cache', 'temp_repo']]
        
        for file in files:
            if file.startswith('.'):
                continue
            file_path = os.path.join(root, file)
            # Относительный путь от корня
            rel_path = os.path.relpath(file_path, '.')
            local_files.append(rel_path.replace('\\', '/'))
    
    return local_files

def main():
    print("=" * 60)
    print("Проверка полноты репозитория")
    print("=" * 60)
    
    print("\n[INFO] Получение списка файлов из GitHub...")
    github_files = get_github_files()
    print(f"[OK] Найдено файлов в GitHub: {len(github_files)}")
    
    print("\n[INFO] Проверка локальных файлов...")
    local_files = check_local_files()
    print(f"[OK] Найдено файлов локально: {len(local_files)}")
    
    # Найти отсутствующие файлы
    github_set = set(github_files)
    local_set = set(local_files)
    
    missing = github_set - local_set
    extra = local_set - github_set
    
    print("\n" + "=" * 60)
    print("Результаты сравнения")
    print("=" * 60)
    
    if missing:
        print(f"\n[WARN] Отсутствующих файлов: {len(missing)}")
        print("Первые 20 отсутствующих файлов:")
        for f in sorted(missing)[:20]:
            print(f"  - {f}")
        if len(missing) > 20:
            print(f"  ... и еще {len(missing) - 20} файлов")
    else:
        print("\n[OK] Все файлы из GitHub присутствуют локально")
    
    if extra:
        print(f"\n[INFO] Дополнительных файлов (не из GitHub): {len(extra)}")
        print("Первые 10 дополнительных файлов:")
        for f in sorted(extra)[:10]:
            print(f"  - {f}")
    
    # Проверить конкретно adaptation директорию
    print("\n" + "=" * 60)
    print("Проверка директории adaptation")
    print("=" * 60)
    
    adaptation_github = [f for f in github_files if 'adaptation' in f]
    adaptation_local = [f for f in local_files if 'adaptation' in f]
    
    print(f"\nФайлов в adaptation (GitHub): {len(adaptation_github)}")
    for f in adaptation_github:
        print(f"  - {f}")
    
    print(f"\nФайлов в adaptation (локально): {len(adaptation_local)}")
    for f in adaptation_local:
        print(f"  - {f}")
    
    if adaptation_github and not adaptation_local:
        print("\n[WARN] Директория adaptation отсутствует локально!")
    elif adaptation_local and not adaptation_github:
        print("\n[WARN] Директория adaptation есть локально, но отсутствует в GitHub (возможно я создал?)")
    
    print("\n" + "=" * 60)
    print("Проверка завершена")
    print("=" * 60)

if __name__ == "__main__":
    main()

