/**
 * Enhanced Chat Component with API Integration
 * Улучшенный чат с подключением к FastAPI backend
 */

const MiraiChatEnhanced = () => {
    const [messages, setMessages] = React.useState([
        {
            id: 1,
            text: "Привет! Я Mirai-chan! ✨ Теперь я подключена к умному API и могу быть еще более полезной!",
            sender: "mirai",
            timestamp: new Date().toISOString(),
            mood: "excited"
        }
    ]);
    const [inputMessage, setInputMessage] = React.useState("");
    const [isTyping, setIsTyping] = React.useState(false);
    const [connectionStatus, setConnectionStatus] = React.useState("connecting");
    const [personality, setPersonality] = React.useState(null);
    const chatEndRef = React.useRef(null);

    // Инициализация при монтировании
    React.useEffect(() => {
        initializeChat();
        setupEventListeners();
        loadPersonality();
    }, []);

    // Прокрутка к последнему сообщению
    React.useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const initializeChat = async () => {
        try {
            const health = await window.miraiAPI.healthCheck();
            setConnectionStatus(health.status === 'offline' ? 'offline' : 'connected');
        } catch (error) {
            setConnectionStatus('offline');
        }
    };

    const setupEventListeners = () => {
        // WebSocket события
        window.miraiAPI.on('connected', () => {
            setConnectionStatus('connected');
            console.log('🔗 Chat connected to API');
        });

        window.miraiAPI.on('disconnected', () => {
            setConnectionStatus('disconnected');
        });

        window.miraiAPI.on('message', (data) => {
            if (data.type === 'chat_response') {
                addMessage(data.message, 'mirai', data.mood);
                setIsTyping(false);
            }
        });
    };

    const loadPersonality = async () => {
        try {
            const personalityData = await window.miraiAPI.getPersonality();
            setPersonality(personalityData);
        } catch (error) {
            console.warn('Failed to load personality, using defaults');
        }
    };

    const addMessage = (text, sender, mood = null) => {
        const newMessage = {
            id: Date.now() + Math.random(),
            text,
            sender,
            timestamp: new Date().toISOString(),
            mood
        };
        setMessages(prev => [...prev, newMessage]);
    };

    const handleSendMessage = async () => {
        if (!inputMessage.trim()) return;

        const userMessage = inputMessage.trim();
        setInputMessage("");
        
        // Добавляем сообщение пользователя
        addMessage(userMessage, "user");
        
        // Показываем индикатор печати
        setIsTyping(true);

        try {
            // Отправляем в API
            const response = await window.miraiAPI.sendMessage(userMessage, {
                personality: personality,
                chatHistory: messages.slice(-5) // Последние 5 сообщений для контекста
            });

            // Добавляем ответ Mirai
            setTimeout(() => {
                addMessage(response.message, "mirai", response.mood);
                setIsTyping(false);
                
                // Обновляем настроение если изменилось
                if (response.mood && personality) {
                    window.miraiAPI.updateMood(response.mood, `Chat response: ${userMessage}`);
                    setPersonality(prev => ({ ...prev, mood: response.mood }));
                }
            }, 1000 + Math.random() * 2000); // Имитация времени размышления

        } catch (error) {
            console.error('Chat API error:', error);
            setIsTyping(false);
            
            // Fallback ответ
            setTimeout(() => {
                const fallback = window.miraiAPI.generateFallbackResponse(userMessage);
                addMessage(fallback.message, "mirai");
            }, 1500);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const getConnectionStatusIcon = () => {
        switch (connectionStatus) {
            case 'connected': return '🟢';
            case 'connecting': return '🟡';
            case 'disconnected': return '🟠';
            case 'offline': return '🔴';
            default: return '⚪';
        }
    };

    const getConnectionStatusText = () => {
        switch (connectionStatus) {
            case 'connected': return 'Подключено к API';
            case 'connecting': return 'Подключение...';
            case 'disconnected': return 'Переподключение...';
            case 'offline': return 'Локальный режим';
            default: return 'Неизвестно';
        }
    };

    const getMoodEmoji = (mood) => {
        const moodEmojis = {
            excited: '✨',
            happy: '😊',
            curious: '🤔',
            thoughtful: '💭',
            playful: '😄',
            content: '😌',
            energetic: '⚡',
            creative: '🎨',
            default: '💫'
        };
        return moodEmojis[mood] || moodEmojis.default;
    };

    return (
        <div className="chat-container">
            {/* Заголовок чата с статусом */}
            <div className="chat-header">
                <div className="chat-title">
                    <span className="chat-avatar">✨</span>
                    <div>
                        <h3>Чат с Mirai-chan</h3>
                        <div className="connection-status">
                            {getConnectionStatusIcon()} {getConnectionStatusText()}
                            {personality && (
                                <span className="mood-indicator">
                                    {getMoodEmoji(personality.mood)} {personality.mood}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Область сообщений */}
            <div className="chat-messages">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.sender}`}>
                        <div className="message-content">
                            <div className="message-text">
                                {message.mood && (
                                    <span className="message-mood">{getMoodEmoji(message.mood)}</span>
                                )}
                                {message.text}
                            </div>
                            <div className="message-time">
                                {new Date(message.timestamp).toLocaleTimeString('ru-RU', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                        </div>
                    </div>
                ))}
                
                {/* Индикатор печати */}
                {isTyping && (
                    <div className="message mirai typing">
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                
                <div ref={chatEndRef} />
            </div>

            {/* Поле ввода */}
            <div className="chat-input-container">
                <div className="chat-input-wrapper">
                    <textarea
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Напиши что-нибудь Mirai-chan..."
                        className="chat-input"
                        rows="1"
                        disabled={isTyping}
                    />
                    <button 
                        onClick={handleSendMessage}
                        className="send-button"
                        disabled={!inputMessage.trim() || isTyping}
                    >
                        ✨
                    </button>
                </div>
                
                {/* Быстрые кнопки */}
                <div className="quick-actions">
                    <button 
                        onClick={() => setInputMessage("Как дела?")}
                        className="quick-btn"
                    >
                        Как дела? 😊
                    </button>
                    <button 
                        onClick={() => setInputMessage("Расскажи что-нибудь интересное")}
                        className="quick-btn"
                    >
                        Расскажи историю 📚
                    </button>
                    <button 
                        onClick={() => setInputMessage("Давай что-нибудь создадим!")}
                        className="quick-btn"
                    >
                        Творчество 🎨
                    </button>
                </div>
            </div>

            <style jsx>{`
                .chat-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    background: white;
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }

                .chat-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 20px 20px 0 0;
                }

                .chat-title {
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }

                .chat-avatar {
                    font-size: 2em;
                    animation: pulse 2s infinite;
                }

                .connection-status {
                    font-size: 0.85em;
                    opacity: 0.9;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-top: 5px;
                }

                .mood-indicator {
                    background: rgba(255,255,255,0.2);
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 0.8em;
                }

                .chat-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                    max-height: 400px;
                }

                .message {
                    display: flex;
                    animation: slideIn 0.3s ease;
                }

                .message.user {
                    justify-content: flex-end;
                }

                .message.mirai {
                    justify-content: flex-start;
                }

                .message-content {
                    max-width: 70%;
                    padding: 12px 16px;
                    border-radius: 18px;
                    position: relative;
                }

                .message.user .message-content {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border-bottom-right-radius: 5px;
                }

                .message.mirai .message-content {
                    background: #f0f2f5;
                    color: #333;
                    border-bottom-left-radius: 5px;
                }

                .message-mood {
                    font-size: 1.1em;
                    margin-right: 5px;
                }

                .message-time {
                    font-size: 0.75em;
                    opacity: 0.7;
                    margin-top: 5px;
                    text-align: right;
                }

                .message.mirai .message-time {
                    text-align: left;
                }

                .typing-indicator {
                    display: flex;
                    gap: 4px;
                    align-items: center;
                    padding: 8px 0;
                }

                .typing-indicator span {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #999;
                    animation: typing 1.4s infinite;
                }

                .typing-indicator span:nth-child(2) {
                    animation-delay: 0.2s;
                }

                .typing-indicator span:nth-child(3) {
                    animation-delay: 0.4s;
                }

                .chat-input-container {
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 0 0 20px 20px;
                }

                .chat-input-wrapper {
                    display: flex;
                    gap: 10px;
                    align-items: flex-end;
                    margin-bottom: 15px;
                }

                .chat-input {
                    flex: 1;
                    border: 2px solid #e1e5e9;
                    border-radius: 20px;
                    padding: 12px 16px;
                    font-family: inherit;
                    font-size: 14px;
                    resize: none;
                    max-height: 100px;
                    transition: border-color 0.2s;
                }

                .chat-input:focus {
                    outline: none;
                    border-color: #667eea;
                }

                .send-button {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    border: none;
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    font-size: 1.2em;
                    cursor: pointer;
                    transition: transform 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .send-button:hover:not(:disabled) {
                    transform: scale(1.05);
                }

                .send-button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .quick-actions {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }

                .quick-btn {
                    background: white;
                    border: 1px solid #e1e5e9;
                    border-radius: 15px;
                    padding: 8px 12px;
                    font-size: 0.85em;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .quick-btn:hover {
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                }

                @keyframes slideIn {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                @keyframes typing {
                    0%, 60%, 100% {
                        transform: translateY(0);
                    }
                    30% {
                        transform: translateY(-10px);
                    }
                }

                @keyframes pulse {
                    0%, 100% {
                        transform: scale(1);
                    }
                    50% {
                        transform: scale(1.05);
                    }
                }
            `}</style>
        </div>
    );
};

// Экспортируем компонент
window.MiraiChatEnhanced = MiraiChatEnhanced;