#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка как LSGv2 LLM клиент использует Anthropic
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

def check_lsg_provider_detection(ssh):
    """Проверка определения провайдера в LSGv2"""
    print("=" * 70)
    print("ПРОВЕРКА LSGv2 LLM КЛИЕНТА")
    print("=" * 70)
    
    # Проверяем как определяется провайдер
    print("\n1. Определение провайдера в LSGv2:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 20 'const provider =' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -25")
    provider_detection = stdout.read().decode('utf-8', errors='ignore')
    print(provider_detection)
    
    # Проверяем как определяется Anthropic по модели
    print("\n2. Определение Anthropic по модели:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'isAnthropic\\|claude' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -15")
    anthropic_detection = stdout.read().decode('utf-8', errors='ignore')
    print(anthropic_detection)
    
    # Проверяем метод callAnthropic полностью
    print("\n3. Полный метод callAnthropic:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 40 'async callAnthropic' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js")
    call_anthropic_full = stdout.read().decode('utf-8', errors='ignore')
    print(call_anthropic_full)

def test_lsg_llm_client(ssh):
    """Тест LSGv2 LLM клиента"""
    print("\n" + "=" * 70)
    print("ТЕСТ LSGv2 LLM КЛИЕНТА")
    print("=" * 70)
    
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
import('./src/local-source-generator/v2/orchestrator/llm-client.js').then(async m => {
    try {
        const llm = m.getLLMClient();
        const config = llm.getConfig();
        console.log('Конфигурация LSGv2 LLM:', JSON.stringify(config, null, 2));
        
        if (config.hasApiKey) {
            console.log('\\nТест генерации...');
            const result = await llm.generate('Say hello in one word', {
                model: process.env.LLM_MODEL || 'claude-sonnet-4-5'
            });
            console.log('✅ Результат:', result.content?.substring(0, 100));
            console.log('Использовано токенов:', result.usage?.total_tokens || 'не указано');
        } else {
            console.log('❌ API ключ не настроен');
        }
    } catch(e) {
        console.log('❌ Ошибка:', e.message);
        console.log(e.stack?.substring(0, 500));
    }
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    output = stdout.read().decode('utf-8', errors='ignore')
    error_output = stderr.read().decode('utf-8', errors='ignore')
    
    print("Вывод:")
    print(output)
    if error_output:
        print("\nОшибки:")
        print(error_output)

def check_model_selection(ssh):
    """Проверка выбора модели"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ВЫБОРА МОДЕЛИ")
    print("=" * 70)
    
    # Проверяем selectModel
    stdin, stdout, stderr = ssh.exec_command("grep -A 15 'selectModel' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js | head -20")
    select_model = stdout.read().decode('utf-8', errors='ignore')
    print(select_model)
    
    # Проверяем какие модели используются по умолчанию
    print("\nДефолтные модели:")
    stdin, stdout, stderr = ssh.exec_command("grep -A 5 'LLM_CODE_MODEL\\|LLM_SMART_MODEL\\|LLM_FAST_MODEL' shannon-uncontained/src/local-source-generator/v2/orchestrator/llm-client.js")
    default_models = stdout.read().decode('utf-8', errors='ignore')
    print(default_models)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_lsg_provider_detection(ssh)
        test_lsg_llm_client(ssh)
        check_model_selection(ssh)
        
        print("\n" + "=" * 70)
        print("АНАЛИЗ")
        print("=" * 70)
        print("\nАгенты используют LSGv2 LLM клиент через getLLMClient()")
        print("Нужно убедиться что LSGv2 правильно определяет Anthropic провайдер")
        print("и использует callAnthropic метод")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

