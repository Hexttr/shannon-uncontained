#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест полного потока query с реальным запросом к API
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

def test_full_query(ssh):
    """Тест полного потока query"""
    print("=" * 70)
    print("ТЕСТ ПОЛНОГО ПОТОКА QUERY")
    print("=" * 70)
    
    # Тест с реальным запросом который должен использовать API
    test_script = """
cd shannon-uncontained && timeout 30 node -e "
require('dotenv').config();
import('./src/ai/llm-client.js').then(async m => {
    try {
        console.log('Начало теста query...');
        const gen = m.query({ 
            prompt: 'Say hello and tell me what model you are', 
            options: { 
                cwd: '/tmp', 
                maxTurns: 2,
                permissionMode: 'auto'
            } 
        });
        
        let step = 0;
        for await (const value of gen) {
            step++;
            console.log(\`Шаг \${step}: тип=\${value.type}\`);
            
            if (value.type === 'assistant' && value.message) {
                console.log('✅ Получен ответ от модели:', value.message.content?.substring(0, 100));
                break; // Останавливаемся после первого ответа
            }
            
            if (value.type === 'result') {
                console.log('Результат:', value.result?.substring(0, 100));
                if (value.error) {
                    console.log('❌ Ошибка:', value.error);
                }
                break;
            }
            
            if (step > 10) {
                console.log('Прервано после 10 шагов');
                break;
            }
        }
        
        console.log('✅ Тест завершен');
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack?.substring(0, 1000));
    }
});
" 2>&1
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    output = stdout.read().decode('utf-8', errors='ignore')
    error_output = stderr.read().decode('utf-8', errors='ignore')
    
    print("Вывод:")
    print(output)
    if error_output:
        print("\nОшибки:")
        print(error_output)

def check_why_agents_finish_quickly(ssh):
    """Проверка почему агенты завершаются мгновенно"""
    print("\n" + "=" * 70)
    print("АНАЛИЗ ПРИЧИНЫ МГНОВЕННОГО ЗАВЕРШЕНИЯ")
    print("=" * 70)
    
    # Проверяем как агенты используют LLM
    print("\n1. Проверка использования LLM в агентах:")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'query\\|llm-client' shannon-uncontained/src/phases shannon-uncontained/src/local-source-generator/v2/agents 2>/dev/null | head -20")
    agent_llm_usage = stdout.read().decode('utf-8', errors='ignore')
    print(agent_llm_usage if agent_llm_usage else "Не найдено")
    
    # Проверяем есть ли ошибки при вызове query
    print("\n2. Проверка обработки ошибок в агентах:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'catch.*error\\|catch.*e' shannon-uncontained/src/phases/*.js 2>/dev/null | head -30")
    error_handling = stdout.read().decode('utf-8', errors='ignore')
    print(error_handling[:1000] if error_handling else "Не найдено")
    
    # Проверяем последний запуск через веб-интерфейс
    print("\n3. Анализ последнего запуска:")
    stdin, stdout, stderr = ssh.exec_command("tail -200 /tmp/web-interface.log 2>/dev/null | grep -A 5 -B 5 'error\\|Error\\|ERROR\\|fail\\|Fail' | tail -50")
    recent_errors = stdout.read().decode('utf-8', errors='ignore')
    if recent_errors:
        print("Найденные ошибки в логах:")
        print(recent_errors)
    else:
        print("Ошибок в логах не найдено")

def check_if_agents_skip_llm(ssh):
    """Проверка пропускают ли агенты LLM"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ПРОПУСКА LLM АГЕНТАМИ")
    print("=" * 70)
    
    # Ищем где агенты должны использовать LLM
    print("\n1. Поиск использования query в коде агентов:")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/src -name '*.js' -exec grep -l 'query.*prompt\\|llm.*query' {} \\; 2>/dev/null | head -10")
    files_with_query = stdout.read().decode('utf-8', errors='ignore')
    print(files_with_query if files_with_query else "Не найдено")
    
    # Проверяем один из агентов детально
    print("\n2. Проверка конкретного агента (например, DocumentationAgent):")
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/src -name '*Documentation*' -o -name '*documentation*' 2>/dev/null | head -3")
    doc_agent_files = stdout.read().decode('utf-8', errors='ignore')
    print(doc_agent_files)
    
    if doc_agent_files:
        first_file = doc_agent_files.split('\n')[0].strip()
        if first_file:
            stdin, stdout, stderr = ssh.exec_command(f"head -100 '{first_file}' | grep -A 20 'query\\|llm'")
            agent_code = stdout.read().decode('utf-8', errors='ignore')
            print(agent_code[:1500] if agent_code else "Не найдено использования LLM")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        test_full_query(ssh)
        check_why_agents_finish_quickly(ssh)
        check_if_agents_skip_llm(ssh)
        
        print("\n" + "=" * 70)
        print("ВЫВОДЫ")
        print("=" * 70)
        print("\nПроверьте:")
        print("1. Работает ли функция query с Anthropic API")
        print("2. Используют ли агенты функцию query")
        print("3. Есть ли ошибки которые игнорируются")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

