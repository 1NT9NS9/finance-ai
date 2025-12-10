/**
 * Gemini AI API Integration
 * Provides AI-powered responses for the investment chat bot
 */

class GeminiAI {
    constructor() {
        // API Configuration
        // 🔒 Uses local backend proxy to protect the actual Gemini API Key
        this.baseURL = '/api/ai/generate';
        // Default to the development backend access key (not the Gemini key)
        this.apiKey = 'fdml_demo_key_12345';
        this.maxRetries = 3;
        this.timeout = 30000; // 30 seconds

        // Initialize API key from Environment if available
        this.initializeFromEnvironment();
    }

    /**
     * Initialize from Environment configuration
     */
    initializeFromEnvironment() {
        // Try to get API key from Environment module
        if (typeof window !== 'undefined' && window.Environment) {
            const env = window.Environment;
            // Check if we have a specific access key for the backend
            if (env.GEMINI_API_KEY && env.GEMINI_API_KEY !== 'YOUR_GEMINI_API_KEY_HERE') {
                this.apiKey = env.GEMINI_API_KEY;
                this.baseURL = env.GEMINI_BASE_URL || this.baseURL;
                this.timeout = env.API_TIMEOUT || this.timeout;
                this.maxRetries = env.API_MAX_RETRIES || this.maxRetries;
                console.log('✅ GeminiAI: Initialized from Environment');
                return true;
            }
        }
        return false;
    }

    /**
     * Initialize API key from environment or configuration
     */
    setApiKey(apiKey) {
        this.apiKey = apiKey;
        console.log('✅ GeminiAI: API key updated');
    }

    /**
     * Validate API configuration
     */
    isConfigured() {
        // We always have at least the default backend key, but valid keys shouldn't be placeholders
        return this.apiKey &&
            this.apiKey !== 'YOUR_GEMINI_API_KEY' &&
            this.apiKey !== 'YOUR_GEMINI_API_KEY_HERE';
    }

    /**
     * Create request payload for Gemini API
     */
    createRequestPayload(userMessage, conversationHistory = []) {
        // Send only user's message; system prompt removed
        const fullPrompt = `${userMessage}`;

        const contents = [
            {
                parts: [
                    {
                        text: fullPrompt
                    }
                ]
            }
        ];

        // Add full conversation history if provided (no truncation)
        if (conversationHistory.length > 0) {
            const historyText = conversationHistory.map(msg =>
                `${msg.role === 'user' ? 'Пользователь' : 'Ассистент'}: ${msg.content}`
            ).join('\n');
            contents[0].parts[0].text = `История разговора:\n${historyText}\n\nТекущий вопрос: ${userMessage}`;
        }

        return {
            contents: contents,
            generationConfig: {
                temperature: 0.45,
                topK: 40,
                topP: 0.9,
                maxOutputTokens: 4096,
            },
            // Safety settings are handled by the backend or Google, but we send them for completeness
            safetySettings: [
                {
                    category: "HARM_CATEGORY_HARASSMENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_HATE_SPEECH",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    category: "HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold: "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        };
    }

    /**
     * Send request to Gemini API (via Backend Proxy)
     */
    async sendRequest(payload, retryCount = 0) {
        if (!this.isConfigured()) {
            throw new Error('API Access key not configured');
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            // Send to local backend proxy
            // Header 'X-API-Key' is used for backend authentication, not Gemini auth
            const response = await fetch(this.baseURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': this.apiKey
                },
                body: JSON.stringify(payload),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`API Error: ${response.status} - ${errorData.error || response.statusText}`);
            }

            const wrapper = await response.json();

            // Backend returns { status: 'success', data: { ...GeminiResponse... } }
            if (wrapper.status === 'success' && wrapper.data) {
                return wrapper.data;
            } else {
                throw new Error('Invalid response format from backend');
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout - AI service took too long to respond');
            }

            // Retry logic for network errors
            if (retryCount < this.maxRetries && this.isRetryableError(error)) {
                console.warn(`API request failed, retrying... (${retryCount + 1}/${this.maxRetries})`);
                await this.delay(Math.pow(2, retryCount) * 1000); // Exponential backoff
                return this.sendRequest(payload, retryCount + 1);
            }

            throw error;
        }
    }

    /**
     * Check if error is retryable
     */
    isRetryableError(error) {
        return error.message.includes('network') ||
            error.message.includes('timeout') ||
            error.message.includes('502') ||
            error.message.includes('503') ||
            error.message.includes('504');
    }

    /**
     * Delay utility for retry backoff
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Extract response text from Gemini API response
     */
    extractResponseText(apiResponse) {
        try {
            // Standard Gemini response structure
            if (apiResponse.candidates && apiResponse.candidates.length > 0) {
                const candidate = apiResponse.candidates[0];
                if (candidate.content && candidate.content.parts && candidate.content.parts.length > 0) {
                    return candidate.content.parts[0].text;
                }
            }
            return 'Извините, не удалось получить разумный ответ от AI.';
        } catch (error) {
            console.error('Error extracting response text:', error);
            return 'Ошибка при обработке ответа AI.';
        }
    }

    /**
     * Retry initialization if modules loaded later
     */
    retryInitialization() {
        if (!this.isConfigured()) {
            console.log('🔄 GeminiAI: Retrying initialization...');
            return this.initializeFromEnvironment();
        }
        return true;
    }

    /**
     * Get demo response when API is not available
     */
    getDemoResponse(userMessage) {
        const responses = [
            'Это демо-режим. Для получения реальных советов по инвестициям настройте API ключ.',
            'В демо-режиме: Рекомендую рассмотреть диверсификацию портфеля между акциями, облигациями и золотом.',
            'Демо-ответ: Российский рынок показывает волатильность, важно учитывать риски при инвестировании.',
            'В тестовом режиме: Для долгосрочных инвестиций рассмотрите акции Сбербанка и Газпрома.'
        ];

        const randomIndex = Math.floor(Math.random() * responses.length);
        return `🤖 ${responses[randomIndex]}`;
    }

    /**
     * Main method to get AI response
     */
    async getResponse(userMessage, conversationHistory = []) {
        try {
            // Validate input
            if (!userMessage || typeof userMessage !== 'string' || userMessage.trim().length === 0) {
                return 'Пожалуйста, задайте вопрос.';
            }

            // Retry initialization if not configured
            if (!this.isConfigured()) {
                const initialized = this.retryInitialization();
                if (!initialized) {
                    console.warn('⚠️ GeminiAI: API not configured, using demo mode');
                    return this.getDemoResponse(userMessage);
                }
            }

            // Clean user input
            const cleanMessage = userMessage.trim().substring(0, 1000); // Limit message length

            // Create request payload
            const payload = this.createRequestPayload(cleanMessage, conversationHistory);

            // Send request to Gemini API
            const apiResponse = await this.sendRequest(payload);

            // Extract and return response text
            return this.extractResponseText(apiResponse);

        } catch (error) {
            console.error('Gemini AI Error:', error);

            // Return appropriate error message based on error type
            if (error.message.includes('API key')) {
                return 'Ошибка конфигурации AI. Обратитесь к администратору.';
            } else if (error.message.includes('timeout')) {
                return 'AI сервис временно недоступен. Попробуйте позже.';
            } else if (error.message.includes('quota') || error.message.includes('limit')) {
                return 'Превышен лимит запросов к AI. Попробуйте позже.';
            } else {
                return 'Произошла ошибка при обращении к AI. Попробуйте переформулировать вопрос.';
            }
        }
    }

    /**
     * Get investment-specific response with enhanced prompting
     */
    async getInvestmentAdvice(userMessage, portfolioData = null) {
        let enhancedPrompt = userMessage;

        // Add portfolio context if available
        if (portfolioData) {
            enhancedPrompt = `Контекст портфеля: доходность ${portfolioData.yield}%, риск ${portfolioData.risk}%, капитал ${portfolioData.capital}, дивиденды ${portfolioData.dividends ? 'важны' : 'не важны'}. 
            
            Вопрос: ${userMessage}`;
        }

        return await this.getResponse(enhancedPrompt);
    }

    /**
     * Get market analysis response
     */
    async getMarketAnalysis(asset, timeframe = 'current') {
        const prompt = `Проанализируйте текущую ситуацию с активом "${asset}" на российском рынке. 
        Временной период: ${timeframe}. 
        Дайте краткий анализ перспектив и рекомендации.`;

        return await this.getResponse(prompt);
    }

    /**
     * Health check for API connectivity
     */
    async healthCheck() {
        try {
            console.log('🔍 GeminiAI Health Check starting...');
            console.log(`API Key configured: ${this.isConfigured()}`);
            console.log(`Base URL: ${this.baseURL}`);

            const response = await this.getResponse('Привет, это тест связи.');

            const result = {
                status: 'healthy',
                message: 'API доступен',
                response: response.substring(0, 50) + '...',
                fullResponse: response,
                apiKey: this.isConfigured() ? 'Configured' : 'Not configured',
                baseURL: this.baseURL
            };

            console.log('✅ Health check successful:', result);
            return result;
        } catch (error) {
            const result = {
                status: 'error',
                message: 'API недоступен',
                error: error.message,
                apiKey: this.isConfigured() ? 'Configured' : 'Not configured',
                baseURL: this.baseURL
            };

            console.error('❌ Health check failed:', result);
            return result;
        }
    }

    /**
     * Debug method to test API from browser console
     */
    async debugTest(message = 'Как дела на российском фондовом рынке?') {
        console.log('🧪 GeminiAI Debug Test');
        console.log('='.repeat(50));
        console.log(`Input: ${message}`);
        console.log(`API Configured: ${this.isConfigured()}`);
        console.log(`API Key: ${this.apiKey.substring(0, 10)}...`);
        console.log(`Base URL: ${this.baseURL}`);
        console.log('-'.repeat(50));

        try {
            const startTime = Date.now();
            const response = await this.getResponse(message);
            const endTime = Date.now();

            console.log(`✅ Response received in ${endTime - startTime}ms:`);
            console.log(response);
            console.log('='.repeat(50));

            return {
                success: true,
                response: response,
                responseTime: endTime - startTime,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('❌ Error during test:', error);
            console.log('='.repeat(50));

            return {
                success: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }
}

/**
 * Initialize GeminiAI when DOM is ready and Environment is loaded
 */
function initializeGeminiAI() {
    if (typeof window !== 'undefined') {
        window.GeminiAI = new GeminiAI();

        // Set up a listener for late Environment loading
        if (!window.GeminiAI.isConfigured()) {
            // Try again after a short delay
            setTimeout(() => {
                if (!window.GeminiAI.isConfigured()) {
                    window.GeminiAI.retryInitialization();
                }
            }, 1000);
        }

        console.log('🤖 GeminiAI: Global instance created');
    }
}

// Initialize immediately if DOM is ready, otherwise wait
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeGeminiAI);
    } else {
        // DOM already loaded
        initializeGeminiAI();
    }
} else {
    // Node.js environment
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = GeminiAI;
    }
}