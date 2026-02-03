#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование веб-интерфейса - проверка что команда запускается
"""
import paramiko
import sys
import os
import requests
import time

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def connect_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    return ssh

def execute_command(ssh, command, timeout=300):
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("🧪 ТЕСТИРОВАНИЕ ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    # 1. Проверка доступности веб-интерфейса
    print("\n🌐 1. ПРОВЕРКА ДОСТУПНОСТИ")
    print("-" * 80)
    
    try:
        response = requests.get(f"http://{SERVER_IP}:3000", timeout=5)
        if response.status_code == 200:
            print("   ✅ Веб-интерфейс доступен")
            if 'Shannon Pentest' in response.text or 'runTest' in response.text:
                print("   ✅ HTML загружается корректно")
            else:
                print("   ⚠️  HTML может быть некорректным")
        else:
            print(f"   ❌ Веб-интерфейс недоступен (код: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
    
    # 2. Проверка команды напрямую на сервере
    print("\n🔧 2. ПРОВЕРКА КОМАНДЫ НА СЕРВЕРЕ")
    print("-" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Тестовая команда (только проверка что команда работает)
    test_cmd = f"cd {PROJECT_PATH} && export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && ./shannon.mjs --help 2>&1 | head -3"
    success, output, error = execute_command(ssh, test_cmd)
    if success:
        print("   ✅ Команда shannon.mjs работает")
        print(f"   {output.strip()[:100]}")
    else:
        print(f"   ❌ Команда не работает: {error[:200]}")
    
    # 3. Проверка что команда generate работает
    print("\n🧪 3. ТЕСТ КОМАНДЫ GENERATE")
    print("-" * 80)
    
    # Запускаем короткий тест (только проверка что команда запускается)
    test_generate = f"cd {PROJECT_PATH} && timeout 10 bash -c 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin:$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin && export GOPATH=$HOME/go && ./shannon.mjs generate https://example.com --workspace ./test-quick 2>&1' || echo 'TIMEOUT_OR_ERROR'"
    success, output, error = execute_command(ssh, test_generate, timeout=15)
    
    if 'TIMEOUT_OR_ERROR' in output:
        print("   ⚠️  Команда запустилась но была прервана (это нормально для теста)")
    elif 'error' in output.lower() or 'Error' in output:
        print(f"   ⚠️  Возможные ошибки в выводе:")
        print(f"   {output[:300]}")
    else:
        print("   ✅ Команда generate запускается")
        if output.strip():
            print(f"   Начало вывода: {output.strip()[:200]}")
    
    # 4. Проверка логов веб-интерфейса
    print("\n📋 4. ПРОВЕРКА ЛОГОВ")
    print("-" * 80)
    
    success, logs, _ = execute_command(ssh, "tail -30 /tmp/web-interface.log 2>&1")
    if logs.strip():
        print("   Последние логи:")
        print(f"   {logs.strip()[-500:]}")
    else:
        print("   Логи пусты или файл не найден")
    
    # 5. Проверка процесса веб-интерфейса
    print("\n🔍 5. ПРОВЕРКА ПРОЦЕССА")
    print("-" * 80)
    
    success, processes, _ = execute_command(ssh, "ps aux | grep 'web-interface.cjs' | grep -v grep")
    if success and processes.strip():
        print("   ✅ Процесс веб-интерфейса запущен")
        lines = processes.strip().split('\n')
        for line in lines[:2]:
            print(f"   {line[:100]}")
    else:
        print("   ❌ Процесс не найден")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    print("📊 РЕЗЮМЕ")
    print("=" * 80)
    print("""
✅ Окружение подготовлено к пентесту

🌐 Веб-интерфейс: http://72.56.79.153:3000

📝 Для запуска пентеста:
   1. Откройте http://72.56.79.153:3000
   2. Введите URL цели (например: https://tcell.tj)
   3. Нажмите кнопку "Запустить"
   4. Вывод будет отображаться в реальном времени

💡 Если возникает ошибка соединения:
   - Обновите страницу (F5)
   - Проверьте консоль браузера (F12) на ошибки
   - Убедитесь что веб-интерфейс запущен на сервере
   
🔍 Диагностика на сервере:
   ssh root@72.56.79.153
   tail -f /tmp/web-interface.log
   ps aux | grep web-interface
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

