#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрое развертывание исправленного веб-интерфейса
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
    print("=" * 80)
    print("🚀 РАЗВЕРТЫВАНИЕ ИСПРАВЛЕННОГО ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 80)
    
    # Читаем локальный файл
    print("\n📖 Чтение web-interface.cjs...")
    try:
        with open('web-interface.cjs', 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Файл прочитан ({len(content)} байт)")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Подключаемся к серверу
    print("\n🔌 Подключение к серверу...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    
    PROJECT_PATH = "/root/shannon-uncontained"
    
    # Останавливаем старый процесс
    print("\n🛑 Остановка старого процесса...")
    stdin, stdout, stderr = ssh.exec_command("pkill -f 'web-interface.cjs' || true")
    stdout.read()
    import time
    time.sleep(1)
    
    # Загружаем файл
    print("📤 Загрузка файла...")
    sftp = ssh.open_sftp()
    try:
        remote_file = sftp.file(f"{PROJECT_PATH}/web-interface.cjs", 'w')
        remote_file.write(content)
        remote_file.close()
        print("✅ Файл загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        sftp.close()
        ssh.close()
        return
    finally:
        sftp.close()
    
    # Устанавливаем права
    stdin, stdout, stderr = ssh.exec_command(f"chmod +x {PROJECT_PATH}/web-interface.cjs")
    stdout.read()
    
    # Проверяем синтаксис
    print("\n✅ Проверка синтаксиса...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {PROJECT_PATH} && node -c web-interface.cjs")
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("✅ Синтаксис корректен")
    else:
        error = stderr.read().decode('utf-8')
        print(f"⚠️  Ошибки синтаксиса:\n{error[:500]}")
    
    # Запускаем веб-интерфейс
    print("\n🚀 Запуск веб-интерфейса...")
    stdin, stdout, stderr = ssh.exec_command(
        f"cd {PROJECT_PATH} && nohup node web-interface.cjs > /tmp/web-interface.log 2>&1 &"
    )
    stdout.read()
    time.sleep(2)
    
    # Проверяем что запустился
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep")
    output = stdout.read().decode('utf-8')
    if output.strip():
        print("✅ Веб-интерфейс запущен")
        print(f"   Процесс: {output.strip()[:100]}")
    else:
        print("⚠️  Процесс не найден, проверяем логи...")
        stdin, stdout, stderr = ssh.exec_command("tail -20 /tmp/web-interface.log")
        log_output = stdout.read().decode('utf-8')
        if log_output:
            print(f"   Логи:\n{log_output}")
    
    # Проверяем порт
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp 2>/dev/null | grep :3000 || netstat -tlnp 2>/dev/null | grep :3000")
    port_output = stdout.read().decode('utf-8')
    if port_output.strip():
        print(f"✅ Порт 3000 слушается")
    else:
        print("⚠️  Порт 3000 не найден")
    
    ssh.close()
    
    print("\n" + "=" * 80)
    print("✅ ГОТОВО")
    print("=" * 80)
    print("\n🌐 Проверьте веб-интерфейс:")
    print("   http://72.56.79.153:3000")
    print("\n📝 Исправления:")
    print("   - Исправлено экранирование \\n[ERROR]")
    print("   - Добавлена проверка event перед preventDefault()")
    print("   - Функция runTest теперь корректно обрабатывает вызовы")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

