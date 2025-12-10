/* ----------------------------- Authentication Utilities ----------------------------- */
// AuthManager is loaded from auth-utils.js - no need to redefine here

/* ----------------------------- Loading States ----------------------------- */
// Using modular approach - functions moved to modules.js
function showLoading(message = 'Загрузка...') {
    return UIModule.showLoading(message);
}

function hideLoading() {
    return UIModule.hideLoading();
}

function setButtonLoading(button, isLoading) {
    return UIModule.setButtonLoading(button, isLoading);
}

async function withLoading(asyncFn, loadingMessage = 'Обработка...') {
    const overlay = showLoading(loadingMessage);
    try {
        const result = await asyncFn();
        return result;
    } finally {
        hideLoading();
    }
}

/* ----------------------------- Error Handling & Notifications ----------------------------- */
// Using modular approach - functions moved to modules.js
function showNotification(message, type = 'info') {
    return UIModule.showNotification(message, type);
}

function handleError(error, context = 'Неизвестная ошибка') {
    console.error(`Error in ${context}:`, error);
    showNotification(`${context}: ${error.message || error}`, 'error');
}

function safeExecute(fn, context = 'Operation') {
    try {
        return fn();
    } catch (error) {
        handleError(error, context);
        return null;
    }
}

/* ----------------------------- Chart.js Plugin ----------------------------- */
const centerTextPlugin = {
    id: "centerTextPlugin",
    beforeDraw: (chart, args, options) => {
        // Draw only if text explicitly provided
        if (!options || !options.text) return;
        const { ctx, chartArea: { width, height } } = chart;
        ctx.save();
        ctx.font = `${options.fontSize || 24}px ${options.fontFamily || "Segoe UI"}`;
        ctx.fillStyle = options.color || "#fff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(options.text), width / 2, height / 2);
    },
};

Chart.register(centerTextPlugin);

/* --------------------------- Data & Configuration -------------------------- */
// Load sectors and companies from backend portfolio1_summary.csv (via API endpoint we already have access to filesystem path for)
const chartsConfig = [];

async function loadSectorsFromSummary() {
    try {
        // Fetch CSV directly (served statically or via same origin file path won't work in browser). Use an API-style fetch we added earlier.
        const resp = await fetch('/api/portfolio1_total_capital?ts=' + Date.now(), { cache: 'no-store' }); // ping to ensure backend is up
        if (!resp.ok) throw new Error('Backend not responding');

        // First portfolio sectors from backend mapping endpoint
        let sectors = [];
        try {
            const respS = await fetch('/api/portfolio1_asset_sectors?ts=' + Date.now(), { cache: 'no-store' });
            if (respS.ok) {
                const j = await respS.json();
                const palette = ['#ff6b6b', '#ffa94d', '#4d96ff'];
                const sectorToCompanies = {};
                (j.data || []).forEach((row) => {
                    const sym = String(row.symbol || '').toUpperCase();
                    const sec = String(row.sector || 'Other');
                    if (!sectorToCompanies[sec]) sectorToCompanies[sec] = new Set();
                    sectorToCompanies[sec].add(sym);
                });
                sectors = Object.entries(sectorToCompanies).map(([name, set], idx) => ({
                    name,
                    color: palette[idx % palette.length],
                    companies: Array.from(set)
                }));
            }
        } catch (_) { /* fallback not needed here */ }
        if (!sectors.length) {
            sectors = [
                { name: 'Information technology', color: '#4d96ff', companies: ['OZON'] },
                { name: 'Oil and Gas', color: '#ffa94d', companies: ['RTGZ'] },
                { name: 'Finance', color: '#ff6b6b', companies: ['SBER'] },
            ];
        }

        chartsConfig.push({ canvasId: 'chart1', yieldText: '—', sectors });

        // Load portfolio2 sectors similarly
        // Second portfolio sectors from backend mapping endpoint
        let sectors2 = [];
        try {
            const respS2 = await fetch('/api/portfolio2_asset_sectors?ts=' + Date.now(), { cache: 'no-store' });
            if (respS2.ok) {
                const j2 = await respS2.json();
                const palette2 = ['#ff6b6b', '#ffa94d', '#4d96ff'];
                const sectorToCompanies2 = {};
                (j2.data || []).forEach((row) => {
                    const sym = String(row.symbol || '').toUpperCase();
                    const sec = String(row.sector || 'Other');
                    if (!sectorToCompanies2[sec]) sectorToCompanies2[sec] = new Set();
                    sectorToCompanies2[sec].add(sym);
                });
                sectors2 = Object.entries(sectorToCompanies2).map(([name, set], idx) => ({
                    name,
                    color: palette2[idx % palette2.length],
                    companies: Array.from(set)
                }));
            }
        } catch (_) { /* ignore */ }
        chartsConfig.push({ canvasId: 'chart2', yieldText: '—', sectors: sectors2.length ? sectors2 : sectors });



    } catch (e) {
        chartsConfig.push({ canvasId: 'chart1', yieldText: '—', sectors: [] });
        chartsConfig.push({ canvasId: 'chart2', yieldText: '—', sectors: [] });

    }
}

// Preload latest per-symbol trade snapshot from CSV into a global cache
async function preloadLastMapBySymbol() {
    try {
        const resp = await fetch('/api/portfolio1_map_last?ts=' + Date.now(), { cache: 'no-store' });
        if (!resp.ok) { window.__lastMapBySymbol = {}; return; }
        const json = await resp.json();
        const arr = (json && json.data) ? json.data : [];
        const map = {};
        arr.forEach(r => {
            const sym = String(r.symbol || '').toUpperCase();
            if (!sym) return;
            map[sym] = {
                date: r.date,
                price: Number(r.price) || 0,
                shares: Number(r.shares) || 0,
                notional: Number(r.notional) || 0,
                action: String(r.action || ''),
                realized_pnl: Number(r.realized_pnl) || 0,
            };
        });
        window.__lastMapBySymbol = map;
    } catch (_) {
        window.__lastMapBySymbol = {};
    }
}

// Preload portfolio2 latest per-symbol trade snapshot
async function preloadLastMapBySymbol2() {
    try {
        const resp = await fetch('/api/portfolio2_map_last?ts=' + Date.now(), { cache: 'no-store' });
        if (!resp.ok) { window.__lastMapBySymbol2 = {}; return; }
        const json = await resp.json();
        const arr = (json && json.data) ? json.data : [];
        const map = {};
        arr.forEach(r => {
            const sym = String(r.symbol || '').toUpperCase();
            if (!sym) return;
            map[sym] = {
                date: r.date,
                price: Number(r.price) || 0,
                shares: Number(r.shares) || 0,
                notional: Number(r.notional) || 0,
                action: String(r.action || ''),
                realized_pnl: Number(r.realized_pnl) || 0,
            };
        });
        window.__lastMapBySymbol2 = map;
    } catch (_) {
        window.__lastMapBySymbol2 = {};
    }
}

/* ------------------------------ Create Charts ------------------------------ */
// Chart creation function moved to wrapper functions section above

/* ---------------------------- Populate Stock List --------------------------- */
function populateStockList(listId, sectors) {
    const ul = document.getElementById(listId);
    sectors.forEach((sector) => {
        sector.companies.forEach((comp) => {
            const li = document.createElement("li");
            li.textContent = `${comp} (${sector.name})`;
            li.style.color = sector.color;
            ul.appendChild(li);
        });
    });
}

/* ----------------------------- Blur Handlers ------------------------------ */
function initBlurHandlers() {
    document.querySelectorAll('.blur-toggle').forEach(icon => {
        icon.addEventListener('click', () => {
            safeExecute(() => {
                // If not logged in, show login modal
                if (!AuthManager.isLoggedIn()) {
                    document.getElementById('login-modal').style.display = 'flex';
                    return;
                }

                // For basic blur removal, just being logged in is enough
                // (Subscription is only required for premium features)
                const targetId = icon.getAttribute('data-target');
                const listEl = document.getElementById(targetId);

                if (!listEl) {
                    throw new Error(`Элемент списка ${targetId} не найден`);
                }

                listEl.classList.toggle('blur');
                const iTag = icon.querySelector('i');
                if (listEl.classList.contains('blur')) {
                    iTag.classList.remove('fa-eye');
                    iTag.classList.add('fa-eye-slash');
                } else {
                    iTag.classList.remove('fa-eye-slash');
                    iTag.classList.add('fa-eye');
                }
            }, 'Переключение видимости списка');
        });
    });
}

/* ---------------------------- Top Buttons Nav ----------------------------- */
function initTopButtons() {
    document.querySelectorAll('.top-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const asset = btn.dataset.asset;
            window.open(`asset.html?asset=${asset}`, '_blank');
        });
    });
}

/* ------------------------------ News Toggle ------------------------------- */
function initNews() {
    const panel = document.getElementById('news-panel');
    const btn = document.getElementById('news-btn');
    const mainSection = document.querySelector('main');
    let newsOpen = false;
    btn.addEventListener('click', () => {
        newsOpen = !newsOpen;
        if (newsOpen) {
            panel.style.display = 'block';
            mainSection.style.display = 'none';
            showAllNewsColumns();
        } else {
            panel.style.display = 'none';
            mainSection.style.display = '';
        }
    });
}

function showAllNewsColumns() {
    const news = {
        day: ['Нефть выросла на 3%', 'ЦБ оставил ставку без изменений'],
        week: ['Индекс МосБиржи прибавил 5% за неделю', 'Рубль укрепился к доллару'],
        month: ['Фондовый рынок растёт 3-й месяц подряд', 'Инфляция замедлилась до 4.2%']
    };

    const columnsHtml = `
        <div class="news-columns">
            <div class="news-column">
                <h4>Дневные новости</h4>
                <ul>${news.day.map(n => `<li>${n}</li>`).join('')}</ul>
            </div>
            <div class="news-column">
                <h4>Недельные новости</h4>
                <ul>${news.week.map(n => `<li>${n}</li>`).join('')}</ul>
            </div>
            <div class="news-column">
                <h4>Месячные новости</h4>
                <ul>${news.month.map(n => `<li>${n}</li>`).join('')}</ul>
            </div>
        </div>
    `;

    document.getElementById('news-panel').innerHTML = columnsHtml;
}

/* -------------------- Diagram Click – rotate & comparison ------------------ */
function initDiagramClicks() {
    document.querySelectorAll('.chart-block canvas').forEach(cv => {
        cv.addEventListener('click', () => {
            cv.classList.add('rotate');
            setTimeout(() => cv.classList.remove('rotate'), 1200);
            showCompareOverlay();
        });
    });
}

function showCompareOverlay() {
    if (document.getElementById('compare-overlay')) return; // already open
    const overlay = document.createElement('div');
    overlay.id = 'compare-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;backdrop-filter:blur(6px);display:flex;justify-content:center;align-items:center;z-index:999;';
    overlay.innerHTML = `<div style="background-color:#1b1b1b;padding:24px;border-radius:16px;max-width:600px;width:90%;position:relative;">
        <span id="close-compare" style="position:absolute;top:8px;right:12px;cursor:pointer;font-size:1.2rem;">&times;</span>
        <canvas id="compare-chart"></canvas>
    </div>`;
    document.body.appendChild(overlay);
    document.getElementById('close-compare').onclick = () => overlay.remove();

    const ctx = document.getElementById('compare-chart').getContext('2d');

    const labels = Array.from({ length: 12 }, (_, i) => `М${i + 1}`);
    // Dummy yield series for current, gold, sber, moex
    function randomSeries(base) { return labels.map(() => base + Math.random() * 3 - 1.5); }
    const datasets = [
        { label: 'Текущая диаграмма', data: randomSeries(30), borderColor: '#ff6b6b', backgroundColor: 'transparent', tension: 0.3 },
        { label: 'Золото', data: randomSeries(34), borderColor: '#b49d00', backgroundColor: 'transparent', tension: 0.3 },
        { label: 'Сбербанк', data: randomSeries(8.5), borderColor: '#00a86b', backgroundColor: 'transparent', tension: 0.3 },
        { label: 'Индекс МосБиржи', data: randomSeries(12), borderColor: '#c0392b', backgroundColor: 'transparent', tension: 0.3 }
    ];

    new Chart(ctx, { type: 'line', data: { labels, datasets }, options: { responsive: true, plugins: { legend: { labels: { color: '#fff' } } }, scales: { y: { ticks: { color: '#fff' }, grid: { color: '#333' } }, x: { ticks: { color: '#fff' }, grid: { color: '#333' } } } } });
}

/* --------------------- Stock list details expansion ----------------------- */
function initStockDetails() {
    document.querySelectorAll('.stock-list li').forEach(li => {
        li.addEventListener('click', () => {
            // remove existing details if present
            const next = li.nextElementSibling;
            if (next && next.classList.contains('stock-details')) { next.remove(); return; }

            // Dummy trade history
            const trades = [
                { qty: 10, time: '2023-11-12', price: 1000 },
                { qty: 5, time: '2023-10-01', price: 950 },
                { qty: 2, time: '2023-07-20', price: 920 }
            ];
            const detail = document.createElement('div');
            detail.className = 'stock-details';
            detail.innerHTML = trades.map(t => `${t.time}: ${t.qty} шт по ${t.price} ₽`).join('<br>');
            li.parentNode.insertBefore(detail, li.nextSibling);
        });
    });
}

/* ----------------------------- Wrapper Functions for Modules ----------------------------- */
// Wrapper functions to maintain backward compatibility
function getUsers() {
    return UserModule.getUsers();
}

function saveUser(userData) {
    return UserModule.saveUser(userData);
}

function findUser(email) {
    return UserModule.findUser(email);
}

function validatePassword(password) {
    return ValidationModule.validatePassword(password);
}

function getPasswordStrength(password) {
    return ValidationModule.getPasswordStrength(password);
}

function validateName(name) {
    return ValidationModule.validateName(name);
}

function createDoughnutChart(cfg) {
    return ChartModule.createDoughnutChart(cfg);
}

function updateLoginButton() {
    const loginBtn = document.getElementById('login-btn');
    if (!loginBtn) return; // sidebar login removed
    const userEmail = localStorage.getItem('userEmail');
    const userName = localStorage.getItem('userName');

    if (userEmail || userName) {
        const displayText = userEmail || userName;
        loginBtn.innerHTML = `<i class="fa-solid fa-user"></i> ${displayText}`;
        loginBtn.className = 'user-name-btn';
        loginBtn.onclick = toggleUserMenu;
    } else {
        loginBtn.innerHTML = '<i class="fa-solid fa-user"></i> Войти';
        loginBtn.className = 'login-btn';
        loginBtn.onclick = () => document.getElementById('login-modal').style.display = 'flex';
    }
}

function toggleUserMenu() {
    const userMenu = document.getElementById('user-menu');
    if (userMenu) userMenu.classList.toggle('open');
}

function logout() {
    safeExecute(() => {
        AuthManager.logout();
        const um = document.getElementById('user-menu');
        if (um) um.classList.remove('open');
        updateLoginButton();
        updateUserBadge();
        showNotification('Вы вышли из аккаунта', 'info');
    }, 'Выход из аккаунта');
}

/* ----------------------------- Login Modal ----------------------------- */
function initLoginModal() {
    const modal = document.getElementById('login-modal');
    const loginBtn = document.getElementById('login-btn');
    const closeBtn = document.getElementById('close-login');

    // Update button on page load
    updateLoginButton();

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            if (!localStorage.getItem('userName')) {
                modal.style.display = 'flex';
            }
        });
    }

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Password toggle functionality
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const targetId = toggle.dataset.target;
            const input = document.getElementById(targetId);
            const icon = toggle.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            }
        });
    });

    // Password strength indicator for registration
    const registerPasswordInput = document.getElementById('register-password');
    if (registerPasswordInput) {
        registerPasswordInput.addEventListener('input', () => {
            const password = registerPasswordInput.value;
            const strengthContainer = document.getElementById('password-strength');
            const strengthText = document.getElementById('strength-text');
            const strengthScore = document.getElementById('strength-score');
            const strengthFill = document.getElementById('strength-fill');

            if (password.length === 0) {
                strengthContainer.style.display = 'none';
                return;
            }

            strengthContainer.style.display = 'block';
            const strength = ValidationModule.getPasswordStrength(password);

            strengthText.textContent = 'Сила пароля:';
            strengthScore.textContent = strength.text;
            strengthScore.style.color = strength.color;

            // Update progress bar
            const widthMap = {
                'weak': '25%',
                'medium': '50%',
                'strong': '75%',
                'very-strong': '100%'
            };

            strengthFill.style.width = widthMap[strength.strength];
            strengthFill.style.backgroundColor = strength.color;
        });
    }

    // User menu functionality
    const subEl = document.getElementById('subscription');
    if (subEl) {
        subEl.addEventListener('click', () => {
            const um = document.getElementById('user-menu');
            if (um) um.classList.remove('open');
            window.open('subscription.html', '_blank');
        });
    }

    const logoutEl = document.getElementById('logout');
    if (logoutEl) {
        logoutEl.addEventListener('click', () => {
            logout();
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const userMenu = document.getElementById('user-menu');
        const loginBtn = document.getElementById('login-btn');
        if (!userMenu) return;
        if (!userMenu.contains(e.target) && (!loginBtn || !loginBtn.contains(e.target))) {
            userMenu.classList.remove('open');
        }
    });

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;

            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');

            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(targetTab + '-form').classList.add('active');
        });
    });

    // Login form submit
    document.getElementById('submit-login').addEventListener('click', async () => {
        console.log('Login button clicked');

        try {
            // Rate limiting check
            if (!SecurityManager.checkRateLimit('login', 5, 60000)) {
                alert('Слишком много попыток входа. Попробуйте позже.');
                return;
            }

            const email = SecurityManager.sanitizeInput(document.getElementById('login-email').value);
            const password = document.getElementById('login-password').value;

            console.log('Login attempt:', { email, password: password ? '***' : 'empty' });

            if (!email || !password) {
                alert('Заполните все поля');
                return;
            }

            // Security validation
            if (!SecurityManager.validateEmail(email)) {
                alert('Некорректный формат email');
                return;
            }

            if (!SecurityManager.validateSafeInput(email) || !SecurityManager.validateSafeInput(password)) {
                alert('Обнаружены недопустимые символы');
                return;
            }

            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 500));

            const user = findUser(email);
            if (!user) {
                alert('Такой пользователь не зарегистрирован');
                return;
            }

            if (user.password !== password) {
                alert('Вы указали неверный пароль');
                return;
            }

            // Successful login
            localStorage.setItem('role', 'user');
            localStorage.setItem('userEmail', email);
            localStorage.setItem('userName', SecurityManager.sanitizeHTML(user.name));
            modal.style.display = 'none';
            updateLoginButton();
            updateUserBadge();

            console.log('Login successful');
            alert('Вход выполнен успешно!');

        } catch (error) {
            console.error('Login error:', error);
            alert('Ошибка при входе: ' + error.message);
        }
    });

    // Register form submit
    document.getElementById('submit-register').addEventListener('click', async () => {
        console.log('Register button clicked');

        try {
            // Rate limiting check
            if (!SecurityManager.checkRateLimit('register', 3, 300000)) { // 3 attempts per 5 min
                alert('Слишком много попыток регистрации. Попробуйте позже.');
                return;
            }

            const name = SecurityManager.sanitizeInput(document.getElementById('register-name').value);
            const email = SecurityManager.sanitizeInput(document.getElementById('register-email').value);
            const password = document.getElementById('register-password').value;

            console.log('Form data:', { name, email, password: password ? '***' : 'empty' });

            if (!name || !email || !password) {
                alert('Заполните все поля');
                return;
            }

            // Security validation
            if (!SecurityManager.validateEmail(email)) {
                alert('Некорректный формат email');
                return;
            }

            if (!SecurityManager.validateSafeInput(name) || !SecurityManager.validateSafeInput(email) || !SecurityManager.validateSafeInput(password)) {
                alert('Обнаружены недопустимые символы');
                return;
            }

            // Validate name
            const nameError = validateName(name);
            if (nameError) {
                alert(nameError);
                return;
            }

            // Validate password
            const passwordError = validatePassword(password);
            if (passwordError) {
                alert(passwordError);
                return;
            }

            // Check if user already exists
            if (findUser(email)) {
                alert('Пользователь с таким email уже зарегистрирован');
                return;
            }

            // Simulate API call delay
            await new Promise(resolve => setTimeout(resolve, 800));

            // Save user to database with sanitized data
            const userData = {
                name: SecurityManager.sanitizeHTML(name),
                email: email, // Already validated
                password: password, // Store as-is for now (in production, hash this!)
                registeredAt: new Date().toISOString()
            };

            console.log('Saving user data:', userData);
            saveUser(userData);

            // Auto login after registration
            localStorage.setItem('role', 'user');
            localStorage.setItem('userEmail', email);
            localStorage.setItem('userName', SecurityManager.sanitizeHTML(name));
            modal.style.display = 'none';
            updateLoginButton();
            updateUserBadge();

            console.log('Registration successful');
            alert('Регистрация выполнена успешно!');

        } catch (error) {
            console.error('Registration error:', error);
            alert('Ошибка при регистрации: ' + error.message);
        }
    });
}

/* ----------------------------- Custom Scrollbar for Main Page ----------------------------- */
class MainCustomScrollbar {
    constructor() {
        this.messagesContainer = document.getElementById('content-messages');
        this.scrollbar = document.querySelector('.main-custom-scrollbar');
        this.thumb = document.querySelector('.main-custom-scrollbar-thumb');

        if (!this.messagesContainer || !this.scrollbar || !this.thumb) {
            console.warn('Main scrollbar elements not found');
            return;
        }

        this.isDragging = false;
        this.startY = 0;
        this.startScrollTop = 0;

        this.init();
    }

    init() {
        this.updateScrollbar();
        this.attachEvents();

        // Update scrollbar when content changes
        const observer = new MutationObserver(() => this.updateScrollbar());
        observer.observe(this.messagesContainer, { childList: true, subtree: true });

        // Update on resize
        window.addEventListener('resize', () => this.updateScrollbar());
    }

    attachEvents() {
        // Mouse wheel scrolling anywhere on screen
        document.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });

        // Thumb drag events
        this.thumb.addEventListener('mousedown', (e) => this.startDrag(e));
        document.addEventListener('mousemove', (e) => this.onDrag(e));
        document.addEventListener('mouseup', () => this.stopDrag());

        // Click on scrollbar track
        this.scrollbar.addEventListener('click', (e) => this.onTrackClick(e));

        // Update when container scrolls
        this.messagesContainer.addEventListener('scroll', () => this.updateScrollbar());
    }

    updateScrollbar() {
        const container = this.messagesContainer;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;

        if (scrollHeight <= clientHeight) {
            this.thumb.style.display = 'none';
            return;
        }

        this.thumb.style.display = 'block';

        const thumbHeight = Math.max(20, (clientHeight / scrollHeight) * window.innerHeight);
        const scrollRatio = container.scrollTop / (scrollHeight - clientHeight);
        const thumbTop = scrollRatio * (window.innerHeight - thumbHeight);

        this.thumb.style.height = thumbHeight + 'px';
        this.thumb.style.top = thumbTop + 'px';
    }

    startDrag(e) {
        e.preventDefault();
        this.isDragging = true;
        this.startY = e.clientY;
        this.startScrollTop = this.messagesContainer.scrollTop;
        document.body.style.userSelect = 'none';
    }

    onDrag(e) {
        if (!this.isDragging) return;

        e.preventDefault();
        const deltaY = e.clientY - this.startY;
        const container = this.messagesContainer;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;
        const maxScroll = scrollHeight - clientHeight;

        const scrollRatio = deltaY / (window.innerHeight - this.thumb.offsetHeight);
        const newScrollTop = this.startScrollTop + (scrollRatio * maxScroll);

        container.scrollTop = Math.max(0, Math.min(maxScroll, newScrollTop));
    }

    stopDrag() {
        this.isDragging = false;
        document.body.style.userSelect = '';
    }

    onTrackClick(e) {
        if (e.target === this.thumb) return;

        const container = this.messagesContainer;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;
        const maxScroll = scrollHeight - clientHeight;

        const clickY = e.clientY;
        const thumbHeight = this.thumb.offsetHeight;

        const scrollRatio = (clickY - thumbHeight / 2) / (window.innerHeight - thumbHeight);
        container.scrollTop = scrollRatio * maxScroll;
    }

    onWheel(e) {
        const container = this.messagesContainer;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;

        // Only handle wheel events if content overflows
        if (scrollHeight <= clientHeight) return;

        // Check if we're not in an input field
        const target = e.target;
        const isInputField = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
        const isScrollableElement = target.scrollHeight > target.clientHeight && target !== document.body;

        if (isInputField || (isScrollableElement && target !== this.messagesContainer)) {
            return;
        }

        e.preventDefault();

        // Use standard website scrolling behavior
        let scrollAmount;

        if (e.deltaMode === 0) {
            scrollAmount = e.deltaY;
        } else if (e.deltaMode === 1) {
            scrollAmount = e.deltaY * 16;
        } else {
            scrollAmount = e.deltaY * clientHeight;
        }

        container.scrollTop += scrollAmount;

        const maxScroll = scrollHeight - clientHeight;
        if (container.scrollTop < 0) container.scrollTop = 0;
        if (container.scrollTop > maxScroll) container.scrollTop = maxScroll;
    }
}

/* ----------------------------- Chat-Style Chart Display ----------------------------- */
async function displayChartsAsMessages() {
    const chartsContainer = document.getElementById('charts-container');
    if (!chartsContainer) return;

    // Clear existing content
    chartsContainer.innerHTML = '';

    // Helper: compute average annual (CAGR) from portfolio total capital
    const computePortfolioAnnualYield = async () => {
        try {
            const resp = await fetch('/api/portfolio1_total_capital?ts=' + Date.now(), { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const json = await resp.json();
            const rows = json.data || [];
            if (!rows.length) return null;
            const base = Number(rows[0].total_capital);
            const last = Number(rows[rows.length - 1].total_capital);
            const start = new Date(rows[0].date + 'T00:00:00');
            const end = new Date(rows[rows.length - 1].date + 'T00:00:00');
            const days = Math.max(1, (end - start) / (1000 * 60 * 60 * 24));
            const cagr = Math.pow(last / base, 365 / days) - 1;
            return cagr * 100; // percent
        } catch (_) {
            return null;
        }
    };

    // Compute annualized yield (CAGR) for portfolio 2
    const computePortfolio2AnnualYield = async () => {
        try {
            const resp = await fetch('/api/portfolio2_total_capital?ts=' + Date.now(), { cache: 'no-store' });
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const json = await resp.json();
            const rows = json.data || [];
            if (!rows.length) return null;
            const base = Number(rows[0].equity);
            const last = Number(rows[rows.length - 1].equity);
            const start = new Date(rows[0].date + 'T00:00:00');
            const end = new Date(rows[rows.length - 1].date + 'T00:00:00');
            const days = Math.max(1, (end - start) / (1000 * 60 * 60 * 24));
            const cagr = Math.pow(last / base, 365 / days) - 1;
            return cagr * 100; // percent
        } catch (_) {
            return null;
        }
    };

    // Always reload latest CSV snapshot to reflect file changes (both portfolios)
    await preloadLastMapBySymbol();
    await preloadLastMapBySymbol2();

    chartsConfig.forEach((config, index) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chart-message';

        // Combined container for chart and stock list
        const combinedContainer = document.createElement('div');
        combinedContainer.className = 'chart-and-list-container';

        // Chart container
        const chartDiv = document.createElement('div');
        chartDiv.className = 'chart-container';
        chartDiv.setAttribute('data-chart-index', index);

        const canvas = document.createElement('canvas');
        canvas.id = `main-chart${index + 1}`;
        canvas.style.width = '100%';
        canvas.style.height = 'auto';

        chartDiv.appendChild(canvas);

        // Stock list container
        const stockListDiv = document.createElement('div');
        stockListDiv.className = 'stock-list-in-message';
        stockListDiv.style.position = 'relative';

        // Blur toggle button (no title, just the toggle)
        const blurToggle = document.createElement('button');
        blurToggle.className = 'blur-toggle';
        blurToggle.setAttribute('data-target', `message-list${index + 1}`);
        blurToggle.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';

        const stockList = document.createElement('ul');
        stockList.id = `message-list${index + 1}`;
        stockList.className = 'blur';

        // Populate stock list with expandable items - show all stocks for scrolling
        let stockIndex = 0;
        config.sectors.forEach(sector => {
            sector.companies.forEach((company, companyIndex) => {
                const li = document.createElement('li');
                li.className = 'stock-item';
                li.setAttribute('data-company', company);

                const recMap = (index === 1 ? (window.__lastMapBySymbol2 || {}) : (window.__lastMapBySymbol || {}));
                const rec = recMap[String(company).toUpperCase()] || {};
                const yield = Number(rec.notional) || 0; // 26854.83 for OZON
                const price = Number(rec.price) || 0; // 4424.0 for OZON
                const quantity = Number(rec.shares) || 0; // 6 for OZON
                const date = rec.date ? new Date(rec.date + 'T00:00:00') : new Date(NaN); // 2025-08-11 for OZON

                li.innerHTML = `
                    <div class="stock-header">
                        <span>${company}</span>
                        <span style="color: ${sector.color}">${yield.toLocaleString('ru-RU')}</span>
                    </div>
                    <div class="stock-details">
                        <p><strong>Дата сделки:</strong> ${isNaN(date.getTime()) ? '-' : date.toLocaleDateString('ru-RU')}</p>
                        <p><strong>Действие:</strong> ${rec.action ? String(rec.action).toUpperCase() : '-'}</p>
                        <p><strong>Цена:</strong> ${price.toLocaleString('ru-RU')} ₽</p>
                        <p><strong>Количество:</strong> ${quantity.toLocaleString('ru-RU')} шт.</p>
                        <p><strong>Позиция:</strong> ${(price * quantity || yield).toLocaleString('ru-RU')} ₽</p>
                        <p><strong>Реализ. PnL:</strong> ${(Number(rec.realized_pnl) || 0).toLocaleString('ru-RU')} ₽</p>
                    </div>
                `;
                stockList.appendChild(li);
                stockIndex++;
            });
        });

        stockListDiv.appendChild(blurToggle);
        stockListDiv.appendChild(stockList);

        // Assemble combined container
        combinedContainer.appendChild(chartDiv);
        combinedContainer.appendChild(stockListDiv);

        // Assemble message
        messageDiv.appendChild(combinedContainer);

        chartsContainer.appendChild(messageDiv);

        // Create chart (for first chart, override yield with portfolio annualized yield)
        if (index === 0) {
            computePortfolioAnnualYield().then((pct) => {
                const newCfg = { ...config };
                if (pct !== null && isFinite(pct)) {
                    newCfg.yieldText = `${pct.toFixed(1)}%`;
                }
                createDoughnutChart({
                    ...newCfg,
                    canvasId: `main-chart${index + 1}`
                });
            }).catch(() => {
                createDoughnutChart({
                    ...config,
                    canvasId: `main-chart${index + 1}`
                });
            });
        } else {
            if (index === 1) {
                computePortfolio2AnnualYield().then((pct) => {
                    const newCfg = { ...config };
                    if (pct !== null && isFinite(pct)) {
                        newCfg.yieldText = `${pct.toFixed(1)}%`;
                    }
                    createDoughnutChart({
                        ...newCfg,
                        canvasId: `main-chart${index + 1}`
                    });
                }).catch(() => {
                    createDoughnutChart({
                        ...config,
                        canvasId: `main-chart${index + 1}`
                    });
                });
            } else {
                createDoughnutChart({
                    ...config,
                    canvasId: `main-chart${index + 1}`
                });
            }
        }
    });

    // Re-initialize handlers
    initBlurHandlers();
    initStockExpansion();
    initChartRotation();
}

/* ----------------------------- Sidebar Navigation ----------------------------- */
function initSidebarNavigation() {
    const sidebarItems = document.querySelectorAll('.sidebar-item[data-section]');

    sidebarItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active class from all items
            sidebarItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');

            const section = item.getAttribute('data-section');
            handleSectionSwitch(section);
        });
    });
}

function handleSectionSwitch(section) {
    const contentMessages = document.getElementById('content-messages');

    switch (section) {
        case 'dashboard':
            // Dashboard content is already in HTML, just update charts
            if (!document.getElementById('charts-container')) {
                // Fallback if charts container doesn't exist
                contentMessages.innerHTML = `
                    <!-- Top rate buttons -->
                    <div class="top-rates-main">
                        <button class="top-rate-button" data-asset="gold">Доходность золота</button>
                        <button class="top-rate-button" data-asset="sber">Ставка вклада Сбербанка</button>
                        <button class="top-rate-button" data-asset="moex">Доходность индекса МосБиржи</button>
                    </div>
                    
                    <!-- Quote bar -->
                    <div class="quote-bar-main">
                        <i class="fa-solid fa-newspaper news-icon"></i>
                        <span class="quote-text">"Лучшее время для инвестиций было вчера. Второе лучшее время – сегодня." Уоррен Баффетт</span>
                        <div class="guest-badge" id="user-badge">Войти</div>
                    </div>
                    
                    <div id="charts-container"></div>
                `;
            }
            displayChartsAsMessages();
            // Re-initialize top button handlers
            initTopButtons();
            // Update user badge
            updateUserBadge();
            break;

        case 'portfolio':
            contentMessages.innerHTML = `
                <div class="content-message">
                    <h2>Портфолио</h2>
                    <p>Создайте свой инвестиционный портфель на основе анализа рынка.</p>
                    <div style="margin: 20px 0;">
                        <a href="chat.html" style="display: inline-block; padding: 12px 24px; background: #4ade80; color: #000; text-decoration: none; border-radius: 8px; font-weight: 600;">
                            Создать портфель
                        </a>
                    </div>
                </div>
            `;
            break;

        case 'news':
            contentMessages.innerHTML = `
                <div class="content-message">
                    <h2>Новости рынка</h2>
                    <p>Последние новости и аналитика российского фондового рынка.</p>
                </div>
                <div class="content-message">
                    <div id="news-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin: 20px 0;">
                        <div class="news-card" data-id="daily" data-source="interfax" style="background: #2a2a2a; padding: 16px; border-radius: 8px; cursor: pointer;">
                            <h4>Дневные новости</h4>
                            <p>Только сегодня и только сейчас</p>
                            <p>Горячие новости</p>
                            <p>Будь первым кто узнает об этом!</p>
                        </div>
                        <div class="news-card" data-id="weekly" data-source="interfax" style="background: #2a2a2a; padding: 16px; border-radius: 8px; cursor: pointer;">
                            <h4>Недельные новости</h4>
                            <p>Еще теплые, но уже негорячие</p>
                            <p>Серебро не золото, но тоже ценно</p>
                            <p>Кто успел тот и съел!</p>
                        </div>
                    </div>
                </div>
            `;
            initNewsCards();
            break;

        case 'analytics':
            contentMessages.innerHTML = `
                <div class="content-message">
                    <h2>Аналитика</h2>
                    <p>Глубокий анализ рынка и прогнозы экспертов.</p>
                </div>
                <div class="content-message">
                    <div style="background: linear-gradient(135deg,#2d2d2d 0%, #252525 50%, #1f1f1f 100%); padding: 20px; border-radius: 12px; margin: 20px 0; border: 1px solid #3a3a3a; display:flex; flex-direction:column; gap:12px; align-items:center; text-align:center;">
                        <div style="display:flex; align-items:center; gap:10px; color:#fff;">
                            <i class="fa-solid fa-crown" style="color:#fbbf24;"></i>
                            <span style="font-weight:700;">Доступно по подписке</span>
                        </div>
                        <div style="opacity:.9;">Получите доступ к сравнительным графикам доходности и расширенной аналитике.</div>
                        <button id="analytics-subscribe-btn" style="margin-top:4px; padding:12px 16px; border:none; border-radius:10px; background: linear-gradient(135deg,#4ade80,#16a34a); color:#000; font-weight:700; cursor:pointer;">Подписаться</button>
                    </div>
                </div>
            `;
            {
                const abtn = document.getElementById('analytics-subscribe-btn');
                if (abtn) abtn.onclick = () => window.open('subscription.html', '_blank');
            }
            break;

        case 'settings':
            contentMessages.innerHTML = `
                <div class="content-message">
                    <h2>Настройки</h2>
                    <p>Управление параметрами системы и персонализация интерфейса.</p>
                </div>
                <div class="content-message">
                    <div style="background:#2a2a2a;padding:20px;border-radius:8px;margin:20px auto;max-width:420px;display:flex;flex-direction:column;gap:12px;">
                        <button id="settings-subscribe" style="padding:12px 16px;border:none;border-radius:10px;background:linear-gradient(135deg,#4ade80,#16a34a);color:#000;font-weight:700;cursor:pointer;">Подписаться</button>
                        <button id="settings-telegram" style="padding:12px 16px;border:none;border-radius:10px;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#fff;font-weight:600;cursor:pointer;">Telegram</button>
                    </div>
                </div>
            `;
            {
                const btnSub = document.getElementById('settings-subscribe');
                if (btnSub) btnSub.onclick = () => window.open('subscription.html', '_blank');
                const btnTg = document.getElementById('settings-telegram');
                if (btnTg) btnTg.onclick = () => window.open('https://t.me/your_channel', '_blank');
            }
            break;
    }

    // Scroll to top
    contentMessages.scrollTop = 0;

    // No dynamic news wiring in static mode
}

/* ----------------------------- News Cards: expand one, hide others, fetch source ----------------------------- */
function initNewsCards() {
    const grid = document.getElementById('news-cards');
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll('.news-card'));
    cards.forEach(card => {
        card.addEventListener('click', async (ev) => {
            // Prevent double-activation while expanded
            if (card.dataset.expanded === 'true') return;
            // Hide other cards
            cards.forEach(c => { if (c !== card) c.style.display = 'none'; });
            // Expand clicked card to full width
            grid.style.gridTemplateColumns = '1fr';
            card.style.cursor = 'default';
            card.dataset.expanded = 'true';

            // Show loading state
            const prevHtml = card.innerHTML;
            card.innerHTML = `
                <div style="display:flex;justify-content:flex-start;align-items:center;margin-bottom:8px;">
                    <button id="news-back" style="background:#444;color:#fff;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;">Назад</button>
                </div>
                <h4 style="margin:4px 0 8px 0;">${card.querySelector('h4')?.textContent || 'Новости'}</h4>
                <div id="news-loading" style="opacity:.8;">Загрузка новостей...</div>
                <div id="news-list" style="display:flex;flex-direction:column;gap:10px;margin-top:8px;"></div>
            `;

            const source = card.getAttribute('data-source') || 'interfax';
            const cardId = card.getAttribute('data-id') || '';

            // Attach Back immediately so it always works
            const backBtn = card.querySelector('#news-back');
            if (backBtn) {
                backBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(250px, 1fr))';
                    cards.forEach(c => { c.style.display = ''; });
                    card.innerHTML = prevHtml;
                    delete card.dataset.expanded;
                    initNewsCards();
                });
            }

            // No external link in expanded view

            try {
                // Try backend endpoint if available; fall back to client-side fetch via RSS2JSON proxy if CORS blocks
                let items = [];
                try {
                    const resp = await fetch(`/api/news?source=${encodeURIComponent(source)}&limit=20`, { cache: 'no-store' });
                    if (resp.ok) {
                        const data = await resp.json();
                        items = Array.isArray(data.items) ? data.items : [];
                    } else {
                        throw new Error('backend failed');
                    }
                } catch (_) {
                    // Optional: skip external proxy to avoid CORS; keep static message instead
                }

                const list = card.querySelector('#news-list');
                const loading = card.querySelector('#news-loading');
                if (loading) loading.remove();

                // Weekly starts from the 7th item (skip first 6)
                if (cardId === 'weekly' && items.length > 6) {
                    items = items.slice(6);
                }

                if (!items.length && list) {
                    // Fallback static items for better UX
                    list.innerHTML = [
                        { t: 'Сбербанк показал рост на 3.2%', d: 'Капитализация компании увеличилась на фоне рыночного роста.' },
                        { t: 'Газпром объявил о дивидендах', d: 'Совет директоров рекомендовал дивиденды по итогам года.' },
                        { t: 'Рубль укрепился к доллару', d: 'Рубль укрепился на фоне роста цен на нефть.' }
                    ].map(it => `
                        <div style="background:#1f1f1f;border-radius:8px;padding:10px;">
                            <div style=\"font-weight:600;margin-bottom:6px;\">${it.t}</div>
                            <div style=\"font-size:13px;opacity:.9;\">${it.d}</div>
                        </div>
                    `).join('');
                } else {
                    list.innerHTML = items.map(it => {
                        const t = (it.title || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        const d = (it.description || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                        const l = '#';
                        const p = it.published_at || '';
                        const publishedHtml = cardId === 'weekly' ? '' : `<span>${p}</span>`;
                        return `
                            <div style="background:#1f1f1f;border-radius:8px;padding:10px;">
                                <div style="font-weight:600;margin-bottom:6px;">${t}</div>
                                <div style="font-size:13px;opacity:.9;">${d}</div>
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:12px;opacity:.8;">
                                    ${publishedHtml}
                                    <span></span>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            } catch (err) {
                const list = card.querySelector('#news-list');
                const loading = card.querySelector('#news-loading');
                if (loading) loading.remove();
                if (list) list.innerHTML = `<div style="color:#f87171;">Ошибка загрузки новостей</div>`;
            }
        });
    });
}

/* ----------------------------- Stock Expansion Functionality ----------------------------- */
function initStockExpansion() {
    document.querySelectorAll('.stock-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const details = item.querySelector('.stock-details');
            if (details) {
                details.classList.toggle('expanded');
            }
        });
    });
}

/* ----------------------------- Chart Rotation and Comparison ----------------------------- */
function initChartRotation() {
    document.querySelectorAll('.chart-container').forEach(container => {
        container.addEventListener('click', (e) => {
            e.stopPropagation();
            const chartIndex = container.getAttribute('data-chart-index');

            // Add rotation effect
            container.classList.add('rotating');

            // Stop rotation after 1 second and show comparison chart
            setTimeout(() => {
                container.classList.remove('rotating');
                showComparisonChart(chartIndex);
            }, 1000);
        });
    });
}

function showComparisonChart(chartIndex) {
    // Create comparison chart overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: stretch;
        justify-content: stretch;
        z-index: 1000;
    `;

    const chartContainer = document.createElement('div');
    chartContainer.style.cssText = `
        background: #2a2a2a;
        width: 100%;
        height: 100%;
        position: relative;
        display: flex;
        flex-direction: column;
        padding: 12px 16px;
        box-sizing: border-box;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        color: #fff;
        font-size: 24px;
        cursor: pointer;
        z-index: 1001;
    `;

    const canvas = document.createElement('canvas');
    canvas.id = `comparison-chart-${chartIndex}`;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.flex = '1 1 auto';
    canvas.style.display = 'block';
    canvas.style.setProperty('max-height', 'none', 'important');

    chartContainer.appendChild(closeBtn);
    chartContainer.appendChild(canvas);
    overlay.appendChild(chartContainer);
    document.body.appendChild(overlay);

    // Create line chart for comparison
    createLineChart(canvas.id, chartIndex);

    // Close handlers
    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); document.body.removeChild(overlay); });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) document.body.removeChild(overlay);
    });
}

function createLineChart(canvasId, chartIndex) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const renderChart = (labels, datasets, isPercent = false, yOnRight = false) => {
        new Chart(ctx, {
            type: 'line',
            data: { labels, datasets },
            options: {
                responsive: true,
                interaction: { mode: 'nearest', intersect: false, axis: 'x' },
                plugins: {
                    title: {
                        display: false
                    },
                    legend: { labels: { color: '#fff' } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const v = ctx.parsed.y;
                                const formatted = isPercent ? (Number(v).toFixed(2) + '%') : Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
                                return ' ' + ctx.dataset.label + ': ' + formatted;
                            }
                        }
                    },
                    decimation: { enabled: true, algorithm: 'lttb', samples: 500 },
                    // Enable wheel zoom and pan (horizontal)
                    zoom: {
                        pan: { enabled: true, mode: 'x' },
                        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'x' }
                    }
                },
                elements: { point: { radius: 0, hitRadius: 10, hoverRadius: 4 } },
                scales: {
                    x: { ticks: { color: '#fff' }, grid: { color: '#444' } },
                    y: {
                        position: yOnRight ? 'right' : 'left',
                        ticks: {
                            color: '#fff',
                            callback: (v) => isPercent ? (Number(v).toFixed(0) + '%') : Number(v).toLocaleString()
                        },
                        grid: { color: '#444' }
                    }
                }
            }
        });
    };

    // For the first main chart, fetch total capital series from backend
    if (String(chartIndex) === '0') {
        fetch('/api/portfolio1_total_capital?ts=' + Date.now(), { cache: 'no-store' })
            .then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)))
            .then(json => {
                const labelsAll = json.data.map(r => r.date);
                const valuesAbsAll = json.data.map(r => Number(r.total_capital));
                const base = valuesAbsAll.find(v => Number.isFinite(v)) || 1;
                const portPct = valuesAbsAll.map(v => ((v / base) - 1) * 100);

                const fetchIndexPct = async (symbol) => {
                    const resp = await fetch('/api/index_csv?symbol=' + encodeURIComponent(symbol) + '&ts=' + Date.now(), { cache: 'no-store' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    const js = await resp.json();
                    const ls = js.data.map(r => r.date);
                    const vs = js.data.map(r => Number(r.close_price));
                    const b = vs.find(v => Number.isFinite(v)) || 1;
                    const pct = vs.map(v => ((v / b) - 1) * 100);
                    return { ls, pct };
                };

                const fetchDepositPct = async () => {
                    const resp = await fetch('/api/deposit_rate?ts=' + Date.now(), { cache: 'no-store' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    const js = await resp.json();
                    const ls = js.data.map(r => r.date);
                    // Use provided Sberbank deposit profitability (rate) directly as percent
                    const pct = js.data.map(r => Number(r.rate));
                    return { ls, pct };
                };

                Promise.allSettled([
                    fetchIndexPct('IMOEX'),
                    fetchIndexPct('XAUT-USD'),
                    fetchDepositPct()
                ]).then(results => {
                    const moex = results[0].status === 'fulfilled' ? results[0].value : { ls: [], pct: [] };
                    const gold = results[1].status === 'fulfilled' ? results[1].value : { ls: [], pct: [] };
                    const depo = results[2].status === 'fulfilled' ? results[2].value : { ls: [], pct: [] };

                    const allDatesSet = new Set([...labelsAll, ...moex.ls, ...gold.ls, ...depo.ls]);
                    const union = Array.from(allDatesSet).sort();
                    const toMap = (ls, pct) => { const m = {}; for (let i = 0; i < ls.length; i += 1) m[ls[i]] = pct[i]; return m; };
                    const mPort = toMap(labelsAll, portPct);
                    const mMoex = toMap(moex.ls, moex.pct);
                    const mGold = toMap(gold.ls, gold.pct);
                    const mDepo = toMap(depo.ls, depo.pct);
                    const series = (m) => union.map(d => (d in m ? m[d] : null));
                    const seriesFF = (m) => {
                        let last = null;
                        return union.map(d => {
                            if (Object.prototype.hasOwnProperty.call(m, d)) {
                                last = m[d];
                                return m[d];
                            }
                            return last;
                        });
                    };

                    const canvasEl = document.getElementById(canvasId);
                    canvasEl.style.width = '100%';
                    canvasEl.style.height = '70vh';
                    const container = canvasEl.parentElement;
                    const caption = document.createElement('div');
                    caption.textContent = 'Сравнение доходностей';
                    caption.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%, -50%);text-align:center;font-size:16px;font-weight:800;color:#e5e5e5;margin:0;width:auto;pointer-events:none;';
                    const panel = document.createElement('div');
                    panel.style.cssText = 'position:relative;display:flex;justify-content:center;align-items:center;margin-bottom:8px;color:#e5e5e5;gap:8px;flex-wrap:wrap;min-height:36px;';
                    panel.appendChild(caption);
                    container.insertBefore(panel, canvasEl);

                    renderChart(union, [
                        { label: 'Портфель 1 (доходность, %)', data: series(mPort), borderColor: '#4d96ff', backgroundColor: 'rgba(77, 150, 255, 0.10)', tension: 0.4, pointRadius: 0, borderWidth: 2, fill: true },
                        { label: 'Индекс МосБиржи (%)', data: series(mMoex), borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.08)', tension: 0.3, pointRadius: 0, borderWidth: 2, fill: false },
                        { label: 'Золото (%)', data: series(mGold), borderColor: '#b49d00', backgroundColor: 'rgba(180, 157, 0, 0.08)', tension: 0.3, pointRadius: 0, borderWidth: 2, fill: false },
                        { label: 'Сбербанк вклад (%)', data: seriesFF(mDepo), borderColor: '#4ade80', backgroundColor: 'rgba(74, 222, 128, 0.08)', tension: 0.2, pointRadius: 0, borderWidth: 2, fill: false }
                    ], true, true);
                }).catch(() => {
                    const canvasEl = document.getElementById(canvasId);
                    canvasEl.style.width = '100%';
                    canvasEl.style.height = '70vh';
                    const container = canvasEl.parentElement;
                    const caption = document.createElement('div');
                    caption.textContent = 'Сравнение доходности активов';
                    caption.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%, -50%);text-align:center;font-size:16px;font-weight:800;color:#e5e5e5;margin:0;width:auto;pointer-events:none;';
                    const panel = document.createElement('div');
                    panel.style.cssText = 'position:relative;display:flex;justify-content:center;align-items:center;margin-bottom:8px;color:#e5e5e5;gap:8px;flex-wrap:wrap;min-height:36px;';
                    panel.appendChild(caption);
                    container.insertBefore(panel, canvasEl);
                    renderChart(labelsAll, [{ label: 'Портфель 1 (доходность, %)', data: portPct, borderColor: '#4d96ff', backgroundColor: 'rgba(77, 150, 255, 0.10)', tension: 0.4, pointRadius: 0, borderWidth: 2, fill: true }], true, true);
                });
            })
            .catch(() => {
                // Fallback to dummy data if API fails
                const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
                const data = months.map(() => Math.floor(Math.random() * 30));
                const canvasEl = document.getElementById(canvasId);
                canvasEl.style.width = '100%';
                canvasEl.style.height = '70vh';
                renderChart(months, [{
                    label: 'Портфель 1 (доходность, %)',
                    data,
                    borderColor: '#4d96ff',
                    backgroundColor: 'rgba(77, 150, 255, 0.10)',
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2,
                    fill: true
                }], true, true);
            });
        return;
    }

    // For the second main chart, mirror portfolio 1 logic but for portfolio 2
    if (String(chartIndex) === '1') {
        fetch('/api/portfolio2_total_capital?ts=' + Date.now(), { cache: 'no-store' })
            .then(r => r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status)))
            .then(json => {
                const labelsAll = json.data.map(r => r.date);
                const valuesAbsAll = json.data.map(r => Number(r.equity));
                const base = valuesAbsAll.find(v => Number.isFinite(v)) || 1;
                const portPct = valuesAbsAll.map(v => ((v / base) - 1) * 100);

                const fetchIndexPct = async (symbol) => {
                    const resp = await fetch('/api/index_csv?symbol=' + encodeURIComponent(symbol) + '&ts=' + Date.now(), { cache: 'no-store' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    const js = await resp.json();
                    const ls = js.data.map(r => r.date);
                    const vs = js.data.map(r => Number(r.close_price));
                    const b = vs.find(v => Number.isFinite(v)) || 1;
                    const pct = vs.map(v => ((v / b) - 1) * 100);
                    return { ls, pct };
                };

                const fetchDepositPct = async () => {
                    const resp = await fetch('/api/deposit_rate?ts=' + Date.now(), { cache: 'no-store' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    const js = await resp.json();
                    const ls = js.data.map(r => r.date);
                    const pct = js.data.map(r => Number(r.rate));
                    return { ls, pct };
                };

                Promise.allSettled([
                    fetchIndexPct('IMOEX'),
                    fetchIndexPct('XAUT-USD'),
                    fetchDepositPct()
                ]).then(results => {
                    const moex = results[0].status === 'fulfilled' ? results[0].value : { ls: [], pct: [] };
                    const gold = results[1].status === 'fulfilled' ? results[1].value : { ls: [], pct: [] };
                    const depo = results[2].status === 'fulfilled' ? results[2].value : { ls: [], pct: [] };

                    const allDatesSet = new Set([...labelsAll, ...moex.ls, ...gold.ls, ...depo.ls]);
                    const union = Array.from(allDatesSet).sort();
                    const toMap = (ls, pct) => { const m = {}; for (let i = 0; i < ls.length; i += 1) m[ls[i]] = pct[i]; return m; };
                    const mPort = toMap(labelsAll, portPct);
                    const mMoex = toMap(moex.ls, moex.pct);
                    const mGold = toMap(gold.ls, gold.pct);
                    const mDepo = toMap(depo.ls, depo.pct);
                    const series = (m) => union.map(d => (d in m ? m[d] : null));
                    const seriesFF = (m) => { let last = null; return union.map(d => { if (Object.prototype.hasOwnProperty.call(m, d)) { last = m[d]; return m[d]; } return last; }); };

                    const canvasEl = document.getElementById(canvasId);
                    canvasEl.style.width = '100%';
                    canvasEl.style.height = '70vh';
                    const container = canvasEl.parentElement;
                    const caption = document.createElement('div');
                    caption.textContent = 'Сравнение доходности активов (Портфель 2)';
                    caption.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%, -50%);text-align:center;font-size:16px;font-weight:800;color:#e5e5e5;margin:0;width:auto;pointer-events:none;';
                    const panel = document.createElement('div');
                    panel.style.cssText = 'position:relative;display:flex;justify-content:center;align-items:center;margin-bottom:8px;color:#e5e5e5;gap:8px;flex-wrap:wrap;min-height:36px;';
                    panel.appendChild(caption);
                    container.insertBefore(panel, canvasEl);

                    renderChart(union, [
                        { label: 'Портфель 2 (доходность, %)', data: series(mPort), borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.10)', tension: 0.4, pointRadius: 0, borderWidth: 2, fill: true },
                        { label: 'Индекс МосБиржи (%)', data: series(mMoex), borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.08)', tension: 0.3, pointRadius: 0, borderWidth: 2, fill: false },
                        { label: 'Золото (%)', data: series(mGold), borderColor: '#b49d00', backgroundColor: 'rgba(180, 157, 0, 0.08)', tension: 0.3, pointRadius: 0, borderWidth: 2, fill: false },
                        { label: 'Сбербанк вклад (%)', data: seriesFF(mDepo), borderColor: '#4ade80', backgroundColor: 'rgba(74, 222, 128, 0.08)', tension: 0.2, pointRadius: 0, borderWidth: 2, fill: false }
                    ], true, true);
                }).catch(() => {
                    const canvasEl = document.getElementById(canvasId);
                    canvasEl.style.width = '100%';
                    canvasEl.style.height = '70vh';
                    const container = canvasEl.parentElement;
                    const caption = document.createElement('div');
                    caption.textContent = 'Сравнение доходности активов (Портфель 2)';
                    caption.style.cssText = 'position:absolute;left:50%;top:50%;transform:translate(-50%, -50%);text-align:center;font-size:16px;font-weight:800;color:#e5e5e5;margin:0;width:auto;pointer-events:none;';
                    const panel = document.createElement('div');
                    panel.style.cssText = 'position:relative;display:flex;justify-content:center;align-items:center;margin-bottom:8px;color:#e5e5e5;gap:8px;flex-wrap:wrap;min-height:36px;';
                    panel.appendChild(caption);
                    container.insertBefore(panel, canvasEl);
                    renderChart(labelsAll, [{ label: 'Портфель 2 (доходность, %)', data: portPct, borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.10)', tension: 0.4, pointRadius: 0, borderWidth: 2, fill: true }], true, true);
                });
            })
            .catch(() => {
                const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
                const data = months.map(() => Math.floor(Math.random() * 30));
                const canvasEl = document.getElementById(canvasId);
                canvasEl.style.width = '100%';
                canvasEl.style.height = '70vh';
                renderChart(months, [{ label: 'Портфель 2 (доходность, %)', data, borderColor: '#ff6b6b', backgroundColor: 'rgba(255, 107, 107, 0.10)', tension: 0.4, pointRadius: 0, borderWidth: 2, fill: true }], true, true);
            });
        return;
    }

    // Default comparison (dummy) for other charts
    const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
    const data1 = months.map(() => Math.floor(Math.random() * 50 + 10));
    const data2 = months.map(() => Math.floor(Math.random() * 50 + 10));
    const data3 = months.map(() => Math.floor(Math.random() * 50 + 10));
    renderChart(months, [
        { label: 'Золото', data: data1, borderColor: '#ffa94d', backgroundColor: 'rgba(255, 169, 77, 0.1)', tension: 0.4 },
        { label: 'Сбербанк', data: data2, borderColor: '#4ade80', backgroundColor: 'rgba(74, 222, 128, 0.1)', tension: 0.4 },
        { label: 'МосБиржа', data: data3, borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.1)', tension: 0.4 }
    ], false);
}

/* ----------------------------- Enhanced Top Button Functionality ----------------------------- */
function initTopButtons() {
    document.querySelectorAll('.top-rate-button').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const asset = button.getAttribute('data-asset');
            showAssetChart(asset);
        });
    });
}

function showAssetChart(asset) {
    // Create asset chart overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;

    const chartContainer = document.createElement('div');
    chartContainer.style.cssText = `
        background: #2a2a2a;
        width: 100%;
        height: 100%;
        position: relative;
        display: flex;
        flex-direction: column;
        padding: 0;
        margin: 0;
    `;

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = `
        position: absolute;
        top: 10px;
        right: 15px;
        background: none;
        border: none;
        color: #fff;
        font-size: 24px;
        cursor: pointer;
        z-index: 1001;
    `;

    const title = document.createElement('h3');
    title.style.color = '#fff';
    title.style.textAlign = 'center';
    title.style.margin = '6px 0 6px 0';

    const canvas = document.createElement('canvas');
    canvas.id = `asset-chart-${asset}`;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.flex = '1 1 auto';
    canvas.style.display = 'block';
    // Ensure canvas ignores global style.css canvas rules
    canvas.style.setProperty('height', '100%', 'important');
    canvas.style.setProperty('max-height', 'none', 'important');


    let titleText = '';
    switch (asset) {
        case 'gold': titleText = 'Доходность золота'; break;
        case 'sber': titleText = 'Ставка вклада Сбербанка'; break;
        case 'moex': titleText = 'Доходность индекса МосБиржи'; break;
    }
    title.textContent = titleText;

    chartContainer.appendChild(closeBtn);
    chartContainer.appendChild(title);
    chartContainer.appendChild(canvas);
    overlay.appendChild(chartContainer);
    document.body.appendChild(overlay);

    // Create asset-specific chart
    createAssetChart(canvas.id, asset);

    // Close handlers
    closeBtn.addEventListener('click', (e) => { e.stopPropagation(); document.body.removeChild(overlay); });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) document.body.removeChild(overlay);
    });
}

async function createAssetChart(canvasId, asset, timelineCanvasId = null) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    let color = '#8b5cf6';
    let label = 'Доходность';
    let symbol = null;

    switch (asset) {
        case 'gold':
            color = '#ffa94d';
            label = 'Доходность золота';
            symbol = 'XAUT-USD';
            break;
        case 'sber':
            color = '#4ade80';
            label = 'Ставка Сбербанка';
            break;
        case 'moex':
            color = '#8b5cf6';
            label = 'Доходность МосБиржи';
            symbol = 'IMOEX';
            break;
    }

    let labelsAll = [];
    let dataAll = [];
    let annualYieldsText = '';

    try {
        if (asset === 'sber') {
            const resp = await fetch('/api/deposit_rate');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const json = await resp.json();
            labelsAll = json.data.map(r => r.date);
            dataAll = json.data.map(r => Number(r.rate));

            // Compute annual yield as average of monthly rates in each year
            const yearToValues = {};
            for (let i = 0; i < labelsAll.length; i += 1) {
                const y = String(labelsAll[i]).slice(0, 4);
                const v = Number(dataAll[i]);
                if (!Number.isFinite(v)) continue;
                if (!yearToValues[y]) yearToValues[y] = [];
                yearToValues[y].push(v);
            }
            const years = Object.keys(yearToValues).sort();
            const formatted = years.slice(-4).map(y => {
                const arr = yearToValues[y];
                const avg = arr.reduce((a, b) => a + b, 0) / arr.length;
                return `${y}: ${avg.toFixed(1)}%`;
            });
            annualYieldsText = formatted.join('   ');
        } else if (symbol) {
            const resp = await fetch('/api/index_csv?symbol=' + encodeURIComponent(symbol));
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const json = await resp.json();
            // Expect json.data as array of {date, close_price}
            labelsAll = json.data.map(r => r.date);
            dataAll = json.data.map(r => Number(r.close_price));

            // Compute annual yields from first/last close within each year
            const yearFirst = {};
            const yearLast = {};
            for (let i = 0; i < labelsAll.length; i += 1) {
                const d = labelsAll[i];
                const y = d.slice(0, 4);
                const v = Number(dataAll[i]);
                if (!Number.isFinite(v)) continue;
                if (!(y in yearFirst)) yearFirst[y] = v;
                yearLast[y] = v;
            }
            const years = Object.keys(yearFirst).sort();
            const yields = years.map(y => {
                const ret = (yearLast[y] / yearFirst[y] - 1) * 100;
                return { year: y, ret };
            });
            const nowYear = String(new Date().getFullYear());
            // Left to right chronological ordering
            const formatted = yields.slice(-4).map(y => {
                const isYTD = y.year === nowYear;
                const tag = isYTD ? y.year : y.year;
                const val = (Math.round(y.ret * 10) / 10).toFixed(1);
                return `${tag}: ${val}%`;
            });
            annualYieldsText = formatted.join('   ');
        } else {
            // Fallback random for assets without CSV mapping
            // Generate synthetic monthly date series for the last 3 years for graceful fallback
            const monthsBack = 36;
            const today = new Date();
            function pad(n) { return n < 10 ? '0' + n : String(n); }
            function formatDate(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
            const tmpLabels = [];
            for (let i = monthsBack - 1; i >= 0; i -= 1) {
                const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
                tmpLabels.push(formatDate(d));
            }
            labelsAll = tmpLabels;
            dataAll = labelsAll.map(() => Math.floor(Math.random() * 30 + 5));
        }
    } catch (e) {
        console.error('Failed to load index CSV data:', e);
        // Graceful fallback
        const monthsBack = 36;
        const today = new Date();
        function pad(n) { return n < 10 ? '0' + n : String(n); }
        function formatDate(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; }
        const tmpLabels = [];
        for (let i = monthsBack - 1; i >= 0; i -= 1) {
            const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
            tmpLabels.push(formatDate(d));
        }
        labelsAll = tmpLabels;
        dataAll = labelsAll.map(() => Math.floor(Math.random() * 30 + 5));
    }

    // Create a nice gradient fill
    const canvas = ctx.canvas;
    const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    gradient.addColorStop(0, color + '55');
    gradient.addColorStop(1, color + '00');

    // Controls: timeframe + mode (% / price)
    const container = ctx.canvas.parentElement;
    container.style.position = container.style.position || 'relative';
    const controls = document.createElement('div');
    controls.style.cssText = 'position:absolute;top:12px;left:12px;display:flex;gap:8px;flex-wrap:wrap;z-index:2;';
    const ranges = ['1Y', '3Y', '5Y', 'MAX'];
    const rangeBtns = ranges.map(r => {
        const b = document.createElement('button');
        b.textContent = r;
        b.dataset.range = r;
        b.style.cssText = 'background:#2a2a2a;color:#ddd;border:1px solid #3a3a3a;border-radius:6px;padding:4px 8px;cursor:pointer;font-size:12px;';
        controls.appendChild(b);
        return b;
    });
    // Interval selector (D/W/M)
    const intervalSelect = document.createElement('select');
    intervalSelect.style.cssText = 'background:#2a2a2a;color:#ddd;border:1px solid #3a3a3a;border-radius:6px;padding:4px 6px;cursor:pointer;font-size:12px;';
    ['D', 'W', 'M'].forEach(k => {
        const opt = document.createElement('option');
        opt.value = k; opt.textContent = ({ D: 'День', W: 'Неделя', M: 'Месяц' })[k];
        intervalSelect.appendChild(opt);
    });
    intervalSelect.value = 'D';
    controls.appendChild(intervalSelect);
    container.appendChild(controls);

    function setActiveRange(active) {
        rangeBtns.forEach(b => {
            b.style.background = (b.dataset.range === active) ? '#3a3a3a' : '#2a2a2a';
        });
    }

    function filterByRange(rangeKey) {
        if (!labelsAll.length) return { labels: [], data: [] };
        const parse = (s) => new Date(s + 'T00:00:00');
        const last = parse(labelsAll[labelsAll.length - 1]);
        let startDate = null;
        const y = last.getFullYear();
        switch (rangeKey) {
            case 'YTD': startDate = new Date(y, 0, 1); break;
            case '1Y': startDate = new Date(last); startDate.setFullYear(startDate.getFullYear() - 1); break;
            case '3Y': startDate = new Date(last); startDate.setFullYear(startDate.getFullYear() - 3); break;
            case '5Y': startDate = new Date(last); startDate.setFullYear(startDate.getFullYear() - 5); break;
            case 'MAX': default: startDate = new Date('1900-01-01');
        }
        const outLabels = [];
        const outData = [];
        for (let i = 0; i < labelsAll.length; i += 1) {
            const d = labelsAll[i];
            const dt = new Date(d + 'T00:00:00');
            if (dt >= startDate && dt <= last) {
                outLabels.push(d);
                outData.push(dataAll[i]);
            }
        }
        return { labels: outLabels, data: outData };
    }

    function toPercentSeries(values) {
        if (!values.length) return values;
        const base = Number(values[0]);
        return values.map(v => (Number(v) / base - 1) * 100);
    }

    // Initial view
    let currentRange = '5Y';
    let currentMode = 'price';
    // Fixed to line per requirement
    let currentType = 'line';
    let currentInterval = 'D';
    setActiveRange(currentRange);
    let { labels, data } = filterByRange(currentRange);

    // Avoid temporal-dead-zone by referencing a mutable ref inside callbacks
    let chartRef = null;
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: color,
                backgroundColor: gradient,
                pointRadius: 0,
                pointHoverRadius: 3,
                borderWidth: 2,
                tension: 0.25,
                fill: true,
                spanGaps: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            resizeDelay: 0,
            plugins: {
                legend: { labels: { color: '#fff' } },
                title: {
                    display: Boolean(annualYieldsText),
                    text: annualYieldsText,
                    color: '#e5e5e5',
                    font: { size: 12, weight: '600' },
                    padding: { top: 8, bottom: 8 }
                },
                subtitle: {
                    display: true,
                    text: '',
                    color: '#cfcfcf',
                    font: { size: 11 },
                    padding: { bottom: 6 }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: (ctx) => {
                            const v = ctx.parsed.y;
                            if (asset === 'sber') {
                                return ` ${label}: ${Number(v).toFixed(2)}%`;
                            } else if (asset === 'moex') {
                                return ` ${label}: ${Number(v).toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ₽`;
                            }
                            return ` ${label}: $${Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#ddd',
                        maxRotation: 0,
                        autoSkip: true,
                        callback: (val, idx) => {
                            // Show year starts for long series
                            const lbl = (chartRef && chartRef.data && chartRef.data.labels[idx]) || (labels[idx] || '');
                            return lbl.endsWith('-01-01') ? lbl.slice(0, 4) : '';
                        }
                    },
                    grid: { color: '#333', drawBorder: false }
                },
                y: {
                    position: 'right',
                    beginAtZero: false,
                    ticks: {
                        color: '#ddd',
                        callback: (v) => {
                            if (asset === 'sber') {
                                return Number(v).toFixed(1) + '%';
                            }
                            if (asset === 'moex') {
                                return Number(v).toLocaleString('ru-RU') + ' ₽';
                            }
                            return '$' + Number(v).toLocaleString('en-US');
                        }
                    },
                    grid: { color: '#333', drawBorder: true }
                }
            }
        }
    });
    chartRef = chart;

    function updateSubtitle(ls, vs) {
        if (!ls.length || !vs.length) {
            chart.options.plugins.subtitle.text = '';
            return;
        }
        const first = Number(vs[0]);
        const last = Number(vs[vs.length - 1]);
        let text = '';
        if (currentMode === 'price') {
            const pct = (last / first - 1) * 100;
            text = `${ls[0]} → ${ls[ls.length - 1]}   Изм: ${pct.toFixed(1)}%`;
        } else {
            text = `${ls[0]} → ${ls[ls.length - 1]}`;
        }
        chart.options.plugins.subtitle.text = text;
    }

    function aggregateInterval(labelsSrc, valuesSrc, intervalKey) {
        if (intervalKey === 'D') return { labels: labelsSrc, data: valuesSrc };
        const outL = [], outV = [];
        let bucket = [];
        let currentKey = null;
        const keyOf = (iso) => {
            const d = new Date(iso + 'T00:00:00');
            if (intervalKey === 'W') {
                // Week key: ISO year-week
                const tmp = new Date(d);
                const day = (d.getDay() + 6) % 7; // Mon=0
                tmp.setDate(d.getDate() - day);
                const y = tmp.getFullYear();
                const m = String(tmp.getMonth() + 1).padStart(2, '0');
                const dayOfMonth = String(tmp.getDate()).padStart(2, '0');
                return `${y}-${m}-${dayOfMonth}`; // week start date
            }
            // Monthly: first day of month
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
        };
        for (let i = 0; i < labelsSrc.length; i += 1) {
            const k = keyOf(labelsSrc[i]);
            if (currentKey === null) currentKey = k;
            if (k !== currentKey) {
                // use last value in bucket (close)
                outL.push(currentKey);
                outV.push(bucket[bucket.length - 1]);
                bucket = [];
                currentKey = k;
            }
            bucket.push(valuesSrc[i]);
        }
        if (bucket.length) {
            outL.push(currentKey);
            outV.push(bucket[bucket.length - 1]);
        }
        return { labels: outL, data: outV };
    }

    function refreshChart() {
        const filtered = filterByRange(currentRange);
        let ls = filtered.labels;
        let vs = filtered.data;
        if (asset !== 'sber' && currentMode === '%') { vs = toPercentSeries(vs); }
        // Interval aggregation
        const agg = aggregateInterval(ls, vs, currentInterval);
        ls = agg.labels; vs = agg.data;

        // Always line
        chart.config.type = 'line';
        chart.data.labels = ls;
        chart.data.datasets = [{
            label: label,
            data: vs,
            borderColor: color,
            backgroundColor: gradient,
            pointRadius: 0,
            pointHoverRadius: 3,
            borderWidth: 2,
            tension: 0.25,
            fill: true,
            spanGaps: true
        }];
        updateSubtitle(ls, vs);
        chart.update('none');

        // No timeline rendering (single chart as requested)
    }

    rangeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            currentRange = btn.dataset.range;
            setActiveRange(currentRange);
            refreshChart();
        });
    });
    // type toggle removed per requirement
    intervalSelect.addEventListener('change', () => {
        currentInterval = intervalSelect.value; // 'D'|'W'|'M'
        refreshChart();
    });
    // no mode toggle

    updateSubtitle(chart.data.labels, chart.data.datasets[0].data);

    // Enable zoom and pan interactions
    chart.options.plugins.zoom = {
        zoom: {
            wheel: { enabled: true },
            pinch: { enabled: true },
            mode: 'x'
        },
        pan: {
            enabled: true,
            mode: 'x',
            modifierKey: null
        },
        limits: {
            x: { minRange: 7 }
        }
    };
    chart.update('none');
}

function updateTimelineChart(timelineCanvasId, fullLabels, fullValues, startIso, endIso, color) {
    const ctx = document.getElementById(timelineCanvasId).getContext('2d');
    const startIdx = fullLabels.findIndex(d => d >= startIso);
    const endIdx = Math.max(startIdx, fullLabels.findIndex(d => d >= endIso));
    const labels = fullLabels;
    const values = fullValues;

    // Build selection overlay values
    const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height);
    gradient.addColorStop(0, color + '33');
    gradient.addColorStop(1, color + '00');

    // Destroy previous chart instance if any
    if (ctx._timelineChart) {
        ctx._timelineChart.destroy();
    }

    ctx._timelineChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Timeline',
                data: values,
                borderColor: '#666',
                backgroundColor: gradient,
                borderWidth: 1,
                pointRadius: 0,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            }
        }
    });
}

/* ----------------------------- User Badge Update ----------------------------- */
function updateUserBadge() {
    const userBadge = document.getElementById('user-badge');
    const guestMenu = document.getElementById('guest-menu');
    const loggedMenu = document.getElementById('logged-menu');

    if (!userBadge) return;

    const isAdmin = AuthManager.isAdmin();
    const isLoggedIn = AuthManager.isLoggedIn();
    const userName = AuthManager.getUserName();
    const userEmail = AuthManager.getUserEmail();

    // reset classes
    userBadge.classList.remove('guest-badge', 'user-badge', 'admin-badge');

    if (isAdmin) {
        userBadge.textContent = 'Admin';
        userBadge.classList.add('admin-badge');
        // Show logged menu for admin
        if (guestMenu && loggedMenu) {
            guestMenu.style.display = 'none';
            loggedMenu.style.display = 'block';
        }
    } else if (isLoggedIn && userEmail) {
        // Show email before @ symbol
        const emailPrefix = userEmail.split('@')[0];
        userBadge.textContent = emailPrefix;
        userBadge.classList.add('user-badge');
        // Show logged menu for user
        if (guestMenu && loggedMenu) {
            guestMenu.style.display = 'none';
            loggedMenu.style.display = 'block';
        }
    } else {
        userBadge.textContent = 'Войти';
        userBadge.classList.add('guest-badge');
        // Show guest menu
        if (guestMenu && loggedMenu) {
            guestMenu.style.display = 'block';
            loggedMenu.style.display = 'none';
        }
    }
    // reveal after set (no-op if already visible)
    userBadge.classList.remove('badge-hidden');
}

/* ----------------------------- Registration Menu Functionality ----------------------------- */
function initRegistrationMenu() {
    const userBadge = document.getElementById('user-badge');
    const registrationMenu = document.getElementById('registration-menu');

    if (!userBadge || !registrationMenu) return;

    // Handle user badge click based on login status
    userBadge.addEventListener('click', (e) => {
        e.stopPropagation();

        const isAdmin = AuthManager.isAdmin();
        const isLoggedIn = AuthManager.isLoggedIn();

        if (isLoggedIn || isAdmin) {
            // Show menu for logged in users
            registrationMenu.classList.toggle('show');
        } else {
            // Open login modal directly for guests
            document.getElementById('login-modal').style.display = 'flex';
        }
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!registrationMenu.contains(e.target) && e.target !== userBadge) {
            registrationMenu.classList.remove('show');
        }
    });

    // Open login modal from guest menu
    const openLogin = document.getElementById('open-login');
    if (openLogin) {
        openLogin.addEventListener('click', () => {
            registrationMenu.classList.remove('show');
            document.getElementById('login-modal').style.display = 'flex';
        });
    }

    // Handle subscription button
    const subscribeBtn = document.getElementById('subscribe-btn');
    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', (e) => {
            registrationMenu.classList.remove('show');
            window.open('subscription.html', '_blank');
        });
    }

    // Handle logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            localStorage.removeItem('role');
            localStorage.removeItem('userName');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('subscribed');
            updateUserBadge();
            registrationMenu.classList.remove('show');
            alert('Вы вышли из системы');
        });
    }
}

// Search removed

/* ------------------------------- Init Script ------------------------------- */
window.addEventListener("DOMContentLoaded", async () => {
    try {
        // Update badge immediately to avoid flicker
        updateUserBadge();
        await loadSectorsFromSummary();
        await preloadLastMapBySymbol();
        // Initialize chat-style layout
        await displayChartsAsMessages();
        initSidebarNavigation();

        // Initialize top buttons immediately
        initTopButtons();

        // Initialize custom scrollbar
        new MainCustomScrollbar();

        // Initialize existing handlers
        initLoginModal();
        updateLoginButton();
        initRegistrationMenu();

        // Badge already updated at start

        const buyBtn = document.getElementById('buy-btn');
        if (buyBtn) {
            buyBtn.onclick = () => { localStorage.setItem('subscribed', 'true'); paywall.style.display = 'none'; };
        }

        // Check if redirected from chat (show login modal)
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('showLogin') === 'true') {
            // Show login modal and notification
            document.getElementById('login-modal').style.display = 'flex';
            alert('Для использования чата необходимо войти в аккаунт или зарегистрироваться');

            // Clear the URL parameter
            const url = new URL(window.location);
            url.searchParams.delete('showLogin');
            window.history.replaceState(null, '', url);
        }

    } catch (error) {
        handleError(error, 'Инициализация страницы');
    }
}); 
