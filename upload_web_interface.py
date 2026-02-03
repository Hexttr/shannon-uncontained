#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Загрузка веб-интерфейса на сервер"""

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

for attempt in range(3):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=15)
        print(f"[OK] Подключено к {HOST} (попытка {attempt+1})\n")
        
        # Остановить веб-интерфейс
        print("[1] Остановка веб-интерфейса...")
        stdin, stdout, stderr = client.exec_command("pkill -9 -f 'web-interface.cjs' || true", timeout=5)
        stdout.channel.close()
        time.sleep(1)
        
        # Загрузить файл
        print("[2] Загрузка web-interface.cjs...")
        sftp = client.open_sftp()
        with open('web-interface-simple.cjs', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with sftp.file(f'{PROJECT_PATH}/web-interface.cjs', 'w') as f:
            f.write(content)
        
        sftp.chmod(f'{PROJECT_PATH}/web-interface.cjs', 0o755)
        sftp.close()
        print("[OK] Файл загружен")
        
        # Проверить что --no-ai убран
        stdin, stdout, stderr = client.exec_command(f"grep -c '--no-ai' {PROJECT_PATH}/web-interface.cjs", timeout=5)
        count = stdout.read().decode('utf-8').strip()
        if count == '0':
            print("[OK] Флаг --no-ai убран")
        else:
            print(f"[WARNING] Найдено упоминаний --no-ai: {count}")
        
        # Запустить веб-интерфейс
        print("\n[3] Запуск веб-интерфейса...")
        cmd = f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 &"
        stdin, stdout, stderr = client.exec_command(cmd, timeout=5)
        stdout.channel.close()
        time.sleep(2)
        
        # Проверить статус
        stdin, stdout, stderr = client.exec_command("ps aux | grep 'web-interface.cjs' | grep -v grep", timeout=5)
        output = stdout.read().decode('utf-8')
        if output.strip():
            print("[OK] Веб-интерфейс запущен")
        else:
            print("[ERROR] Веб-интерфейс не запустился")
        
        client.close()
        print("\n[OK] Готово!")
        break
        
    except Exception as e:
        print(f"[ERROR] Попытка {attempt+1} не удалась: {e}")
        if attempt < 2:
            print("Повтор через 2 секунды...")
            time.sleep(2)
        else:
            print("\nНе удалось подключиться. Проверьте соединение с сервером.")
            sys.exit(1)

