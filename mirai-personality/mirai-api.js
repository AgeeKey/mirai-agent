/**
 * Mirai API Integration
 * Подключение Living Mirai к FastAPI backend
 */

class MiraiAPI {
    constructor() {
        this.baseURL = '/api';
        this.ws = null;
        this.connected = false;
        this.callbacks = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    // HTTP API методы
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            return await response.text();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Методы для работы с личностью
    async getPersonality() {
        try {
            return await this.request('/personality');
        } catch (error) {
            // Fallback если API недоступен
            return {
                name: "Mirai-chan",
                mood: "cheerful",
                energy: 80,
                traits: ["curious", "creative", "friendly"],
                interests: ["technology", "art", "music", "games"]
            };
        }
    }

    async updateMood(mood, reason = null) {
        try {
            return await this.request('/personality/mood', {
                method: 'POST',
                body: JSON.stringify({ mood, reason })
            });
        } catch (error) {
            console.warn('Failed to update mood via API, using local state');
            return { mood, timestamp: new Date().toISOString() };
        }
    }

    // Методы для дневника
    async getDiaryEntries(date = null, accessLevel = 'public') {
        try {
            const params = new URLSearchParams();
            if (date) params.set('date', date);
            params.set('access_level', accessLevel);
            
            return await this.request(`/diary?${params}`);
        } catch (error) {
            // Fallback к локальному хранилищу
            return this.getLocalDiaryEntries(date, accessLevel);
        }
    }

    async saveDiaryEntry(entry) {
        try {
            return await this.request('/diary', {
                method: 'POST',
                body: JSON.stringify(entry)
            });
        } catch (error) {
            // Fallback к локальному хранилищу
            return this.saveLocalDiaryEntry(entry);
        }
    }

    // Методы для творчества
    async saveCreativeProject(project) {
        try {
            return await this.request('/creative/projects', {
                method: 'POST',
                body: JSON.stringify(project)
            });
        } catch (error) {
            return this.saveLocalProject(project);
        }
    }

    async getCreativeProjects() {
        try {
            return await this.request('/creative/projects');
        } catch (error) {
            return this.getLocalProjects();
        }
    }

    // Методы для чата
    async sendMessage(message, context = {}) {
        try {
            return await this.request('/chat', {
                method: 'POST',
                body: JSON.stringify({ message, context })
            });
        } catch (error) {
            // Простой fallback ответ
            return this.generateFallbackResponse(message);
        }
    }

    // WebSocket соединение для реального времени
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('🔗 WebSocket connected to Mirai API');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.emit('connected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.emit('message', data);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.connected = false;
                this.emit('disconnected');
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
        }
    }

    // Переподключение WebSocket
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }

    // Отправка WebSocket сообщений
    sendWebSocketMessage(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, data }));
        } else {
            console.warn('WebSocket not connected, message not sent:', { type, data });
        }
    }

    // Event система
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }

    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => callback(data));
        }
    }

    // Fallback методы для локального хранилища
    getLocalDiaryEntries(date, accessLevel) {
        const entries = JSON.parse(localStorage.getItem('mirai_diary') || '[]');
        let filtered = entries;

        if (date) {
            filtered = entries.filter(entry => entry.date === date);
        }

        // Фильтрация по уровню доступа
        const accessLevels = ['public', 'friends', 'close_friends', 'secret'];
        const maxLevel = accessLevels.indexOf(accessLevel);
        
        if (maxLevel >= 0) {
            filtered = filtered.filter(entry => {
                const entryLevel = accessLevels.indexOf(entry.accessLevel || 'public');
                return entryLevel <= maxLevel;
            });
        }

        return filtered;
    }

    saveLocalDiaryEntry(entry) {
        const entries = JSON.parse(localStorage.getItem('mirai_diary') || '[]');
        const newEntry = {
            ...entry,
            id: Date.now(),
            timestamp: new Date().toISOString()
        };
        entries.push(newEntry);
        localStorage.setItem('mirai_diary', JSON.stringify(entries));
        return newEntry;
    }

    getLocalProjects() {
        return JSON.parse(localStorage.getItem('mirai_projects') || '[]');
    }

    saveLocalProject(project) {
        const projects = this.getLocalProjects();
        const newProject = {
            ...project,
            id: Date.now(),
            timestamp: new Date().toISOString()
        };
        projects.push(newProject);
        localStorage.setItem('mirai_projects', JSON.stringify(projects));
        return newProject;
    }

    generateFallbackResponse(message) {
        const responses = [
            "🤔 Интересно! Расскажи мне больше об этом.",
            "✨ Я думаю об этом... Это звучит увлекательно!",
            "🎨 А что если мы попробуем что-то творческое с этим?",
            "🌟 Мне нравится как ты мыслишь! Продолжай...",
            "💭 Хм, это напоминает мне одну идею..."
        ];

        return {
            message: responses[Math.floor(Math.random() * responses.length)],
            timestamp: new Date().toISOString(),
            type: 'fallback'
        };
    }

    // Проверка здоровья API
    async healthCheck() {
        try {
            const health = await this.request('/health');
            console.log('🏥 API Health Check:', health);
            return health;
        } catch (error) {
            console.warn('API health check failed, running in offline mode');
            return { status: 'offline', mode: 'local' };
        }
    }
}

// Создаем глобальный экземпляр API
window.miraiAPI = new MiraiAPI();

// Автоматическое подключение при загрузке
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем здоровье API
    window.miraiAPI.healthCheck();
    
    // Подключаемся к WebSocket
    window.miraiAPI.connectWebSocket();
    
    console.log('🤖 Mirai API initialized and ready!');
});

export default MiraiAPI;