#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка статуса веб-интерфейса
"""
import paramiko
import sys
import os

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    
    print("=" * 80)
    print("🔍 ПРОВЕРКА СТАТУСА ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    # Проверяем процессы
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface' | grep -v grep")
    processes = stdout.read().decode('utf-8')
    if processes.strip():
        print("\n✅ Процессы веб-интерфейса:")
        print(processes)
    else:
        print("\n⚠️  Процессы не найдены")
    
    # Проверяем порт
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp 2>/dev/null | grep :3000 || netstat -tlnp 2>/dev/null | grep :3000")
    port_info = stdout.read().decode('utf-8')
    if port_info.strip():
        print("\n✅ Порт 3000:")
        print(port_info)
    else:
        print("\n⚠️  Порт 3000 не найден")
    
    # Проверяем логи
    stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web-interface.log 2>&1")
    logs = stdout.read().decode('utf-8')
    if logs.strip():
        print("\n📋 Последние логи:")
        print(logs)
    
    # Проверяем файл
    stdin, stdout, stderr = ssh.exec_command("ls -lh /root/shannon-uncontained/web-interface.cjs")
    file_info = stdout.read().decode('utf-8')
    if file_info.strip():
        print("\n📁 Файл веб-интерфейса:")
        print(file_info)
    
    # Проверяем синтаксис
    stdin, stdout, stderr = ssh.exec_command("cd /root/shannon-uncontained && node -c web-interface.cjs 2>&1")
    syntax_check = stderr.read().decode('utf-8')
    if not syntax_check.strip():
        print("\n✅ Синтаксис файла корректен")
    else:
        print("\n⚠️  Ошибки синтаксиса:")
        print(syntax_check)
    
    # Если процесс не запущен, запускаем
    if not processes.strip():
        print("\n🚀 Запуск веб-интерфейса...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/shannon-uncontained && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
        stdout.read()
        import time
        time.sleep(2)
        print("✅ Команда запуска выполнена")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    print("🌐 Веб-интерфейс доступен по адресу:")
    print("   http://72.56.79.153:3000")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

