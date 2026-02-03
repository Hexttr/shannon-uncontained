#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка полноты репозитория
"""
import paramiko
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def check_server_structure(ssh):
    """Проверка структуры на сервере"""
    print("=" * 70)
    print("СТРУКТУРА РЕПОЗИТОРИЯ НА СЕРВЕРЕ")
    print("=" * 70)
    
    # Основные директории
    print("\n1. Основные директории:")
    stdin, stdout, stderr = ssh.exec_command("ls -la shannon-uncontained/ | head -30")
    root_dirs = stdout.read().decode('utf-8', errors='ignore')
    print(root_dirs)
    
    # Проверяем src
    print("\n2. Структура src/:")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/src -type d -maxdepth 2 2>/dev/null | sort | head -30")
    src_dirs = stdout.read().decode('utf-8', errors='ignore')
    print(src_dirs)
    
    # Подсчитываем файлы
    print("\n3. Подсчет файлов:")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/src -type f | wc -l")
    file_count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Файлов в src/: {file_count}")
    
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained -type f -name '*.js' -o -name '*.mjs' -o -name '*.json' | wc -l")
    js_files = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"JS/MJS/JSON файлов: {js_files}")
    
    # Проверяем важные файлы
    print("\n4. Важные файлы:")
    important_files = [
        "shannon-uncontained/shannon.mjs",
        "shannon-uncontained/package.json",
        "shannon-uncontained/src/cli/commands/RunCommand.js",
        "shannon-uncontained/src/ai/llm-client.js",
        "shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js"
    ]
    
    for file_path in important_files:
        stdin, stdout, stderr = ssh.exec_command(f"test -f '{file_path}' && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode('utf-8', errors='ignore').strip()
        status = "✅" if exists == "EXISTS" else "❌"
        print(f"{status} {os.path.basename(file_path)}")

def check_local_structure():
    """Проверка локальной структуры"""
    print("\n" + "=" * 70)
    print("ЛОКАЛЬНАЯ СТРУКТУРА")
    print("=" * 70)
    
    # Проверяем что есть локально
    local_dirs = []
    if os.path.exists("src"):
        local_dirs.append("src")
    if os.path.exists("server_files"):
        local_dirs.append("server_files")
    
    print(f"\nЛокальные директории: {', '.join(local_dirs) if local_dirs else 'Нет'}")
    
    # Подсчитываем файлы
    if os.path.exists("src"):
        js_files = list(Path("src").rglob("*.js")) + list(Path("src").rglob("*.mjs"))
        print(f"JS/MJS файлов в src/: {len(js_files)}")
    
    if os.path.exists("server_files"):
        server_files_count = len(list(Path("server_files").rglob("*")))
        print(f"Файлов в server_files/: {server_files_count}")

def compare_with_upstream(ssh):
    """Сравнение с upstream"""
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ С UPSTREAM")
    print("=" * 70)
    
    # Проверяем что на сервере это клон upstream
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && git remote -v 2>/dev/null | head -5")
    remotes = stdout.read().decode('utf-8', errors='ignore')
    print("Remotes на сервере:")
    print(remotes if remotes else "Не git репозиторий")
    
    # Проверяем размер репозитория
    stdin, stdout, stderr = ssh.exec_command("du -sh shannon-uncontained 2>/dev/null")
    size = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"\nРазмер репозитория на сервере: {size}")

def check_critical_files(ssh):
    """Проверка критичных файлов для разработки"""
    print("\n" + "=" * 70)
    print("КРИТИЧНЫЕ ФАЙЛЫ ДЛЯ РАЗРАБОТКИ")
    print("=" * 70)
    
    critical_paths = [
        ("Основной скрипт", "shannon-uncontained/shannon.mjs"),
        ("Package.json", "shannon-uncontained/package.json"),
        ("LLM клиент", "shannon-uncontained/src/ai/llm-client.js"),
        ("LSGv2 LLM клиент", "shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js"),
        ("RunCommand", "shannon-uncontained/src/cli/commands/RunCommand.js"),
        ("Веб-интерфейс", "shannon-uncontained/web-interface.cjs"),
        ("Агенты", "shannon-uncontained/src/local-source-generator/v2/agents"),
        ("Phases", "shannon-uncontained/src/phases"),
        ("Utils", "shannon-uncontained/src/utils"),
    ]
    
    print("\nПроверка критичных файлов:")
    for name, path in critical_paths:
        stdin, stdout, stderr = ssh.exec_command(f"test -e '{path}' && echo 'EXISTS' || echo 'MISSING'")
        exists = stdout.read().decode('utf-8', errors='ignore').strip()
        status = "✅" if exists == "EXISTS" else "❌"
        print(f"{status} {name}: {path}")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_server_structure(ssh)
        check_local_structure()
        compare_with_upstream(ssh)
        check_critical_files(ssh)
        
        print("\n" + "=" * 70)
        print("ВЫВОДЫ")
        print("=" * 70)
        print("\nДля разработки критично иметь:")
        print("1. ✅ Весь код из src/")
        print("2. ✅ package.json и зависимости")
        print("3. ✅ Конфигурационные файлы")
        print("4. ✅ Скрипты запуска (shannon.mjs)")
        print("\nНЕ критично:")
        print("- test-output/ (результаты пентестов)")
        print("- node_modules/ (можно переустановить)")
        print("- .git/ (если есть доступ к репозиторию)")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

