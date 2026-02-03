#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск проблемы в агентах
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

def check_agent_llm_usage(ssh):
    """Проверка использования LLM в агентах"""
    print("=" * 70)
    print("ПРОВЕРКА ИСПОЛЬЗОВАНИЯ LLM В АГЕНТАХ")
    print("=" * 70)
    
    # Проверяем DocumentationAgent детально
    print("\n1. DocumentationAgent - использование LLM:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 30 'generateReadme\\|generateAPIDocs' shannon-uncontained/src/local-source-generator/v2/agents/synthesis/documentation-agent.js | head -40")
    doc_agent_llm = stdout.read().decode('utf-8', errors='ignore')
    print(doc_agent_llm[:2000])
    
    # Проверяем есть ли проверки доступности LLM
    print("\n2. Проверки доступности LLM в агентах:")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'isAvailable\\|hasApiKey\\|!llm' shannon-uncontained/src/local-source-generator/v2/agents 2>/dev/null | head -20")
    availability_checks = stdout.read().decode('utf-8', errors='ignore')
    print(availability_checks if availability_checks else "Не найдено")
    
    # Проверяем обработку ошибок
    print("\n3. Обработка ошибок LLM в агентах:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 5 'catch.*llm\\|catch.*LLM\\|catch.*error' shannon-uncontained/src/local-source-generator/v2/agents/synthesis/documentation-agent.js | head -20")
    error_handling = stdout.read().decode('utf-8', errors='ignore')
    print(error_handling if error_handling else "Не найдено")

def check_actual_execution(ssh):
    """Проверка реального выполнения агента"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА РЕАЛЬНОГО ВЫПОЛНЕНИЯ")
    print("=" * 70)
    
    # Симулируем запуск DocumentationAgent
    test_agent = """
cd shannon-uncontained && node -e "
require('dotenv').config();
import('./src/local-source-generator/v2/agents/synthesis/documentation-agent.js').then(async m => {
    try {
        const agent = new m.DocumentationAgent();
        const llm = agent.llm;
        const config = llm.getConfig();
        console.log('LLM конфигурация агента:', JSON.stringify(config, null, 2));
        
        if (!config.hasApiKey) {
            console.log('❌ API ключ не найден!');
        } else {
            console.log('✅ API ключ найден');
            console.log('Провайдер:', config.provider);
            console.log('Модель:', config.model);
            
            // Пробуем вызвать generate
            console.log('\\nТест generate...');
            const result = await llm.generate('Say hello', {
                model: config.model
            });
            console.log('✅ Результат:', result.content?.substring(0, 50));
        }
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack?.substring(0, 500));
    }
});
" 2>&1
"""
    stdin, stdout, stderr = ssh.exec_command(test_agent)
    agent_test = stdout.read().decode('utf-8', errors='ignore')
    error_test = stderr.read().decode('utf-8', errors='ignore')
    
    print("Тест агента:")
    print(agent_test)
    if error_test:
        print("\nОшибки:")
        print(error_test)

def check_why_agents_skip(ssh):
    """Проверка почему агенты пропускают LLM"""
    print("\n" + "=" * 70)
    print("ПОИСК ПРИЧИНЫ ПРОПУСКА LLM")
    print("=" * 70)
    
    # Ищем где агенты могут пропускать LLM вызовы
    print("\n1. Поиск условий пропуска LLM:")
    stdin, stdout, stderr = ssh.exec_command("grep -r 'if.*!llm\\|if.*!config\\|skip.*llm\\|return.*early' shannon-uncontained/src/local-source-generator/v2/agents 2>/dev/null | head -20")
    skip_conditions = stdout.read().decode('utf-8', errors='ignore')
    print(skip_conditions if skip_conditions else "Не найдено")
    
    # Проверяем как агенты обрабатывают отсутствие LLM
    print("\n2. Обработка отсутствия LLM:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'if.*!.*available\\|if.*!.*hasApiKey' shannon-uncontained/src/local-source-generator/v2/agents 2>/dev/null | head -30")
    no_llm_handling = stdout.read().decode('utf-8', errors='ignore')
    print(no_llm_handling if no_llm_handling else "Не найдено")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_agent_llm_usage(ssh)
        check_actual_execution(ssh)
        check_why_agents_skip(ssh)
        
        print("\n" + "=" * 70)
        print("ВЫВОДЫ")
        print("=" * 70)
        print("\nПроверено:")
        print("1. Как агенты используют LLM")
        print("2. Есть ли проверки доступности")
        print("3. Обработка ошибок")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

