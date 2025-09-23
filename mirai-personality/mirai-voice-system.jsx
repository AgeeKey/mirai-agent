/**
 * Mirai Voice System
 * Голосовое взаимодействие с Web Speech API
 */

const MiraiVoiceSystem = () => {
    const [isListening, setIsListening] = React.useState(false);
    const [isSpeaking, setIsSpeaking] = React.useState(false);
    const [transcript, setTranscript] = React.useState('');
    const [voiceEnabled, setVoiceEnabled] = React.useState(false);
    const [selectedVoice, setSelectedVoice] = React.useState(null);
    const [availableVoices, setAvailableVoices] = React.useState([]);
    const [volume, setVolume] = React.useState(0.8);
    const [pitch, setPitch] = React.useState(1.2);
    const [rate, setRate] = React.useState(0.9);
    const [lastSpoken, setLastSpoken] = React.useState('');

    const recognitionRef = React.useRef(null);
    const synthRef = React.useRef(null);

    // Инициализация Speech API
    React.useEffect(() => {
        initializeSpeechRecognition();
        initializeSpeechSynthesis();
        
        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
            }
            if (synthRef.current) {
                speechSynthesis.cancel();
            }
        };
    }, []);

    // Инициализация распознавания речи
    const initializeSpeechRecognition = () => {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.warn('Speech Recognition не поддерживается в этом браузере');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'ru-RU';
        
        recognition.onstart = () => {
            setIsListening(true);
            console.log('🎤 Начинаю слушать...');
        };
        
        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            setTranscript(finalTranscript + interimTranscript);
            
            if (finalTranscript && finalTranscript.trim()) {
                handleVoiceInput(finalTranscript.trim());
            }
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            setIsListening(false);
        };
        
        recognition.onend = () => {
            setIsListening(false);
            console.log('🎤 Остановил слушать');
        };
        
        recognitionRef.current = recognition;
    };

    // Инициализация синтеза речи
    const initializeSpeechSynthesis = () => {
        if (!('speechSynthesis' in window)) {
            console.warn('Speech Synthesis не поддерживается в этом браузере');
            return;
        }

        const updateVoices = () => {
            const voices = speechSynthesis.getVoices();
            setAvailableVoices(voices);
            
            // Попытка найти русский женский голос
            const russianVoices = voices.filter(voice => 
                voice.lang.includes('ru') || voice.name.toLowerCase().includes('russian')
            );
            
            const femaleVoices = voices.filter(voice => 
                voice.name.toLowerCase().includes('female') || 
                voice.name.toLowerCase().includes('woman') ||
                voice.name.toLowerCase().includes('anna') ||
                voice.name.toLowerCase().includes('elena') ||
                voice.name.toLowerCase().includes('irina')
            );
            
            // Приоритет: русский женский голос
            const preferredVoice = russianVoices.find(voice => 
                voice.name.toLowerCase().includes('female') ||
                voice.name.toLowerCase().includes('anna')
            ) || russianVoices[0] || femaleVoices[0] || voices[0];
            
            setSelectedVoice(preferredVoice);
            setVoiceEnabled(true);
        };

        // Voices загружаются асинхронно
        speechSynthesis.onvoiceschanged = updateVoices;
        updateVoices(); // Попытка загрузить сразу
    };

    // Обработка голосового ввода
    const handleVoiceInput = async (text) => {
        console.log('🗣️ Распознана речь:', text);
        
        // Обработка команд
        if (text.toLowerCase().includes('мираи') || text.toLowerCase().includes('mirai')) {
            if (text.toLowerCase().includes('привет') || text.toLowerCase().includes('здравствуй')) {
                speak('Привет! Как дела? Я так рада тебя слышать!');
            } else if (text.toLowerCase().includes('как дела')) {
                speak('У меня всё замечательно! Спасибо что спросил. А как твои дела?');
            } else if (text.toLowerCase().includes('что умеешь')) {
                speak('Я умею разговаривать, помогать с торговлей, рисовать, играть в игры и многое другое! Что тебя интересует?');
            } else if (text.toLowerCase().includes('пока') || text.toLowerCase().includes('до свидания')) {
                speak('До свидания! Было приятно с тобой поговорить. Возвращайся скорее!');
            } else {
                // Отправка в API для обработки
                try {
                    if (window.miraiAPI) {
                        const response = await window.miraiAPI.sendMessage(text, {
                            type: 'voice',
                            source: 'speech_recognition'
                        });
                        speak(response.message || 'Интересно! Расскажи мне больше.');
                    } else {
                        speak('Очень интересно! Я думаю об этом...');
                    }
                } catch (error) {
                    speak('Хм, дай мне подумать об этом...');
                }
            }
        }
    };

    // Синтез речи
    const speak = (text) => {
        if (!voiceEnabled || !selectedVoice || !text) return;
        
        // Остановка текущего воспроизведения
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = selectedVoice;
        utterance.volume = volume;
        utterance.pitch = pitch;
        utterance.rate = rate;
        
        utterance.onstart = () => {
            setIsSpeaking(true);
            setLastSpoken(text);
            console.log('🗣️ Начинаю говорить:', text);
        };
        
        utterance.onend = () => {
            setIsSpeaking(false);
            console.log('🗣️ Закончил говорить');
        };
        
        utterance.onerror = (event) => {
            console.error('Speech synthesis error:', event.error);
            setIsSpeaking(false);
        };
        
        speechSynthesis.speak(utterance);
    };

    // Управление записью
    const toggleListening = () => {
        if (!recognitionRef.current) return;
        
        if (isListening) {
            recognitionRef.current.stop();
        } else {
            setTranscript('');
            recognitionRef.current.start();
        }
    };

    // Остановка речи
    const stopSpeaking = () => {
        speechSynthesis.cancel();
        setIsSpeaking(false);
    };

    // Тестовые фразы
    const testPhrases = [
        'Привет! Я Mirai-chan! Как дела?',
        'Готова помочь тебе с торговлей!',
        'Давай создадим что-нибудь вместе!',
        'Я изучаю рынки каждый день!',
        'Хочешь поиграть в игру?'
    ];

    const speakTestPhrase = () => {
        const phrase = testPhrases[Math.floor(Math.random() * testPhrases.length)];
        speak(phrase);
    };

    return (
        <div className="voice-system">
            <div className="voice-header">
                <h2>🎤 Голосовое взаимодействие</h2>
                <div className="voice-status">
                    {voiceEnabled ? (
                        <span className="status-enabled">✅ Голос активен</span>
                    ) : (
                        <span className="status-disabled">❌ Голос недоступен</span>
                    )}
                </div>
            </div>

            {/* Основные управления */}
            <div className="voice-controls">
                <div className="main-controls">
                    <button 
                        onClick={toggleListening}
                        disabled={!voiceEnabled}
                        className={`control-btn ${isListening ? 'listening' : ''}`}
                    >
                        {isListening ? '🔴 Слушаю...' : '🎤 Начать запись'}
                    </button>
                    
                    <button 
                        onClick={stopSpeaking}
                        disabled={!isSpeaking}
                        className="control-btn stop"
                    >
                        {isSpeaking ? '⏹️ Остановить' : '⏸️ Не говорю'}
                    </button>
                    
                    <button 
                        onClick={speakTestPhrase}
                        disabled={!voiceEnabled || isSpeaking}
                        className="control-btn test"
                    >
                        ✨ Тест голоса
                    </button>
                </div>

                {/* Визуализация */}
                <div className="voice-visualization">
                    {isListening && (
                        <div className="listening-indicator">
                            <div className="sound-wave">
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <p>Говорите что-нибудь...</p>
                        </div>
                    )}
                    
                    {isSpeaking && (
                        <div className="speaking-indicator">
                            <div className="speaking-avatar">🗣️</div>
                            <p>Mirai говорит...</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Транскрипт */}
            {transcript && (
                <div className="transcript">
                    <h3>Распознанная речь:</h3>
                    <p>{transcript}</p>
                </div>
            )}

            {/* Последнее сказанное */}
            {lastSpoken && (
                <div className="last-spoken">
                    <h3>Последний ответ Mirai:</h3>
                    <p>{lastSpoken}</p>
                </div>
            )}

            {/* Настройки голоса */}
            <div className="voice-settings">
                <h3>Настройки голоса</h3>
                
                <div className="setting-group">
                    <label>Голос:</label>
                    <select 
                        value={selectedVoice?.name || ''}
                        onChange={(e) => {
                            const voice = availableVoices.find(v => v.name === e.target.value);
                            setSelectedVoice(voice);
                        }}
                    >
                        {availableVoices.map((voice) => (
                            <option key={voice.name} value={voice.name}>
                                {voice.name} ({voice.lang})
                            </option>
                        ))}
                    </select>
                </div>

                <div className="setting-group">
                    <label>Громкость: {Math.round(volume * 100)}%</label>
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                    />
                </div>

                <div className="setting-group">
                    <label>Высота тона: {pitch.toFixed(1)}</label>
                    <input
                        type="range"
                        min="0.5"
                        max="2"
                        step="0.1"
                        value={pitch}
                        onChange={(e) => setPitch(parseFloat(e.target.value))}
                    />
                </div>

                <div className="setting-group">
                    <label>Скорость: {rate.toFixed(1)}</label>
                    <input
                        type="range"
                        min="0.5"
                        max="2"
                        step="0.1"
                        value={rate}
                        onChange={(e) => setRate(parseFloat(e.target.value))}
                    />
                </div>
            </div>

            {/* Инструкции */}
            <div className="voice-instructions">
                <h3>💡 Как использовать</h3>
                <ul>
                    <li>Нажмите "Начать запись" и скажите что-нибудь</li>
                    <li>Обращайтесь к Mirai по имени для активации</li>
                    <li>Попробуйте: "Мираи, привет!" или "Mirai, как дела?"</li>
                    <li>Настройте голос под свои предпочтения</li>
                </ul>
            </div>

            <style jsx>{`
                .voice-system {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }

                .voice-header {
                    text-align: center;
                    margin-bottom: 30px;
                }

                .voice-header h2 {
                    margin-bottom: 10px;
                    font-size: 2em;
                }

                .status-enabled {
                    color: #4CAF50;
                    font-weight: bold;
                }

                .status-disabled {
                    color: #ff6b6b;
                    font-weight: bold;
                }

                .main-controls {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                }

                .control-btn {
                    background: rgba(255,255,255,0.2);
                    border: 2px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 15px 25px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 1em;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                }

                .control-btn:hover:not(:disabled) {
                    background: rgba(255,255,255,0.3);
                    transform: translateY(-2px);
                }

                .control-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .control-btn.listening {
                    background: #ff6b6b;
                    border-color: #ff6b6b;
                    animation: pulse 2s infinite;
                }

                .control-btn.stop {
                    background: #ff8c42;
                    border-color: #ff8c42;
                }

                .control-btn.test {
                    background: #4ecdc4;
                    border-color: #4ecdc4;
                }

                .voice-visualization {
                    text-align: center;
                    min-height: 80px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .listening-indicator, .speaking-indicator {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 15px;
                }

                .sound-wave {
                    display: flex;
                    gap: 5px;
                    align-items: end;
                }

                .sound-wave span {
                    width: 4px;
                    background: #ffd93d;
                    border-radius: 2px;
                    animation: wave 1.5s infinite ease-in-out;
                }

                .sound-wave span:nth-child(1) { height: 10px; animation-delay: 0s; }
                .sound-wave span:nth-child(2) { height: 20px; animation-delay: 0.2s; }
                .sound-wave span:nth-child(3) { height: 15px; animation-delay: 0.4s; }
                .sound-wave span:nth-child(4) { height: 25px; animation-delay: 0.6s; }
                .sound-wave span:nth-child(5) { height: 12px; animation-delay: 0.8s; }

                .speaking-avatar {
                    font-size: 3em;
                    animation: bounce 1s infinite;
                }

                .transcript, .last-spoken {
                    background: rgba(255,255,255,0.1);
                    border-radius: 15px;
                    padding: 20px;
                    margin: 20px 0;
                    backdrop-filter: blur(10px);
                }

                .transcript h3, .last-spoken h3 {
                    margin-bottom: 10px;
                    color: #ffd93d;
                }

                .voice-settings {
                    background: rgba(0,0,0,0.2);
                    border-radius: 15px;
                    padding: 20px;
                    margin: 20px 0;
                }

                .voice-settings h3 {
                    margin-bottom: 20px;
                    color: #ffd93d;
                }

                .setting-group {
                    margin-bottom: 15px;
                }

                .setting-group label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }

                .setting-group select,
                .setting-group input[type="range"] {
                    width: 100%;
                    padding: 8px;
                    border-radius: 10px;
                    border: none;
                    background: rgba(255,255,255,0.2);
                    color: white;
                }

                .setting-group select option {
                    background: #333;
                    color: white;
                }

                .voice-instructions {
                    background: rgba(255,217,61,0.2);
                    border-radius: 15px;
                    padding: 20px;
                    margin-top: 20px;
                }

                .voice-instructions h3 {
                    margin-bottom: 15px;
                    color: #ffd93d;
                }

                .voice-instructions ul {
                    padding-left: 20px;
                }

                .voice-instructions li {
                    margin-bottom: 8px;
                    line-height: 1.5;
                }

                @keyframes pulse {
                    0%, 100% {
                        opacity: 1;
                    }
                    50% {
                        opacity: 0.7;
                    }
                }

                @keyframes wave {
                    0%, 100% {
                        transform: scaleY(1);
                    }
                    50% {
                        transform: scaleY(2);
                    }
                }

                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% {
                        transform: translateY(0);
                    }
                    40% {
                        transform: translateY(-10px);
                    }
                    60% {
                        transform: translateY(-5px);
                    }
                }

                @media (max-width: 768px) {
                    .voice-system {
                        padding: 20px;
                    }
                    
                    .main-controls {
                        flex-direction: column;
                        align-items: center;
                    }
                    
                    .control-btn {
                        width: 100%;
                        max-width: 250px;
                    }
                }
            `}</style>
        </div>
    );
};

// Экспортируем компонент
window.MiraiVoiceSystem = MiraiVoiceSystem;