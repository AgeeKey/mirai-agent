// ===== Main JavaScript for Mirai Website =====

class MiraiWebsite {
    constructor() {
        this.init();
        this.setupVoiceChat();
        this.setupNavigation();
        this.updateSystemStatus();
    }

    init() {
        console.log('🤖 Mirai website initialized');

        // Add smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    setupNavigation() {
        const navToggle = document.getElementById('navToggle');
        const navMenu = document.getElementById('navMenu');

        if (navToggle && navMenu) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
                navToggle.classList.toggle('active');
            });
        }

        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
                navToggle.classList.remove('active');
            }
        });

        // Active page highlighting
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    setupVoiceChat() {
        const voiceBtn = document.getElementById('voiceBtn');
        const voiceStatus = document.getElementById('voiceStatus');
        let isListening = false;
        let recognition = null;

        // Check if Web Speech API is supported
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();

            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'ru-RU';

            recognition.onstart = () => {
                isListening = true;
                voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
                voiceBtn.style.background = 'linear-gradient(45deg, #ef4444, #dc2626)';
                this.updateVoiceStatus('Слушаю... Говорите!');
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.handleVoiceInput(transcript);
            };

            recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.updateVoiceStatus('Ошибка распознавания речи');
                this.resetVoiceButton();
            };

            recognition.onend = () => {
                this.resetVoiceButton();
            };

            voiceBtn.addEventListener('click', () => {
                if (isListening) {
                    recognition.stop();
                } else {
                    recognition.start();
                }
            });
        } else {
            voiceBtn.addEventListener('click', () => {
                alert('Ваш браузер не поддерживает голосовое взаимодействие. Используйте Chrome или Edge.');
            });
        }
    }

    updateVoiceStatus(message) {
        const voiceStatus = document.getElementById('voiceStatus');
        if (voiceStatus) {
            voiceStatus.textContent = message;
        }
    }

    resetVoiceButton() {
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.style.background = 'linear-gradient(45deg, #6366f1, #4f46e5)';
        this.updateVoiceStatus('Нажми для общения с Mirai');
    }

    async handleVoiceInput(text) {
        this.updateVoiceStatus(`Вы сказали: "${text}"`);

        try {
            // Send to voice chat API
            const response = await fetch('/api/voice/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            if (data.response) {
                this.speakResponse(data.response);
                this.updateVoiceStatus(`Mirai: ${data.response}`);
            }
        } catch (error) {
            console.error('Voice chat error:', error);
            this.updateVoiceStatus('Ошибка связи с Mirai');
        }
    }

    speakResponse(text) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'ru-RU';
            utterance.rate = 0.9;
            utterance.pitch = 1.1;

            // Try to find a female voice
            const voices = speechSynthesis.getVoices();
            const femaleVoice = voices.find(voice =>
                voice.lang.includes('ru') && voice.name.includes('female')
            ) || voices.find(voice => voice.lang.includes('ru'));

            if (femaleVoice) {
                utterance.voice = femaleVoice;
            }

            speechSynthesis.speak(utterance);
        }
    }

    async updateSystemStatus() {
        const statusIndicator = document.getElementById('systemStatus');
        const lastUpdate = document.getElementById('lastUpdate');

        if (!statusIndicator) return;

        try {
            // Check our local API
            const localResponse = await fetch('/api/status');
            const localData = await localResponse.json();

            // Try to check trading API
            let tradingStatus = 'unknown';
            try {
                const tradingResponse = await fetch('https://aimirai.online/api/health');
                tradingStatus = tradingResponse.ok ? 'online' : 'offline';
            } catch {
                tradingStatus = 'offline';
            }

            // Update status display
            const statusDot = statusIndicator.querySelector('.status-dot');
            const statusText = statusIndicator.querySelector('span:last-child');

            if (localData.status === 'online' && tradingStatus === 'online') {
                statusDot.style.background = '#10b981'; // green
                statusText.textContent = 'Все системы работают';
            } else if (localData.status === 'online') {
                statusDot.style.background = '#f59e0b'; // yellow
                statusText.textContent = 'Веб-сайт работает';
            } else {
                statusDot.style.background = '#ef4444'; // red
                statusText.textContent = 'Проблемы с системой';
            }

            if (lastUpdate) {
                lastUpdate.textContent = `Обновлено: ${new Date().toLocaleTimeString('ru-RU')}`;
            }

        } catch (error) {
            console.error('Status check error:', error);
            const statusDot = statusIndicator.querySelector('.status-dot');
            const statusText = statusIndicator.querySelector('span:last-child');
            statusDot.style.background = '#ef4444';
            statusText.textContent = 'Ошибка проверки';
        }
    }

    // Utility functions
    formatNumber(num) {
        return new Intl.NumberFormat('ru-RU').format(num);
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize website when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MiraiWebsite();
});

// Add some CSS for notifications
const notificationCSS = `
.notification {
    position: fixed;
    top: 100px;
    right: 20px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    border-left: 4px solid var(--primary);
    box-shadow: var(--shadow-lg);
    z-index: 1001;
    max-width: 400px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    animation: slideIn 0.3s ease;
}

.notification-success {
    border-left-color: var(--success);
}

.notification-warning {
    border-left-color: var(--warning);
}

.notification-error {
    border-left-color: var(--danger);
}

.notification button {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
`;

// Inject notification CSS
const style = document.createElement('style');
style.textContent = notificationCSS;
document.head.appendChild(style);

// Global utilities
window.MiraiUtils = {
    formatNumber: (num) => new Intl.NumberFormat('ru-RU').format(num),
    formatCurrency: (amount) => new Intl.NumberFormat('ru-RU', {
        style: 'currency',
        currency: 'USD'
    }).format(amount),
    showNotification: (message, type = 'info') => {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        document.body.appendChild(notification);
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
};

console.log('🤖 Mirai website scripts loaded successfully!');