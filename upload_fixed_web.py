#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Загрузка исправленного веб-интерфейса на сервер
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
    print("📤 ЗАГРУЗКА ИСПРАВЛЕННОГО ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    # Читаем локальный файл
    print("\n📖 Чтение локального файла...")
    try:
        with open('web-interface.cjs', 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Файл прочитан, размер: {len(content)} байт")
    except Exception as e:
        print(f"❌ Ошибка чтения локального файла: {e}")
        return
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Загружаем на сервер
    print("\n📤 Загрузка на сервер...")
    temp_file = "/tmp/web-interface-fixed.cjs"
    
    try:
        with ssh.open_sftp() as sftp:
            with sftp.file(temp_file, 'w') as f:
                f.write(content)
        print("✅ Файл загружен во временную директорию")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        ssh.close()
        return
    
    # Копируем на место
    print("📝 Копирование на место...")
    success, output, error = execute_command(ssh, f"cp {temp_file} {PROJECT_PATH}/web-interface.cjs && chmod +x {PROJECT_PATH}/web-interface.cjs")
    if success:
        print("✅ Файл скопирован")
    else:
        print(f"❌ Ошибка копирования: {error}")
        ssh.close()
        return
    
    # Проверяем синтаксис
    print("\n✅ Проверка синтаксиса...")
    success, output, error = execute_command(ssh, f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1")
    if success:
        print("✅ Синтаксис корректен")
    else:
        print(f"⚠️  Ошибки синтаксиса:")
        print(error[:500])
    
    # Перезапускаем веб-интерфейс
    print("\n🔄 Перезапуск веб-интерфейса...")
    execute_command(ssh, "pkill -f 'web-interface.cjs' || pkill -f 'web-interface' || true")
    import time
    time.sleep(2)
    
    execute_command(ssh, f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &")
    time.sleep(2)
    
    # Проверяем что он запустился
    success, output, error = execute_command(ssh, "ps aux | grep 'web-interface.cjs' | grep -v grep")
    if success and output.strip():
        print("✅ Веб-интерфейс запущен")
        # Проверяем порт
        success2, output2, _ = execute_command(ssh, "netstat -tlnp 2>/dev/null | grep :3000 || ss -tlnp 2>/dev/null | grep :3000")
        if success2 and output2.strip():
            print(f"✅ Порт 3000 слушается")
        else:
            print("⚠️  Порт 3000 не найден")
    else:
        print("⚠️  Веб-интерфейс возможно не запустился")
        # Проверяем логи
        success, log_output, _ = execute_command(ssh, "tail -30 /tmp/web-interface.log 2>&1")
        if log_output:
            print(f"Логи:\n{log_output}")
    
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

