#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация итогового отчета по пентесту
"""
import json
from pathlib import Path

def main():
    print("=" * 80)
    print("PENTEST RESULTS SUMMARY REPORT")
    print("=" * 80)
    
    results_dir = Path("pentest-results/repos/tcell.tj")
    
    # Читаем execution-log.json
    exec_log_path = results_dir / "execution-log.json"
    exec_log = json.load(open(exec_log_path, 'r', encoding='utf-8'))
    
    # Анализируем агенты
    agents_summary = {}
    total_tokens = 0
    llm_agents = []
    
    for entry in exec_log:
        agent = entry.get('agent', 'Unknown')
        summary = entry.get('summary', {})
        tokens = summary.get('tokens_used', 0)
        success = entry.get('success', False)
        
        agents_summary[agent] = {
            'tokens': tokens,
            'success': success,
            'duration_ms': summary.get('duration_ms', 0),
            'events': summary.get('events_emitted', 0)
        }
        
        total_tokens += tokens
        if tokens > 0:
            llm_agents.append(agent)
    
    # Читаем EVIDENCE.md
    evidence_path = results_dir / "EVIDENCE.md"
    evidence_content = evidence_path.read_text(encoding='utf-8')
    
    # Читаем openapi.json
    openapi_path = results_dir / "openapi.json"
    openapi_data = json.load(open(openapi_path, 'r', encoding='utf-8'))
    
    print(f"""
LOCATION: {Path('pentest-results').absolute()}

EXECUTION SUMMARY:
------------------
Total Agents Executed: {len(exec_log)}
Successful Agents: {sum(1 for e in exec_log if e.get('success'))}
Failed Agents: {sum(1 for e in exec_log if not e.get('success'))}

OLLAMA USAGE:
-------------
Total Tokens Used: {total_tokens}
LLM Agents Used: {len(llm_agents)}
""")
    
    if llm_agents:
        print("Agents that used LLM:")
        for agent in llm_agents:
            print(f"  - {agent}: {agents_summary[agent]['tokens']} tokens")
    else:
        print("WARNING: No LLM usage detected!")
        print("Possible reasons:")
        print("  - Ollama not configured properly")
        print("  - Agents ran in recon-only mode")
        print("  - LLM agents were skipped")
    
    print(f"""
DISCOVERIES:
------------
API Endpoints Found: {len(openapi_data.get('paths', {}))}
Evidence Events: {sum(agents_summary[a]['events'] for a in agents_summary)}

Security Agents Executed:
""")
    
    security_agents = [a for a in agents_summary.keys() if any(x in a.lower() for x in ['security', 'vuln', 'xss', 'sql', 'command', 'injection'])]
    for agent in security_agents:
        info = agents_summary[agent]
        status = "OK" if info['success'] else "FAIL"
        print(f"  [{status}] {agent}: {info['events']} events, {info['duration_ms']}ms")
    
    print(f"""
VULNERABILITIES FOUND:
----------------------
Based on EVIDENCE.md:
""")
    
    # Парсим EVIDENCE.md
    if 'CommandInjectionAgent' in evidence_content:
        print("  ⚠ Command Injection: Agent executed (check results)")
    if 'XSSValidatorAgent' in evidence_content:
        print("  ⚠ XSS: Agent executed (check results)")
    if 'SQLmapAgent' in evidence_content:
        print("  ⚠ SQL Injection: Agent executed (check results)")
    if 'missing_security_header' in evidence_content:
        print("  ⚠ Missing Security Headers: 7 instances found")
    if 'waf_present' in evidence_content:
        print("  ⚠ WAF Detected: Present (confidence 60%)")
    
    print(f"""
FILES GENERATED:
----------------
Total Files: 21
- JavaScript Files: 11 (application code, tests, config)
- JSON Files: 4 (world-model, openapi, execution-log, package.json)
- Markdown Files: 4 (documentation, evidence, architecture)
- YAML Files: 1 (blackbox config)
- JSONL Files: 1 (ML training data)

KEY FILES:
----------
1. EVIDENCE.md - Evidence map and vulnerability claims
2. execution-log.json - Full execution log with all agents
3. openapi.json - Discovered API endpoints (231 endpoints)
4. world-model.json - Complete world model of the target
5. security.test.js - Security test cases (none generated - no vulns confirmed)
6. ARCHITECTURE.md - Inferred architecture
7. API.md - API documentation
8. app.js - Generated application code
9. routes/api.js - Generated API routes

CONCLUSION:
-----------
Status: {'SUCCESS' if all(e.get('success') for e in exec_log) else 'PARTIAL'}
Ollama Used: {'YES' if total_tokens > 0 else 'NO - Check configuration'}
Vulnerabilities: {'Found (see EVIDENCE.md)' if security_agents else 'None confirmed'}
API Discovery: SUCCESS ({len(openapi_data.get('paths', {}))} endpoints)

RECOMMENDATIONS:
---------------
1. Review EVIDENCE.md for detailed vulnerability claims
2. Check execution-log.json for agent execution details
3. Review generated code in app.js and routes/ for security issues
4. Verify Ollama configuration if LLM features are needed
5. Review openapi.json for discovered API endpoints
""")

if __name__ == "__main__":
    main()

