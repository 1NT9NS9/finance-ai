/* ----------------------------- Security & Input Sanitization ----------------------------- */
class SecurityManager {
    // XSS Prevention - sanitize HTML input
    static sanitizeHTML(input) {
        if (typeof input !== 'string') return '';
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
    }
    
    // SQL Injection Prevention - sanitize for storage
    static sanitizeInput(input) {
        if (typeof input !== 'string') return '';
        return input.trim()
            .replace(/[<>]/g, '') // Remove potential HTML tags
            .replace(/javascript:/gi, '') // Remove javascript: protocol
            .replace(/on\w+=/gi, '') // Remove event handlers
            .slice(0, 1000); // Limit length
    }
    
    // Email validation
    static validateEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return emailRegex.test(email) && email.length <= 254;
    }
    
    // Validate input against common injection patterns
    static validateSafeInput(input) {
        const dangerousPatterns = [
            /<script/i,
            /javascript:/i,
            /on\w+\s*=/i,
            /eval\(/i,
            /expression\(/i,
            /vbscript:/i,
            /data:text\/html/i
        ];
        
        return !dangerousPatterns.some(pattern => pattern.test(input));
    }
    
    // Rate limiting for form submissions
    static checkRateLimit(action, limit = 5, timeWindow = 60000) {
        const key = `rateLimit_${action}`;
        const now = Date.now();
        const attempts = JSON.parse(localStorage.getItem(key) || '[]');
        
        // Remove old attempts outside time window
        const recentAttempts = attempts.filter(time => now - time < timeWindow);
        
        if (recentAttempts.length >= limit) {
            return false; // Rate limit exceeded
        }
        
        // Add current attempt
        recentAttempts.push(now);
        localStorage.setItem(key, JSON.stringify(recentAttempts));
        return true;
    }
}

/* ----------------------------- Authentication Utilities ----------------------------- */
class AuthManager {
    static isLoggedIn() {
        return !!localStorage.getItem('userName') || this.isAdmin();
    }
    
    static isAdmin() {
        return localStorage.getItem('role') === 'admin';
    }
    
    static hasSubscription() {
        return localStorage.getItem('subscribed') === 'true';
    }
    
    static getUserName() {
        return localStorage.getItem('userName') || '';
    }
    
    static getUserEmail() {
        return localStorage.getItem('userEmail') || '';
    }
    
    static canAccessFeature(featureType = 'basic') {
        if (this.isAdmin()) return true;
        
        switch (featureType) {
            case 'basic':
                return this.isLoggedIn();
            case 'premium':
                return this.isLoggedIn() && this.hasSubscription();
            default:
                return false;
        }
    }
    
    static requireAuth() {
        if (!localStorage.getItem('role')) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    }
    
    static logout() {
        localStorage.removeItem('role');
        localStorage.removeItem('userName');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('subscribed');
    }
}

// Initialize auth check on page load
document.addEventListener('DOMContentLoaded', () => {
    AuthManager.requireAuth();
});