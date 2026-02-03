#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная диагностика веб-интерфейса и агентов
"""
import paramiko
import sys
import json
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

def check_web_interface_code(ssh):
    """Проверка кода веб-интерфейса"""
    print("=" * 70)
    print("ДИАГНОСТИКА ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Читаем код веб-интерфейса
    print("\n1. Код веб-интерфейса (web-interface.cjs):")
    stdin, stdout, stderr = ssh.exec_command("head -200 shannon-uncontained/web-interface.cjs")
    web_code = stdout.read().decode('utf-8', errors='ignore')
    print(web_code[:2000])
    
    # Проверяем как обрабатывается команда generate
    print("\n2. Обработка команды generate:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'generate\\|shannon.mjs' shannon-uncontained/web-interface.cjs | head -50")
    generate_handler = stdout.read().decode('utf-8', errors='ignore')
    print(generate_handler)
    
    # Проверяем как обрабатывается вывод
    print("\n3. Обработка вывода команды:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'stdout\\|stderr\\|data' shannon-uncontained/web-interface.cjs | head -40")
    output_handler = stdout.read().decode('utf-8', errors='ignore')
    print(output_handler)

def check_web_interface_running(ssh):
    """Проверка запущенного веб-интерфейса"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ЗАПУЩЕННОГО ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Проверяем процессы
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'web-interface|node.*web' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    print("Процессы веб-интерфейса:")
    print(processes if processes else "Не найдено")
    
    # Проверяем логи
    print("\n--- Последние логи веб-интерфейса (50 строк) ---")
    stdin, stdout, stderr = ssh.exec_command("tail -50 /tmp/web-interface.log 2>/dev/null || tail -50 shannon-uncontained/web-interface.log 2>/dev/null || echo 'Лог не найден'")
    logs = stdout.read().decode('utf-8', errors='ignore')
    print(logs)

def test_agent_execution(ssh):
    """Тест выполнения агентов"""
    print("\n" + "=" * 70)
    print("ТЕСТ ВЫПОЛНЕНИЯ АГЕНТОВ")
    print("=" * 70)
    
    # Тестируем запуск через командную строку
    print("\n1. Тест запуска через командную строку:")
    test_target = "https://test.example.com"
    
    command = f"""
cd shannon-uncontained && timeout 30 node shannon.mjs generate "{test_target}" --output ./test-output 2>&1 | head -100
"""
    
    print(f"Запуск пентеста для: {test_target}")
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Читаем вывод постепенно
    output_lines = []
    start_time = time.time()
    
    while True:
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(1024).decode('utf-8', errors='ignore')
            if data:
                output_lines.append(data)
                print(data, end='')
        elif stdout.channel.exit_status_ready():
            break
        elif time.time() - start_time > 5:  # Таймаут 5 секунд для чтения
            break
        time.sleep(0.1)
    
    remaining = stdout.read().decode('utf-8', errors='ignore')
    if remaining:
        print(remaining)
    
    elapsed = time.time() - start_time
    print(f"\nВремя выполнения команды: {elapsed:.2f} секунд")

def check_agent_implementation(ssh):
    """Проверка реализации агентов"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА РЕАЛИЗАЦИИ АГЕНТОВ")
    print("=" * 70)
    
    # Проверяем базовый агент
    print("\n1. Базовый агент (base-agent.js):")
    stdin, stdout, stderr = ssh.exec_command("head -100 shannon-uncontained/src/local-source-generator/v2/agents/base-agent.js")
    base_agent = stdout.read().decode('utf-8', errors='ignore')
    print(base_agent[:1500])
    
    # Проверяем как агенты регистрируются
    print("\n2. Регистрация агентов:")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'registerAgent\\|addAgent\\|Agent.*register' shannon-uncontained/src/local-source-generator/v2 2>/dev/null | head -10")
    agent_registration = stdout.read().decode('utf-8', errors='ignore')
    print(agent_registration if agent_registration else "Не найдено")
    
    # Проверяем scheduler
    print("\n3. Scheduler (планировщик агентов):")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'execute\\|run\\|schedule' shannon-uncontained/src/local-source-generator/v2/orchestrator/scheduler.js | head -40")
    scheduler = stdout.read().decode('utf-8', errors='ignore')
    print(scheduler[:1500])

def check_upstream_comparison(ssh):
    """Сравнение с upstream репозиторием"""
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ С UPSTREAM")
    print("=" * 70)
    
    # Проверяем есть ли различия в веб-интерфейсе
    print("\n1. Проверка веб-интерфейса в upstream:")
    stdin, stdout, stderr = ssh.exec_command("test -f shannon-uncontained/web-interface.cjs && echo 'EXISTS' || echo 'MISSING'")
    web_exists = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Веб-интерфейс: {web_exists}")
    
    # Проверяем документацию по запуску
    print("\n2. Документация по запуску:")
    stdin, stdout, stderr = ssh.exec_command("grep -i 'web\\|frontend\\|interface' shannon-uncontained/README.md shannon-uncontained/*.md 2>/dev/null | head -20")
    docs = stdout.read().decode('utf-8', errors='ignore')
    print(docs if docs else "Не найдено")

def check_missing_components(ssh):
    """Проверка отсутствующих компонентов"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ОТСУТСТВУЮЩИХ КОМПОНЕНТОВ")
    print("=" * 70)
    
    # Проверяем зависимости
    print("\n1. Проверка зависимостей:")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && npm list --depth=0 2>&1 | head -30")
    dependencies = stdout.read().decode('utf-8', errors='ignore')
    print(dependencies)
    
    # Проверяем установлены ли инструменты
    print("\n2. Проверка инструментов пентеста:")
    tools = ['nmap', 'subfinder', 'nuclei', 'katana', 'httpx', 'sqlmap']
    for tool in tools:
        stdin, stdout, stderr = ssh.exec_command(f"which {tool} 2>/dev/null && echo 'INSTALLED' || echo 'MISSING'")
        status = stdout.read().decode('utf-8', errors='ignore').strip()
        icon = "✅" if status == "INSTALLED" else "❌"
        print(f"{icon} {tool}: {status}")

def check_execution_flow(ssh):
    """Проверка потока выполнения"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ПОТОКА ВЫПОЛНЕНИЯ")
    print("=" * 70)
    
    # Проверяем RunCommand
    print("\n1. RunCommand (основная команда запуска):")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'async.*runCommand\\|export.*runCommand' shannon-uncontained/src/cli/commands/RunCommand.js | head -50")
    runcommand = stdout.read().decode('utf-8', errors='ignore')
    print(runcommand[:2000])
    
    # Проверяем как вызывается pipeline
    print("\n2. Вызов pipeline:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'pipeline\\|Pipeline\\|executePipeline' shannon-uncontained/src/cli/commands/RunCommand.js | head -30")
    pipeline_call = stdout.read().decode('utf-8', errors='ignore')
    print(pipeline_call)

def main():
    print("=" * 70)
    print("ПОЛНАЯ ДИАГНОСТИКА ПЕНТЕСТЕРА")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_web_interface_code(ssh)
        check_web_interface_running(ssh)
        test_agent_execution(ssh)
        check_agent_implementation(ssh)
        check_upstream_comparison(ssh)
        check_missing_components(ssh)
        check_execution_flow(ssh)
        
        print("\n" + "=" * 70)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 70)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

