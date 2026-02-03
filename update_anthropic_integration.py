#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление интеграции Anthropic SDK в llm-client.js
"""
import paramiko
import sys
import re

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

def update_query_function(ssh):
    """Обновление функции query для поддержки Anthropic"""
    print("--- Обновление функции query для Anthropic ---")
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Проверяем, есть ли уже обработка Anthropic в query
        if "config.provider === 'anthropic'" in content:
            print("[INFO] Anthropic уже интегрирован в query функцию")
            sftp.close()
            return True
        
        # Находим начало функции query
        query_start = content.find("export async function* query({ prompt, options }) {")
        if query_start == -1:
            print("[ERROR] Не найдена функция query")
            sftp.close()
            return False
        
        # Находим место после getProviderConfig()
        config_line = content.find("const config = getProviderConfig();", query_start)
        if config_line == -1:
            print("[ERROR] Не найден вызов getProviderConfig()")
            sftp.close()
            return False
        
        # Находим место после console.log с моделью
        log_line = content.find("console.log(`🤖 Using", config_line)
        if log_line == -1:
            print("[ERROR] Не найден console.log с моделью")
            sftp.close()
            return False
        
        # Находим место где создается OpenAI client
        client_line = content.find("const client = new OpenAI({", log_line)
        if client_line == -1:
            print("[ERROR] Не найден создание OpenAI client")
            sftp.close()
            return False
        
        # Вставляем код для Anthropic перед созданием OpenAI client
        anthropic_code = """
    // Initialize Anthropic client if provider is anthropic
    let anthropicClient = null;
    if (config.provider === 'anthropic') {
        anthropicClient = new Anthropic({
            apiKey: config.apiKey
        });
    }
    
    // For Anthropic, we'll use a different approach in the loop
"""
        
        # Вставляем код перед созданием OpenAI client
        content = content[:client_line] + anthropic_code + "\n    " + content[client_line:]
        
        # Теперь нужно обновить цикл while для поддержки Anthropic
        # Находим цикл while
        while_start = content.find("while (keepGoing && turn < maxTurns) {", client_line)
        if while_start == -1:
            print("[WARNING] Не найден цикл while, возможно структура другая")
        else:
            # Находим место где создается response
            response_line = content.find("const response = await client.chat.completions.create({", while_start)
            if response_line != -1:
                # Заменяем на условную логику для Anthropic
                old_response_code = """            const response = await client.chat.completions.create({
                messages: messagesToSend,
                model: modelName,
                tools: tools,
                tool_choice: "auto"
            });"""
                
                new_response_code = """            let response;
            if (config.provider === 'anthropic') {
                // Anthropic API uses different format
                // Convert messages format for Anthropic
                const anthropicMessages = messagesToSend.map(msg => {
                    if (msg.role === 'system') {
                        return { role: 'user', content: msg.content };
                    }
                    return {
                        role: msg.role === 'assistant' ? 'assistant' : 'user',
                        content: typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)
                    };
                });
                
                // Anthropic doesn't support tools in the same way, so we'll use messages API
                response = await anthropicClient.messages.create({
                    model: modelName,
                    max_tokens: 4096,
                    messages: anthropicMessages.filter(m => m.role !== 'system'),
                    system: messagesToSend.find(m => m.role === 'system')?.content || ''
                });
                
                // Convert Anthropic response to OpenAI format
                response = {
                    choices: [{
                        message: {
                            content: response.content[0].text,
                            role: 'assistant'
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
                
                if old_response_code in content:
                    content = content.replace(old_response_code, new_response_code)
                    print("[OK] Обновлен код создания response для Anthropic")
                else:
                    print("[WARNING] Не найден точный паттерн для замены response")
        
        # Сохраняем обновленный файл
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        print("[OK] Функция query обновлена для поддержки Anthropic")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при обновлении: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== Обновление интеграции Anthropic SDK ===\n")
    
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        update_query_function(ssh)
        print("\n=== Обновление завершено! ===")
        print("Теперь Claude API будет использоваться через Anthropic SDK")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

