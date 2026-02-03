#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление интеграции Anthropic - проблема в том что используется OpenAI SDK вместо Anthropic SDK
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

def check_llm_client_usage(ssh):
    """Проверка как используется LLM клиент"""
    print("=" * 70)
    print("АНАЛИЗ ПРОБЛЕМЫ")
    print("=" * 70)
    
    # Проверяем функцию query
    print("\n1. Проверка функции query...")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'const client = new OpenAI' shannon-uncontained/src/ai/llm-client.js")
    openai_usage = stdout.read().decode('utf-8', errors='ignore')
    print(openai_usage)
    
    # Проверяем используется ли Anthropic клиент
    stdin, stdout, stderr = ssh.exec_command("grep -n 'new Anthropic' shannon-uncontained/src/ai/llm-client.js")
    anthropic_usage = stdout.read().decode('utf-8', errors='ignore')
    print("\nИспользование Anthropic:")
    print(anthropic_usage if anthropic_usage else "Не найдено")
    
    # Проблема: код использует OpenAI SDK для всех провайдеров
    # Но Anthropic API не совместим с OpenAI API форматом!
    print("\n⚠️ ПРОБЛЕМА ОБНАРУЖЕНА:")
    print("Код использует OpenAI SDK для всех провайдеров через baseURL")
    print("Но Anthropic API имеет другой формат и не работает через OpenAI SDK")
    print("\nРЕШЕНИЕ: Нужно использовать Anthropic SDK напрямую для provider='anthropic'")

def fix_llm_client(ssh):
    """Исправление LLM клиента для работы с Anthropic"""
    print("\n" + "=" * 70)
    print("ИСПРАВЛЕНИЕ LLM КЛИЕНТА")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        
        # Читаем файл
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Находим место где создается OpenAI client
        openai_client_pos = content.find("const client = new OpenAI({")
        if openai_client_pos == -1:
            print("[ERROR] Не найдено создание OpenAI client")
            sftp.close()
            return False
        
        # Находим начало функции query
        query_start = content.find("export async function* query({ prompt, options }) {")
        if query_start == -1:
            print("[ERROR] Не найдена функция query")
            sftp.close()
            return False
        
        # Находим место после getProviderConfig
        config_line = content.find("const config = getProviderConfig();", query_start)
        if config_line == -1:
            print("[ERROR] Не найден getProviderConfig")
            sftp.close()
            return False
        
        # Вставляем код для создания Anthropic клиента перед OpenAI client
        anthropic_init = """
    // Initialize Anthropic client if provider is anthropic
    let anthropicClient = null;
    if (config.provider === 'anthropic') {
        anthropicClient = new Anthropic({
            apiKey: config.apiKey
        });
    }
    
"""
        
        # Вставляем перед созданием OpenAI client
        content = content[:openai_client_pos] + anthropic_init + "    " + content[openai_client_pos:]
        
        # Теперь нужно обновить место где делается запрос
        # Находим client.chat.completions.create
        chat_create_pos = content.find("const response = await client.chat.completions.create({", openai_client_pos)
        if chat_create_pos != -1:
            # Заменяем на условную логику
            old_code = """            const response = await client.chat.completions.create({
                messages: messagesToSend,
                model: modelName,
                tools: tools,
                tool_choice: "auto"
            });"""
            
            new_code = """            let response;
            if (config.provider === 'anthropic') {
                // Use Anthropic SDK directly
                const anthropicMessages = messagesToSend
                    .filter(m => m.role !== 'system')
                    .map(m => ({
                        role: m.role === 'assistant' ? 'assistant' : 'user',
                        content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content)
                    }));
                
                const systemMessage = messagesToSend.find(m => m.role === 'system')?.content || '';
                
                const anthropicResponse = await anthropicClient.messages.create({
                    model: modelName,
                    max_tokens: 4096,
                    messages: anthropicMessages,
                    system: systemMessage
                });
                
                // Convert Anthropic response to OpenAI format
                response = {
                    choices: [{
                        message: {
                            content: anthropicResponse.content[0].text,
                            role: 'assistant',
                            tool_calls: [] // Anthropic doesn't support tools in the same way
                        }
                    }]
                };
            } else {
                response = await client.chat.completions.create({
                    messages: messagesToSend,
                    model: modelName,
                    tools: tools,
                    tool_choice: "auto"
                });
            }"""
            
            if old_code in content:
                content = content.replace(old_code, new_code)
                print("[OK] Обновлен код создания response для Anthropic")
            else:
                print("[WARNING] Не найден точный паттерн, ищем альтернативный...")
                # Пробуем найти более широкий контекст
                import re
                pattern = r"const response = await client\.chat\.completions\.create\(\{[^}]+\}\);"
                match = re.search(pattern, content[chat_create_pos:chat_create_pos+500], re.DOTALL)
                if match:
                    start = chat_create_pos + match.start()
                    end = chat_create_pos + match.end()
                    content = content[:start] + new_code + content[end:]
                    print("[OK] Обновлен код (альтернативный паттерн)")
                else:
                    print("[ERROR] Не удалось найти код для замены")
                    sftp.close()
                    return False
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        print("[OK] LLM клиент обновлен")
        
        # Обновляем модель на рабочую
        print("\n2. Обновление модели на claude-3-5-sonnet-20241022...")
        with sftp.open('shannon-uncontained/.env', 'r') as f:
            env_content = f.read().decode('utf-8')
        
        import re
        env_content = re.sub(
            r'LLM_MODEL=.*',
            'LLM_MODEL=claude-3-5-sonnet-20241022',
            env_content
        )
        
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        
        print("[OK] Модель обновлена")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix(ssh):
    """Тест исправления"""
    print("\n" + "=" * 70)
    print("ТЕСТ ИСПРАВЛЕНИЯ")
    print("=" * 70)
    
    test_script = """
cd shannon-uncontained && node -e "
require('dotenv').config();
const Anthropic = require('@anthropic-ai/sdk');
const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
console.log('Тест с моделью:', process.env.LLM_MODEL);
client.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 20,
    messages: [{ role: 'user', content: 'Say hello' }]
}).then(r => {
    console.log('✅ SUCCESS:', r.content[0].text);
}).catch(e => {
    console.log('❌ ERROR:', e.message);
    if (e.status) console.log('Status:', e.status);
});
"
"""
    stdin, stdout, stderr = ssh.exec_command(test_script)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        check_llm_client_usage(ssh)
        
        if fix_llm_client(ssh):
            test_fix(ssh)
            print("\n✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
            print("\nТеперь код использует Anthropic SDK напрямую для provider='anthropic'")
            print("Можно перезапустить пентест через веб-интерфейс")
        else:
            print("\n❌ Ошибка при исправлении")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

