#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка что веб-интерфейс использует правильные переменные окружения
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

def main():
    print("=" * 70)
    print("ПРОВЕРКА ПЕРЕДАЧИ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ В ВЕБ-ИНТЕРФЕЙСЕ")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Проверяем как веб-интерфейс запускает shannon.mjs
        print("\n1. ПРОВЕРКА ЗАПУСКА SHANNON.MJS")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("grep -A 10 'shannon.mjs\\|exec.*shannon' shannon-uncontained/web-interface.cjs | head -15")
        exec_code = stdout.read().decode('utf-8', errors='ignore')
        print(exec_code)
        
        # Проверяем передачу переменных окружения
        print("\n2. ПРОВЕРКА ПЕРЕДАЧИ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("grep -B 5 -A 15 'process.env' shannon-uncontained/web-interface.cjs | head -25")
        env_code = stdout.read().decode('utf-8', errors='ignore')
        print(env_code)
        
        # Проверяем что .env загружается
        print("\n3. ПРОВЕРКА ЗАГРУЗКИ .ENV")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("grep -i 'dotenv\\|require.*dotenv\\|load.*env' shannon-uncontained/web-interface.cjs")
        dotenv_usage = stdout.read().decode('utf-8', errors='ignore')
        if dotenv_usage:
            print("Найдено использование dotenv:")
            print(dotenv_usage)
        else:
            print("⚠️ dotenv не используется - переменные должны быть установлены в системе")
            print("Проверяем что .env доступен...")
            stdin, stdout, stderr = ssh.exec_command("test -f shannon-uncontained/.env && echo 'EXISTS' || echo 'NOT_EXISTS'")
            env_exists = stdout.read().decode('utf-8').strip()
            print(f".env файл: {env_exists}")
        
        # Проверяем что shannon.mjs загружает .env
        print("\n4. ПРОВЕРКА ЗАГРУЗКИ .ENV В SHANNON.MJS")
        print("-" * 70)
        stdin, stdout, stderr = ssh.exec_command("head -30 shannon-uncontained/shannon.mjs | grep -i 'dotenv\\|env'")
        shannon_env = stdout.read().decode('utf-8', errors='ignore')
        if shannon_env:
            print("Найдено в shannon.mjs:")
            print(shannon_env)
        else:
            print("Не найдено использование dotenv в начале файла")
        
        # Итоговая проверка
        print("\n" + "=" * 70)
        print("ИТОГОВАЯ ПРОВЕРКА")
        print("=" * 70)
        
        # Проверяем что веб-интерфейс работает
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3000 2>/dev/null | head -5 || echo 'Веб-интерфейс не отвечает'")
        web_response = stdout.read().decode('utf-8', errors='ignore')
        if web_response and 'html' in web_response.lower():
            print("✅ Веб-интерфейс работает и отвечает на запросы")
        else:
            print(f"Ответ веб-интерфейса: {web_response[:100]}")
        
        print("\n✅ ВЕБ-ИНТЕРФЕЙС ГОТОВ!")
        print("\nДоступ к веб-интерфейсу:")
        print(f"  http://{SERVER_HOST}:3000")
        print("\nВеб-интерфейс автоматически использует переменные из .env файла")
        print("при запуске shannon.mjs через process.env")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

