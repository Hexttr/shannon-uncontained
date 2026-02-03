#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка и исправление структуры функции
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

def restore_from_backup(ssh):
    """Восстановление из резервной копии или исправление вручную"""
    print("=" * 70)
    print("ВОССТАНОВЛЕНИЕ ФАЙЛА")
    print("=" * 70)
    
    # Проверяем есть ли backup
    stdin, stdout, stderr = ssh.exec_command("ls -la shannon-uncontained/src/ai/llm-client.js* 2>/dev/null")
    backups = stdout.read().decode('utf-8', errors='ignore')
    print("Доступные файлы:")
    print(backups)
    
    # Скачиваем оригинальный файл с сервера заново
    print("\nСкачивание оригинального файла...")
    stdin, stdout, stderr = ssh.exec_command("cd shannon-uncontained && git checkout src/ai/llm-client.js 2>&1 || echo 'Git не доступен'")
    git_result = stdout.read().decode('utf-8', errors='ignore')
    print(git_result)
    
    # Если git не помог, используем локальную версию
    if "Git не доступен" in git_result or "error" in git_result.lower():
        print("\nИспользуем локальную версию из src/ai/llm-client.js...")
        try:
            with open('src/ai/llm-client.js', 'r', encoding='utf-8') as f:
                local_content = f.read()
            
            sftp = ssh.open_sftp()
            with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
                f.write(local_content)
            sftp.close()
            print("[OK] Восстановлен из локальной версии")
        except Exception as e:
            print(f"[ERROR] Не удалось восстановить: {e}")
            return False
    
    # Теперь правильно исправляем только case 'anthropic'
    print("\nИсправление только case 'anthropic'...")
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Ищем и заменяем только case 'anthropic'
        import re
        pattern = r"case 'anthropic':\s*if \(!anthropicKey\) throw new Error\('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set'\);\s*throw new Error\('Anthropic provider requires"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # Находим конец throw
            end_pos = content.find("';", match.end()) + 2
            # Заменяем
            new_case = """case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-3-5-sonnet-20241022'
                };"""
            
            content = content[:match.start()] + new_case + content[end_pos:]
            print("[OK] Case 'anthropic' исправлен")
        else:
            print("[INFO] Case 'anthropic' уже исправлен или имеет другой формат")
        
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
            print("Ошибки:")
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

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        if restore_from_backup(ssh):
            print("\n✅ ФАЙЛ ВОССТАНОВЛЕН И ИСПРАВЛЕН!")
            print("\nТеперь case 'anthropic' возвращает правильную конфигурацию")
            print("НО: функция query все еще использует OpenAI SDK")
            print("Это означает что Anthropic будет работать через OpenAI-совместимый прокси или нужно использовать другой подход")
        else:
            print("\n❌ Ошибка при восстановлении")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

