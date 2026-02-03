import OpenAI from 'openai';
import Anthropic from '@anthropic-ai/sdk';

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'fs/promises';
import path from 'path';

const execAsync = promisify(exec);

/**
 * Model Limits Registry
 * Dynamically detects and caches model context limits from API error responses.
 * Persists to .shannon-model-limits.json for future runs.
 */
const MODEL_LIMITS_FILE = path.join(process.cwd(), '.shannon-model-limits.json');

// In-memory cache of model limits
let modelLimitsCache = {};

/**
 * Load model limits from persistent storage
 */
async function loadModelLimits() {
    try {
        const data = await fs.readFile(MODEL_LIMITS_FILE, 'utf8');
        modelLimitsCache = JSON.parse(data);
        console.log(`📊 Loaded ${Object.keys(modelLimitsCache).length} known model limits`);
    } catch {
        // File doesn't exist yet, start with empty cache
        modelLimitsCache = {};
    }
    return modelLimitsCache;
}

/**
 * Save model limits to persistent storage
 */
async function saveModelLimits() {
    try {
        await fs.writeFile(MODEL_LIMITS_FILE, JSON.stringify(modelLimitsCache, null, 2));
    } catch (err) {
        console.warn(`⚠️ Failed to save model limits: ${err.message}`);
    }
}

/**
 * Parse context limit from API error message
 * Example: "This endpoint's maximum context length is 262144 tokens."
 */
function parseContextLimitFromError(errorMessage) {
    // Pattern: "maximum context length is X tokens"
    const match = errorMessage.match(/maximum context length is (\d+) tokens/i);
    if (match) {
        return parseInt(match[1], 10);
    }
    return null;
}

/**
 * Record a discovered model limit
 */
async function recordModelLimit(modelName, limit) {
    const existingLimit = modelLimitsCache[modelName];
    if (existingLimit !== limit) {
        modelLimitsCache[modelName] = limit;
        console.log(`📊 Discovered model limit: ${modelName} → ${limit.toLocaleString()} tokens`);
        await saveModelLimits();
    }
}

/**
 * Get known limit for a model (if any)
 */
export function getModelLimit(modelName) {
    return modelLimitsCache[modelName] || null;
}

/**
 * Get all known model limits
 */
export function getAllModelLimits() {
    return { ...modelLimitsCache };
}

// Load limits on module initialization
loadModelLimits().catch(() => { });

/**
 * Detect garbled/corrupted output from model
 * Returns { isGarbled: boolean, reason: string | null }
 */
export function detectGarbledOutput(content) {
    if (!content || typeof content !== 'string') {
        return { isGarbled: false, reason: null };
    }

    // Check for unexpected CJK characters (Chinese/Japanese/Korean) when not expected
    // Pattern: significant amount of CJK in otherwise English text
    const cjkChars = content.match(/[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/g) || [];
    const latinChars = content.match(/[a-zA-Z]/g) || [];

    if (cjkChars.length > 10 && latinChars.length > 50) {
        const cjkRatio = cjkChars.length / (latinChars.length + cjkChars.length);
        if (cjkRatio > 0.05 && cjkRatio < 0.5) {
            // Suspiciously mixed - likely encoding corruption
            return {
                isGarbled: true,
                reason: `Unexpected CJK characters (${cjkChars.length} chars, ${(cjkRatio * 100).toFixed(1)}% of text)`
            };
        }
    }

    // Check for repeated character sequences (sign of model loop/corruption)
    // Pattern: same 5+ character sequence repeated 3+ times consecutively
    const repeatedPattern = /(.{5,})\1{2,}/;
    const match = content.match(repeatedPattern);
    if (match && match[1].length > 4) {
        return {
            isGarbled: true,
            reason: `Repeated sequence detected: "${match[1].slice(0, 20)}..." (${match[0].length} chars)`
        };
    }

    // Check for excessive whitespace/newlines (sign of malformed output)
    const excessiveNewlines = /\n{10,}/.test(content);
    if (excessiveNewlines) {
        return { isGarbled: true, reason: 'Excessive consecutive newlines' };
    }

    return { isGarbled: false, reason: null };
}

/**
 * Detect and parse malformed tool calls from model output
 * Some models output XML-style <tool_call> tags instead of proper function calls
 * Returns array of parsed tool calls or empty array if none found
 */
export function parseMalformedToolCalls(content) {
    if (!content || typeof content !== 'string') {
        return [];
    }

    const toolCalls = [];

    // Pattern 1: XML-style <tool_call><function=NAME><parameter=KEY>VALUE</parameter>...</function></tool_call>
    const xmlStylePattern = /<tool_call>\s*<function=(\w+)>([\s\S]*?)<\/function>\s*<\/tool_call>/gi;
    let match;

    while ((match = xmlStylePattern.exec(content)) !== null) {
        const functionName = match[1];
        const paramsBlock = match[2];
        const args = {};

        // Extract parameters
        const paramPattern = /<parameter=(\w+)>([\s\S]*?)<\/parameter>/gi;
        let paramMatch;
        while ((paramMatch = paramPattern.exec(paramsBlock)) !== null) {
            args[paramMatch[1]] = paramMatch[2].trim();
        }

        toolCalls.push({
            id: `malformed_${Date.now()}_${toolCalls.length}`,
            type: 'function',
            function: {
                name: functionName,
                arguments: JSON.stringify(args)
            }
        });
    }

    // Pattern 2: Markdown-style ```tool_call or similar
    const markdownPattern = /```(?:tool_call|function)\s*(\w+)\s*\n([\s\S]*?)```/gi;
    while ((match = markdownPattern.exec(content)) !== null) {
        try {
            const functionName = match[1];
            const argsText = match[2].trim();
            // Try to parse as JSON first
            let args;
            try {
                args = JSON.parse(argsText);
            } catch {
                // Try to parse key=value pairs
                args = {};
                argsText.split('\n').forEach(line => {
                    const [key, ...valueParts] = line.split('=');
                    if (key && valueParts.length > 0) {
                        args[key.trim()] = valueParts.join('=').trim();
                    }
                });
            }

            toolCalls.push({
                id: `malformed_md_${Date.now()}_${toolCalls.length}`,
                type: 'function',
                function: {
                    name: functionName,
                    arguments: JSON.stringify(args)
                }
            });
        } catch (e) {
            // Skip unparseable blocks
        }
    }

    if (toolCalls.length > 0) {
        console.warn(`⚠️ Detected ${toolCalls.length} malformed tool call(s) in text output - parsing and executing`);
    }

    return toolCalls;
}

/**
 * Estimate token count from text (approximation: ~3.5 chars per token for English)
 * Note: This is slightly conservative to account for edge cases
 */
export function estimateTokens(text) {
    if (!text) return 0;
    // Use 3.5 chars/token (more accurate than 4) + 5% overhead for JSON encoding
    return Math.ceil((text.length / 3.5) * 1.05);
}

// Estimated token overhead for tool definitions sent with each request
const TOOL_TOKEN_OVERHEAD = 4000;

/**
 * Compress context to fit within model's token limit
 * Uses "middle-out" compression: keep start/end, summarize middle
 */
export function compressContext(messages, maxTokens) {
    if (!maxTokens || maxTokens <= 0) {
        return messages; // No limit, return as-is
    }

    // Calculate current token estimate
    const totalTokens = messages.reduce((sum, m) => {
        const content = typeof m.content === 'string' ? m.content : JSON.stringify(m.content);
        return sum + estimateTokens(content);
    }, 0);

    if (totalTokens <= maxTokens) {
        return messages; // Already within limit
    }

    console.log(`📊 Context compression: ${totalTokens.toLocaleString()} tokens → ${maxTokens.toLocaleString()} limit`);

    // Keep system message and last few messages, truncate middle
    const systemMessages = messages.filter(m => m.role === 'system');
    const nonSystemMessages = messages.filter(m => m.role !== 'system');

    // Reserve tokens for system + buffer + tool overhead
    const systemTokens = systemMessages.reduce((sum, m) => sum + estimateTokens(m.content), 0);
    const availableTokens = maxTokens - systemTokens - TOOL_TOKEN_OVERHEAD - 2000; // 2000 token safety buffer

    if (availableTokens <= 0) {
        console.warn('⚠️ System messages alone exceed token limit');
        return messages.slice(0, 2); // Return minimum viable context
    }

    // Keep most recent messages that fit
    const keptMessages = [];
    let keptTokens = 0;

    for (let i = nonSystemMessages.length - 1; i >= 0; i--) {
        const msg = nonSystemMessages[i];
        const msgTokens = estimateTokens(typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content));

        if (keptTokens + msgTokens <= availableTokens) {
            keptMessages.unshift(msg);
            keptTokens += msgTokens;
        } else {
            break;
        }
    }

    console.log(`📊 Kept ${keptMessages.length}/${nonSystemMessages.length} messages (${keptTokens.toLocaleString()} tokens)`);

    return [...systemMessages, ...keptMessages];
}



/**
 * Detect and configure LLM provider based on environment variables
 * 
 * Priority:
 * 1. LLM_PROVIDER + LLM_BASE_URL (fully custom endpoint)
 * 2. LLM_PROVIDER explicit selection
 * 3. Auto-detect from available API keys
 * 
 * Supported providers:
 * - github: GitHub Models (https://models.github.ai/inference)
 * - openai: OpenAI API (https://api.openai.com/v1)
 * - ollama: Local Ollama (http://localhost:11434/v1)
 * - llamacpp: Local llama.cpp server (http://localhost:8080/v1)
 * - custom: Any OpenAI-compatible endpoint (requires LLM_BASE_URL)
 */
export function getProviderConfig() {
    const explicitProvider = process.env.LLM_PROVIDER?.toLowerCase();
    const customBaseURL = process.env.LLM_BASE_URL;
    const githubToken = process.env.GITHUB_TOKEN;
    const openaiKey = process.env.OPENAI_API_KEY;
    const openrouterKey = process.env.OPENROUTER_API_KEY;
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    const modelOverride = process.env.LLM_MODEL;

    // For local providers that don't need real API keys
    const dummyKey = 'not-needed';

    // Explicit provider selection
    if (explicitProvider) {
        switch (explicitProvider) {
            case 'github':
                if (!githubToken) throw new Error('LLM_PROVIDER=github but GITHUB_TOKEN not set');
                return {
                    provider: 'github',
                    baseURL: customBaseURL || 'https://models.github.ai/inference',
                    apiKey: githubToken,
                    model: modelOverride || 'openai/gpt-4.1'
                };

            case 'openai':
                if (!openaiKey) throw new Error('LLM_PROVIDER=openai but OPENAI_API_KEY not set');
                return {
                    provider: 'openai',
                    baseURL: customBaseURL || 'https://api.openai.com/v1',
                    apiKey: openaiKey,
                    model: modelOverride || 'gpt-4o'
                };

            case 'openrouter':
                if (!openrouterKey) throw new Error('LLM_PROVIDER=openrouter but OPENROUTER_API_KEY not set');
                return {
                    provider: 'openrouter',
                    baseURL: customBaseURL || 'https://openrouter.ai/api/v1',
                    apiKey: openrouterKey,
                    model: modelOverride || 'openai/gpt-4o-2024-08-06',
                    defaultHeaders: {
                        'HTTP-Referer': 'https://keygraph.dev', // Required by OpenRouter for widely used apps
                        'X-Title': 'Shannon Agent'
                    }
                };

            case 'ollama':
                // Ollama exposes OpenAI-compatible API at /v1
                // See: https://ollama.ai/blog/openai-compatibility
                return {
                    provider: 'ollama',
                    baseURL: customBaseURL || 'http://localhost:11434/v1',
                    apiKey: dummyKey,
                    model: modelOverride || 'llama3.2'
                };

            case 'llamacpp':
            case 'llama.cpp':
            case 'llama-cpp':
                // llama-cpp-python server exposes OpenAI-compatible API
                // See: https://github.com/abetlen/llama-cpp-python#openai-compatible-web-server
                return {
                    provider: 'llamacpp',
                    baseURL: customBaseURL || 'http://localhost:8080/v1',
                    apiKey: dummyKey,
                    model: modelOverride || 'local-model'
                };

            case 'lmstudio':
                // LM Studio exposes OpenAI-compatible API
                return {
                    provider: 'lmstudio',
                    baseURL: customBaseURL || 'http://localhost:1234/v1',
                    apiKey: dummyKey,
                    model: modelOverride || 'local-model'
                };

            case 'custom':
                // Fully custom endpoint - requires LLM_BASE_URL
                if (!customBaseURL) {
                    throw new Error('LLM_PROVIDER=custom requires LLM_BASE_URL to be set');
                }
                return {
                    provider: 'custom',
                    baseURL: customBaseURL,
                    apiKey: openaiKey || githubToken || openrouterKey || dummyKey,
                    model: modelOverride || 'default'
                };

                        case 'anthropic':
                if (!anthropicKey) throw new Error('LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY not set');
                return {
                    provider: 'anthropic',
                    baseURL: 'https://api.anthropic.com/v1',
                    apiKey: anthropicKey,
                    model: modelOverride || 'claude-sonnet-3-5-20241022'
                };
                                const cwd = functionArgs.cwd || functionArgs.Cwd || options.cwd;
                                const { stdout, stderr } = await execAsync(command, { cwd });
                                result = stdout + (stderr ? "\nStderr: " + stderr : "");
                            } else if (functionName === "read_file") {
                                const filePath = path.resolve(options.cwd, functionArgs.path);
                                result = await fs.readFile(filePath, 'utf8');
                            } else if (functionName === "write_file") {
                                const filePath = path.resolve(options.cwd, functionArgs.path);
                                await fs.writeFile(filePath, functionArgs.content);
                                result = "File written successfully";
                            } else if (functionName === "list_files") {
                                const searchPath = path.resolve(options.cwd, functionArgs.path);
                                const files = await fs.readdir(searchPath);
                                result = files.join('\n');
                            } else {
                                result = `Unknown malformed tool: ${functionName}`;
                                isError = true;
                            }
                        } catch (err) {
                            result = `Error executing malformed ${functionName}: ${err.message}`;
                            isError = true;
                        }

                        yield {
                            type: "tool_result",
                            content: result,
                            isError: isError
                        };

                        // Add the malformed tool call to message history as if it was proper
                        messages.push({
                            role: "assistant",
                            content: null,
                            tool_calls: [toolCall]
                        });
                        messages.push({
                            tool_call_id: toolCall.id,
                            role: "tool",
                            name: functionName,
                            content: result
                        });
                    }
                    // Continue the loop - don't terminate
                } else {
                    // No tool calls and no malformed tool calls - terminate normally
                    keepGoing = false;
                    let finalResult = message.content || "";
                    yield {
                        type: "result",
                        result: finalResult,
                        total_cost_usd: totalCost,
                        duration_ms: Date.now() - startTime,
                        subtype: "success"
                    };
                }
            }
        }
    } catch (error) {
        // Detect and record model context limits from 400 errors
        let limitDiscovered = false;
        if (error.status === 400 && error.message) {
            const detectedLimit = parseContextLimitFromError(error.message);
            if (detectedLimit) {
                await recordModelLimit(modelName, detectedLimit);
                limitDiscovered = true;
            }
        }

        // Classify error for retry logic
        // Context limit errors ARE retryable if we just discovered the limit
        const nonRetryable = isNonRetryableError(error) && !limitDiscovered;
        if (nonRetryable) {
            console.error(`🚫 Non-retryable error (${error.status}):`, error.message);
        } else if (limitDiscovered) {
            console.log(`📊 Context limit discovered (${modelLimitsCache[modelName]?.toLocaleString()} tokens). Will retry with compression.`);
        } else {
            console.error("LLM CLIENT CRASHED:", error);
        }

        yield {
            type: "result",
            result: null,
            error: error.message,
            duration_ms: Date.now() - startTime,
            nonRetryable: nonRetryable,
            errorCode: error.status || error.code,
            subtype: limitDiscovered ? "context_limit_discovered" : "error_during_execution"
        };
    } finally {
        // Cleanup with EPIPE protection
        for (const mcp of mcpClients) {
            try {
                await mcp.transport.close();
            } catch (e) {
                // Suppress EPIPE errors during cleanup (process already exiting)
                if (e.code !== 'EPIPE' && e.code !== 'ERR_STREAM_DESTROYED') {
                    console.warn(`⚠️ MCP cleanup error: ${e.message}`);
                }
            }
        }
    }
}
