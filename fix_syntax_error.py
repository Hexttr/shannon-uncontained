#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление синтаксической ошибки
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

def fix_syntax(ssh):
    """Исправление синтаксической ошибки"""
    print("=" * 70)
    print("ИСПРАВЛЕНИЕ СИНТАКСИЧЕСКОЙ ОШИБКИ")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Ищем проблемное место
        # Ошибка: "const response" дважды
        problem_pattern = r"} else \{\s*const response = await"
        match = re.search(problem_pattern, content)
        
        if match:
            print(f"Найдена проблема на позиции: {match.start()}")
            # Заменяем на правильный код
            content = content[:match.start()] + "} else {\n                response = await" + content[match.end():]
            print("[OK] Исправлена двойная декларация const response")
        else:
            # Ищем по-другому
            problem_pattern2 = r"} else \{\s*const response"
            match2 = re.search(problem_pattern2, content)
            if match2:
                print(f"Найдена проблема (вариант 2) на позиции: {match2.start()}")
                content = content[:match2.start()] + "} else {\n                response" + content[match2.start()+len("} else {\n                const response"):]
                print("[OK] Исправлена двойная декларация")
            else:
                print("[WARNING] Не найдена проблема, проверяем вручную...")
                # Ищем строку 398
                lines = content.split('\n')
                if len(lines) > 397:
                    print(f"Строка 398: {lines[397]}")
                    print(f"Строка 397: {lines[396]}")
                    print(f"Строка 399: {lines[398]}")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c src/ai/llm-client.js 2>&1")
        syntax_check = stdout.read().decode('utf-8', errors='ignore')
        error_check = stderr.read().decode('utf-8', errors='ignore')
        
        if syntax_check or error_check:
            print("Остались ошибки:")
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

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if fix_syntax(ssh):
            print("\n✅ СИНТАКСИЧЕСКАЯ ОШИБКА ИСПРАВЛЕНА!")
        else:
            print("\n❌ Ошибка при исправлении")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

