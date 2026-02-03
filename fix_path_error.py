#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление ошибки с path в веб-интерфейсе
"""
import paramiko
import sys

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

def fix_path_error(ssh):
    """Исправление ошибки с path"""
    print("=" * 70)
    print("ИСПРАВЛЕНИЕ ОШИБКИ С PATH")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/web-interface.cjs', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Проверяем есть ли path в начале файла
        if "const path = require('path')" not in content[:200]:
            # Добавляем path в начало после других require
            require_end = content.find("const execAsync = promisify(exec);")
            if require_end != -1:
                path_require = "const path = require('path');\n"
                content = content[:require_end + len("const execAsync = promisify(exec);")] + "\n" + path_require + content[require_end + len("const execAsync = promisify(exec);"):]
                print("[OK] Добавлен require('path') в начало файла")
        
        # Удаляем дубликат const path если есть в блоке очистки
        import re
        # Ищем блок очистки с const path
        cleanup_pattern = r'// Удаляем старые результаты.*?const path = require\([\'"]path[\'"]\);\s*'
        if re.search(cleanup_pattern, content, re.DOTALL):
            # Удаляем const path из блока очистки
            content = re.sub(
                r'(// Удаляем старые результаты.*?)const path = require\([\'"]path[\'"]\);\s*',
                r'\1',
                content,
                flags=re.DOTALL
            )
            print("[OK] Удален дубликат const path из блока очистки")
        
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
    time.sleep(3)
    
    # Проверяем
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    if processes:
        print("✅ Веб-интерфейс запущен")
        # Проверяем логи
        stdin, stdout, stderr = ssh.exec_command("tail -10 /tmp/web-interface.log")
        logs = stdout.read().decode('utf-8', errors='ignore')
        print("\nПоследние логи:")
        print(logs)
        
        # Проверяем доступность
        time.sleep(1)
        stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 2>&1")
        http_code = stdout.read().decode('utf-8', errors='ignore').strip()
        if http_code == "200":
            print("\n✅ Веб-интерфейс доступен на порту 3000")
        else:
            print(f"\n⚠️  HTTP код: {http_code}")
        
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
        if fix_path_error(ssh):
            if restart_web_interface(ssh):
                print("\n✅ ВЕБ-ИНТЕРФЕЙС ИСПРАВЛЕН И ЗАПУЩЕН!")
                print("\nТеперь можно запускать пентест через веб-интерфейс")
            else:
                print("\n❌ Ошибка при запуске веб-интерфейса")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

