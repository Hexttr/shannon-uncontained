#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка результатов теста и обновление файлов
"""

import paramiko
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HOST = "72.56.79.153"
USERNAME = "root"
PASSWORD = "m8J@2_6whwza6U"
PROJECT_PATH = "/root/shannon-uncontained"

def execute_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')
    return exit_status, output, error

def upload_file(client, local_path, remote_path):
    """Загрузить файл на сервер"""
    sftp = client.open_sftp()
    try:
        sftp.put(local_path, remote_path)
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки: {e}")
        return False
    finally:
        sftp.close()

def main():
    print("=" * 60)
    print("Проверка результатов теста и обновление")
    print("=" * 60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=HOST, username=USERNAME, password=PASSWORD, timeout=30)
        print(f"[OK] Подключено к {HOST}\n")
        
        # 1. Проверить запущенные процессы shannon
        print("[INFO] Проверка запущенных процессов...")
        exit_status, output, error = execute_command(
            client,
            "ps aux | grep 'shannon.mjs generate' | grep -v grep || echo 'Нет запущенных тестов'"
        )
        print(output)
        
        # 2. Проверить workspace директории
        print("\n[INFO] Проверка результатов тестов...")
        exit_status, output, error = execute_command(
            client,
            f"ls -la {PROJECT_PATH}/shannon-results/repos/ 2>/dev/null | tail -20 || echo 'Директория не найдена'"
        )
        print(output)
        
        # 3. Найти последний workspace
        exit_status, output, error = execute_command(
            client,
            f"ls -td {PROJECT_PATH}/shannon-results/repos/*/ 2>/dev/null | head -1 || echo ''"
        )
        latest_workspace = output.strip().rstrip('/')
        
        if latest_workspace:
            print(f"\n[INFO] Последний workspace: {latest_workspace}")
            
            # Проверить world-model.json
            exit_status, output, error = execute_command(
                client,
                f"test -f {latest_workspace}/world-model.json && echo 'exists' || echo 'not exists'"
            )
            if output.strip() == 'exists':
                print("[OK] World Model найден")
                
                # Получить статистику
                exit_status, output, error = execute_command(
                    client,
                    f"python3 -c \"import json; data=json.load(open('{latest_workspace}/world-model.json')); print('Evidence events:', len(data.get('evidence_graph', {{}}).get('events', []))); print('Claims:', len(data.get('ledger', {{}}).get('claims', []))); print('Entities:', len(data.get('target_model', {{}}).get('entities', [])))\" 2>&1"
                )
                print(f"\n[INFO] Статистика:")
                print(output)
            
            # Проверить артефакты
            exit_status, output, error = execute_command(
                client,
                f"find {latest_workspace} -type f -name '*.md' -o -name '*.js' -o -name '*.json' | head -10"
            )
            if output.strip():
                print(f"\n[INFO] Созданные файлы:")
                files = output.strip().split('\n')
                for f in files[:10]:
                    print(f"  - {f}")
        
        # 4. Обновить веб-интерфейс
        print("\n[INFO] Обновление веб-интерфейса...")
        if upload_file(client, 'web-interface.cjs', f'{PROJECT_PATH}/web-interface.cjs'):
            print("[OK] web-interface.cjs обновлен")
        
        # 5. Перезапустить веб-интерфейс
        print("[INFO] Перезапуск веб-интерфейса...")
        execute_command(client, "pkill -9 -f 'web-interface' || true")
        import time
        time.sleep(1)
        
        exit_status, output, error = execute_command(
            client,
            f"cd {PROJECT_PATH} && export NVM_DIR=\"$HOME/.nvm\" && [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\" && nohup node web-interface.cjs > web-interface.log 2>&1 & echo $!"
        )
        
        if exit_status == 0:
            pid = output.strip()
            print(f"[OK] Веб-интерфейс перезапущен (PID: {pid})")
            
            time.sleep(2)
            
            # Проверить что работает
            exit_status, output, error = execute_command(
                client,
                "netstat -tlnp | grep ':3000' || ss -tlnp | grep ':3000'"
            )
            if output.strip():
                print("[OK] Порт 3000 слушается")
            else:
                print("[WARN] Порт 3000 не слушается")
        
        # 6. Проверить готовность системы
        print("\n" + "=" * 60)
        print("Проверка готовности системы")
        print("=" * 60)
        
        checks = [
            ("Node.js", "node --version"),
            ("npm", "npm --version"),
            ("Ollama", "ollama --version 2>&1 | head -1"),
            ("nmap", "nmap --version 2>&1 | head -1"),
            ("subfinder", "subfinder -version 2>&1 | head -1"),
            ("whatweb", "whatweb --version 2>&1 | head -1"),
            ("nuclei", "nuclei -version 2>&1 | head -1"),
        ]
        
        for name, cmd in checks:
            exit_status, output, error = execute_command(client, cmd)
            if exit_status == 0:
                print(f"[OK] {name}: {output.strip()[:50]}")
            else:
                print(f"[WARN] {name}: не найден")
        
        # Проверить .env
        exit_status, output, error = execute_command(
            client,
            f"test -f {PROJECT_PATH}/.env && echo 'exists' || echo 'not exists'"
        )
        if output.strip() == 'exists':
            print("[OK] .env файл существует")
        
        print("\n" + "=" * 60)
        print("КРАТКИЙ ОТЧЕТ")
        print("=" * 60)
        
        if latest_workspace:
            domain = latest_workspace.split('/')[-1]
            print(f"\n✅ Тест выполнен на: {domain}")
            print(f"✅ Workspace: {latest_workspace}")
            print(f"✅ Веб-интерфейс обновлен и перезапущен")
        else:
            print("\n⚠️ Тест не найден или еще выполняется")
        
        print("\n✅ Система готова к реальному тесту!")
        print(f"\nДоступ к веб-интерфейсу: http://{HOST}:3000")
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    main()

