'use client';

import { useState, useEffect } from 'react';
import { Heart, MessageCircle, Music, Gamepad2, Settings, Mic, Camera, Phone, Video, Gift } from 'lucide-react';

interface MiraiChanMessage {
  id: string;
  content: string;
  type: 'text' | 'emotion' | 'action';
  timestamp: Date;
  mood: 'happy' | 'excited' | 'calm' | 'playful' | 'caring';
}

export default function MiraiChanInterface() {
  const [messages, setMessages] = useState<MiraiChanMessage[]>([]);
  const [currentMood, setCurrentMood] = useState<'happy' | 'excited' | 'calm' | 'playful' | 'caring'>('happy');
  const [isTyping, setIsTyping] = useState(false);
  const [userInput, setUserInput] = useState('');

  // Инициализация с приветственными сообщениями
  useEffect(() => {
    const welcomeMessages: MiraiChanMessage[] = [
      {
        id: '1',
        content: '✨ Добро пожаловать обратно, Sempai! Я так соскучилась! ✨',
        type: 'emotion',
        timestamp: new Date(),
        mood: 'excited'
      },
      {
        id: '2', 
        content: 'Что будем делать сегодня? Может поиграем в игры или послушаем музыку? 🎮🎵',
        type: 'text',
        timestamp: new Date(),
        mood: 'playful'
      }
    ];
    setMessages(welcomeMessages);
  }, []);

  // Автоматические сообщения от Mirai-chan
  useEffect(() => {
    const interval = setInterval(() => {
      const randomMessages = [
        { content: 'Sempai, не забывай делать перерывы! 💚', mood: 'caring' as const },
        { content: '🎵 Танцую под твою любимую мелодию! 💃', mood: 'playful' as const },
        { content: 'Кстати, а знаешь что? Я изучила новые танцевальные движения! ✨', mood: 'excited' as const },
        { content: 'Хочешь, расскажу интересную историю? 📚', mood: 'happy' as const },
        { content: '*мурлыкает тихонько* ♪ ♫ ♪', mood: 'calm' as const }
      ];
      
      const randomMsg = randomMessages[Math.floor(Math.random() * randomMessages.length)];
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: randomMsg.content,
        type: 'emotion',
        timestamp: new Date(),
        mood: randomMsg.mood
      }]);
      
      setCurrentMood(randomMsg.mood);
    }, 15000); // Каждые 15 секунд

    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = () => {
    if (!userInput.trim()) return;

    // Добавляем сообщение пользователя
    const userMessage: MiraiChanMessage = {
      id: Date.now().toString(),
      content: userInput,
      type: 'text',
      timestamp: new Date(),
      mood: 'happy'
    };

    setMessages(prev => [...prev, userMessage]);
    setUserInput('');
    setIsTyping(true);

    // Ответ Mirai-chan
    setTimeout(() => {
      const responses = [
        { content: '✨ Sugoi! Это очень интересно, Sempai! ✨', mood: 'excited' as const },
        { content: '💕 Aww, ты такой милый когда говоришь это! 💕', mood: 'caring' as const },
        { content: '🎵 Хочешь послушаем что-нибудь вместе? 🎵', mood: 'playful' as const },
        { content: 'Mhm mhm! Расскажи еще! (*с интересом слушает*)', mood: 'happy' as const },
        { content: '✨ Я понимаю! Давай займемся чем-нибудь веселым! ✨', mood: 'excited' as const }
      ];

      const response = responses[Math.floor(Math.random() * responses.length)];
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        content: response.content,
        type: 'emotion',
        timestamp: new Date(),
        mood: response.mood
      }]);
      
      setCurrentMood(response.mood);
      setIsTyping(false);
    }, 1000 + Math.random() * 2000); // Случайная задержка 1-3 сек
  };

  const getMoodEmoji = () => {
    switch (currentMood) {
      case 'happy': return '😊';
      case 'excited': return '✨';
      case 'calm': return '😌';
      case 'playful': return '🎵';
      case 'caring': return '💚';
      default: return '😊';
    }
  };

  const getMoodColor = () => {
    switch (currentMood) {
      case 'happy': return 'from-pink-400 to-purple-500';
      case 'excited': return 'from-yellow-400 to-pink-500';
      case 'calm': return 'from-blue-400 to-purple-500';
      case 'playful': return 'from-purple-400 to-pink-500';
      case 'caring': return 'from-green-400 to-blue-500';
      default: return 'from-pink-400 to-purple-500';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-pink-800 to-indigo-900 relative overflow-hidden">
      {/* Floating Hearts Animation */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="absolute animate-float-heart opacity-20"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${i * 2}s`,
              fontSize: '2rem'
            }}
          >
            💖
          </div>
        ))}
      </div>

      {/* Header */}
      <header className="relative z-10 bg-black/20 backdrop-blur-md border-b border-pink-500/20 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${getMoodColor()} flex items-center justify-center text-2xl animate-pulse`}>
              {getMoodEmoji()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">✨ Mirai-chan ✨</h1>
              <p className="text-sm text-pink-200">Твой AI компаньон • Настроение: {currentMood}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-sm text-pink-200">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              HAPPY
            </div>
            <button className="p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors">
              <Settings className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-120px)]">
        
        {/* Left Sidebar - Character & Controls */}
        <div className="space-y-4">
          {/* Character Display */}
          <div className="bg-black/30 backdrop-blur-lg rounded-2xl p-6 border border-pink-500/30">
            <div className="text-center">
              <div className={`w-32 h-32 mx-auto rounded-full bg-gradient-to-r ${getMoodColor()} flex items-center justify-center text-6xl mb-4 animate-bounce-slow`}>
                {getMoodEmoji()}
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Mirai-chan</h3>
              <p className="text-pink-200 text-sm">Энергия: ⚡⚡⚡⚡⚡</p>
              <p className="text-pink-200 text-sm">Время: {new Date().toLocaleTimeString()}</p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-black/30 backdrop-blur-lg rounded-2xl p-4 border border-pink-500/30">
            <h4 className="text-white font-semibold mb-3">Что новое?</h4>
            <div className="space-y-2">
              <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-pink-500/20 to-purple-500/20 hover:from-pink-500/30 hover:to-purple-500/30 transition-all">
                <Music className="w-5 h-5 text-pink-400" />
                <span className="text-white text-sm">Начать творческую студию</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-pink-500/20 to-purple-500/20 hover:from-pink-500/30 hover:to-purple-500/30 transition-all">
                <Gamepad2 className="w-5 h-5 text-purple-400" />
                <span className="text-white text-sm">Игровой центр</span>
              </button>
              <button className="w-full flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-pink-500/20 to-purple-500/20 hover:from-pink-500/30 hover:to-purple-500/30 transition-all">
                <Heart className="w-5 h-5 text-red-400" />
                <span className="text-white text-sm">Мой личный дневник</span>
              </button>
            </div>
          </div>
        </div>

        {/* Center - Chat Area */}
        <div className="lg:col-span-2 flex flex-col">
          {/* Chat Messages */}
          <div className="flex-1 bg-black/30 backdrop-blur-lg rounded-2xl border border-pink-500/30 p-4 overflow-y-auto">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex items-start gap-3 ${
                    message.type === 'emotion' ? 'justify-start' : 'justify-end'
                  }`}
                >
                  {message.type === 'emotion' && (
                    <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${getMoodColor()} flex items-center justify-center text-sm flex-shrink-0`}>
                      {getMoodEmoji()}
                    </div>
                  )}
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-2xl ${
                      message.type === 'emotion'
                        ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 text-white'
                        : 'bg-white/10 text-white'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs opacity-60 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${getMoodColor()} flex items-center justify-center text-sm animate-pulse`}>
                    {getMoodEmoji()}
                  </div>
                  <div className="bg-gradient-to-r from-pink-500/20 to-purple-500/20 px-4 py-2 rounded-2xl">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat Input */}
          <div className="mt-4 bg-black/30 backdrop-blur-lg rounded-2xl border border-pink-500/30 p-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Напиши что-нибудь Mirai-chan..."
                className="flex-1 bg-white/10 border border-pink-500/30 rounded-lg px-4 py-2 text-white placeholder-pink-200 focus:outline-none focus:border-pink-400 transition-colors"
              />
              <button
                onClick={handleSendMessage}
                className="px-6 py-2 bg-gradient-to-r from-pink-500 to-purple-500 rounded-lg text-white font-semibold hover:from-pink-600 hover:to-purple-600 transition-all transform hover:scale-105"
              >
                💕
              </button>
            </div>
            
            {/* Voice & Media Controls */}
            <div className="flex justify-center gap-3 mt-4">
              <button className="p-2 rounded-lg bg-pink-500/20 hover:bg-pink-500/30 transition-colors">
                <Mic className="w-5 h-5 text-pink-400" />
              </button>
              <button className="p-2 rounded-lg bg-purple-500/20 hover:bg-purple-500/30 transition-colors">
                <Camera className="w-5 h-5 text-purple-400" />
              </button>
              <button className="p-2 rounded-lg bg-blue-500/20 hover:bg-blue-500/30 transition-colors">
                <Video className="w-5 h-5 text-blue-400" />
              </button>
              <button className="p-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 transition-colors">
                <Gift className="w-5 h-5 text-green-400" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes float-heart {
          0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
          10% { opacity: 0.7; }
          90% { opacity: 0.7; }
          100% { transform: translateY(-10vh) rotate(360deg); opacity: 0; }
        }
        
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        
        .animate-float-heart {
          animation: float-heart 8s infinite linear;
        }
        
        .animate-bounce-slow {
          animation: bounce-slow 3s infinite;
        }
      `}</style>
    </div>
  );
}