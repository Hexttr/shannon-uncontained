#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Принудительное обновление веб-интерфейса с проверкой"""

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
print("ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ВЕБ-ИНТЕРФЕЙСА")
print("=" * 60)

# 1. Убить все процессы
print("\n[1] Остановка всех процессов...")
stdin, stdout, stderr = client.exec_command("pkill -9 -f 'web-interface' || pkill -9 -f 'node.*web' || true", timeout=5)
stdout.channel.close()
time.sleep(2)

# 2. Освободить порт
print("[2] Освобождение порта 3000...")
stdin, stdout, stderr = client.exec_command("fuser -k 3000/tcp 2>/dev/null || true", timeout=5)
stdout.channel.close()
time.sleep(1)

# 3. Загрузить файл
print("[3] Загрузка web-interface.cjs...")
sftp = client.open_sftp()

with open('web-interface-simple.cjs', 'r', encoding='utf-8') as f:
    local_content = f.read()

print(f"[INFO] Локальный файл: {len(local_content)} символов")

with sftp.file(f'{PROJECT_PATH}/web-interface.cjs', 'w') as f:
    f.write(local_content)

sftp.chmod(f'{PROJECT_PATH}/web-interface.cjs', 0o755)
sftp.close()
print("[OK] Файл загружен")

# 4. Проверить что файл действительно обновлен
print("\n[4] Проверка файла на сервере...")
stdin, stdout, stderr = client.exec_command(f"wc -c {PROJECT_PATH}/web-interface.cjs", timeout=5)
server_size = stdout.read().decode('utf-8').strip()
print(f"Размер на сервере: {server_size}")

stdin, stdout, stderr = client.exec_command(f"grep -c 'color: #f48771' {PROJECT_PATH}/web-interface.cjs", timeout=5)
red_count = stdout.read().decode('utf-8').strip()
print(f"Найдено красных заголовков: {red_count}")

# 5. Проверить синтаксис
print("\n[5] Проверка синтаксиса...")
stdin, stdout, stderr = client.exec_command(
    f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && node -c web-interface.cjs 2>&1",
    timeout=10
)
syntax_check = stdout.read().decode('utf-8')
if syntax_check.strip():
    print(f"[ERROR] Синтаксис: {syntax_check}")
else:
    print("[OK] Синтаксис корректен")

# 6. Запустить веб-интерфейс
print("\n[6] Запуск веб-интерфейса...")
cmd = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 &"
stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
stdout.channel.close()
time.sleep(2)

# 7. Проверить что запустился
print("\n[7] Проверка статуса...")
stdin, stdout, stderr = client.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep", timeout=5)
output = stdout.read().decode('utf-8')
if output.strip():
    print("[OK] Веб-интерфейс запущен")
    print(output)
else:
    print("[ERROR] Веб-интерфейс не запустился!")
    stdin, stdout, stderr = client.exec_command(f"tail -20 {PROJECT_PATH}/web-interface.log 2>&1", timeout=5)
    print("\nЛоги:")
    print(stdout.read().decode('utf-8'))

# 8. Проверить порт
print("\n[8] Проверка порта 3000...")
stdin, stdout, stderr = client.exec_command("netstat -tlnp | grep ':3000' || ss -tlnp | grep ':3000'", timeout=5)
output = stdout.read().decode('utf-8')
if output.strip():
    print("[OK] Порт 3000 слушается")
else:
    print("[ERROR] Порт 3000 не слушается!")

client.close()

print("\n" + "=" * 60)
print("ГОТОВО")
print("=" * 60)
print(f"\nДоступ: http://{HOST}:3000")
print("ВАЖНО: Обновите страницу с очисткой кеша (Ctrl+F5)")

