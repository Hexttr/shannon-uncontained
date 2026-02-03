#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Принудительное обновление файла на сервере"""

import paramiko
import sys
import io
import os
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"
LOCAL_FILE = "web-interface-simple.cjs"

# Подключение
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=15)

print("=" * 60)
print("ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ФАЙЛА НА СЕРВЕРЕ")
print("=" * 60)

# 1. Остановить веб-интерфейс
print("\n[1] Остановка веб-интерфейса...")
stdin, stdout, stderr = client.exec_command(
    f"pkill -f 'node.*web-interface' 2>&1 || true"
)
stdout.read()
time.sleep(1)

# 2. Загрузить файл через SFTP
print("[2] Загрузка файла через SFTP...")
sftp = client.open_sftp()

try:
    # Прочитать локальный файл
    with open(LOCAL_FILE, 'rb') as f:
        local_content = f.read()
    
    print(f"Локальный файл: {len(local_content)} байт")
    
    # Записать на сервер
    remote_file = sftp.file(f"{PROJECT_PATH}/web-interface.cjs", 'wb')
    remote_file.write(local_content)
    remote_file.close()
    
    print("[OK] Файл загружен")
    
    # Установить права
    stdin, stdout, stderr = client.exec_command(
        f"chmod +x {PROJECT_PATH}/web-interface.cjs"
    )
    stdout.read()
    
except Exception as e:
    print(f"[ERROR] Ошибка загрузки: {e}")
finally:
    sftp.close()

# 3. Проверить файл на сервере
print("\n[3] Проверка файла на сервере...")
stdin, stdout, stderr = client.exec_command(
    f"wc -c {PROJECT_PATH}/web-interface.cjs"
)
size_output = stdout.read().decode('utf-8', errors='ignore')
print(f"Размер файла на сервере: {size_output.strip()}")

# Проверить строку 135
stdin, stdout, stderr = client.exec_command(
    f"sed -n '135p' {PROJECT_PATH}/web-interface.cjs | cat -A"
)
line_135 = stdout.read().decode('utf-8', errors='ignore')
print(f"\nСтрока 135: {repr(line_135)}")

# Проверить строку 160
stdin, stdout, stderr = client.exec_command(
    f"sed -n '160p' {PROJECT_PATH}/web-interface.cjs | cat -A"
)
line_160 = stdout.read().decode('utf-8', errors='ignore')
print(f"Строка 160: {repr(line_160)}")

# 4. Проверить синтаксис
print("\n[4] Проверка синтаксиса...")
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && node -c web-interface.cjs 2>&1"
)
exit_status = stdout.channel.recv_exit_status()
syntax_output = stdout.read().decode('utf-8', errors='ignore')
if exit_status == 0:
    print("[OK] Синтаксис корректен")
else:
    print(f"[ERROR] Синтаксическая ошибка:")
    print(syntax_output)

# 5. Запустить веб-интерфейс
print("\n[5] Запуск веб-интерфейса...")
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && nohup node web-interface.cjs > web-interface.log 2>&1 &"
)
stdout.read()
time.sleep(2)

# Проверить что процесс запущен
stdin, stdout, stderr = client.exec_command(
    f"ps aux | grep '[n]ode.*web-interface' | wc -l"
)
process_count = stdout.read().decode('utf-8', errors='ignore').strip()
if process_count == '1':
    print("[OK] Веб-интерфейс запущен")
else:
    print(f"[WARNING] Процессов найдено: {process_count}")

client.close()

print("\n" + "=" * 60)
print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
print("=" * 60)

