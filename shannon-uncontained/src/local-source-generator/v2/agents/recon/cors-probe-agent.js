/**
 * CORSProbeAgent - CORS preflight analysis for method discovery
 * 
 * Sends OPTIONS requests to discovered endpoints to extract allowed HTTP methods
 * from Access-Control-Allow-Methods headers.
 */

import { BaseAgent } from '../base-agent.js';
import { EVENT_TYPES, createEvidenceEvent } from '../../worldmodel/evidence-graph.js';
import { getLLMClient, LLM_CAPABILITIES } from '../../orchestrator/llm-client.js';
import fetch from 'node-fetch';

export class CORSProbeAgent extends BaseAgent {
    constructor(options = {}) {
        super('CORSProbeAgent', options);

        this.inputs_schema = {
            type: 'object',
            required: ['target'],
            properties: {
                target: { type: 'string', description: 'Target URL' },
            },
        };

        this.outputs_schema = {
            type: 'object',
            properties: {
                endpoints_probed: { type: 'number' },
                methods_discovered: { type: 'number' },
            },
        };

        this.requires = {
            evidence_kinds: ['endpoint_discovered'],
            model_nodes: ['endpoint']
        };
        this.emits = {
            evidence_events: ['cors_analysis', EVENT_TYPES.ENDPOINT_DISCOVERED],
            model_updates: [],
            claims: [],
            artifacts: [],
        };

        this.default_budget = {
            max_time_ms: 60000,
            max_network_requests: 100,
            max_tokens: 2000,  // Добавлено для LLM анализа
            max_tool_invocations: 0,
        };

        this.llm = getLLMClient();
    }

    async run(ctx, inputs) {
        const { target } = inputs;
        const baseUrl = this.normalizeBaseUrl(target);

        const results = {
            endpoints_probed: 0,
            methods_discovered: 0,
            cors_enabled: [],
        };

        // Get endpoints from TargetModel
        const endpoints = ctx.targetModel.getEndpoints();
        const probed = new Set();

        this.setStatus(`Probing ${endpoints.length} endpoints for CORS...`);

        // Also add common API paths to probe
        const commonPaths = [
            '/api',
            '/api/v1',
            '/api/v2',
            '/v1',
            '/v2',
            '/graphql',
            '/rest',
        ];

        const pathsToProbe = [
            ...endpoints.map(e => e.attributes?.path).filter(Boolean),
            ...commonPaths,
        ];

        for (const path of pathsToProbe) {
            if (probed.has(path)) continue;
            probed.add(path);

            const url = path.startsWith('http') ? path : `${baseUrl}${path}`;

            try {
                ctx.recordNetworkRequest();
                const corsInfo = await this.probeCORS(url);
                results.endpoints_probed++;

                if (corsInfo.enabled) {
                    results.cors_enabled.push({
                        path,
                        methods: corsInfo.methods,
                        origin: corsInfo.origin,
                    });

                    // Emit CORS analysis evidence
                    ctx.emitEvidence({
                        source: this.name,
                        event_type: 'cors_analysis',
                        target,
                        payload: {
                            url,
                            path,
                            cors_enabled: true,
                            allowed_methods: corsInfo.methods,
                            allowed_origin: corsInfo.origin,
                            allowed_headers: corsInfo.headers,
                            credentials: corsInfo.credentials,
                        },
                    });

                    // Emit endpoint for each discovered method
                    for (const method of corsInfo.methods) {
                        if (method !== 'OPTIONS') {
                            ctx.emitEvidence({
                                source: this.name,
                                event_type: EVENT_TYPES.ENDPOINT_DISCOVERED,
                                target,
                                payload: {
                                    method,
                                    path,
                                    url,
                                    source: 'cors_probe',
                                },
                            });
                            results.methods_discovered++;
                        }
                    }
                }
            } catch {
                // Skip failed probes
            }
        }

        // LLM анализ CORS конфигурации для выявления уязвимостей
        if (this.llm?.isAvailable() && results.cors_enabled.length > 0) {
            ctx.recordTokens(1000);
            
            const analysisPrompt = `Проанализируй CORS конфигурацию и определи потенциальные уязвимости:

Target: ${target}
CORS-enabled endpoints: ${JSON.stringify(results.cors_enabled, null, 2)}

Задачи:
1. Определи уязвимые CORS конфигурации (например, allow-origin: *, allow-credentials: true)
2. Предложи методы эксплуатации найденных уязвимостей
3. Оцени критичность каждой найденной конфигурации
4. Предложи дополнительные endpoints для проверки CORS

Верни JSON с анализом безопасности CORS.`;

            const analysisResponse = await this.llm.generate(analysisPrompt, {
                capability: LLM_CAPABILITIES.EXTRACT_CLAIMS,
                maxTokens: 2000
            });

            if (analysisResponse.success) {
                ctx.recordTokens(analysisResponse.tokens_used);
                
                try {
                    const corsAnalysis = JSON.parse(analysisResponse.content);
                    
                    // Добавляем гипотезы об уязвимостях CORS
                    if (corsAnalysis.vulnerabilities) {
                        for (const vuln of corsAnalysis.vulnerabilities) {
                            ctx.emitEvidence({
                                type: 'cors_vulnerability_hypothesis',
                                source: `${this.name}_llm`,
                                data: {
                                    endpoint: vuln.endpoint,
                                    vulnerability_type: vuln.type,
                                    severity: vuln.severity,
                                    exploit_method: vuln.exploit_method,
                                    confidence: vuln.confidence || 0.4
                                }
                            });

                            // Создаем claim для уязвимости
                            ctx.emitClaim({
                                claim_type: 'cors_misconfiguration',
                                subject: vuln.endpoint,
                                predicate: {
                                    vulnerability_type: vuln.type,
                                    severity: vuln.severity
                                },
                                base_rate: vuln.confidence || 0.4
                            });
                        }
                    }
                } catch (e) {
                    console.warn('[CORSProbeAgent] LLM analysis parsing failed:', e.message);
                }
            }
        }

        this.setStatus(`Discovered ${results.methods_discovered} methods on ${results.cors_enabled.length} CORS-enabled endpoints`);
        return results;
    }

    normalizeBaseUrl(target) {
        try {
            const url = new URL(target);
            return `${url.protocol}//${url.host}`;
        } catch {
            return target.replace(/\/$/, '');
        }
    }

    async probeCORS(url) {
        const result = {
            enabled: false,
            methods: [],
            origin: null,
            headers: [],
            credentials: false,
        };

        try {
            const response = await fetch(url, {
                method: 'OPTIONS',
                headers: {
                    'Origin': 'https://example.com',
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type, Authorization',
                    'User-Agent': 'Mozilla/5.0 (compatible; SecurityScanner/1.0)',
                },
                timeout: 10000,
            });

            // Check CORS headers
            const allowOrigin = response.headers.get('access-control-allow-origin');
            const allowMethods = response.headers.get('access-control-allow-methods');
            const allowHeaders = response.headers.get('access-control-allow-headers');
            const allowCredentials = response.headers.get('access-control-allow-credentials');

            if (allowOrigin || allowMethods) {
                result.enabled = true;
                result.origin = allowOrigin;
                result.credentials = allowCredentials === 'true';

                if (allowMethods) {
                    result.methods = allowMethods
                        .split(',')
                        .map(m => m.trim().toUpperCase())
                        .filter(m => m);
                }

                if (allowHeaders) {
                    result.headers = allowHeaders
                        .split(',')
                        .map(h => h.trim())
                        .filter(h => h);
                }
            }
        } catch {
            // Ignore errors
        }

        return result;
    }
}

export default CORSProbeAgent;
