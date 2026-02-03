#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Обновление llm-client.js с использованием готовой реализации Anthropic из LSGv2
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
    """Обновление функции query для использования Anthropic SDK"""
    print("=" * 70)
    print("ОБНОВЛЕНИЕ ФУНКЦИИ QUERY ДЛЯ ANTHROPIC")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Находим функцию query
        query_start = content.find("export async function* query({ prompt, options }) {")
        if query_start == -1:
            print("[ERROR] Функция query не найдена")
            sftp.close()
            return False
        
        # Находим место после getProviderConfig
        config_pos = content.find("const config = getProviderConfig();", query_start)
        if config_pos == -1:
            print("[ERROR] getProviderConfig не найден")
            sftp.close()
            return False
        
        # Находим создание OpenAI client
        openai_client_pos = content.find("const client = new OpenAI({", config_pos)
        if openai_client_pos == -1:
            print("[ERROR] Создание OpenAI client не найдено")
            sftp.close()
            return False
        
        # Вставляем создание Anthropic client перед OpenAI client
        anthropic_init = """
    // Initialize Anthropic client if provider is anthropic
    let anthropicClient = null;
    if (config.provider === 'anthropic') {
        anthropicClient = new Anthropic({
            apiKey: config.apiKey
        });
    }
    
"""
        content = content[:openai_client_pos] + anthropic_init + "    " + content[openai_client_pos:]
        
        # Обновляем позиции после вставки
        openai_client_pos += len(anthropic_init)
        
        # Находим место где делается запрос к API
        # Ищем цикл while и внутри него client.chat.completions.create
        while_pos = content.find("while (keepGoing && turn < maxTurns) {", openai_client_pos)
        if while_pos == -1:
            print("[WARNING] Цикл while не найден, ищем по-другому...")
            # Ищем напрямую client.chat.completions.create
            chat_create_pos = content.find("const response = await client.chat.completions.create({", openai_client_pos)
            if chat_create_pos != -1:
                # Находим конец этого блока
                end_pos = content.find("});", chat_create_pos) + 3
                old_code = content[chat_create_pos:end_pos]
                
                new_code = """let response;
            if (config.provider === 'anthropic') {
                // Use Anthropic SDK directly (based on LSGv2 implementation)
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
                const response = await client.chat.completions.create({
                    messages: messagesToSend,
                    model: modelName,
                    tools: tools,
                    tool_choice: "auto"
                });
            }"""
                
                content = content[:chat_create_pos] + new_code + content[end_pos:]
                print("[OK] Обновлен код создания response для Anthropic")
        else:
            # Ищем внутри цикла while
            chat_create_pos = content.find("const response = await client.chat.completions.create({", while_pos)
            if chat_create_pos != -1:
                # Находим конец блока
                end_pos = content.find("});", chat_create_pos) + 3
                old_code = content[chat_create_pos:end_pos]
                
                new_code = """let response;
            if (config.provider === 'anthropic') {
                // Use Anthropic SDK directly (based on LSGv2 implementation)
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
                
                content = content[:chat_create_pos] + new_code + content[end_pos:]
                print("[OK] Обновлен код создания response для Anthropic (в цикле while)")
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        
        # Проверяем синтаксис
        print("\nПроверка синтаксиса...")
        stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c src/ai/llm-client.js 2>&1")
        syntax_check = stdout.read().decode('utf-8', errors='ignore')
        error_check = stderr.read().decode('utf-8', errors='ignore')
        
        if syntax_check or error_check:
            print("Ошибки синтаксиса:")
            print(syntax_check)
            print(error_check)
            return False
        else:
            print("[OK] Синтаксис корректен")
            return True
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_model_to_4_5(ssh):
    """Обновление модели на Claude 4.5 Sonnet"""
    print("\n" + "=" * 70)
    print("ОБНОВЛЕНИЕ МОДЕЛИ НА CLAUDE 4.5 SONNET")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        
        # Обновляем .env
        with sftp.open('shannon-uncontained/.env', 'r') as f:
            env_content = f.read().decode('utf-8')
        
        env_content = re.sub(
            r'LLM_MODEL=.*',
            'LLM_MODEL=claude-sonnet-4-5',
            env_content
        )
        
        with sftp.open('shannon-uncontained/.env', 'w') as f:
            f.write(env_content)
        print("[OK] .env обновлен: LLM_MODEL=claude-sonnet-4-5")
        
        # Обновляем llm-client.js дефолтную модель
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            llm_content = f.read().decode('utf-8')
        
        llm_content = re.sub(
            r"model: modelOverride \|\| 'claude-[^']+'",
            "model: modelOverride || 'claude-sonnet-4-5'",
            llm_content
        )
        
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(llm_content)
        print("[OK] llm-client.js обновлен")
        
        sftp.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        return False

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        # Обновляем модель
        update_model_to_4_5(ssh)
        
        # Обновляем функцию query
        if update_query_function(ssh):
            print("\n✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
            print("\nТеперь:")
            print("1. Модель обновлена на claude-sonnet-4-5")
            print("2. Функция query использует Anthropic SDK напрямую для provider='anthropic'")
            print("3. Реализация основана на готовом коде из LSGv2")
            print("\nМожно перезапустить пентест через веб-интерфейс!")
        else:
            print("\n⚠️ Ошибка при обновлении функции query")
            print("Но модель обновлена на claude-sonnet-4-5")
            
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

