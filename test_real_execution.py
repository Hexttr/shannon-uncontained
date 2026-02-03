#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест реального выполнения через веб-интерфейс
"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

SERVER_HOST = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASSWORD = "m8J@2_6whwza6U"
SERVER_PORT = 22

def connect_to_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=SERVER_HOST, port=SERVER_PORT, username=SERVER_USER, password=SERVER_PASSWORD, timeout=10)
        return ssh
    except Exception as e:
        print(f"[ERROR] Ошибка подключения: {e}")
        return None

def simulate_web_interface_run(ssh):
    """Симуляция запуска через веб-интерфейс"""
    print("=" * 70)
    print("СИМУЛЯЦИЯ ЗАПУСКА ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС")
    print("=" * 70)
    
    # Запускаем команду как веб-интерфейс
    target = "https://test.example.com"
    print(f"\nЗапуск пентеста для: {target}")
    
    command = f"""
cd shannon-uncontained && timeout 60 node shannon.mjs generate "{target}" --output ./test-output 2>&1 | tee /tmp/pentest-test.log
"""
    
    print("Выполнение команды...")
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Читаем вывод в реальном времени
    output_lines = []
    error_lines = []
    
    # Читаем stdout
    import select
    import socket
    
    channel = stdout.channel
    while not channel.exit_status_ready():
        if channel.recv_ready():
            data = channel.recv(1024).decode('utf-8', errors='ignore')
            if data:
                output_lines.append(data)
                print(data, end='')
        if channel.recv_stderr_ready():
            data = channel.recv_stderr(1024).decode('utf-8', errors='ignore')
            if data:
                error_lines.append(data)
                print(data, end='', file=sys.stderr)
        time.sleep(0.1)
    
    # Читаем остаток
    remaining_stdout = stdout.read().decode('utf-8', errors='ignore')
    remaining_stderr = stderr.read().decode('utf-8', errors='ignore')
    
    if remaining_stdout:
        print(remaining_stdout)
    if remaining_stderr:
        print("Ошибки:", remaining_stderr, file=sys.stderr)
    
    # Проверяем лог файл
    print("\n--- Содержимое лог файла ---")
    stdin, stdout, stderr = ssh.exec_command("tail -100 /tmp/pentest-test.log 2>/dev/null || echo 'Лог не создан'")
    log_content = stdout.read().decode('utf-8', errors='ignore')
    print(log_content)

def check_execution_log_after_run(ssh):
    """Проверка execution-log после запуска"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА EXECUTION-LOG ПОСЛЕ ЗАПУСКА")
    print("=" * 70)
    
    # Находим последний execution-log
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'execution-log.json' -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1")
    last_log = stdout.read().decode('utf-8').strip()
    
    if last_log:
        print(f"\nПоследний лог: {last_log}")
        
        # Парсим и анализируем
        stdin, stdout, stderr = ssh.exec_command(f"cat '{last_log}' | python3 -m json.tool 2>/dev/null | head -200")
        log_json = stdout.read().decode('utf-8', errors='ignore')
        print("\nПервые 200 строк:")
        print(log_json)
        
        # Подсчитываем статистику
        stats_cmd = f"cat '{last_log}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print(\"Всего агентов:\", len(d)); print(\"С токенами:\", sum(1 for a in d if a.get(\"summary\",{{}}).get(\"tokens_used\",0)>0)); print(\"Без токенов:\", sum(1 for a in d if a.get(\"summary\",{{}}).get(\"tokens_used\",0)==0)); print(\"Успешных:\", sum(1 for a in d if a.get(\"success\")==True)); print(\"Неуспешных:\", sum(1 for a in d if a.get(\"success\")==False))'"
        stdin, stdout, stderr = ssh.exec_command(stats_cmd)
        stats = stdout.read().decode('utf-8', errors='ignore')
        print("\nСтатистика:")
        print(stats)

def check_web_interface_command(ssh):
    """Проверка команды которую выполняет веб-интерфейс"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА КОМАНДЫ ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Смотрим как веб-интерфейс запускает команду
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'shannon.mjs generate' shannon-uncontained/web-interface.cjs | head -15")
    web_command = stdout.read().decode('utf-8', errors='ignore')
    print("Команда веб-интерфейса:")
    print(web_command)
    
    # Проверяем передаются ли переменные окружения
    stdin, stdout, stderr = ssh.exec_command("grep -A 5 'env:' shannon-uncontained/web-interface.cjs | head -10")
    env_passing = stdout.read().decode('utf-8', errors='ignore')
    print("\nПередача переменных окружения:")
    print(env_passing)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_web_interface_command(ssh)
        simulate_web_interface_run(ssh)
        check_execution_log_after_run(ssh)
        
        print("\n" + "=" * 70)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 70)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

