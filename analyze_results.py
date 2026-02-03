#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Детальный анализ результатов пентеста
"""
import json
import os
from pathlib import Path
import re

def analyze_file(file_path):
    """Анализ конкретного файла"""
    try:
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        return None

def main():
    print("=" * 80)
    print("DETAILED ANALYSIS OF PENTEST RESULTS")
    print("=" * 80)
    
    results_dir = Path("pentest-results")
    if not results_dir.exists():
        print(f"ERROR: Results directory not found: {results_dir}")
        return
    
    # 1. Анализ execution-log.json
    print("\n1. EXECUTION LOG ANALYSIS")
    print("-" * 80)
    
    exec_log = results_dir / "repos" / "tcell.tj" / "execution-log.json"
    if exec_log.exists():
        log_data = analyze_file(exec_log)
        if log_data:
            print(f"   File: {exec_log.name}")
            
            # Проверяем использование Ollama
            log_str = json.dumps(log_data).lower()
            ollama_used = 'ollama' in log_str or 'codellama' in log_str
            print(f"   Ollama used: {'YES' if ollama_used else 'NO'}")
            
            # Агенты которые выполнялись
            agents = set()
            if isinstance(log_data, dict):
                for key, value in log_data.items():
                    if 'agent' in key.lower() or 'Agent' in str(value):
                        agents.add(key)
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if 'agent' in str(k).lower() or 'Agent' in str(v):
                                agents.add(str(k))
            
            if agents:
                print(f"   Agents found: {len(agents)}")
                for agent in list(agents)[:10]:
                    print(f"     - {agent}")
            
            # Проверяем ошибки
            errors = []
            if isinstance(log_data, dict):
                def find_errors(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if 'error' in str(k).lower() or 'fail' in str(k).lower():
                                errors.append(f"{path}.{k}: {str(v)[:100]}")
                            find_errors(v, f"{path}.{k}")
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj):
                            find_errors(item, f"{path}[{i}]")
                    elif isinstance(obj, str):
                        if 'error' in obj.lower() or 'fail' in obj.lower():
                            errors.append(f"{path}: {obj[:100]}")
                find_errors(log_data)
            
            if errors:
                print(f"   Errors found: {len(errors)}")
                for err in errors[:5]:
                    print(f"     - {err}")
    else:
        print(f"   File not found: {exec_log}")
    
    # 2. Анализ world-model.json
    print("\n2. WORLD MODEL ANALYSIS")
    print("-" * 80)
    
    world_model = results_dir / "repos" / "tcell.tj" / "world-model.json"
    if world_model.exists():
        model_data = analyze_file(world_model)
        if model_data:
            print(f"   File: {world_model.name}")
            
            if isinstance(model_data, dict):
                # Подсчитываем сущности
                entities = {}
                def count_entities(obj, depth=0):
                    if depth > 5:
                        return
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if k not in ['_id', 'id', 'type']:
                                entities[k] = entities.get(k, 0) + 1
                            count_entities(v, depth+1)
                    elif isinstance(obj, list):
                        for item in obj:
                            count_entities(item, depth+1)
                
                count_entities(model_data)
                print(f"   Entity types found: {len(entities)}")
                for entity_type, count in sorted(entities.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"     - {entity_type}: {count}")
    else:
        print(f"   File not found: {world_model}")
    
    # 3. Анализ EVIDENCE.md
    print("\n3. EVIDENCE ANALYSIS")
    print("-" * 80)
    
    evidence_file = results_dir / "repos" / "tcell.tj" / "EVIDENCE.md"
    if evidence_file.exists():
        evidence = analyze_file(evidence_file)
        if evidence:
            print(f"   File: {evidence_file.name}")
            print(f"   Size: {len(evidence)} characters")
            
            # Ищем упоминания уязвимостей
            vuln_patterns = [
                r'CVE-\d{4}-\d+',
                r'XSS',
                r'SQL.?injection',
                r'RCE',
                r'LFI',
                r'RFI',
                r'CSRF',
                r'SSRF',
                r'authentication.*bypass',
                r'authorization.*bypass',
                r'path.*traversal',
                r'command.*injection',
            ]
            
            found_vulns = []
            for pattern in vuln_patterns:
                matches = re.findall(pattern, evidence, re.IGNORECASE)
                if matches:
                    found_vulns.extend(matches)
            
            if found_vulns:
                print(f"   Vulnerability patterns found: {len(set(found_vulns))}")
                for vuln in list(set(found_vulns))[:10]:
                    print(f"     - {vuln}")
            else:
                print(f"   No obvious vulnerability patterns found")
            
            # Показываем первые строки
            lines = evidence.split('\n')[:20]
            print(f"\n   First 20 lines:")
            for i, line in enumerate(lines, 1):
                if line.strip():
                    print(f"     {i}: {line[:80]}")
    else:
        print(f"   File not found: {evidence_file}")
    
    # 4. Анализ openapi.json
    print("\n4. API DISCOVERY ANALYSIS")
    print("-" * 80)
    
    openapi_file = results_dir / "repos" / "tcell.tj" / "openapi.json"
    if openapi_file.exists():
        api_data = analyze_file(openapi_file)
        if api_data:
            print(f"   File: {openapi_file.name}")
            
            if isinstance(api_data, dict):
                paths = api_data.get('paths', {})
                print(f"   API endpoints discovered: {len(paths)}")
                
                # Группируем по методам
                methods = {}
                for path, methods_dict in paths.items():
                    if isinstance(methods_dict, dict):
                        for method in methods_dict.keys():
                            methods[method.upper()] = methods.get(method.upper(), 0) + 1
                
                print(f"   HTTP methods:")
                for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
                    print(f"     - {method}: {count}")
                
                # Показываем примеры endpoints
                print(f"\n   Sample endpoints:")
                for i, path in enumerate(list(paths.keys())[:10]):
                    print(f"     - {path}")
    else:
        print(f"   File not found: {openapi_file}")
    
    # 5. Анализ security.test.js
    print("\n5. SECURITY TESTS ANALYSIS")
    print("-" * 80)
    
    security_test = results_dir / "repos" / "tcell.tj" / "security.test.js"
    if security_test.exists():
        test_content = analyze_file(security_test)
        if test_content:
            print(f"   File: {security_test.name}")
            print(f"   Size: {len(test_content)} characters")
            
            # Ищем тесты
            test_patterns = [
                r'it\(["\']([^"\']+)',
                r'test\(["\']([^"\']+)',
                r'describe\(["\']([^"\']+)',
            ]
            
            tests = []
            for pattern in test_patterns:
                matches = re.findall(pattern, test_content)
                tests.extend(matches)
            
            if tests:
                print(f"   Security tests found: {len(tests)}")
                for test in tests[:15]:
                    print(f"     - {test}")
            
            # Ищем упоминания уязвимостей в тестах
            vuln_in_tests = []
            for pattern in vuln_patterns:
                matches = re.findall(pattern, test_content, re.IGNORECASE)
                if matches:
                    vuln_in_tests.extend(matches)
            
            if vuln_in_tests:
                print(f"\n   Vulnerability tests:")
                for vuln in list(set(vuln_in_tests))[:10]:
                    print(f"     - {vuln}")
    else:
        print(f"   File not found: {security_test}")
    
    # 6. Проверка использования Ollama в коде
    print("\n6. OLLAMA USAGE CHECK")
    print("-" * 80)
    
    ollama_found = False
    js_files = list(results_dir.rglob("*.js"))
    
    for js_file in js_files[:10]:
        content = analyze_file(js_file)
        if content and isinstance(content, str):
            if 'ollama' in content.lower() or 'codellama' in content.lower():
                ollama_found = True
                print(f"   Found Ollama reference in: {js_file.name}")
                # Показываем контекст
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'ollama' in line.lower() or 'codellama' in line.lower():
                        print(f"     Line {i+1}: {line.strip()[:100]}")
                        break
    
    if not ollama_found:
        print(f"   No Ollama references found in code files")
        print(f"   Note: Ollama might be used via environment variables or config")
    
    # Итоговый отчет
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    # Подсчитываем файлы по типам
    all_files = list(results_dir.rglob("*"))
    files_by_type = {}
    for f in all_files:
        if f.is_file():
            ext = f.suffix or 'no-extension'
            files_by_type[ext] = files_by_type.get(ext, 0) + 1
    
    print(f"""
Results Location: {results_dir.absolute()}
Total Files: {len([f for f in all_files if f.is_file()])}

Files by Type:
""")
    for ext, count in sorted(files_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count}")
    
    print(f"""
Key Findings:
- Ollama Usage: {'YES - Found in code/logs' if ollama_found else 'UNKNOWN - May be configured via env'}
- API Endpoints: Check openapi.json
- Security Tests: Check security.test.js
- Evidence: Check EVIDENCE.md
- World Model: Check world-model.json

Next Steps:
1. Review EVIDENCE.md for discovered vulnerabilities
2. Check security.test.js for security test cases
3. Review openapi.json for API endpoints discovered
4. Check execution-log.json for full execution details
""")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

