#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полная диагностика проблемы с пентестом
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

def check_logs(ssh):
    """Проверка логов"""
    print("=" * 70)
    print("1. ПРОВЕРКА ЛОГОВ")
    print("=" * 70)
    
    # Логи веб-интерфейса
    print("\n--- Логи веб-интерфейса ---")
    stdin, stdout, stderr = ssh.exec_command("tail -50 /tmp/web-interface.log 2>/dev/null || tail -50 shannon-uncontained/web-interface.log 2>/dev/null || echo 'Лог не найден'")
    web_logs = stdout.read().decode('utf-8', errors='ignore')
    print(web_logs)
    
    # Логи shannon
    print("\n--- Логи shannon.mjs ---")
    stdin, stdout, stderr = ssh.exec_command("ls -lt shannon-uncontained/test-output/*/execution-log.json 2>/dev/null | head -1 | awk '{print $NF}' | xargs tail -100 2>/dev/null || echo 'Логи не найдены'")
    shannon_logs = stdout.read().decode('utf-8', errors='ignore')
    print(shannon_logs)
    
    # Последние результаты
    print("\n--- Последние результаты ---")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name '*.json' -o -name '*.md' 2>/dev/null | head -5")
    results = stdout.read().decode('utf-8', errors='ignore')
    print(results)

def check_processes(ssh):
    """Проверка процессов"""
    print("\n" + "=" * 70)
    print("2. ПРОВЕРКА ПРОЦЕССОВ")
    print("=" * 70)
    
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'shannon|node.*shannon|web-interface' | grep -v grep")
    processes = stdout.read().decode('utf-8', errors='ignore')
    print(processes if processes else "Процессы не найдены")

def test_claude_api(ssh):
    """Тест Claude API"""
    print("\n" + "=" * 70)
    print("3. ТЕСТ CLAUDE API")
    print("=" * 70)
    
    # Проверяем переменные окружения
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -e \"require('dotenv').config(); console.log('LLM_PROVIDER:', process.env.LLM_PROVIDER); console.log('ANTHROPIC_API_KEY:', process.env.ANTHROPIC_API_KEY ? 'SET (' + process.env.ANTHROPIC_API_KEY.substring(0,20) + '...)' : 'NOT SET'); console.log('LLM_MODEL:', process.env.LLM_MODEL);\"")
    env_test = stdout.read().decode('utf-8', errors='ignore')
    print("Переменные окружения:")
    print(env_test)
    
    # Тест импорта Anthropic
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -e \"try { const Anthropic = require('@anthropic-ai/sdk'); console.log('Anthropic SDK OK'); } catch(e) { console.log('ERROR:', e.message); }\"")
    anthropic_test = stdout.read().decode('utf-8', errors='ignore')
    print("\nТест Anthropic SDK:")
    print(anthropic_test)
    
    # Тест простого запроса к Claude
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
client.messages.create({
    model: process.env.LLM_MODEL || 'claude-3-5-sonnet-20241022',
    max_tokens: 10,
    messages: [{ role: 'user', content: 'Say hello' }]
}).then(r => {
    console.log('SUCCESS:', r.content[0].text);
}).catch(e => {
    console.log('ERROR:', e.message);
    console.log('Status:', e.status);
    console.log('Details:', JSON.stringify(e, null, 2));
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    api_test = stdout.read().decode('utf-8', errors='ignore')
    error_test = stderr.read().decode('utf-8', errors='ignore')
    print("\nТест API запроса:")
    print(api_test)
    if error_test:
        print("Ошибки:")
        print(error_test)

def check_shannon_execution(ssh):
    """Проверка выполнения shannon.mjs"""
    print("\n" + "=" * 70)
    print("4. ПРОВЕРКА ВЫПОЛНЕНИЯ SHANNON.MJS")
    print("=" * 70)
    
    # Проверяем что происходит при запуске
    test_run = """
cd shannon-uncontained && timeout 10 node shannon.mjs --help 2>&1 | head -20
"""
    stdin, stdout, stderr = ssh.exec_command(test_run)
    help_output = stdout.read().decode('utf-8', errors='ignore')
    error_output = stderr.read().decode('utf-8', errors='ignore')
    print("Тест запуска shannon.mjs --help:")
    print(help_output)
    if error_output:
        print("Ошибки:")
        print(error_output)
    
    # Проверяем структуру shannon.mjs
    stdin, stdout, stderr = ssh.exec_command("head -50 shannon-uncontained/shannon.mjs | grep -E 'import|require|dotenv|LLM'")
    imports = stdout.read().decode('utf-8', errors='ignore')
    print("\nИмпорты в shannon.mjs:")
    print(imports)

def check_llm_client_config(ssh):
    """Проверка конфигурации LLM клиента"""
    print("\n" + "=" * 70)
    print("5. ПРОВЕРКА КОНФИГУРАЦИИ LLM КЛИЕНТА")
    print("=" * 70)
    
    # Проверяем getProviderConfig
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'case.*anthropic' shannon-uncontained/src/ai/llm-client.js | head -25")
    anthropic_case = stdout.read().decode('utf-8', errors='ignore')
    print("Case 'anthropic':")
    print(anthropic_case)
    
    # Проверяем что происходит при ошибке
    stdin, stdout, stderr = ssh.exec_command("grep -B 5 -A 10 'throw new Error.*Anthropic' shannon-uncontained/src/ai/llm-client.js")
    error_handling = stdout.read().decode('utf-8', errors='ignore')
    if error_handling:
        print("\nОбработка ошибок Anthropic:")
        print(error_handling)

def check_recent_output(ssh):
    """Проверка последнего вывода"""
    print("\n" + "=" * 70)
    print("6. ПРОВЕРКА ПОСЛЕДНЕГО ВЫВОДА")
    print("=" * 70)
    
    # Ищем последние файлы результатов
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -type f -name '*.json' -o -name '*.md' 2>/dev/null | xargs ls -lt 2>/dev/null | head -5")
    recent_files = stdout.read().decode('utf-8', errors='ignore')
    print("Последние файлы результатов:")
    print(recent_files)
    
    # Читаем последний execution-log
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'execution-log.json' 2>/dev/null | xargs ls -t 2>/dev/null | head -1 | xargs cat 2>/dev/null | head -100")
    last_log = stdout.read().decode('utf-8', errors='ignore')
    if last_log:
        print("\nПоследний execution-log.json:")
        print(last_log)

def main():
    print("=" * 70)
    print("ПОЛНАЯ ДИАГНОСТИКА ПРОБЛЕМЫ С ПЕНТЕСТОМ")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_logs(ssh)
        check_processes(ssh)
        test_claude_api(ssh)
        check_shannon_execution(ssh)
        check_llm_client_config(ssh)
        check_recent_output(ssh)
        
        print("\n" + "=" * 70)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 70)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

