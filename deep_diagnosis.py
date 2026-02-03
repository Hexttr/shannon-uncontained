#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Глубокая диагностика проблемы мгновенного завершения пентеста
"""
import paramiko
import sys
import json

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

def check_recent_logs(ssh):
    """Проверка последних логов"""
    print("=" * 70)
    print("1. ПРОВЕРКА ПОСЛЕДНИХ ЛОГОВ")
    print("=" * 70)
    
    # Логи веб-интерфейса
    print("\n--- Логи веб-интерфейса (последние 100 строк) ---")
    stdin, stdout, stderr = ssh.exec_command("tail -100 /tmp/web-interface.log 2>/dev/null || tail -100 shannon-uncontained/web-interface.log 2>/dev/null || echo 'Лог не найден'")
    web_logs = stdout.read().decode('utf-8', errors='ignore')
    print(web_logs[-2000:])  # Последние 2000 символов
    
    # Последние execution-log.json
    print("\n--- Последний execution-log.json ---")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'execution-log.json' -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1")
    last_log_file = stdout.read().decode('utf-8').strip()
    
    if last_log_file:
        stdin, stdout, stderr = ssh.exec_command(f"cat '{last_log_file}' | tail -50")
        log_content = stdout.read().decode('utf-8', errors='ignore')
        print(f"Файл: {last_log_file}")
        print(log_content)
        
        # Парсим JSON для анализа
        try:
            stdin, stdout, stderr = ssh.exec_command(f"cat '{last_log_file}'")
            full_log = stdout.read().decode('utf-8', errors='ignore')
            log_data = json.loads(full_log)
            
            print("\n--- Анализ execution-log ---")
            print(f"Всего агентов: {len(log_data)}")
            
            agents_with_tokens = [a for a in log_data if a.get('summary', {}).get('tokens_used', 0) > 0]
            agents_without_tokens = [a for a in log_data if a.get('summary', {}).get('tokens_used', 0) == 0]
            
            print(f"Агентов с использованием токенов: {len(agents_with_tokens)}")
            print(f"Агентов без токенов: {len(agents_without_tokens)}")
            
            if agents_without_tokens:
                print("\nАгенты без использования токенов (не использовали LLM):")
                for agent in agents_without_tokens[:10]:
                    print(f"  - {agent.get('agent', 'unknown')}: tokens={agent.get('summary', {}).get('tokens_used', 0)}")
            
        except Exception as e:
            print(f"Ошибка при парсинге JSON: {e}")

def check_llm_client_errors(ssh):
    """Проверка ошибок LLM клиента"""
    print("\n" + "=" * 70)
    print("2. ПРОВЕРКА ОШИБОК LLM КЛИЕНТА")
    print("=" * 70)
    
    # Проверяем что происходит при вызове getProviderConfig
    print("\n--- Тест getProviderConfig ---")
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
import('./src/ai/llm-client.js').then(m => {
    try {
        const config = m.getProviderConfig();
        console.log('✅ Конфигурация:', JSON.stringify(config, null, 2));
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack);
    }
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    config_test = stdout.read().decode('utf-8', errors='ignore')
    error_test = stderr.read().decode('utf-8', errors='ignore')
    print(config_test)
    if error_test:
        print("Ошибки:")
        print(error_test)
    
    # Проверяем что происходит при попытке использовать query
    print("\n--- Тест функции query (упрощенный) ---")
    test_query = """
cd shannon-uncontained && timeout 5 node -e "
require('dotenv').config();
import('./src/ai/llm-client.js').then(async m => {
    try {
        const gen = m.query({ 
            prompt: 'Say hello', 
            options: { cwd: '/tmp', maxTurns: 1 } 
        });
        const first = await gen.next();
        console.log('✅ Первый результат:', JSON.stringify(first.value, null, 2));
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack);
    }
});
" 2>&1
"""
    stdin, stdout, stderr = ssh.exec_command(test_query)
    query_test = stdout.read().decode('utf-8', errors='ignore')
    print(query_test[:1000])

def check_agent_execution(ssh):
    """Проверка выполнения агентов"""
    print("\n" + "=" * 70)
    print("3. ПРОВЕРКА ВЫПОЛНЕНИЯ АГЕНТОВ")
    print("=" * 70)
    
    # Проверяем последний world-model.json
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'world-model.json' -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1")
    world_model_file = stdout.read().decode('utf-8').strip()
    
    if world_model_file:
        print(f"\n--- Анализ world-model.json: {world_model_file} ---")
        stdin, stdout, stderr = ssh.exec_command(f"cat '{world_model_file}' | jq '.claims | length' 2>/dev/null || echo 'jq не установлен'")
        claims_count = stdout.read().decode('utf-8').strip()
        print(f"Количество claims: {claims_count}")
        
        stdin, stdout, stderr = ssh.exec_command(f"cat '{world_model_file}' | jq '.entities | length' 2>/dev/null || echo '0'")
        entities_count = stdout.read().decode('utf-8').strip()
        print(f"Количество entities: {entities_count}")
        
        # Проверяем есть ли ошибки в world-model
        stdin, stdout, stderr = ssh.exec_command(f"grep -i 'error\\|fail\\|exception' '{world_model_file}' | head -10")
        errors_in_model = stdout.read().decode('utf-8', errors='ignore')
        if errors_in_model:
            print("\nОшибки в world-model:")
            print(errors_in_model)

def check_web_interface_output(ssh):
    """Проверка вывода веб-интерфейса"""
    print("\n" + "=" * 70)
    print("4. ПРОВЕРКА ВЫВОДА ВЕБ-ИНТЕРФЕЙСА")
    print("=" * 70)
    
    # Проверяем последние процессы shannon
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'shannon|node.*shannon' | grep -v grep | tail -5")
    processes = stdout.read().decode('utf-8', errors='ignore')
    print("Последние процессы shannon:")
    print(processes if processes else "Процессы не найдены")
    
    # Проверяем что возвращает веб-интерфейс
    print("\n--- Тест веб-интерфейса ---")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:3000 2>/dev/null | head -20")
    web_response = stdout.read().decode('utf-8', errors='ignore')
    print("Ответ веб-интерфейса (первые 20 строк):")
    print(web_response)

def check_anthropic_integration(ssh):
    """Проверка интеграции Anthropic"""
    print("\n" + "=" * 70)
    print("5. ПРОВЕРКА ИНТЕГРАЦИИ ANTHROPIC")
    print("=" * 70)
    
    # Проверяем что Anthropic SDK используется правильно
    print("\n--- Проверка кода query функции ---")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'if (config.provider ===.*anthropic' shannon-uncontained/src/ai/llm-client.js | head -40")
    anthropic_code = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_code)
    
    # Проверяем есть ли ошибки при создании Anthropic client
    print("\n--- Тест создания Anthropic client ---")
    test_anthropic = """
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
try {
    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
    console.log('✅ Anthropic client создан успешно');
    console.log('API Key:', process.env.ANTHROPIC_API_KEY ? 'SET' : 'NOT SET');
    console.log('Model:', process.env.LLM_MODEL);
} catch(e) {
    console.log('❌ Ошибка:', e.message);
}
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_anthropic)
    anthropic_test = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_test)

def check_shannon_execution_flow(ssh):
    """Проверка потока выполнения shannon.mjs"""
    print("\n" + "=" * 70)
    print("6. ПРОВЕРКА ПОТОКА ВЫПОЛНЕНИЯ")
    print("=" * 70)
    
    # Проверяем что происходит при запуске generate команды
    print("\n--- Тест команды generate (dry-run) ---")
    test_generate = """
cd shannon-uncontained && timeout 10 node shannon.mjs generate "test.example.com" --output ./test-output 2>&1 | head -50
"""
    stdin, stdout, stderr = ssh.exec_command(test_generate)
    generate_output = stdout.read().decode('utf-8', errors='ignore')
    generate_errors = stderr.read().decode('utf-8', errors='ignore')
    
    print("Вывод:")
    print(generate_output)
    if generate_errors:
        print("\nОшибки:")
        print(generate_errors)
    
    # Проверяем что происходит в RunCommand
    print("\n--- Проверка RunCommand ---")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'getLLMClient\\|llm\\.' shannon-uncontained/src/cli/commands/RunCommand.js | head -20")
    runcommand_llm = stdout.read().decode('utf-8', errors='ignore')
    print(runcommand_llm)

def main():
    print("=" * 70)
    print("ГЛУБОКАЯ ДИАГНОСТИКА МГНОВЕННОГО ЗАВЕРШЕНИЯ ПЕНТЕСТА")
    print("=" * 70)
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_recent_logs(ssh)
        check_llm_client_errors(ssh)
        check_agent_execution(ssh)
        check_web_interface_output(ssh)
        check_anthropic_integration(ssh)
        check_shannon_execution_flow(ssh)
        
        print("\n" + "=" * 70)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("=" * 70)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

