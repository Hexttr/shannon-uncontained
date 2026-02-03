#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание отсутствующих файлов из оригинального репозитория
"""

import requests
import os
from pathlib import Path

REPO_OWNER = "Steake"
REPO_NAME = "shannon-uncontained"
RAW_BASE_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main"

# Список отсутствующих файлов
MISSING_FILES = [
    ".dockerignore",
    ".env.example",
    ".gitignore",
    ".shannon-model-limits.json",
    "docs/gitbook/.gitbook.yaml",
    "prompts/pipeline-testing/exploit-authz.txt",
    "sample-reports/shannon-report-capital-api.md",
    "src/analyzers/ErrorPatternAnalyzer.js",
    "src/cli/prompts.js",
    "src/core/LegacyPentestRunner.js",
    "src/local-source-generator/crawlers/active-crawl.",
    "src/local-source-generator/crawlers/js-analysis.",
    "src/utils/metrics.js",
    # domain-profiler.js - нужно перезаписать оригиналом
    "src/local-source-generator/v2/adaptation/domain-profiler.js",
]

def download_file(file_path):
    """Загрузить файл из GitHub"""
    url = f"{RAW_BASE_URL}/{file_path}"
    
    # Исправление проблемных путей
    local_path = file_path
    if file_path.endswith('.'):
        # Для Windows создаем с другим именем, но сохраняем оригинальное содержимое
        local_path = file_path[:-1] + '_'
    
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Для бинарных файлов
            if file_path.endswith(('.png', '.jpg', '.gif', '.ico')):
                local_path.write_bytes(response.content)
            else:
                # Текстовые файлы
                content = response.text
                local_path.write_text(content, encoding='utf-8')
            
            print(f"[OK] {file_path}")
            return True
        else:
            print(f"[FAIL] {file_path} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {file_path} - {e}")
        return False

def main():
    print("=" * 60)
    print("Загрузка отсутствующих файлов из оригинала")
    print("=" * 60)
    
    downloaded = 0
    failed = 0
    
    for file_path in MISSING_FILES:
        if download_file(file_path):
            downloaded += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"[OK] Загружено: {downloaded}")
    print(f"[FAIL] Ошибок: {failed}")
    print("=" * 60)
    
    # Удалить мой созданный domain-profiler если он отличается
    print("\n[INFO] Проверка domain-profiler.js...")
    local_file = Path("src/local-source-generator/v2/adaptation/domain-profiler.js")
    if local_file.exists():
        print("[OK] Файл существует, должен быть заменен оригиналом")

if __name__ == "__main__":
    main()

