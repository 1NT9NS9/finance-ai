/* ----------------------------- Modular Architecture ----------------------------- */

// Utility function for safe execution
function safeExecute(fn, context = 'Operation') {
    try {
        return fn();
    } catch (error) {
        console.error(`Error in ${context}:`, error);
        if (typeof window.UIModule !== 'undefined' && window.UIModule.showNotification) {
            window.UIModule.showNotification(`${context}: ${error.message || error}`, 'error');
        }
        return null;
    }
}

// UI Module - handles all UI-related functions
const UIModule = {
    // Notification system (disabled - no pop-ups)
    showNotification(message, type = 'info') {
        // Notifications disabled - do nothing
        console.log(`[${type.toUpperCase()}] ${message}`); // Log to console instead
    },

    // Loading states (disabled - no loading overlays)
    showLoading(message = 'Загрузка...') {
        // Loading overlays disabled - do nothing
        console.log(`[LOADING] ${message}`);
        return null; // Return null instead of overlay element
    },

    hideLoading() {
        // Loading overlays disabled - do nothing
        console.log('[LOADING] Hide loading called');
    },

    setButtonLoading(button, isLoading) {
        // Button loading disabled - do nothing
        console.log(`[BUTTON] Loading state: ${isLoading}`);
    }
};

// Chart Module - handles chart operations
const ChartModule = {
    createDoughnutChart(cfg) {
        return safeExecute(() => {
            if (!cfg || !cfg.canvasId || !cfg.sectors) {
                throw new Error('Некорректная конфигурация диаграммы');
            }

            const canvas = document.getElementById(cfg.canvasId);
            if (!canvas) {
                throw new Error(`Элемент canvas с ID "${cfg.canvasId}" не найден`);
            }

            const data = [];
            const colors = [];
            const labels = [];

            cfg.sectors.forEach((sector) => {
                if (!sector.companies || !Array.isArray(sector.companies)) {
                    console.warn(`Сектор "${sector.name}" не содержит корректного списка компаний`);
                    return;
                }
                
                sector.companies.forEach((company) => {
                    data.push(1);
                    colors.push(sector.color);
                    labels.push(`${sector.name}: ${typeof SecurityManager !== 'undefined' ? SecurityManager.sanitizeHTML(company) : company}`);
                });
            });

            if (data.length === 0) {
                throw new Error('Нет данных для отображения диаграммы');
            }

            const ctx = canvas.getContext("2d");
            return new Chart(ctx, {
                type: "doughnut",
                data: {
                    datasets: [{
                        data,
                        backgroundColor: colors,
                        borderWidth: 0,
                    }],
                    labels,
                },
                options: {
                    responsive: true,
                    cutout: "70%",
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    return context.label || "";
                                },
                            },
                        },
                        legend: { display: false },
                        centerTextPlugin: {
                            text: cfg.yieldText,
                            fontSize: 26,
                            color: "#fff",
                        },
                    },
                },
            });
        }, `Создание диаграммы ${cfg.canvasId}`);
    }
};

// User Module - handles user-related operations
const UserModule = {
    // Database simulation with security
    getUsers() {
        return safeExecute(() => {
            const users = localStorage.getItem('userDatabase');
            return users ? JSON.parse(users) : [];
        }, 'Получение пользователей') || [];
    },

    saveUser(userData) {
        return safeExecute(() => {
            if (!userData || !userData.email || !userData.name) {
                throw new Error('Некорректные данные пользователя');
            }
            
            // Sanitize user data before saving
            const sanitizedData = {
                ...userData,
                name: typeof SecurityManager !== 'undefined' ? SecurityManager.sanitizeHTML(userData.name) : userData.name,
                email: typeof SecurityManager !== 'undefined' ? SecurityManager.sanitizeInput(userData.email) : userData.email
            };
            
            const users = this.getUsers();
            users.push(sanitizedData);
            localStorage.setItem('userDatabase', JSON.stringify(users));
            return true;
        }, 'Сохранение пользователя');
    },

    findUser(email) {
        return safeExecute(() => {
            if (!email || typeof email !== 'string') {
                throw new Error('Некорректный email для поиска');
            }
            
            const users = this.getUsers();
            return users.find(user => user.email === email);
        }, 'Поиск пользователя');
    }
};

// Validation Module - handles all validation logic
const ValidationModule = {
    validatePassword(password) {
        const errors = [];
        
        if (password.length < 8) errors.push('минимум 8 символов');
        if (password.length > 128) errors.push('максимум 128 символов');
        if (!/[a-z]/.test(password)) errors.push('строчную букву (a-z)');
        if (!/[A-Z]/.test(password)) errors.push('заглавную букву (A-Z)');
        if (!/\d/.test(password)) errors.push('цифру (0-9)');
        if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password)) {
            errors.push('специальный символ (!@#$%^&*...)');
        }
        
        if (/(.)\1{2,}/.test(password)) {
            errors.push('не должен содержать более 2 одинаковых символов подряд');
        }
        
        const commonPatterns = [/123456/, /password/i, /qwerty/i, /admin/i, /login/i];
        if (commonPatterns.some(pattern => pattern.test(password))) {
            errors.push('не должен содержать распространенные комбинации');
        }
        
        if (errors.length > 0) {
            return `Пароль должен содержать: ${errors.join(', ')}`;
        }
        
        return null;
    },

    validateName(name) {
        const nameRegex = /^[a-zA-Zа-яёА-ЯЁ\s]+$/;
        if (!nameRegex.test(name)) {
            return 'ФИО может содержать только русские и английские буквы';
        }
        return null;
    },

    getPasswordStrength(password) {
        let score = 0;
        
        if (password.length >= 8) score += 1;
        if (password.length >= 12) score += 1;
        if (password.length >= 16) score += 1;
        if (/[a-z]/.test(password)) score += 1;
        if (/[A-Z]/.test(password)) score += 1;
        if (/\d/.test(password)) score += 1;
        if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password)) score += 1;
        
        if (password.length >= 10 && /[a-z]/.test(password) && /[A-Z]/.test(password) && /\d/.test(password) && /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/.test(password)) {
            score += 2;
        }
        
        if (score <= 3) return { strength: 'weak', color: '#dc3545', text: 'Слабый' };
        if (score <= 6) return { strength: 'medium', color: '#ffc107', text: 'Средний' };
        if (score <= 8) return { strength: 'strong', color: '#28a745', text: 'Сильный' };
        return { strength: 'very-strong', color: '#17a2b8', text: 'Очень сильный' };
    }
};

// Export modules for use in main.js
window.UIModule = UIModule;
window.ChartModule = ChartModule;
window.UserModule = UserModule;
window.ValidationModule = ValidationModule;