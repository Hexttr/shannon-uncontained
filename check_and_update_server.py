#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка и обновление файлов на сервере
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

def check_imports(ssh):
    """Проверка импортов на сервере"""
    print("=" * 70)
    print("ПРОВЕРКА ИМПОРТОВ НА СЕРВЕРЕ")
    print("=" * 70)
    
    # Проверяем импорт Anthropic
    stdin, stdout, stderr = ssh.exec_command("head -10 shannon-uncontained/src/ai/llm-client.js | grep -i anthropic")
    anthropic_import = stdout.read().decode('utf-8', errors='ignore')
    
    if anthropic_import:
        print("✅ Импорт Anthropic найден:")
        print(anthropic_import)
        return True
    else:
        print("❌ Импорт Anthropic НЕ найден!")
        return False

def update_server_files(ssh):
    """Обновление файлов на сервере"""
    print("\n" + "=" * 70)
    print("ОБНОВЛЕНИЕ ФАЙЛОВ НА СЕРВЕРЕ")
    print("=" * 70)
    
    try:
        # Читаем локальный файл
        with open('src/ai/llm-client.js', 'r', encoding='utf-8') as f:
            local_content = f.read()
        
        # Проверяем что локальный файл имеет импорт
        if "import Anthropic" not in local_content:
            print("[ERROR] Локальный файл не имеет импорта Anthropic!")
            return False
        
        # Загружаем на сервер
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'w') as f:
            f.write(local_content)
        sftp.close()
        
        print("[OK] llm-client.js обновлен на сервере")
        
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

def test_query_after_update(ssh):
    """Тест query после обновления"""
    print("\n" + "=" * 70)
    print("ТЕСТ QUERY ПОСЛЕ ОБНОВЛЕНИЯ")
    print("=" * 70)
    
    test_script = """
cd shannon-uncontained && timeout 10 node -e "
require('dotenv').config();
import('./src/ai/llm-client.js').then(async m => {
    try {
        const gen = m.query({ 
            prompt: 'Say hello', 
            options: { cwd: '/tmp', maxTurns: 1 } 
        });
        const first = await gen.next();
        if (first.value?.type === 'assistant' && first.value?.message) {
            console.log('✅ SUCCESS - получен ответ:', first.value.message.content?.substring(0, 50));
        } else {
            console.log('⚠️ Неожиданный результат:', first.value?.type);
        }
    } catch(e) {
        console.log('❌ ERROR:', e.message);
        console.log(e.stack?.substring(0, 300));
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

def check_recent_execution(ssh):
    """Проверка последнего выполнения"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА ПОСЛЕДНЕГО ВЫПОЛНЕНИЯ")
    print("=" * 70)
    
    # Находим последний execution-log
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'execution-log.json' -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1")
    last_log = stdout.read().decode('utf-8').strip()
    
    if last_log:
        print(f"\nПоследний лог: {last_log}")
        
        # Проверяем время выполнения
        stdin, stdout, stderr = ssh.exec_command(f"cat '{last_log}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print(\"Всего агентов:\", len(d)); print(\"Общее время (мс):\", sum(a.get(\"summary\",{{}}).get(\"duration_ms\",0) for a in d)); print(\"С токенами:\", sum(1 for a in d if a.get(\"summary\",{{}}).get(\"tokens_used\",0)>0)); print(\"Без токенов:\", sum(1 for a in d if a.get(\"summary\",{{}}).get(\"tokens_used\",0)==0))'")
        stats = stdout.read().decode('utf-8', errors='ignore')
        print("\nСтатистика:")
        print(stats)
        
        # Проверяем есть ли ошибки
        error_check_cmd = f"cat '{last_log}' | python3 -c \"import json,sys; d=json.load(sys.stdin); errors=[a for a in d if not a.get('success',True)]; print('Ошибок:', len(errors)); [print(f'  - {{a.get(\\\"agent\\\")}}: {{a.get(\\\"error\\\",\\\"unknown\\\")}}') for a in errors[:5]]\""
        stdin, stdout, stderr = ssh.exec_command(error_check_cmd)
        errors = stdout.read().decode('utf-8', errors='ignore')
        if errors:
            print("\nОшибки:")
            print(errors)

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        has_import = check_imports(ssh)
        
        if not has_import:
            print("\n[ДЕЙСТВИЕ] Обновляю файлы на сервере...")
            if update_server_files(ssh):
                test_query_after_update(ssh)
            else:
                print("\n❌ Ошибка при обновлении файлов")
        else:
            print("\n✅ Файлы на сервере актуальны")
            test_query_after_update(ssh)
        
        check_recent_execution(ssh)
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

