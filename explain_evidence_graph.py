#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Объяснение Evidence Graph и анализ событий
"""
import json
from pathlib import Path
from collections import Counter

def main():
    print("=" * 80)
    print("EVIDENCE GRAPH - ЧТО ЭТО ТАКОЕ?")
    print("=" * 80)
    
    print("""
Evidence Graph - это неизменяемое (immutable) хранилище всех наблюдений,
собранных во время пентеста. Это центральный источник правды (source of truth)
для всех агентов.

Ключевые особенности:
- Append-only: события только добавляются, никогда не удаляются
- Content-hashed IDs: одинаковое наблюдение = одинаковый ID
- Индексирование: по источнику, цели, типу события
- Provenance: полная история откуда взялось каждое наблюдение
""")
    
    results_dir = Path("pentest-results/repos/tcell.tj")
    world_model_path = results_dir / "world-model.json"
    
    if not world_model_path.exists():
        print(f"ERROR: {world_model_path} not found")
        return
    
    print("\n" + "=" * 80)
    print("АНАЛИЗ СОБЫТИЙ ИЗ ВАШЕГО ПЕНТЕСТА")
    print("=" * 80)
    
    with open(world_model_path, 'r', encoding='utf-8') as f:
        world_model = json.load(f)
    
    evidence_graph = world_model.get('evidence_graph', {})
    events = evidence_graph.get('events', [])
    
    print(f"\nВсего событий: {len(events)}")
    
    # Группируем по типам
    event_types = Counter()
    sources = Counter()
    
    for event in events:
        event_type = event.get('event_type') or event.get('type', 'unknown')
        source = event.get('source', 'unknown')
        event_types[event_type] += 1
        sources[source] += 1
    
    print("\n1. ТИПЫ СОБЫТИЙ:")
    print("-" * 80)
    for event_type, count in event_types.most_common(20):
        print(f"   {event_type}: {count} событий")
    
    print("\n2. ИСТОЧНИКИ СОБЫТИЙ:")
    print("-" * 80)
    for source, count in sources.most_common(15):
        print(f"   {source}: {count} событий")
    
    print("\n3. ПРИМЕРЫ СОБЫТИЙ:")
    print("-" * 80)
    
    # Показываем примеры разных типов
    examples_shown = set()
    examples = []
    
    for event in events[:100]:  # Проверяем первые 100
        event_type = event.get('event_type') or event.get('type', 'unknown')
        if event_type not in examples_shown:
            examples_shown.add(event_type)
            examples.append((event_type, event))
            if len(examples) >= 10:
                break
    
    for i, (event_type, event) in enumerate(examples, 1):
        print(f"\n   Пример {i}: {event_type}")
        print(f"   Источник: {event.get('source', 'unknown')}")
        print(f"   Цель: {event.get('target', 'N/A')}")
        print(f"   Время: {event.get('timestamp', 'N/A')}")
        
        payload = event.get('payload') or event.get('data', {})
        if isinstance(payload, dict):
            print(f"   Данные:")
            for key, value in list(payload.items())[:3]:
                value_str = str(value)
                if len(value_str) > 60:
                    value_str = value_str[:60] + "..."
                print(f"     - {key}: {value_str}")
        elif payload:
            payload_str = str(payload)
            if len(payload_str) > 100:
                payload_str = payload_str[:100] + "..."
            print(f"   Данные: {payload_str}")
    
    # Анализ по категориям
    print("\n4. КАТЕГОРИЗАЦИЯ СОБЫТИЙ:")
    print("-" * 80)
    
    categories = {
        'Network Recon': ['dns_record', 'port_scan', 'tls_cert', 'subdomain'],
        'Endpoint Discovery': ['endpoint_discovered', 'form_discovered', 'link_discovered'],
        'Technology Detection': ['tech_detection', 'waf_detected'],
        'Security Testing': ['validation_result', 'tool_error', 'tool_timeout'],
        'Other': []
    }
    
    categorized = {cat: 0 for cat in categories}
    
    for event in events:
        event_type = event.get('event_type') or event.get('type', 'unknown')
        found = False
        for cat, types in categories.items():
            if event_type in types:
                categorized[cat] += 1
                found = True
                break
        if not found:
            categorized['Other'] += 1
    
    for cat, count in categorized.items():
        if count > 0:
            percentage = (count / len(events)) * 100
            print(f"   {cat}: {count} событий ({percentage:.1f}%)")
    
    # Статистика по агентам
    print("\n5. СТАТИСТИКА ПО АГЕНТАМ:")
    print("-" * 80)
    
    exec_log_path = results_dir / "execution-log.json"
    if exec_log_path.exists():
        with open(exec_log_path, 'r', encoding='utf-8') as f:
            exec_log = json.load(f)
        
        print("   Агенты и количество событий:")
        for entry in exec_log:
            agent = entry.get('agent', 'Unknown')
            events_count = entry.get('summary', {}).get('events_emitted', 0)
            if events_count > 0:
                print(f"     - {agent}: {events_count} событий")
    
    print("\n" + "=" * 80)
    print("ЧТО ДЕЛАЕТ С ЭОБЫТИЯМИ SHANNON?")
    print("=" * 80)
    
    print("""
1. Evidence Graph собирает все события от агентов
2. Target Model анализирует события и создает нормализованные сущности:
   - Endpoints (API endpoints)
   - Components (компоненты системы)
   - Data Models (модели данных)
   - Auth Flows (потоки аутентификации)
   - Workflows (бизнес-логика)

3. Epistemic Ledger создает claims (утверждения) с оценкой уверенности:
   - b (belief): степень уверенности что утверждение верно
   - d (disbelief): степень уверенности что утверждение ложно
   - u (uncertainty): степень неопределенности
   - a (base rate): базовая вероятность

4. Artifact Manifest генерирует код на основе модели

Все это позволяет:
- Отслеживать provenance (откуда взялась информация)
- Количественно оценивать неопределенность
- Генерировать код с пониманием уверенности в данных
- Воспроизводить результаты (детерминированно)
""")
    
    print("\n" + "=" * 80)
    print("ИТОГО")
    print("=" * 80)
    print(f"""
В вашем пентесте собрано {len(events)} событий от {len(sources)} различных источников.

Основные типы событий:
- Endpoint Discovery: {categorized.get('Endpoint Discovery', 0)} событий
- Network Recon: {categorized.get('Network Recon', 0)} событий  
- Technology Detection: {categorized.get('Technology Detection', 0)} событий
- Security Testing: {categorized.get('Security Testing', 0)} событий

Эти события используются для:
1. Построения модели цели (world-model.json)
2. Генерации кода приложения
3. Создания документации
4. Оценки уверенности в находках

Все события хранятся в: pentest-results/repos/tcell.tj/world-model.json
""")

if __name__ == "__main__":
    main()

