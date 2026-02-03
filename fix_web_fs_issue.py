#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблемы с fs в веб-интерфейсе
"""
import paramiko
import sys
import re

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

def fix_fs_duplicate(ssh):
    """Исправление дублирования fs"""
    print("=" * 70)
    print("ИСПРАВЛЕНИЕ ДУБЛИРОВАНИЯ FS")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/web-interface.cjs', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Находим все объявления fs
        fs_declarations = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'const fs' in line or 'let fs' in line or 'var fs' in line:
                fs_declarations.append((i+1, line))
        
        print(f"\nНайдено объявлений fs: {len(fs_declarations)}")
        for line_num, line in fs_declarations:
            print(f"  Строка {line_num}: {line.strip()}")
        
        # Удаляем дубликаты - оставляем только первое
        if len(fs_declarations) > 1:
            # Находим позицию второго объявления
            second_decl_line = fs_declarations[1][0] - 1  # Индекс с 0
            second_decl_text = fs_declarations[1][1]
            
            # Удаляем второе объявление если оно в блоке очистки
            if 'Cleaning up old results' in content[:content.find(second_decl_text)+500]:
                # Заменяем на версию без const fs
                old_cleanup = re.search(r'// Удаляем старые результаты.*?const fs = require\(.*?\);', content, re.DOTALL)
                if old_cleanup:
                    cleanup_block = old_cleanup.group(0)
                    # Удаляем const fs = require('fs'); из блока
                    new_cleanup = re.sub(r'const fs = require\([\'"]fs[\'"]\);\s*', '', cleanup_block)
                    content = content.replace(cleanup_block, new_cleanup)
                    print("[OK] Удалено дублирование fs")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/web-interface.cjs', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c web-interface.cjs 2>&1")
        syntax_check = stdout.read().decode('utf-8', errors='ignore')
        error_check = stderr.read().decode('utf-8', errors='ignore')
        
        if syntax_check or error_check:
            print("Ошибки:")
            print(syntax_check)
            print(error_check)
            # Показываем проблемные строки
            stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && sed -n '245,255p' web-interface.cjs")
            problem_lines = stdout.read().decode('utf-8', errors='ignore')
            print("\nПроблемные строки:")
            print(problem_lines)
            return False
        else:
            print("[OK] Синтаксис корректен")
            return True
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def restart_web_interface(ssh):
    """Перезапуск веб-интерфейса"""
    import time
    
    print("\n" + "=" * 70)
    print("ПЕРЕЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Останавливаем старый процесс
    print("\n1. Остановка старого процесса...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'web-interface.cjs' 2>&1")
    time.sleep(2)
    
    # Запускаем новый
    print("\n2. Запуск нового процесса...")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    time.sleep(2)
    
    # Проверяем
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    if processes:
        print("✅ Веб-интерфейс запущен")
        # Проверяем логи
        stdin, stdout, stderr = ssh.exec_command("tail -5 /tmp/web-interface.log")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print("\nПоследние логи:")
        print(logs)
        return True
    else:
        print("❌ Веб-интерфейс не запущен")
        # Проверяем ошибки
        stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web-interface.log")
        errors = stdout.read().decode('utf-8', errors='ignore')
        print("\nОшибки:")
        print(errors)
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if fix_fs_duplicate(ssh):
            if restart_web_interface(ssh):
                print("\n✅ ВЕБ-ИНТЕРФЕЙС ИСПРАВЛЕН И ЗАПУЩЕН!")
            else:
                print("\n❌ Ошибка при запуске веб-интерфейса")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

