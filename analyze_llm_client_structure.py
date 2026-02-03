#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ структуры llm-client.js на сервере
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

def download_and_analyze(ssh):
    """Скачивание и анализ файла"""
    print("=" * 70)
    print("АНАЛИЗ LLM-CLIENT.JS")
    print("=" * 70)
    
    # Скачиваем файл
    try:
        sftp = ssh.open_sftp()
        with sftp.open('shannon-uncontained/src/ai/llm-client.js', 'r') as f:
            content = f.read().decode('utf-8')
        
        # Анализируем структуру
        print("\n1. Поиск функции query:")
        query_pos = content.find("export async function* query")
        if query_pos != -1:
            print(f"   Найдена на позиции: {query_pos}")
            print(f"   Следующие 200 символов:")
            print(content[query_pos:query_pos+200])
        else:
            print("   Не найдена")
        
        print("\n2. Поиск создания клиентов:")
        openai_pos = content.find("new OpenAI")
        anthropic_pos = content.find("new Anthropic")
        print(f"   new OpenAI: {'Найдено' if openai_pos != -1 else 'Не найдено'}")
        print(f"   new Anthropic: {'Найдено' if anthropic_pos != -1 else 'Не найдено'}")
        
        if openai_pos != -1:
            print(f"\n   Контекст new OpenAI:")
            print(content[max(0, openai_pos-50):openai_pos+100])
        
        print("\n3. Поиск client.chat.completions.create:")
        chat_pos = content.find("client.chat.completions.create")
        if chat_pos != -1:
            print(f"   Найдено на позиции: {chat_pos}")
            print(f"   Контекст:")
            print(content[max(0, chat_pos-100):chat_pos+200])
        else:
            print("   Не найдено")
        
        print("\n4. Проверка использования config.provider:")
        provider_checks = content.count("config.provider")
        print(f"   Упоминаний config.provider: {provider_checks}")
        
        if provider_checks > 0:
            import re
            matches = list(re.finditer(r"config\.provider\s*===\s*['\"]anthropic['\"]", content))
            print(f"   Проверок на 'anthropic': {len(matches)}")
            for i, match in enumerate(matches[:3]):
                print(f"\n   Проверка {i+1}:")
                print(content[max(0, match.start()-50):match.end()+100])
        
        # Сохраняем локально для анализа
        with open('llm-client-server.js', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n[OK] Файл сохранен локально как llm-client-server.js")
        
        sftp.close()
        return content
        
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        content = download_and_analyze(ssh)
        if content:
            print("\n" + "=" * 70)
            print("АНАЛИЗ ЗАВЕРШЕН")
            print("=" * 70)
            print("\nФайл сохранен для дальнейшего анализа")
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

