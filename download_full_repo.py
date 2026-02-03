#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание полного репозитория с сервера
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

def download_directory(sftp, remote_dir, local_dir, exclude_dirs=None):
    """Рекурсивное скачивание директории"""
    if exclude_dirs is None:
        exclude_dirs = ['node_modules', '.git', 'test-output', '__pycache__', '.pytest_cache']
    
    try:
        # Создаем локальную директорию
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        
        # Получаем список файлов и директорий
        items = sftp.listdir_attr(remote_dir)
        
        for item in items:
            remote_path = f"{remote_dir}/{item.filename}"
            local_path = Path(local_dir) / item.filename
            
            # Пропускаем исключенные директории
            if item.filename in exclude_dirs:
                print(f"⏭️  Пропущено: {item.filename}")
                continue
            
            if item.st_mode & 0o040000:  # Директория
                print(f"📁 {remote_path}")
                download_directory(sftp, remote_path, local_path, exclude_dirs)
            else:  # Файл
                try:
                    sftp.get(remote_path, str(local_path))
                    print(f"✅ {item.filename}")
                except Exception as e:
                    print(f"⚠️  {item.filename}: {e}")
                    
    except Exception as e:
        print(f"[ERROR] Ошибка при скачивании {remote_dir}: {e}")

def download_critical_files(ssh):
    """Скачивание критичных файлов"""
    print("=" * 70)
    print("СКАЧИВАНИЕ КРИТИЧНЫХ ФАЙЛОВ")
    print("=" * 70)
    
    sftp = ssh.open_sftp()
    
    # Критичные файлы в корне
    root_files = [
        "shannon.mjs",
        "package.json",
        "package-lock.json",
        ".env.example",
        ".gitignore",
        "README.md",
        "LICENSE",
        "Dockerfile",
        "web-interface.cjs"
    ]
    
    local_root = Path("shannon-uncontained")
    local_root.mkdir(exist_ok=True)
    
    print("\n1. Корневые файлы:")
    for filename in root_files:
        try:
            remote_path = f"shannon-uncontained/{filename}"
            local_path = local_root / filename
            sftp.get(remote_path, str(local_path))
            print(f"✅ {filename}")
        except Exception as e:
            print(f"⚠️  {filename}: {e}")
    
    # Скачиваем всю директорию src/
    print("\n2. Директория src/ (критично для разработки):")
    print("Это может занять некоторое время...")
    download_directory(sftp, "shannon-uncontained/src", local_root / "src", 
                     exclude_dirs=['node_modules', '.git', 'test-output', '__pycache__', '.pytest_cache'])
    
    # Скачиваем документацию
    print("\n3. Документация:")
    doc_files = [
        "ARCHITECTURE.md",
        "AGENTS.md",
        "CLAUDE.md",
        "DEPENDENCIES.md",
        "LLM_SETUP_GUIDE.md",
        "EQBSL-Primer.md"
    ]
    
    for filename in doc_files:
        try:
            remote_path = f"shannon-uncontained/{filename}"
            local_path = local_root / filename
            sftp.get(remote_path, str(local_path))
            print(f"✅ {filename}")
        except Exception as e:
            print(f"⚠️  {filename}: {e}")
    
    sftp.close()
    
    print(f"\n✅ Критичные файлы скачаны в: {local_root.absolute()}")

def main():
    print("=" * 70)
    print("СКАЧИВАНИЕ ПОЛНОГО РЕПОЗИТОРИЯ")
    print("=" * 70)
    print("\n⚠️  ВНИМАНИЕ: Локально отсутствует большая часть кода!")
    print("   На сервере: 161 файл в src/, 13,289 JS/MJS/JSON файлов")
    print("   Локально: только 1 файл в src/")
    print("\nСкачиваю критичные файлы для разработки...")
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        download_critical_files(ssh)
        
        print("\n" + "=" * 70)
        print("ГОТОВО!")
        print("=" * 70)
        print("\nСкачано:")
        print("✅ Весь код из src/")
        print("✅ package.json и конфигурация")
        print("✅ Документация")
        print("\nНЕ скачано (не критично):")
        print("⏭️  node_modules/ (можно установить через npm install)")
        print("⏭️  test-output/ (результаты пентестов)")
        print("⏭️  .git/ (есть доступ к репозиторию)")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

