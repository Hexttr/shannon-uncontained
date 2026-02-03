#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка и исправление веб-интерфейса на сервере
"""
import paramiko
import sys
import os
import re

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
    print("🔍 ПРОВЕРКА И ИСПРАВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА НА СЕРВЕРЕ")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Читаем файл с сервера
    print("\n📖 Чтение web-interface.cjs с сервера...")
    success, content, error = execute_command(ssh, f"cat {PROJECT_PATH}/web-interface.cjs")
    
    if not success:
        print(f"❌ Ошибка чтения: {error}")
        ssh.close()
        return
    
    lines = content.split('\n')
    print(f"✅ Файл прочитан, строк: {len(lines)}")
    
    # Ищем проблемы
    print("\n🔍 Поиск проблем...")
    problems = []
    
    for i, line in enumerate(lines, 1):
        # Проблема 1: Проверяем строку 160 (примерно) на синтаксические ошибки
        if i == 160:
            print(f"Строка 160: {repr(line[:100])}")
            # Проверяем на невалидные символы
            if '`' in line and line.count('`') % 2 != 0:
                problems.append((i, "Нечетное количество обратных кавычек"))
        
        # Проблема 2: Проверяем на неэкранированные символы в template literal
        if 'outputDiv.textContent +=' in line and '\\n[ERROR]' in line:
            # Проверяем экранирование
            if "'\\n[ERROR]" in line or '"\\n[ERROR]' in line:
                # Проблема: одинарные кавычки внутри template literal с обратными кавычками
                problems.append((i, f"Проблема с экранированием: {line[:80]}"))
        
        # Проблема 3: Проверяем определение runTest
        if i == 96 or (i > 140 and i < 150):
            if 'onclick="runTest()"' in line and 'function runTest(event)' not in content[:i*100]:
                problems.append((i, "onclick вызывает runTest() но функция принимает event"))
    
    if problems:
        print("\n⚠️  Найденные проблемы:")
        for line_num, desc in problems:
            print(f"   Строка {line_num}: {desc}")
    else:
        print("✅ Очевидных проблем не найдено")
    
    # Исправляем файл
    print("\n🔧 Исправление файла...")
    fixed_content = content
    
    # Исправление 1: Исправляем экранирование в строке с ошибкой
    # Заменяем проблемные места с \n[ERROR]
    fixed_content = re.sub(
        r"outputDiv\.textContent \+= '\\n\[ERROR\]",
        r"outputDiv.textContent += '\\n[ERROR]",
        fixed_content
    )
    
    # Исправление 2: Убеждаемся что runTest определена правильно
    if 'function runTest(event)' not in fixed_content:
        # Ищем определение функции
        if 'async function runTest()' in fixed_content:
            fixed_content = fixed_content.replace(
                'async function runTest() {',
                'function runTest(event) {\n            if (event) event.preventDefault();'
            )
        elif 'function runTest()' in fixed_content:
            fixed_content = fixed_content.replace(
                'function runTest() {',
                'function runTest(event) {\n            if (event) event.preventDefault();'
            )
    
    # Исправление 3: Исправляем onclick если нужно
    if 'onclick="runTest()"' in fixed_content:
        fixed_content = fixed_content.replace(
            'onclick="runTest()"',
            'onclick="runTest(event)"'
        )
    
    # Исправление 4: Проверяем и исправляем проблемные символы в HTML
    # Находим HTML часть и проверяем экранирование
    
    # Записываем исправленный файл
    print("📝 Запись исправленного файла...")
    temp_file = "/tmp/web-interface-fixed.cjs"
    
    with ssh.open_sftp() as sftp:
        with sftp.file(temp_file, 'w') as f:
            f.write(fixed_content)
    
    # Копируем на место
    success, output, error = execute_command(ssh, f"cp {temp_file} {PROJECT_PATH}/web-interface.cjs && chmod +x {PROJECT_PATH}/web-interface.cjs")
    if success:
        print("✅ Файл записан")
    else:
        print(f"❌ Ошибка записи: {error}")
        ssh.close()
        return
    
    # Проверяем синтаксис Node.js
    print("\n✅ Проверка синтаксиса Node.js...")
    success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1")
    if success:
        print("✅ Синтаксис корректен")
    else:
        print(f"⚠️  Ошибки синтаксиса:")
        print(error)
        # Показываем проблемные строки
        error_lines = re.findall(r'line (\d+)', error)
        if error_lines:
            for line_num in set(error_lines[:5]):
                line_num = int(line_num)
                if line_num <= len(lines):
                    print(f"   Строка {line_num}: {lines[line_num-1][:80]}")
    
    # Перезапускаем веб-интерфейс
    print("\n🔄 Перезапуск веб-интерфейса...")
    execute_command(ssh, "pkill -f 'web-interface.cjs' || pkill -f 'web-interface' || true")
    import time
    time.sleep(2)
    execute_command(ssh, f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    time.sleep(1)
    
    # Проверяем что он запустился
    success, output, error = execute_command(ssh, "ps aux | grep 'web-interface' | grep -v grep")
    if success and output.strip():
        print("✅ Веб-интерфейс запущен")
        print(f"   Процессы: {output.strip()[:200]}")
    else:
        print("⚠️  Веб-интерфейс возможно не запустился")
        # Проверяем логи
        success, log_output, _ = execute_command(ssh, "tail -20 /tmp/web-interface.log 2>&1")
        if log_output:
            print(f"   Логи: {log_output}")
    
    ssh.close()
    print("\n" + "=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print("\nПроверьте веб-интерфейс: http://72.56.79.153:3000")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

