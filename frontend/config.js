/**
 * Configuration file for the Investment Website
 * Contains API keys, settings, and environment variables
 */

const Config = {
    // API Configuration - Now loaded from Environment
    api: {
        gemini: {
            apiKey: 'YOUR_GEMINI_API_KEY', // Will be overridden by Environment
            baseURL: 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent',
            timeout: 30000,
            maxRetries: 3,
            model: 'gemini-2.5-flash-lite'
        }
    },

    // Application Settings - Now loaded from Environment
    app: {
        name: 'Russian Stock Market Investment Platform',
        version: '2.0',
        environment: 'production', // 'development' | 'production'
        debugMode: false
    },

    // User Limits - Now loaded from Environment
    limits: {
        messagesPerDay: 10,
        maxMessageLength: 1000,
        maxConversationHistory: 20
    },

    // Features Flags - Now loaded from Environment
    features: {
        aiResponses: true,
        userRegistration: true,
        paywall: true,
        analytics: false,
        debugging: true
    },

    // Russian Market Data (Mock Data)
    marketData: {
        sberbank: {
            depositRate: '8.5%',
            color: '#00a650'
        },
        gold: {
            yield: '12.3%',
            color: '#ffd700'
        },
        moexIndex: {
            yield: '15.7%',
            color: '#dc3545'
        }
    },

    // AI Prompts and Responses
    prompts: {
        // system prompt disabled per requirement; raw user question + history is sent
        // system: `...`,

        fallback: 'Извините, я специализируюсь на инвестиционных вопросах. Как я могу помочь вам с российским фондовым рынком?',

        error: 'Произошла техническая ошибка. Попробуйте переформулировать вопрос.',

        welcome: 'Добро пожаловать! Я помогу вам с вопросами по инвестициям в российский фондовый рынок.',

        portfolioCreated: 'Отличный выбор! Ваш инвестиционный портфель создан с учетом ваших предпочтений.'
    },

    // Error Messages
    errors: {
        apiKeyMissing: 'API ключ не настроен. Обратитесь к администратору.',
        apiTimeout: 'AI сервис временно недоступен. Попробуйте позже.',
        apiQuotaExceeded: 'Превышен лимит запросов к AI. Попробуйте позже.',
        networkError: 'Ошибка сети. Проверьте подключение к интернету.',
        invalidInput: 'Некорректный ввод. Пожалуйста, проверьте данные.',
        accessDenied: 'Доступ запрещен. Войдите в систему или оформите подписку.'
    },

    // Security Settings
    security: {
        rateLimiting: true,
        inputSanitization: true,
        xssProtection: true,
        maxLoginAttempts: 5,
        sessionTimeout: 24 * 60 * 60 * 1000 // 24 hours
    },

    // Development/Debug Settings
    debug: {
        logApiCalls: false,
        logUserActions: false,
        showErrorDetails: false,
        mockAiResponses: false
    }
};

/**
 * Initialize configuration based on environment
 */
Config.init = function () {
    // 🌍 Load settings from Environment if available
    if (typeof window !== 'undefined' && window.Environment) {
        this.loadFromEnvironment();
    }

    // Load environment-specific settings
    if (this.app.environment === 'production') {
        this.debug.logApiCalls = false;
        this.debug.logUserActions = false;
        this.debug.showErrorDetails = false;
        this.app.debugMode = false;
    }

    // Load API key from process environment if available (Node.js)
    if (typeof process !== 'undefined' && process.env) {
        this.api.gemini.apiKey = process.env.GEMINI_API_KEY || this.api.gemini.apiKey;
    }

    // Initialize AI service if available
    if (typeof window !== 'undefined' && window.GeminiAI) {
        window.GeminiAI.setApiKey(this.api.gemini.apiKey);
    }

    console.log(`${this.app.name} v${this.app.version} initialized in ${this.app.environment} mode`);
};

/**
 * 🌍 Load configuration from Environment module
 */
Config.loadFromEnvironment = function () {
    if (!window.Environment) return;

    const env = window.Environment;

    // API Configuration
    this.api.gemini.apiKey = env.GEMINI_API_KEY;
    this.api.gemini.baseURL = env.GEMINI_BASE_URL;
    this.api.gemini.timeout = env.API_TIMEOUT;
    this.api.gemini.maxRetries = env.API_MAX_RETRIES;
    this.api.gemini.model = env.GEMINI_MODEL;

    // Application Settings
    this.app.name = env.APP_NAME;
    this.app.version = env.APP_VERSION;
    this.app.environment = env.APP_ENVIRONMENT;
    this.app.debugMode = env.ENABLE_DEBUG_MODE;

    // User Limits
    this.limits.messagesPerDay = env.MESSAGES_PER_DAY;
    this.limits.maxMessageLength = env.MAX_MESSAGE_LENGTH;
    this.limits.maxConversationHistory = env.MAX_CONVERSATION_HISTORY;

    // Feature Flags
    this.features.aiResponses = env.ENABLE_AI_RESPONSES;
    this.features.userRegistration = env.ENABLE_USER_REGISTRATION;
    this.features.paywall = env.ENABLE_PAYWALL;
    this.features.analytics = env.ENABLE_ANALYTICS;
    this.features.debugging = env.ENABLE_DEBUG_MODE;

    // Market Data
    this.marketData.sberbank.depositRate = env.SBERBANK_DEPOSIT_RATE;
    this.marketData.gold.yield = env.GOLD_YIELD;
    this.marketData.moexIndex.yield = env.MOEX_INDEX_YIELD;

    // Security Settings
    this.security.maxLoginAttempts = env.MAX_LOGIN_ATTEMPTS;
    this.security.sessionTimeout = env.SESSION_TIMEOUT;

    // Debug Settings
    this.debug.logApiCalls = env.LOG_API_CALLS;
    this.debug.logUserActions = env.LOG_USER_ACTIONS;
    this.debug.showErrorDetails = env.SHOW_ERROR_DETAILS;
    this.debug.mockAiResponses = env.MOCK_AI_RESPONSES;

    console.log('🌍 Configuration loaded from Environment');
};

/**
 * Get configuration value safely
 */
Config.get = function (path, defaultValue = null) {
    const keys = path.split('.');
    let current = this;

    for (const key of keys) {
        if (current && typeof current === 'object' && key in current) {
            current = current[key];
        } else {
            return defaultValue;
        }
    }

    return current;
};

/**
 * Set configuration value safely
 */
Config.set = function (path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = this;

    for (const key of keys) {
        if (!(key in current)) {
            current[key] = {};
        }
        current = current[key];
    }

    current[lastKey] = value;
};

/**
 * Validate required configuration
 */
Config.validate = function () {
    const issues = [];

    // Check API key
    if (!this.api.gemini.apiKey || this.api.gemini.apiKey === 'YOUR_GEMINI_API_KEY') {
        issues.push('Gemini API key not configured');
    }

    // Check required settings
    if (!this.app.name || !this.app.version) {
        issues.push('App name or version missing');
    }

    return {
        valid: issues.length === 0,
        issues: issues
    };
};

// Auto-initialize when loaded
if (typeof window !== 'undefined') {
    // Browser environment
    window.Config = Config;
    document.addEventListener('DOMContentLoaded', () => Config.init());
} else if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = Config;
}