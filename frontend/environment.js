/**
 * 🔐 Environment Configuration
 * Central place for all API keys and sensitive configuration
 * Set your values here once and they will be applied everywhere
 */

const Environment = {
    // ===== 🤖 GEMINI AI CONFIGURATION =====
    // ===== 🤖 GEMINI AI CONFIGURATION =====
    // This key is now used to authenticate with YOUR BACKEND, not Gemini directly
    // The actual Gemini Key is securely stored in your backend .env file
    GEMINI_API_KEY: "fdml_demo_key_12345",
    GEMINI_MODEL: 'gemini-2.5-flash-lite',
    GEMINI_BASE_URL: '/api/ai/generate', // Point to local backend proxy

    // ===== 📱 APPLICATION SETTINGS =====
    APP_NAME: 'Russian Stock Market Investment Platform',
    APP_VERSION: '2.0',
    APP_ENVIRONMENT: 'production', // 'development' | 'production'

    // ===== ⏱️ API LIMITS & TIMEOUTS =====
    API_TIMEOUT: 30000,           // 30 seconds
    API_MAX_RETRIES: 3,           // 3 retry attempts
    MAX_MESSAGE_LENGTH: 1000,     // Max characters per message
    MESSAGES_PER_DAY: 10,         // Daily message limit for users
    MAX_CONVERSATION_HISTORY: 20, // Max messages in conversation history

    // ===== 🔒 SECURITY SETTINGS =====
    MAX_LOGIN_ATTEMPTS: 5,        // Max login attempts before lockout
    SESSION_TIMEOUT: 86400000,    // 24 hours in milliseconds
    RATE_LIMIT_WINDOW: 60000,     // 1 minute rate limit window

    // ===== 🎛️ FEATURE FLAGS =====
    ENABLE_AI_RESPONSES: true,     // Enable/disable AI functionality
    ENABLE_USER_REGISTRATION: true, // Enable/disable user registration
    ENABLE_PAYWALL: true,          // Enable/disable subscription paywall
    ENABLE_ANALYTICS: false,       // Enable/disable usage analytics
    ENABLE_DEBUG_MODE: false,      // Disable debug by default for safety

    // ===== 📊 MARKET DATA =====
    SBERBANK_DEPOSIT_RATE: '8.5%',
    GOLD_YIELD: '12.3%',
    MOEX_INDEX_YIELD: '15.7%',

    // ===== 👑 ADMIN SETTINGS =====
    ADMIN_PASSWORD: 'CHANGE_ME',
    ADMIN_EMAIL: 'admin@system.local',
    ADMIN_NAME: 'Admin',

    // ===== 💰 SUBSCRIPTION SETTINGS =====
    SUBSCRIPTION_PRICE: 10000,
    SUBSCRIPTION_CURRENCY: '₽',

    // ===== 📝 LOGGING & DEBUG =====
    LOG_API_CALLS: false,
    LOG_USER_ACTIONS: false,
    SHOW_ERROR_DETAILS: false,
    MOCK_AI_RESPONSES: false,

    // ===== 🎨 UI COLORS =====
    COLORS: {
        SBERBANK: '#00a650',
        GOLD: '#ffd700',
        MOEX: '#dc3545',
        SUCCESS: '#28a745',
        ERROR: '#dc3545',
        WARNING: '#ffc107',
        INFO: '#17a2b8'
    },

    // ===== 📱 RESPONSIVE BREAKPOINTS =====
    BREAKPOINTS: {
        MOBILE: 768,
        TABLET: 1024,
        DESKTOP: 1200
    }
};

/**
 * 🔧 Environment Validator
 * Checks if all required settings are configured
 */
Environment.validate = function () {
    const issues = [];

    // Check required API key
    if (!this.GEMINI_API_KEY || this.GEMINI_API_KEY === 'YOUR_GEMINI_API_KEY_HERE') {
        issues.push('❌ GEMINI_API_KEY not configured');
    }

    // Check numeric values
    if (typeof this.API_TIMEOUT !== 'number' || this.API_TIMEOUT <= 0) {
        issues.push('❌ API_TIMEOUT must be a positive number');
    }

    if (typeof this.MESSAGES_PER_DAY !== 'number' || this.MESSAGES_PER_DAY <= 0) {
        issues.push('❌ MESSAGES_PER_DAY must be a positive number');
    }

    // Check environment
    if (!['development', 'production'].includes(this.APP_ENVIRONMENT)) {
        issues.push('❌ APP_ENVIRONMENT must be "development" or "production"');
    }

    return {
        valid: issues.length === 0,
        issues: issues,
        summary: issues.length === 0 ? '✅ All settings configured correctly' : `⚠️ ${issues.length} configuration issues found`
    };
};

/**
 * 🎯 Get environment value with fallback
 */
Environment.get = function (key, fallback = null) {
    return this[key] !== undefined ? this[key] : fallback;
};

/**
 * 🔄 Set environment value
 */
Environment.set = function (key, value) {
    this[key] = value;
    // Persist API key so other pages (chat.html) can pick it up after setup.html
    try {
        if (key === 'GEMINI_API_KEY' && typeof localStorage !== 'undefined') {
            if (value && value !== 'YOUR_GEMINI_API_KEY_HERE') {
                localStorage.setItem('GEMINI_API_KEY', value);
            } else {
                localStorage.removeItem('GEMINI_API_KEY');
            }
        }

        if (key === 'GEMINI_MODEL' && typeof localStorage !== 'undefined') {
            localStorage.setItem('GEMINI_MODEL', value);
            // Automatically update Base URL
            // DO NOT overwrite GEMINI_BASE_URL - we must use the backend proxy
            // this.GEMINI_BASE_URL = `https://generativelanguage.googleapis.com/v1beta/models/${value}:generateContent`;
        }
    } catch (_) { /* ignore storage errors */ }
    this.notifyChange(key, value);
};

/**
 * 📢 Notify other components of environment changes
 */
Environment.notifyChange = function (key, value) {
    // Update Config if available
    if (typeof window !== 'undefined' && window.Config) {
        if (key === 'GEMINI_API_KEY') {
            window.Config.set('api.gemini.apiKey', value);
        }
    }

    // Update GeminiAI if available
    if (typeof window !== 'undefined' && window.GeminiAI && key === 'GEMINI_API_KEY') {
        window.GeminiAI.setApiKey(value);
        // Trigger reinitialization
        window.GeminiAI.retryInitialization();
    }

    // Log change in debug mode
    if (this.ENABLE_DEBUG_MODE) {
        console.log(`🔧 Environment updated: ${key} = ${key.includes('KEY') || key.includes('PASSWORD') ? '***' : value}`);
    }
};

/**
 * 🚀 Initialize environment
 */
Environment.init = function () {
    console.log(`🚀 ${this.APP_NAME} v${this.APP_VERSION}`);
    console.log(`🌍 Environment: ${this.APP_ENVIRONMENT}`);

    // Load persisted API key from localStorage removal
    // We do NOT want to load GEMINI_API_KEY from localStorage anymore because
    // it used to store the direct Google Key, but now we need the Backend Access Key.
    // Keeping this commented out to prevent "taking key from wrong place".
    /* 
    try {
        if (typeof localStorage !== 'undefined') {
            const storedKey = localStorage.getItem('GEMINI_API_KEY');
            if (storedKey && storedKey !== 'YOUR_GEMINI_API_KEY_HERE') {
                this.GEMINI_API_KEY = storedKey;
            }
        }
    } catch (_) { } 
    */

    // Load persisted Model preference
    try {
        if (typeof localStorage !== 'undefined') {
            const storedModel = localStorage.getItem('GEMINI_MODEL');
            if (storedModel) {
                this.GEMINI_MODEL = storedModel;
                // DO NOT overwrite GEMINI_BASE_URL - we must use the backend proxy
                // this.GEMINI_BASE_URL = `https://generativelanguage.googleapis.com/v1beta/models/${storedModel}:generateContent`;
            }
        }
    } catch (_) { /* ignore */ }

    // Validate configuration
    const validation = this.validate();
    console.log(validation.summary);

    if (!validation.valid) {
        console.warn('⚠️ Configuration issues:');
        validation.issues.forEach(issue => console.warn(`  ${issue}`));
    }

    // Apply settings to other modules
    this.applyToModules();

    // Set production optimizations
    if (this.APP_ENVIRONMENT === 'production') {
        this.LOG_API_CALLS = false;
        this.LOG_USER_ACTIONS = false;
        this.SHOW_ERROR_DETAILS = false;
        this.ENABLE_DEBUG_MODE = false;
    }

    return validation;
};

/**
 * ⚙️ Apply environment settings to other modules
 */
Environment.applyToModules = function () {
    // Update Config module
    if (typeof window !== 'undefined' && window.Config) {
        window.Config.api.gemini.apiKey = this.GEMINI_API_KEY;
        window.Config.api.gemini.timeout = this.API_TIMEOUT;
        window.Config.api.gemini.maxRetries = this.API_MAX_RETRIES;
        window.Config.limits.messagesPerDay = this.MESSAGES_PER_DAY;
        window.Config.limits.maxMessageLength = this.MAX_MESSAGE_LENGTH;
        window.Config.limits.maxConversationHistory = this.MAX_CONVERSATION_HISTORY;
        window.Config.features.aiResponses = this.ENABLE_AI_RESPONSES;
        window.Config.features.userRegistration = this.ENABLE_USER_REGISTRATION;
        window.Config.features.paywall = this.ENABLE_PAYWALL;
        window.Config.debug.logApiCalls = this.LOG_API_CALLS;
        window.Config.debug.logUserActions = this.LOG_USER_ACTIONS;
        window.Config.debug.showErrorDetails = this.SHOW_ERROR_DETAILS;
    }

    // Update GeminiAI module
    if (typeof window !== 'undefined' && window.GeminiAI) {
        window.GeminiAI.setApiKey(this.GEMINI_API_KEY);
        window.GeminiAI.timeout = this.API_TIMEOUT;
        window.GeminiAI.maxRetries = this.API_MAX_RETRIES;
        // Force reinitialization with new settings
        window.GeminiAI.retryInitialization();
    }
};

/**
 * 📊 Get environment status
 */
Environment.getStatus = function () {
    return {
        timestamp: new Date().toISOString(),
        environment: this.APP_ENVIRONMENT,
        version: this.APP_VERSION,
        apiConfigured: this.GEMINI_API_KEY !== 'YOUR_GEMINI_API_KEY_HERE',
        featuresEnabled: {
            ai: this.ENABLE_AI_RESPONSES,
            registration: this.ENABLE_USER_REGISTRATION,
            paywall: this.ENABLE_PAYWALL,
            analytics: this.ENABLE_ANALYTICS,
            debug: this.ENABLE_DEBUG_MODE
        },
        limits: {
            messagesPerDay: this.MESSAGES_PER_DAY,
            apiTimeout: this.API_TIMEOUT,
            maxRetries: this.API_MAX_RETRIES
        }
    };
};

/**
 * 💾 Export configuration for backup
 */
Environment.export = function () {
    const config = { ...this };

    // Remove functions
    Object.keys(config).forEach(key => {
        if (typeof config[key] === 'function') {
            delete config[key];
        }
    });

    // Hide sensitive data
    if (config.GEMINI_API_KEY && config.GEMINI_API_KEY !== 'YOUR_GEMINI_API_KEY_HERE') {
        config.GEMINI_API_KEY = '***HIDDEN***';
    }

    return JSON.stringify(config, null, 2);
};

/**
 * 🔄 Reset to defaults
 */
Environment.reset = function () {
    this.GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE';
    this.APP_ENVIRONMENT = 'development';
    this.ENABLE_DEBUG_MODE = true;
    this.LOG_API_CALLS = true;
    this.LOG_USER_ACTIONS = true;
    this.SHOW_ERROR_DETAILS = true;
    try { if (typeof localStorage !== 'undefined') localStorage.removeItem('GEMINI_API_KEY'); } catch (_) { }

    console.log('🔄 Environment reset to defaults');
    this.init();
};

// 🌍 Make available globally
if (typeof window !== 'undefined') {
    window.Environment = Environment;

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => Environment.init());
    } else {
        Environment.init();
    }
} else if (typeof module !== 'undefined' && module.exports) {
    module.exports = Environment;
}

// 📝 Export for ES6 modules
if (typeof exports !== 'undefined') {
    exports.Environment = Environment;
}