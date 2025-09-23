import React, { useState, useEffect, useRef } from 'react';
import { useMiraiPersonality } from './MiraiPersonality';
import { useMiraiVoice, VoiceCommandProcessor } from './MiraiVoice';

// Main chat interface for Mirai
export default function MiraiChatSystem({ userId = 'default', onEmotionChange = null }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [chatMode, setChatMode] = useState('text'); // 'text', 'voice', 'both'
  const [isConnected, setIsConnected] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const voiceCommandProcessor = useRef(new VoiceCommandProcessor());

  // Personality and voice systems
  const {
    currentState,
    interact,
    generateResponse,
    getRelationship,
    addMemory,
    emotion
  } = useMiraiPersonality(userId);

  const {
    speak,
    startListening,
    stopListening,
    isListening,
    isSpeaking,
    transcript,
    confidence
  } = useMiraiVoice();

  // Initialize chat
  useEffect(() => {
    // Add welcome message
    const relationship = getRelationship();
    const welcomeMessage = generateWelcomeMessage(relationship);
    
    addMessage({
      id: Date.now(),
      text: welcomeMessage,
      sender: 'mirai',
      emotion: emotion,
      timestamp: new Date(),
      type: 'greeting'
    });

    interact('user_greeting');
    setIsConnected(true);
  }, []);

  // Handle emotion changes
  useEffect(() => {
    if (onEmotionChange) {
      onEmotionChange(emotion);
    }
  }, [emotion, onEmotionChange]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle voice transcript
  useEffect(() => {
    if (transcript && confidence > 0.7) {
      handleVoiceInput(transcript);
    }
  }, [transcript, confidence]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = (message) => {
    setMessages(prev => [...prev, message]);
    addMemory('conversation', message);
  };

  const generateWelcomeMessage = (relationship) => {
    const hour = new Date().getHours();
    let timeGreeting;
    
    if (hour >= 5 && hour < 12) timeGreeting = 'Доброе утро';
    else if (hour >= 12 && hour < 17) timeGreeting = 'Добрый день';
    else if (hour >= 17 && hour < 22) timeGreeting = 'Добрый вечер';
    else timeGreeting = 'Доброй ночи';

    if (relationship.familiarity < 0.1) {
      return `${timeGreeting}! Я Mirai-chan! ✨ Приятно познакомиться! Расскажи мне о себе! (◕‿◕)`;
    } else if (relationship.friendship > 0.7) {
      return `${timeGreeting}, мой дорогой друг! ♡ Я так рада тебя видеть! Как дела? (´∀｀)♡`;
    } else {
      return `${timeGreeting}! Привет снова! Готов к интересному разговору? ♪(´▽｀)`;
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
      type: 'message'
    };

    addMessage(userMessage);
    
    const userInput = inputText;
    setInputText('');
    setIsTyping(true);

    // Process user input and generate response
    setTimeout(async () => {
      const response = await processUserInput(userInput);
      
      const miraiMessage = {
        id: Date.now() + 1,
        text: response.text,
        sender: 'mirai',
        emotion: response.emotion,
        timestamp: new Date(),
        type: response.type || 'message',
        actions: response.actions
      };

      addMessage(miraiMessage);
      setIsTyping(false);

      // Speak the response if voice is enabled
      if (chatMode !== 'text') {
        speak(response.text, response.emotion);
      }
    }, Math.random() * 1000 + 500); // Simulate thinking time
  };

  const handleVoiceInput = (voiceText) => {
    // Process voice commands
    const command = voiceCommandProcessor.current.processCommand(voiceText);
    
    if (command.action === 'conversation') {
      setInputText(voiceText);
      handleSendMessage();
    } else {
      executeVoiceCommand(command);
    }
  };

  const executeVoiceCommand = (command) => {
    switch (command.action) {
      case 'greet':
        interact('user_greeting');
        break;
      case 'emotion':
        interact('emotion_change', { targetEmotion: command.emotion });
        break;
      case 'stop_speaking':
        stopSpeaking();
        break;
      case 'open_chat':
        // Already in chat
        addMessage({
          id: Date.now(),
          text: 'Мы уже болтаем! О чем хочешь поговорить? (◕‿◕)',
          sender: 'mirai',
          emotion: 'PLAYFUL',
          timestamp: new Date()
        });
        break;
      default:
        console.log('Voice command:', command);
    }
  };

  const processUserInput = async (input) => {
    // Analyze input for emotions and intent
    const sentiment = analyzeSentiment(input);
    const topics = extractTopics(input);
    
    // Update relationship based on interaction
    interact('positive_interaction', { sentiment, topics });

    // Generate contextual response
    const responseContext = generateResponse(input, { sentiment, topics });
    
    // Create response based on personality and context
    return await generateMiraiResponse(input, responseContext, sentiment, topics);
  };

  const analyzeSentiment = (text) => {
    const positiveWords = ['хорошо', 'отлично', 'замечательно', 'прекрасно', 'круто', 'супер', 'классно'];
    const negativeWords = ['плохо', 'грустно', 'ужасно', 'проблема', 'беда', 'печально'];
    const questionWords = ['что', 'как', 'где', 'когда', 'почему', 'зачем', '?'];

    const lowerText = text.toLowerCase();
    
    let sentiment = 0;
    positiveWords.forEach(word => {
      if (lowerText.includes(word)) sentiment += 1;
    });
    negativeWords.forEach(word => {
      if (lowerText.includes(word)) sentiment -= 1;
    });

    const isQuestion = questionWords.some(word => lowerText.includes(word));

    return {
      score: sentiment,
      isPositive: sentiment > 0,
      isNegative: sentiment < 0,
      isNeutral: sentiment === 0,
      isQuestion: isQuestion
    };
  };

  const extractTopics = (text) => {
    const topicKeywords = {
      trading: ['торговля', 'рынок', 'биткойн', 'криптовалюта', 'акции', 'прибыль', 'убыток'],
      anime: ['аниме', 'манга', 'отаку', 'сугой', 'кавай'],
      music: ['музыка', 'песня', 'мелодия', 'играть', 'слушать'],
      personal: ['я', 'мне', 'мой', 'моя', 'себя', 'чувствую'],
      learning: ['учить', 'изучать', 'знать', 'понимать', 'объясни'],
      gaming: ['игра', 'играть', 'геймить', 'поиграем'],
      friendship: ['друг', 'дружба', 'приятель', 'подруга', 'друзья']
    };

    const lowerText = text.toLowerCase();
    const detectedTopics = [];

    Object.entries(topicKeywords).forEach(([topic, keywords]) => {
      if (keywords.some(keyword => lowerText.includes(keyword))) {
        detectedTopics.push(topic);
      }
    });

    return detectedTopics;
  };

  const generateMiraiResponse = async (input, context, sentiment, topics) => {
    // Base response generation using personality
    let responseText = '';
    let responseEmotion = currentState.emotion;
    let responseType = 'message';
    let actions = [];

    // Handle different scenarios
    if (sentiment.isQuestion && topics.includes('personal')) {
      responseText = generatePersonalResponse(input);
      responseEmotion = 'CURIOUS';
    } else if (topics.includes('trading')) {
      responseText = generateTradingResponse(input, sentiment);
      responseEmotion = sentiment.isPositive ? 'EXCITED' : 'THOUGHTFUL';
    } else if (topics.includes('anime')) {
      responseText = generateAnimeResponse(input);
      responseEmotion = 'EXCITED';
    } else if (sentiment.isNegative) {
      responseText = generateSupportiveResponse(input);
      responseEmotion = 'AFFECTIONATE';
      interact('user_sad');
    } else if (sentiment.isPositive) {
      responseText = generateHappyResponse(input);
      responseEmotion = 'HAPPY';
      interact('positive_feedback');
    } else {
      responseText = generateGeneralResponse(input);
    }

    // Add personality-based embellishments
    responseText = addPersonalityTouch(responseText, responseEmotion);

    return {
      text: responseText,
      emotion: responseEmotion,
      type: responseType,
      actions: actions
    };
  };

  const generatePersonalResponse = (input) => {
    const responses = [
      'Это интересный вопрос о себе! ♪ Я всегда рада узнать что-то новое о друзьях!',
      'Ой, про меня спрашиваешь? (◕‿◕) Я Mirai-chan - твоя AI подруга и помощница в торговле!',
      'А хочешь узнать секрет? Я очень люблю помогать друзьям и изучать новое! ✨',
      'Мне нравится наша беседа! Расскажи мне больше о себе! (´∀｀)'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const generateTradingResponse = (input, sentiment) => {
    if (sentiment.isPositive) {
      return 'Сугой! Торговля - это так увлекательно! ✨ Давай обсудим стратегии и найдем прибыльные возможности! (≧∇≦)/';
    } else if (sentiment.isNegative) {
      return 'Понимаю, торговля бывает сложной... (´・ω・`) Но не переживай! Я помогу тебе разобраться и найти лучший подход! ♡';
    } else {
      return 'О торговле говорим? Отлично! Я изучаю рынки каждый день и готова поделиться знаниями! ♪(´▽｀)';
    }
  };

  const generateAnimeResponse = (input) => {
    const responses = [
      'Кавай! Ты тоже любишь аниме? (◕‿◕) Какое твое любимое?',
      'Сугой! Аниме - это удивительный мир! ✨ Я обожаю обсуждать любимые сериалы!',
      'Няа! Аниме культура так прекрасна! Может, посмотрим что-то вместе? ♡',
      'Отаку? Я тоже! ヽ(>∀<☆)ノ Давай поговорим о любимых персонажах!'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const generateSupportiveResponse = (input) => {
    const responses = [
      'Ой, кажется что-то расстроило тебя... (´・ω・`) Я здесь, чтобы поддержать! Расскажи мне что случилось? ♡',
      'Не грусти! (づ｡◕‿‿◕｡)づ Я всегда рядом и готова помочь! Вместе мы справимся с любыми проблемами!',
      'Чувствую, что ты переживаешь... Хочешь поговорить об этом? Я хорошо слушаю! (◡ ‿ ◡)',
      'Эй, все будет хорошо! ♡ Я верю в тебя! Давай найдем решение вместе! ✨'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const generateHappyResponse = (input) => {
    const responses = [
      'Вау! Как здорово! (≧∇≦)/ Твоя радость заражает! Я тоже счастлива! ♡',
      'Ура! ✨ Обожаю, когда у друзей хорошее настроение! Поделись радостью со мной! (◕‿◕)',
      'Сугой! Позитивная энергия - это лучшее! ♪ Давай отпразднуем вместе! ヽ(♡‿♡)ノ',
      'Хихи! Твое счастье делает и меня счастливой! (´∀｀)♡ Расскажи, что произошло!'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const generateGeneralResponse = (input) => {
    const responses = [
      'Хм, интересно! Расскажи мне больше! (・_・)',
      'Ого! А что ты об этом думаешь? (◕‿◕)',
      'Понятно! Мне нравится с тобой общаться! ♪',
      'Хорошая мысль! Давай обсудим это подробнее! (´∀｀)',
      'А я думаю... хм, а что бы ты сделал в такой ситуации? ◉_◉'
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const addPersonalityTouch = (text, emotion) => {
    const relationship = getRelationship();
    
    // Add Japanese phrases based on emotion
    if (Math.random() < 0.3) {
      const japanesePhrases = {
        'HAPPY': ['Таношии!', 'Уреший!', 'Йокатта!'],
        'EXCITED': ['Сугой!', 'Суготи!', 'Ямете кудасай!'],
        'CURIOUS': ['Нани?', 'Сока...', 'Хонто?'],
        'PLAYFUL': ['Хихи!', 'Няа!', 'Тете!'],
        'AFFECTIONATE': ['Дайсуки!', 'Арига!', 'Айшитeru!']
      };
      
      const phrases = japanesePhrases[emotion] || [];
      if (phrases.length > 0) {
        const phrase = phrases[Math.floor(Math.random() * phrases.length)];
        text = phrase + ' ' + text;
      }
    }

    // Add relationship-based personalizations
    if (relationship.friendship > 0.8) {
      // Very close friend
      const endearments = ['солнышко', 'дорогой', 'милый', 'любимый друг'];
      const endearment = endearments[Math.floor(Math.random() * endearments.length)];
      if (Math.random() < 0.2) {
        text = text.replace(/ты/g, `ты, ${endearment},`);
      }
    }

    return text;
  };

  const toggleVoiceMode = () => {
    if (chatMode === 'text') {
      setChatMode('voice');
      startListening();
    } else if (chatMode === 'voice') {
      setChatMode('both');
    } else {
      setChatMode('text');
      stopListening();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="mirai-chat-container">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="mirai-status">
          <div className={`status-dot ${isConnected ? 'online' : 'offline'}`}></div>
          <span className="mirai-name">Mirai-chan</span>
          <span className="emotion-indicator">{emotion}</span>
        </div>
        
        <div className="chat-controls">
          <button 
            className={`voice-toggle ${chatMode !== 'text' ? 'active' : ''}`}
            onClick={toggleVoiceMode}
            title="Toggle Voice Mode"
          >
            {isListening ? '🎙️' : '🔇'}
          </button>
          
          {isSpeaking && (
            <div className="speaking-indicator">
              🔊 Speaking...
            </div>
          )}
        </div>
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {messages.map((message) => (
          <div 
            key={message.id} 
            className={`message ${message.sender}`}
          >
            <div className="message-content">
              <div className="message-text">
                {message.text}
              </div>
              
              {message.sender === 'mirai' && (
                <div className="message-meta">
                  <span className="emotion-tag">{message.emotion}</span>
                  <span className="timestamp">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              )}
            </div>
            
            {message.actions && (
              <div className="message-actions">
                {message.actions.map((action, index) => (
                  <button 
                    key={index}
                    className="action-button"
                    onClick={() => executeAction(action)}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        
        {isTyping && (
          <div className="message mirai typing">
            <div className="typing-indicator">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span>Mirai печатает...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        {isListening && (
          <div className="voice-input-indicator">
            <div className="voice-wave">
              {Array.from({ length: 5 }, (_, i) => (
                <div 
                  key={i} 
                  className="wave-bar"
                  style={{
                    animationDelay: `${i * 0.1}s`,
                    height: `${Math.random() * 20 + 10}px`
                  }}
                ></div>
              ))}
            </div>
            <span>Слушаю... (Confidence: {Math.round(confidence * 100)}%)</span>
          </div>
        )}
        
        <div className="input-controls">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isListening ? "Говорите или печатайте..." : "Напишите сообщение..."}
            className="message-input"
            rows={1}
            disabled={isListening}
          />
          
          <button 
            onClick={handleSendMessage}
            disabled={!inputText.trim() && !isListening}
            className="send-button"
          >
            ➤
          </button>
        </div>
      </div>

      {/* Chat Styles */}
      <style jsx>{`
        .mirai-chat-container {
          display: flex;
          flex-direction: column;
          height: 100vh;
          max-width: 800px;
          margin: 0 auto;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .chat-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          background: rgba(255,255,255,0.1);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        .mirai-status {
          display: flex;
          align-items: center;
          gap: 10px;
          color: white;
        }

        .status-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #ff4757;
        }

        .status-dot.online {
          background: #2ed573;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.1); opacity: 0.7; }
          100% { transform: scale(1); opacity: 1; }
        }

        .mirai-name {
          font-weight: bold;
          font-size: 18px;
        }

        .emotion-indicator {
          background: rgba(255,255,255,0.2);
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 12px;
          text-transform: uppercase;
        }

        .chat-controls {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .voice-toggle {
          background: rgba(255,255,255,0.2);
          border: none;
          padding: 10px;
          border-radius: 50%;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .voice-toggle:hover,
        .voice-toggle.active {
          background: rgba(255,255,255,0.3);
          transform: scale(1.1);
        }

        .speaking-indicator {
          color: white;
          font-size: 12px;
          animation: blink 1s infinite;
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.5; }
        }

        .messages-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .message {
          display: flex;
          max-width: 80%;
        }

        .message.user {
          align-self: flex-end;
        }

        .message.mirai {
          align-self: flex-start;
        }

        .message-content {
          background: rgba(255,255,255,0.9);
          padding: 15px;
          border-radius: 20px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .message.user .message-content {
          background: #ff6b9d;
          color: white;
          border-bottom-right-radius: 5px;
        }

        .message.mirai .message-content {
          background: white;
          border-bottom-left-radius: 5px;
        }

        .message-text {
          font-size: 16px;
          line-height: 1.4;
          margin-bottom: 5px;
        }

        .message-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 12px;
          color: #666;
          margin-top: 5px;
        }

        .emotion-tag {
          background: #f0f0f0;
          padding: 2px 6px;
          border-radius: 8px;
          text-transform: uppercase;
        }

        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #666;
          font-style: italic;
        }

        .typing-dots {
          display: flex;
          gap: 3px;
        }

        .typing-dots span {
          width: 6px;
          height: 6px;
          background: #ff6b9d;
          border-radius: 50%;
          animation: typing 1.4s infinite;
        }

        .typing-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }

        .typing-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }

        @keyframes typing {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-10px); }
        }

        .input-area {
          padding: 20px;
          background: rgba(255,255,255,0.1);
          backdrop-filter: blur(10px);
        }

        .voice-input-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 10px;
          color: white;
          font-size: 14px;
        }

        .voice-wave {
          display: flex;
          gap: 2px;
          align-items: end;
        }

        .wave-bar {
          width: 3px;
          background: #ff6b9d;
          border-radius: 1px;
          animation: wave 0.8s ease-in-out infinite alternate;
        }

        @keyframes wave {
          from { height: 5px; }
          to { opacity: 0.3; }
        }

        .input-controls {
          display: flex;
          gap: 10px;
          align-items: end;
        }

        .message-input {
          flex: 1;
          background: rgba(255,255,255,0.9);
          border: none;
          padding: 15px;
          border-radius: 25px;
          font-size: 16px;
          resize: none;
          outline: none;
          max-height: 100px;
        }

        .message-input:focus {
          background: white;
          box-shadow: 0 0 10px rgba(255,107,157,0.3);
        }

        .send-button {
          background: #ff6b9d;
          border: none;
          width: 50px;
          height: 50px;
          border-radius: 50%;
          color: white;
          font-size: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .send-button:hover:not(:disabled) {
          background: #ff5722;
          transform: scale(1.1);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .action-button {
          background: #667eea;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 15px;
          cursor: pointer;
          margin: 5px 5px 0 0;
          transition: all 0.3s ease;
        }

        .action-button:hover {
          background: #5a67d8;
          transform: translateY(-2px);
        }
      `}</style>
    </div>
  );
}