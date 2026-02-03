#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание и анализ результатов пентеста
"""
import paramiko
import sys
import os
import json
from pathlib import Path
from datetime import datetime

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

def find_latest_pentest(ssh):
    """Поиск последнего пентеста"""
    print("=" * 70)
    print("ПОИСК ПОСЛЕДНЕГО ПЕНТЕСТА")
    print("=" * 70)
    
    # Находим последний execution-log.json
    stdin, stdout, stderr = ssh.exec_command("find shannon-uncontained/test-output -name 'execution-log.json' -type f 2>/dev/null | xargs ls -t 2>/dev/null | head -1")
    last_log = stdout.read().decode('utf-8').strip()
    
    if not last_log:
        print("❌ Последний пентест не найден")
        return None
    
    # Получаем директорию пентеста
    pentest_dir = os.path.dirname(last_log)
    print(f"\n✅ Найден последний пентест:")
    print(f"   Директория: {pentest_dir}")
    print(f"   Лог: {last_log}")
    
    # Получаем информацию о времени
    stdin, stdout, stderr = ssh.exec_command(f"stat -c '%y' '{last_log}' 2>/dev/null || stat -f '%Sm' '{last_log}' 2>/dev/null")
    mod_time = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"   Время: {mod_time}")
    
    return pentest_dir

def download_pentest_results(ssh, pentest_dir):
    """Скачивание результатов пентеста"""
    print("\n" + "=" * 70)
    print("СКАЧИВАНИЕ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    
    # Создаем локальную директорию с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_dir = Path(f"pentest_results_{timestamp}")
    local_dir.mkdir(exist_ok=True)
    
    print(f"\nЛокальная директория: {local_dir.absolute()}")
    
    # Файлы для скачивания
    files_to_download = [
        "execution-log.json",
        "world-model.json",
        "README.md",
        "API.md",
        "ARCHITECTURE.md",
        "EVIDENCE.md",
        "manifest.json",
        "package.json",
        "openapi.json"
    ]
    
    sftp = ssh.open_sftp()
    
    downloaded = []
    for filename in files_to_download:
        remote_path = f"{pentest_dir}/{filename}"
        local_path = local_dir / filename
        
        try:
            sftp.get(remote_path, str(local_path))
            print(f"✅ {filename}")
            downloaded.append(filename)
        except Exception as e:
            if "No such file" not in str(e):
                print(f"⚠️  {filename}: {e}")
    
    # Скачиваем все JSON файлы
    print("\n--- Скачивание дополнительных файлов ---")
    stdin, stdout, stderr = ssh.exec_command(f"find '{pentest_dir}' -type f \\( -name '*.json' -o -name '*.md' -o -name '*.js' \\) 2>/dev/null | head -20")
    all_files = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    
    for file_path in all_files:
        if not file_path:
            continue
        filename = os.path.basename(file_path)
        local_path = local_dir / filename
        
        # Пропускаем если уже скачали
        if filename in downloaded:
            continue
        
        try:
            sftp.get(file_path, str(local_path))
            print(f"✅ {filename}")
        except Exception as e:
            print(f"⚠️  {filename}: {e}")
    
    sftp.close()
    
    print(f"\n✅ Файлы скачаны в: {local_dir.absolute()}")
    return local_dir

def analyze_results(local_dir):
    """Анализ результатов пентеста"""
    print("\n" + "=" * 70)
    print("АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("=" * 70)
    
    analysis = {}
    
    # Анализ execution-log.json
    execution_log = local_dir / "execution-log.json"
    if execution_log.exists():
        print("\n1. Execution Log:")
        with open(execution_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        total_agents = len(log_data)
        successful = sum(1 for a in log_data if a.get('success', False))
        failed = total_agents - successful
        
        agents_with_tokens = [a for a in log_data if a.get('summary', {}).get('tokens_used', 0) > 0]
        total_tokens = sum(a.get('summary', {}).get('tokens_used', 0) for a in log_data)
        
        total_duration = sum(a.get('summary', {}).get('duration_ms', 0) for a in log_data)
        
        analysis['execution'] = {
            'total_agents': total_agents,
            'successful': successful,
            'failed': failed,
            'agents_with_llm': len(agents_with_tokens),
            'total_tokens': total_tokens,
            'total_duration_ms': total_duration,
            'total_duration_sec': total_duration / 1000
        }
        
        print(f"   Всего агентов: {total_agents}")
        print(f"   Успешных: {successful}")
        print(f"   Неудачных: {failed}")
        print(f"   Агентов с LLM: {len(agents_with_tokens)}")
        print(f"   Всего токенов: {total_tokens:,}")
        print(f"   Общее время: {total_duration/1000:.1f} секунд ({total_duration/60000:.1f} минут)")
        
        # Агенты с токенами
        if agents_with_tokens:
            print(f"\n   Агенты использовавшие LLM:")
            for agent in agents_with_tokens[:10]:
                name = agent.get('agent', 'unknown')
                tokens = agent.get('summary', {}).get('tokens_used', 0)
                print(f"     - {name}: {tokens:,} токенов")
    
    # Анализ world-model.json
    world_model = local_dir / "world-model.json"
    if world_model.exists():
        print("\n2. World Model:")
        with open(world_model, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        entities_count = len(model_data.get('entities', []))
        claims_count = len(model_data.get('claims', []))
        
        analysis['world_model'] = {
            'entities': entities_count,
            'claims': claims_count
        }
        
        print(f"   Entities: {entities_count}")
        print(f"   Claims: {claims_count}")
    
    # Анализ документации
    print("\n3. Документация:")
    docs = ['README.md', 'API.md', 'ARCHITECTURE.md', 'EVIDENCE.md']
    for doc in docs:
        doc_path = local_dir / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"   ✅ {doc}: {size:,} байт")
        else:
            print(f"   ⚠️  {doc}: не найден")
    
    return analysis

def create_report(local_dir, analysis):
    """Создание отчета"""
    report_path = local_dir / "ANALYSIS_REPORT.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# ОТЧЕТ О РЕЗУЛЬТАТАХ ПЕНТЕСТА\n\n")
        f.write(f"**Дата анализа**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if 'execution' in analysis:
            exec_data = analysis['execution']
            f.write("## Статистика выполнения\n\n")
            f.write(f"- **Всего агентов**: {exec_data['total_agents']}\n")
            f.write(f"- **Успешных**: {exec_data['successful']}\n")
            f.write(f"- **Неудачных**: {exec_data['failed']}\n")
            f.write(f"- **Агентов с LLM**: {exec_data['agents_with_llm']}\n")
            f.write(f"- **Всего токенов**: {exec_data['total_tokens']:,}\n")
            f.write(f"- **Общее время**: {exec_data['total_duration_sec']:.1f} секунд ({exec_data['total_duration_sec']/60:.1f} минут)\n\n")
        
        if 'world_model' in analysis:
            model_data = analysis['world_model']
            f.write("## World Model\n\n")
            f.write(f"- **Entities**: {model_data['entities']}\n")
            f.write(f"- **Claims**: {model_data['claims']}\n\n")
        
        f.write("## Файлы результатов\n\n")
        f.write(f"Все файлы сохранены в: `{local_dir.absolute()}`\n\n")
        f.write("### Основные файлы:\n")
        f.write("- `execution-log.json` - логи выполнения всех агентов\n")
        f.write("- `world-model.json` - модель мира с entities и claims\n")
        f.write("- `README.md` - основная документация\n")
        f.write("- `API.md` - API документация\n")
        f.write("- `ARCHITECTURE.md` - архитектурная документация\n")
        f.write("- `EVIDENCE.md` - карта доказательств\n")
    
    print(f"\n✅ Отчет создан: {report_path}")

def main():
    ssh = connect_to_server()
    if not ssh:
        return
    
    try:
        pentest_dir = find_latest_pentest(ssh)
        if not pentest_dir:
            return
        
        local_dir = download_pentest_results(ssh, pentest_dir)
        analysis = analyze_results(local_dir)
        create_report(local_dir, analysis)
        
        print("\n" + "=" * 70)
        print("ГОТОВО!")
        print("=" * 70)
        print(f"\n📁 Результаты сохранены в: {local_dir.absolute()}")
        print(f"📄 Отчет: {local_dir.absolute() / 'ANALYSIS_REPORT.md'}")
        
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

