#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Принудительный перезапуск веб-интерфейса"""

import paramiko
import sys
import io
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=10)

print("=" * 60)
print("ПРИНУДИТЕЛЬНЫЙ ПЕРЕЗАПУСК ВЕБ-ИНТЕРФЕЙСА")
print("=" * 60)

# 1. Убить все процессы
print("\n[1] Остановка всех процессов...")
stdin, stdout, stderr = client.exec_command("pkill -9 -f 'web-interface' || true", timeout=5)
stdout.channel.close()
time.sleep(1)

# 2. Освободить порт
print("[2] Освобождение порта 3000...")
stdin, stdout, stderr = client.exec_command("fuser -k 3000/tcp 2>/dev/null || true", timeout=5)
stdout.channel.close()
time.sleep(1)

# 3. Загрузить файл заново
print("[3] Загрузка web-interface.cjs...")
sftp = client.open_sftp()
with open('web-interface.cjs', 'r', encoding='utf-8') as f:
    content = f.read()

with sftp.file(f'{PROJECT_PATH}/web-interface.cjs', 'w') as f:
    f.write(content)

sftp.chmod(f'{PROJECT_PATH}/web-interface.cjs', 0o755)
sftp.close()
print("[OK] Файл загружен")

# 4. Проверить содержимое файла
print("\n[4] Проверка содержимого файла...")
stdin, stdout, stderr = client.exec_command(f"grep -c 'runTest(event)' {PROJECT_PATH}/web-interface.cjs", timeout=5)
count = stdout.read().decode('utf-8').strip()
print(f"Найдено упоминаний 'runTest(event)': {count}")

# 5. Запустить веб-интерфейс
print("\n[5] Запуск веб-интерфейса...")
cmd = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 &"
stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
stdout.channel.close()
time.sleep(2)

# 6. Проверить что запустился
print("\n[6] Проверка статуса...")
stdin, stdout, stderr = client.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep", timeout=5)
output = stdout.read().decode('utf-8')
if output.strip():
    print("[OK] Веб-интерфейс запущен")
    print(output)
else:
    print("[ERROR] Веб-интерфейс не запустился!")
    # Проверить логи
    stdin, stdout, stderr = client.exec_command(f"tail -20 {PROJECT_PATH}/web-interface.log 2>&1", timeout=5)
    print("\nЛоги:")
    print(stdout.read().decode('utf-8'))

# 7. Проверить порт
print("\n[7] Проверка порта 3000...")
stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep ':3000' || ss -tlnp | grep ':3000'", timeout=5)
output = stdout.read().decode('utf-8')
if output.strip():
    print("[OK] Порт 3000 слушается")
    print(output)
else:
    print("[ERROR] Порт 3000 не слушается!")

client.close()

print("\n" + "=" * 60)
print("ГОТОВО")
print("=" * 60)
print(f"\nДоступ: http://{HOST}:3000")
print("ВАЖНО: Обновите страницу с очисткой кеша (Ctrl+F5)")

