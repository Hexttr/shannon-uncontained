#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def cmd(client, c):
    stdin, stdout, stderr = client.exec_command(c)
    return stdout.read().decode('utf-8'), stderr.read().decode('utf-8')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)

# Проверка процессов
out, err = cmd(client, "ps aux | grep 'shannon.mjs' | grep -v grep")
print("Процессы:", out[:200] if out else "Нет")

# Последний workspace
out, err = cmd(client, f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1")
ws = out.strip().rstrip('/')
if ws:
    print(f"\nПоследний workspace: {ws.split('/')[-1]}")
    out, err = cmd(client, f"ls -lh {ws}/world-model.json 2>/dev/null")
    print("World Model:", "Найден" if out else "Не найден")

# Обновить веб-интерфейс
sftp = client.open_sftp()
sftp.put('web-interface.cjs', f'{PROJECT_PATH}/web-interface.cjs')
sftp.close()
print("\n✅ Веб-интерфейс обновлен")

# Перезапуск
cmd(client, "pkill -9 -f web-interface; sleep 1")
out, err = cmd(client, f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > /dev/null 2>&1 &")
print("✅ Веб-интерфейс перезапущен")

# Проверка порта
out, err = cmd(client, "ss -tlnp | grep ':3000'")
print("✅ Порт 3000:", "Работает" if out else "Не работает")

print("\n✅ Система готова к реальному тесту!")
client.close()

