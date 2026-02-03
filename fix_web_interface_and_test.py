#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление веб-интерфейса и тестирование агентов
"""
import paramiko
import sys

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

def check_web_interface_issue(ssh):
    """Проверка проблемы веб-интерфейса"""
    print("=" * 70)
    print("ПРОБЛЕМА ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Проверяем код который убивает процесс
    print("\n1. Поиск 'kill' в веб-интерфейсе:")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'kill\\|disconnect' shannon-uncontained/web-interface.cjs")
    kill_code = stdout.read().decode('utf-8', errors='ignore')
    print(kill_code)
    
    # Проверяем обработку disconnect
    print("\n2. Обработка disconnect:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 -B 5 'disconnect\\|close' shannon-uncontained/web-interface.cjs | head -30")
    disconnect_handler = stdout.read().decode('utf-8', errors='ignore')
    print(disconnect_handler)

def check_resume_logic(ssh):
    """Проверка логики resume"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ЛОГИКИ RESUME")
    print("=" * 70)
    
    # Проверяем как работает resume
    print("\n1. Логика resume в RunCommand:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'resume\\|Resuming' shannon-uncontained/src/cli/commands/RunCommand.js | head -40")
    resume_logic = stdout.read().decode('utf-8', errors='ignore')
    print(resume_logic)
    
    # Проверяем есть ли старые результаты
    print("\n2. Проверка старых результатов:")
    stdin, stdout, stderr = ssh.exec_command("ls -la shannon-uncontained/test-output/repos/test.example.com/ 2>/dev/null | head -10")
    old_results = stdout.read().decode('utf-8', errors='ignore')
    print(old_results if old_results else "Старых результатов нет")

def check_agent_execution_logic(ssh):
    """Проверка логики выполнения агентов"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ЛОГИКИ ВЫПОЛНЕНИЯ АГЕНТОВ")
    print("=" * 70)
    
    # Проверяем как агенты выполняются
    print("\n1. Выполнение pipeline:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'executePipeline\\|runPipeline' shannon-uncontained/src/cli/commands/RunCommand.js | head -50")
    pipeline_exec = stdout.read().decode('utf-8', errors='ignore')
    print(pipeline_exec[:2000])
    
    # Проверяем scheduler
    print("\n2. Scheduler execute:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'async execute\\|executeStage' shannon-uncontained/src/local-source-generator/v2/orchestrator/scheduler.js | head -50")
    scheduler_exec = stdout.read().decode('utf-8', errors='ignore')
    print(scheduler_exec[:2000])

def check_missing_tools(ssh):
    """Проверка отсутствующих инструментов"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ОТСУТСТВУЮЩИХ ИНСТРУМЕНТОВ")
    print("=" * 70)
    
    # Проверяем katana
    print("\n1. Katana:")
    stdin, stdout, stderr = ssh.exec_command("which katana 2>/dev/null || echo 'NOT FOUND'")
    katana = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Katana: {katana}")
    
    if katana == "NOT FOUND":
        print("\n⚠️ Katana не установлен!")
        print("Установка katana...")
        stdin, stdout, stderr = ssh.exec_command("go install github.com/projectdiscovery/katana/cmd/katana@latest 2>&1")
        install_output = stdout.read().decode('utf-8', errors='ignore')
        print(install_output)
        
        # Проверяем после установки
        stdin, stdout, stderr = ssh.exec_command("which katana 2>/dev/null && echo 'INSTALLED' || echo 'FAILED'")
        status = stdout.read().decode('utf-8', errors='ignore').strip()
        print(f"Статус: {status}")

def test_full_pentest(ssh):
    """Тест полного пентеста без resume"""
    print("\n" + "=" * 70)
    print("ТЕСТ ПОЛНОГО ПЕНТЕСТА БЕЗ RESUME")
    print("=" * 70)
    
    # Удаляем старые результаты
    print("\n1. Удаление старых результатов:")
    stdin, stdout, stderr = ssh.exec_command("rm -rf shannon-uncontained/test-output/repos/test.example.com 2>&1")
    rm_output = stdout.read().decode('utf-8', errors='ignore')
    print(rm_output if rm_output else "Удалено")
    
    # Запускаем пентест с --no-resume
    print("\n2. Запуск пентеста с --no-resume:")
    command = """
cd shannon-uncontained && timeout 120 node shannon.mjs generate "https://test.example.com" --output ./test-output --no-resume 2>&1 | tee /tmp/pentest-full-test.log
"""
    
    print("Выполнение (это может занять время)...")
    stdin, stdout, stderr = ssh.exec_command(command)
    
    # Читаем вывод постепенно
    import time
    output_lines = []
    start_time = time.time()
    max_time = 30  # Максимум 30 секунд на чтение
    
    while time.time() - start_time < max_time:
        if stdout.channel.recv_ready():
            data = stdout.channel.recv(4096).decode('utf-8', errors='ignore')
            if data:
                output_lines.append(data)
                print(data, end='')
        elif stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)
    
    remaining = stdout.read().decode('utf-8', errors='ignore')
    if remaining:
        print(remaining)
    
    elapsed = time.time() - start_time
    print(f"\nВремя выполнения: {elapsed:.2f} секунд")
    
    # Проверяем результаты
    print("\n3. Проверка результатов:")
    stdin, stdout, stderr = ssh.exec_command("cat /tmp/pentest-full-test.log | tail -50")
    log_tail = stdout.read().decode('utf-8', errors='ignore')
    print(log_tail)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_web_interface_issue(ssh)
        check_resume_logic(ssh)
        check_agent_execution_logic(ssh)
        check_missing_tools(ssh)
        test_full_pentest(ssh)
        
        print("\n" + "=" * 70)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 70)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

