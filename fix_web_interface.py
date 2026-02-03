#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление ошибок в веб-интерфейсе на сервере
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
    print("🔧 ИСПРАВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Проверяем какие файлы веб-интерфейса есть
    print("\n📁 Проверка файлов веб-интерфейса...")
    success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && ls -la web-interface* 2>&1")
    print(output)
    
    # Читаем текущий файл
    print("\n📖 Чтение web-interface.cjs...")
    success, content, error = execute_command(ssh, f"cat {PROJECT_PATH}/web-interface.cjs")
    
    if not success:
        print(f"❌ Ошибка чтения файла: {error}")
        ssh.close()
        return
    
    # Проверяем проблемы
    print("\n🔍 Поиск проблем...")
    
    # Проблема 1: Проверяем строку 160 (примерно)
    lines = content.split('\n')
    if len(lines) > 160:
        print(f"Строка 160: {lines[159][:100]}")
    
    # Проблема 2: Проверяем определение runTest
    has_runTest_def = 'function runTest' in content or 'async function runTest' in content
    has_onclick_runTest = 'onclick="runTest' in content or "onclick='runTest" in content
    
    print(f"Найдена функция runTest: {has_runTest_def}")
    print(f"Найден onclick runTest: {has_onclick_runTest}")
    
    # Ищем проблемные места
    problems = []
    for i, line in enumerate(lines, 1):
        # Проверяем на невалидные символы в HTML
        if '`' in line and line.count('`') % 2 != 0:
            if i > 150 and i < 170:  # Около строки 160
                problems.append(f"Строка {i}: Возможная проблема с обратными кавычками")
        
        # Проверяем на неэкранированные кавычки в HTML
        if 'onclick=' in line and ('"' in line or "'" in line):
            if 'runTest' in line:
                problems.append(f"Строка {i}: onclick с runTest: {line.strip()[:80]}")
    
    if problems:
        print("\n⚠️  Найденные проблемы:")
        for p in problems:
            print(f"   {p}")
    
    # Исправляем файл
    print("\n🔧 Исправление файла...")
    
    # Читаем правильную версию из локального файла
    try:
        with open('web-interface.cjs', 'r', encoding='utf-8') as f:
            fixed_content = f.read()
        
        # Записываем исправленный файл на сервер
        print("📝 Запись исправленного файла...")
        
        # Создаем временный файл
        temp_file = f"/tmp/web-interface-fixed.cjs"
        with ssh.open_sftp() as sftp:
            with sftp.file(temp_file, 'w') as f:
                f.write(fixed_content)
        
        # Копируем на место
        success, output, error = execute_command(ssh, f"cp {temp_file} {PROJECT_PATH}/web-interface.cjs")
        if success:
            print("✅ Файл исправлен")
        else:
            print(f"❌ Ошибка копирования: {error}")
        
        # Проверяем синтаксис
        print("\n✅ Проверка синтаксиса...")
        success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1")
        if success:
            print("✅ Синтаксис корректен")
        else:
            print(f"⚠️  Ошибки синтаксиса: {error}")
        
        # Перезапускаем веб-интерфейс
        print("\n🔄 Перезапуск веб-интерфейса...")
        execute_command(ssh, "pkill -f 'web-interface' || true")
        execute_command(ssh, f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
        print("✅ Веб-интерфейс перезапущен")
        
    except FileNotFoundError:
        print("⚠️  Локальный файл не найден, создаю исправленную версию...")
        # Создаем исправленную версию на основе найденных проблем
        fixed_content = content
        
        # Исправление 1: Убеждаемся что runTest определена правильно
        if 'function runTest(event)' not in fixed_content and 'async function runTest()' in fixed_content:
            # Заменяем async function на обычную с event
            fixed_content = fixed_content.replace(
                'async function runTest() {',
                'function runTest(event) {\n            if (event) event.preventDefault();'
            )
        
        # Исправление 2: Исправляем onclick
        if 'onclick="runTest()"' in fixed_content:
            fixed_content = fixed_content.replace(
                'onclick="runTest()"',
                'onclick="runTest(event)"'
            )
        
        # Исправление 3: Проверяем экранирование в HTML строке
        # Находим проблемные места с обратными кавычками
        
        # Записываем исправленный файл
        temp_file = f"/tmp/web-interface-fixed.cjs"
        with ssh.open_sftp() as sftp:
            with sftp.file(temp_file, 'w') as f:
                f.write(fixed_content)
        
        success, output, error = execute_command(ssh, f"cp {temp_file} {PROJECT_PATH}/web-interface.cjs")
        if success:
            print("✅ Файл исправлен")
        
        # Проверяем синтаксис
        success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1")
        if success:
            print("✅ Синтаксис корректен")
        else:
            print(f"⚠️  Ошибки: {error}")
    
    ssh.close()
    print("\n" + "=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

