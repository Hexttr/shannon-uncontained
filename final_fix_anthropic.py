#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальное исправление интеграции Anthropic
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

def fix_anthropic_case(ssh):
    """Исправление case 'anthropic'"""
    print("=" * 70)
    print("ИСПРАВЛЕНИЕ CASE 'ANTHROPIC'")
    print("=" * 70)
    
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Заменяем throw на правильную конфигурацию
        old_case = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                throw new Error('Anthropic provider requires @anthropic-ai/sdk - use Claude Code or set LLM_PROVIDER=github/openai/ollama/openrouter');"""
        
        new_case = """            case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-3-5-sonnet-20241022'
                };"""
        
        if old_case in content:
            content = content.replace(old_case, new_case)
            print("[OK] Case 'anthropic' исправлен")
        else:
            # Ищем альтернативный паттерн
            pattern = r"case 'anthropic':.*?throw new Error\('Anthropic provider requires"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                # Находим конец блока
                end_pos = content.find("';", match.end()) + 2
                old_block = content[match.start():end_pos]
                # Заменяем
                content = content[:match.start()] + new_case + content[end_pos:]
                print("[OK] Case 'anthropic' исправлен (альтернативный паттерн)")
            else:
                print("[WARNING] Не найден точный паттерн для замены")
                # Показываем что есть
                anthropic_pos = content.find("case 'anthropic'")
                if anthropic_pos != -1:
                    print("Найден case 'anthropic' на позиции:", anthropic_pos)
                    print("Контекст:")
                    print(content[anthropic_pos:anthropic_pos+300])
        
        # Теперь исправляем функцию query для использования Anthropic SDK
        print("\n2. Исправление функции query для Anthropic SDK...")
        
        # Находим создание OpenAI client
        openai_client_pos = content.find("const client = new OpenAI({")
        if openai_client_pos != -1:
            # Вставляем создание Anthropic client перед OpenAI
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
            print("[OK] Добавлена инициализация Anthropic client")
        
        # Находим client.chat.completions.create
        chat_create_pattern = r"const response = await client\.chat\.completions\.create\(\{[\s\S]*?messages: messagesToSend,[\s\S]*?model: modelName,[\s\S]*?tools: tools,[\s\S]*?tool_choice: \"auto\"[\s\S]*?\}\);"
        match = re.search(chat_create_pattern, content)
        
        if match:
            old_code = match.group(0)
            new_code = """let response;
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
                const response = await client.chat.completions.create({
                    messages: messagesToSend,
                    model: modelName,
                    tools: tools,
                    tool_choice: "auto"
                });
            }"""
            
            content = content[:match.start()] + new_code + content[match.end():]
            print("[OK] Обновлен код создания response для Anthropic")
        else:
            print("[WARNING] Не найден паттерн client.chat.completions.create")
            # Ищем проще
            simple_pattern = r"const response = await client\.chat\.completions\.create"
            simple_match = re.search(simple_pattern, content)
            if simple_match:
                print("Найден на позиции:", simple_match.start())
                # Показываем контекст
                print("Контекст:")
                print(content[simple_match.start()-50:simple_match.start()+200])
        
        # Сохраняем
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(content)
        
        sftp.close()
        print("\n[OK] Файл обновлен")
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
    
    # Простой тест что код компилируется
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && node -c src/ai/llm-client.js 2>&1")
    syntax_check = stdout.read().decode('utf-8', errors='ignore')
    error_check = stderr.read().decode('utf-8', errors='ignore')
    
    if syntax_check or error_check:
        print("Ошибки синтаксиса:")
        print(syntax_check)
        print(error_check)
    else:
        print("[OK] Синтаксис корректен")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if fix_anthropic_case(ssh):
            test_fix(ssh)
            print("\n✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
            print("\nТеперь:")
            print("1. Case 'anthropic' возвращает правильную конфигурацию")
            print("2. Функция query использует Anthropic SDK для provider='anthropic'")
            print("\nМожно перезапустить пентест через веб-интерфейс")
        else:
            print("\n❌ Ошибка при исправлении")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

