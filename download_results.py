#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скачивание результатов пентеста с сервера
"""
import paramiko
import sys
import os
import json
from pathlib import Path

SERVER_IP = "72.56.79.153"
SERVER_USER = "root"
SERVER_PASS = "m8J@2_6whwza6U"

if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

def connect_server():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER_IP, username=SERVER_USER, password=SERVER_PASS, timeout=10)
    return ssh

def execute_command(ssh, command, timeout=300):
    try:
        stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        exit_status = stdout.channel.recv_exit_status()
        return exit_status == 0, output, error
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("DOWNLOADING PENTEST RESULTS")
    print("=" * 80)
    
    ssh = connect_server()
    PROJECT_PATH = "/root/shannon-uncontained"
    OUTPUT_DIR = f"{PROJECT_PATH}/test-output"
    
    # 1. Проверяем что результаты существуют
    print("\n1. CHECKING RESULTS DIRECTORY")
    print("-" * 80)
    
    success, output, error = execute_command(ssh, f"ls -la {OUTPUT_DIR} 2>&1")
    if success and 'total' in output:
        print(f"   OK: Results directory exists")
        print(f"   Contents:")
        print(output)
    else:
        # Проверяем другие возможные места
        print(f"   Checking alternative locations...")
        success2, output2, _ = execute_command(ssh, f"find {PROJECT_PATH} -name 'shannon-results' -type d 2>/dev/null | head -5")
        if success2 and output2.strip():
            OUTPUT_DIR = output2.strip().split('\n')[0]
            print(f"   Found results in: {OUTPUT_DIR}")
        else:
            print(f"   ERROR: Results directory not found")
            print(f"   Error: {error}")
            ssh.close()
            return
    
    # 2. Список всех файлов
    print("\n2. LISTING ALL FILES")
    print("-" * 80)
    
    success, file_list, _ = execute_command(ssh, f"find {OUTPUT_DIR} -type f 2>/dev/null | head -50")
    if success and file_list.strip():
        files = file_list.strip().split('\n')
        print(f"   Found {len(files)} files")
        for f in files[:20]:
            print(f"   - {f}")
        if len(files) > 20:
            print(f"   ... and {len(files) - 20} more files")
    else:
        print(f"   No files found")
    
    # 3. Создаем локальную папку
    local_dir = Path("pentest-results")
    local_dir.mkdir(exist_ok=True)
    print(f"\n3. CREATING LOCAL DIRECTORY")
    print("-" * 80)
    print(f"   Local directory: {local_dir.absolute()}")
    
    # 4. Скачиваем файлы через SFTP
    print(f"\n4. DOWNLOADING FILES")
    print("-" * 80)
    
    sftp = ssh.open_sftp()
    downloaded = 0
    
    def download_recursive(remote_path, local_path):
        nonlocal downloaded
        try:
            # Получаем список файлов и директорий
            items = sftp.listdir_attr(remote_path)
            
            for item in items:
                remote_item = f"{remote_path}/{item.filename}"
                local_item = local_path / item.filename
                
                if item.st_mode & 0o040000:  # Directory
                    local_item.mkdir(exist_ok=True)
                    download_recursive(remote_item, local_item)
                else:  # File
                    try:
                        sftp.get(remote_item, str(local_item))
                        downloaded += 1
                        if downloaded % 10 == 0:
                            print(f"   Downloaded {downloaded} files...")
                    except Exception as e:
                        print(f"   Warning: Could not download {remote_item}: {e}")
        except Exception as e:
            print(f"   Error accessing {remote_path}: {e}")
    
    try:
        download_recursive(OUTPUT_DIR, local_dir)
        print(f"   Total downloaded: {downloaded} files")
    except Exception as e:
        print(f"   Error during download: {e}")
    finally:
        sftp.close()
    
    # 5. Анализ результатов
    print(f"\n5. ANALYZING RESULTS")
    print("-" * 80)
    
    # Ищем JSON файлы с результатами
    json_files = list(local_dir.rglob("*.json"))
    report_files = list(local_dir.rglob("*report*"))
    evidence_files = list(local_dir.rglob("*evidence*"))
    vulnerability_files = list(local_dir.rglob("*vulnerability*"))
    model_files = list(local_dir.rglob("*model*"))
    
    print(f"   JSON files: {len(json_files)}")
    print(f"   Report files: {len(report_files)}")
    print(f"   Evidence files: {len(evidence_files)}")
    print(f"   Vulnerability files: {len(vulnerability_files)}")
    print(f"   Model files: {len(model_files)}")
    
    # Проверяем использование Ollama
    print(f"\n6. CHECKING OLLAMA USAGE")
    print("-" * 80)
    
    ollama_used = False
    for json_file in json_files[:10]:  # Проверяем первые 10 JSON файлов
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'ollama' in content.lower() or 'codellama' in content.lower():
                    ollama_used = True
                    print(f"   Found Ollama reference in: {json_file.name}")
                    break
        except:
            pass
    
    if not ollama_used:
        # Проверяем логи
        log_files = list(local_dir.rglob("*.log"))
        for log_file in log_files[:5]:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'ollama' in content.lower() or 'codellama' in content.lower():
                        ollama_used = True
                        print(f"   Found Ollama reference in log: {log_file.name}")
                        break
            except:
                pass
    
    if ollama_used:
        print(f"   OK: Ollama was used")
    else:
        print(f"   WARNING: No Ollama references found")
    
    # Проверяем уязвимости
    print(f"\n7. CHECKING FOR VULNERABILITIES")
    print("-" * 80)
    
    vulnerabilities_found = []
    vuln_keywords = ['vulnerability', 'vuln', 'cve', 'exploit', 'xss', 'sql injection', 'rce', 'lfi', 'rfi']
    
    for json_file in json_files[:20]:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Рекурсивно ищем уязвимости
                def find_vulns(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if any(keyword in str(k).lower() for keyword in vuln_keywords):
                                vulnerabilities_found.append(f"{json_file.name}: {k}")
                            find_vulns(v, f"{path}.{k}")
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            find_vulns(item, f"{path}[{i}]")
                    elif isinstance(obj, str):
                        if any(keyword in obj.lower() for keyword in vuln_keywords):
                            vulnerabilities_found.append(f"{json_file.name}: {obj[:100]}")
                find_vulns(data)
        except:
            pass
    
    # Также проверяем текстовые файлы
    txt_files = list(local_dir.rglob("*.txt"))
    for txt_file in txt_files[:10]:
        try:
            with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
                if any(keyword in content for keyword in vuln_keywords):
                    vulnerabilities_found.append(f"{txt_file.name}: Contains vulnerability keywords")
        except:
            pass
    
    if vulnerabilities_found:
        print(f"   Found {len(vulnerabilities_found)} potential vulnerability references:")
        for vuln in vulnerabilities_found[:10]:
            print(f"   - {vuln}")
        if len(vulnerabilities_found) > 10:
            print(f"   ... and {len(vulnerabilities_found) - 10} more")
    else:
        print(f"   No obvious vulnerability references found")
    
    ssh.close()
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
Results location: {local_dir.absolute()}
Files downloaded: {downloaded}
JSON files: {len(json_files)}
Ollama used: {'Yes' if ollama_used else 'Unknown'}
Vulnerabilities found: {len(vulnerabilities_found)} references

Key files to check:
- JSON files: {', '.join([f.name for f in json_files[:5]])}
- Reports: {', '.join([f.name for f in report_files[:5]])}
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

