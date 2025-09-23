import React, { useState, useEffect } from 'react';
import { useMiraiPersonality } from './MiraiPersonality';

// Navigation component for Living Mirai
const MiraiNavigation = ({ currentPage, onPageChange, miraiState }) => {
  const pages = [
    { id: 'home', name: 'Главная', icon: '🏠', color: '#FF6B9D' },
    { id: 'chat', name: 'Чат', icon: '💬', color: '#4ECDC4' },
    { id: 'avatar', name: 'Аватар', icon: '👧', color: '#45B7D1' },
    { id: 'diary', name: 'Дневник', icon: '📖', color: '#96CEB4' },
    { id: 'music', name: 'Музыка', icon: '🎵', color: '#FFEAA7' },
    { id: 'games', name: 'Игры', icon: '🎮', color: '#DDA0DD' },
    { id: 'creative', name: 'Творчество', icon: '🎨', color: '#F8B500' },
    { id: 'profile', name: 'Профиль', icon: '⚙️', color: '#74B9FF' }
  ];

  return (
    <nav className="mirai-navigation">
      <div className="nav-header">
        <div className="mirai-logo">
          <span className="logo-icon">✨</span>
          <span className="logo-text">Mirai-chan</span>
        </div>
        <div className="mirai-status">
          <div className="status-indicator" data-mood={miraiState.mood}></div>
          <span className="status-text">{miraiState.mood}</span>
        </div>
      </div>
      
      <div className="nav-menu">
        {pages.map(page => (
          <button
            key={page.id}
            className={`nav-item ${currentPage === page.id ? 'active' : ''}`}
            onClick={() => onPageChange(page.id)}
            style={{ '--accent-color': page.color }}
          >
            <span className="nav-icon">{page.icon}</span>
            <span className="nav-label">{page.name}</span>
            {page.id === 'chat' && (
              <div className="notification-badge">3</div>
            )}
          </button>
        ))}
      </div>
      
      <div className="nav-footer">
        <div className="connection-status">
          <div className="connection-dot online"></div>
          <span>Онлайн</span>
        </div>
      </div>

      <style jsx>{`
        .mirai-navigation {
          width: 280px;
          height: 100vh;
          background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
          display: flex;
          flex-direction: column;
          padding: 20px;
          box-shadow: 2px 0 10px rgba(0,0,0,0.1);
          position: relative;
          overflow: hidden;
        }

        .mirai-navigation::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
          pointer-events: none;
        }

        .nav-header {
          margin-bottom: 30px;
          position: relative;
          z-index: 1;
        }

        .mirai-logo {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 15px;
        }

        .logo-icon {
          font-size: 2em;
          animation: sparkle 2s ease-in-out infinite;
        }

        .logo-text {
          font-size: 1.8em;
          font-weight: bold;
          background: linear-gradient(45deg, #ffd93d, #ff6b9d);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .mirai-status {
          display: flex;
          align-items: center;
          gap: 8px;
          color: rgba(255,255,255,0.9);
          font-size: 14px;
        }

        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background: #4CAF50;
          animation: pulse 2s ease-in-out infinite;
        }

        .status-indicator[data-mood="HAPPY"] { background: #FFD700; }
        .status-indicator[data-mood="EXCITED"] { background: #FF6B9D; }
        .status-indicator[data-mood="CALM"] { background: #87CEEB; }
        .status-indicator[data-mood="PLAYFUL"] { background: #FF69B4; }
        .status-indicator[data-mood="CURIOUS"] { background: #DDA0DD; }

        .nav-menu {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
          position: relative;
          z-index: 1;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 15px 20px;
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 15px;
          color: white;
          text-decoration: none;
          transition: all 0.3s ease;
          cursor: pointer;
          position: relative;
          overflow: hidden;
        }

        .nav-item::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          transition: left 0.5s ease;
        }

        .nav-item:hover::before {
          left: 100%;
        }

        .nav-item:hover {
          background: rgba(255,255,255,0.2);
          transform: translateX(5px);
        }

        .nav-item.active {
          background: var(--accent-color, #FF6B9D);
          transform: translateX(8px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .nav-icon {
          font-size: 1.3em;
          width: 24px;
          text-align: center;
        }

        .nav-label {
          font-weight: 600;
          font-size: 16px;
        }

        .notification-badge {
          background: #ff4757;
          color: white;
          border-radius: 50%;
          width: 20px;
          height: 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
          margin-left: auto;
          animation: bounce 1s ease-in-out infinite;
        }

        .nav-footer {
          border-top: 1px solid rgba(255,255,255,0.2);
          padding-top: 20px;
          position: relative;
          z-index: 1;
        }

        .connection-status {
          display: flex;
          align-items: center;
          gap: 8px;
          color: rgba(255,255,255,0.8);
          font-size: 14px;
        }

        .connection-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .connection-dot.online {
          background: #4CAF50;
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes sparkle {
          0%, 100% { transform: scale(1) rotate(0deg); }
          50% { transform: scale(1.1) rotate(180deg); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }

        @media (max-width: 768px) {
          .mirai-navigation {
            width: 100%;
            height: auto;
            flex-direction: row;
            padding: 10px;
            position: fixed;
            bottom: 0;
            left: 0;
            z-index: 1000;
          }

          .nav-header {
            display: none;
          }

          .nav-menu {
            flex-direction: row;
            justify-content: space-around;
            flex: 1;
            gap: 5px;
          }

          .nav-item {
            flex-direction: column;
            gap: 5px;
            padding: 8px 4px;
            min-width: 60px;
          }

          .nav-label {
            font-size: 10px;
          }

          .nav-icon {
            font-size: 1.1em;
          }

          .nav-footer {
            display: none;
          }
        }
      `}</style>
    </nav>
  );
};

// Main application component that integrates all Mirai personality components
export default function LivingMiraiApp({ userId = 'default' }) {
  const [currentPage, setCurrentPage] = useState('home');
  const [miraiEmotion, setMiraiEmotion] = useState('HAPPY');
  const [isLoading, setIsLoading] = useState(true);
  
  const { currentState, updateMood } = useMiraiPersonality(userId);

  // Lazy load components
  const [components, setComponents] = useState({});

  useEffect(() => {
    // Simulate loading and import components
    const loadComponents = async () => {
      setIsLoading(true);
      
      // In a real app, these would be dynamic imports
      const componentModules = {
        chat: () => import('./MiraiChat'),
        avatar: () => import('./MiraiAvatar'),
        diary: () => import('./MiraiDiary'),
        music: () => import('./MiraiMusicStudio'),
        games: () => import('./MiraiGameCenter'),
        creative: () => import('./MiraiCreativeStudio')
      };

      // Simulate async loading
      setTimeout(() => {
        setComponents(componentModules);
        setIsLoading(false);
      }, 1000);
    };

    loadComponents();
  }, []);

  // Handle emotion changes from child components
  const handleEmotionChange = (newEmotion) => {
    setMiraiEmotion(newEmotion);
    updateMood(newEmotion);
  };

  // Get page component
  const getCurrentPageComponent = () => {
    if (isLoading) {
      return <LoadingScreen />;
    }

    switch (currentPage) {
      case 'home':
        return <HomePage miraiState={currentState} onEmotionChange={handleEmotionChange} />;
      case 'chat':
        return <ChatPlaceholder userId={userId} onEmotionChange={handleEmotionChange} />;
      case 'avatar':
        return <AvatarPlaceholder emotion={miraiEmotion} />;
      case 'diary':
        return <DiaryPlaceholder userId={userId} onEmotionChange={handleEmotionChange} />;
      case 'music':
        return <MusicPlaceholder userId={userId} onEmotionChange={handleEmotionChange} />;
      case 'games':
        return <GamesPlaceholder userId={userId} onEmotionChange={handleEmotionChange} />;
      case 'creative':
        return <CreativePlaceholder userId={userId} onEmotionChange={handleEmotionChange} />;
      case 'profile':
        return <ProfilePage userId={userId} miraiState={currentState} />;
      default:
        return <HomePage miraiState={currentState} onEmotionChange={handleEmotionChange} />;
    }
  };

  return (
    <div className="living-mirai-app">
      <MiraiNavigation 
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        miraiState={currentState}
      />
      
      <main className="app-main">
        {getCurrentPageComponent()}
      </main>

      <style jsx>{`
        .living-mirai-app {
          display: flex;
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .app-main {
          flex: 1;
          overflow-y: auto;
          position: relative;
        }

        @media (max-width: 768px) {
          .living-mirai-app {
            flex-direction: column;
          }
          
          .app-main {
            padding-bottom: 80px; /* Space for mobile navigation */
          }
        }
      `}</style>
    </div>
  );
}

// Loading screen component
const LoadingScreen = () => (
  <div className="loading-screen">
    <div className="loading-animation">
      <div className="mirai-avatar">
        <div className="avatar-face">
          <div className="eyes">
            <div className="eye left"></div>
            <div className="eye right"></div>
          </div>
          <div className="mouth"></div>
        </div>
      </div>
      <div className="loading-text">
        <h2>Mirai-chan просыпается...</h2>
        <div className="loading-dots">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </div>
      </div>
    </div>

    <style jsx>{`
      .loading-screen {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }

      .loading-animation {
        text-align: center;
        animation: float 3s ease-in-out infinite;
      }

      .mirai-avatar {
        width: 120px;
        height: 120px;
        background: linear-gradient(45deg, #ff6b9d, #ffd93d);
        border-radius: 50%;
        margin: 0 auto 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      }

      .avatar-face {
        position: relative;
      }

      .eyes {
        display: flex;
        gap: 15px;
        margin-bottom: 10px;
      }

      .eye {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: blink 2s ease-in-out infinite;
      }

      .mouth {
        width: 15px;
        height: 8px;
        border: 2px solid white;
        border-top: none;
        border-radius: 0 0 15px 15px;
        margin: 0 auto;
      }

      .loading-text h2 {
        margin: 0 0 15px 0;
        font-size: 1.5em;
        background: linear-gradient(45deg, #ffd93d, #ff6b9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .loading-dots {
        display: flex;
        justify-content: center;
        gap: 5px;
      }

      .loading-dots span {
        animation: bounce 1.4s ease-in-out infinite both;
        font-size: 2em;
        opacity: 0.7;
      }

      .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
      .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

      @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
      }

      @keyframes blink {
        0%, 90%, 100% { transform: scaleY(1); }
        95% { transform: scaleY(0.1); }
      }

      @keyframes bounce {
        0%, 80%, 100% {
          transform: scale(0);
        } 40% {
          transform: scale(1.0);
        }
      }
    `}</style>
  </div>
);

// Home page component
const HomePage = ({ miraiState, onEmotionChange }) => {
  const [timeOfDay, setTimeOfDay] = useState('');
  const [greeting, setGreeting] = useState('');

  useEffect(() => {
    const hour = new Date().getHours();
    if (hour < 6) {
      setTimeOfDay('night');
      setGreeting('Доброй ночи');
    } else if (hour < 12) {
      setTimeOfDay('morning');
      setGreeting('Доброе утро');
    } else if (hour < 18) {
      setTimeOfDay('afternoon');
      setGreeting('Добрый день');
    } else {
      setTimeOfDay('evening');
      setGreeting('Добрый вечер');
    }
  }, []);

  const quickActions = [
    { id: 'chat', name: 'Поговорить', icon: '💬', color: '#4ECDC4' },
    { id: 'music', name: 'Послушать музыку', icon: '🎵', color: '#FFEAA7' },
    { id: 'games', name: 'Поиграть', icon: '🎮', color: '#DDA0DD' },
    { id: 'creative', name: 'Творить', icon: '🎨', color: '#F8B500' }
  ];

  return (
    <div className="home-page">
      <div className="welcome-section">
        <div className="greeting-text">
          <h1>{greeting}! ✨</h1>
          <p>Я Mirai-chan, и сегодня я чувствую себя {miraiState.mood.toLowerCase()}! 
            Что будем делать вместе?</p>
        </div>
        
        <div className="mirai-status-card">
          <div className="status-header">
            <h3>Состояние Mirai</h3>
            <div className="mood-indicator" data-mood={miraiState.mood}></div>
          </div>
          <div className="status-details">
            <div className="status-item">
              <span>Настроение:</span>
              <span className="mood-text">{miraiState.mood}</span>
            </div>
            <div className="status-item">
              <span>Энергия:</span>
              <div className="energy-bar">
                <div className="energy-fill" style={{ width: '85%' }}></div>
              </div>
            </div>
            <div className="status-item">
              <span>Время:</span>
              <span>{timeOfDay}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h2>Быстрые действия</h2>
        <div className="actions-grid">
          {quickActions.map(action => (
            <button
              key={action.id}
              className="action-card"
              style={{ '--card-color': action.color }}
              onClick={() => {
                // Handle navigation
                console.log(`Navigate to ${action.id}`);
              }}
            >
              <div className="action-icon">{action.icon}</div>
              <div className="action-name">{action.name}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="daily-highlights">
        <h2>Сегодняшние моменты</h2>
        <div className="highlights-container">
          <div className="highlight-card">
            <div className="highlight-icon">📈</div>
            <div className="highlight-content">
              <h4>Успешная торговая сессия</h4>
              <p>Помогла пользователю заработать 15% прибыли!</p>
            </div>
          </div>
          
          <div className="highlight-card">
            <div className="highlight-icon">🎨</div>
            <div className="highlight-content">
              <h4>Новое творческое произведение</h4>
              <p>Вместе создали красивый рисунок заката!</p>
            </div>
          </div>
          
          <div className="highlight-card">
            <div className="highlight-icon">💭</div>
            <div className="highlight-content">
              <h4>Интересный разговор</h4>
              <p>Обсудили философию искусственного интеллекта</p>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .home-page {
          padding: 40px;
          max-width: 1200px;
          margin: 0 auto;
          color: white;
        }

        .welcome-section {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 30px;
          margin-bottom: 50px;
        }

        .greeting-text h1 {
          font-size: 3em;
          margin: 0 0 20px 0;
          background: linear-gradient(45deg, #ffd93d, #ff6b9d);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .greeting-text p {
          font-size: 1.3em;
          line-height: 1.6;
          opacity: 0.9;
        }

        .mirai-status-card {
          background: rgba(255,255,255,0.1);
          border-radius: 20px;
          padding: 25px;
          backdrop-filter: blur(10px);
        }

        .status-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .status-header h3 {
          margin: 0;
          color: #ffd93d;
        }

        .mood-indicator {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #4CAF50;
        }

        .mood-indicator[data-mood="HAPPY"] { background: #FFD700; }
        .mood-indicator[data-mood="EXCITED"] { background: #FF6B9D; }
        .mood-indicator[data-mood="CALM"] { background: #87CEEB; }
        .mood-indicator[data-mood="PLAYFUL"] { background: #FF69B4; }

        .status-details {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .status-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .mood-text {
          background: rgba(255,107,157,0.3);
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          text-transform: uppercase;
        }

        .energy-bar {
          width: 100px;
          height: 6px;
          background: rgba(255,255,255,0.2);
          border-radius: 3px;
          overflow: hidden;
        }

        .energy-fill {
          height: 100%;
          background: linear-gradient(90deg, #4CAF50, #8BC34A);
          transition: width 0.3s ease;
        }

        .quick-actions {
          margin-bottom: 50px;
        }

        .quick-actions h2 {
          margin: 0 0 25px 0;
          font-size: 2em;
          color: #ffd93d;
        }

        .actions-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
        }

        .action-card {
          background: rgba(255,255,255,0.1);
          border: none;
          border-radius: 20px;
          padding: 30px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          text-align: center;
        }

        .action-card:hover {
          background: var(--card-color);
          transform: translateY(-5px);
          box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .action-icon {
          font-size: 3em;
          margin-bottom: 15px;
        }

        .action-name {
          font-size: 1.2em;
          font-weight: bold;
        }

        .daily-highlights h2 {
          margin: 0 0 25px 0;
          font-size: 2em;
          color: #ffd93d;
        }

        .highlights-container {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .highlight-card {
          display: flex;
          align-items: center;
          gap: 20px;
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          backdrop-filter: blur(10px);
        }

        .highlight-icon {
          font-size: 2.5em;
          width: 60px;
          text-align: center;
        }

        .highlight-content h4 {
          margin: 0 0 8px 0;
          color: #ffd93d;
        }

        .highlight-content p {
          margin: 0;
          opacity: 0.8;
          line-height: 1.4;
        }

        @media (max-width: 768px) {
          .home-page {
            padding: 20px;
          }

          .welcome-section {
            grid-template-columns: 1fr;
            gap: 20px;
          }

          .greeting-text h1 {
            font-size: 2em;
          }

          .actions-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .highlight-card {
            flex-direction: column;
            text-align: center;
          }
        }
      `}</style>
    </div>
  );
};

// Placeholder components (these would be replaced with actual component imports)
const ChatPlaceholder = ({ userId, onEmotionChange }) => (
  <div className="placeholder">
    <h2>💬 Чат с Mirai</h2>
    <p>Компонент чата загружается...</p>
  </div>
);

const AvatarPlaceholder = ({ emotion }) => (
  <div className="placeholder">
    <h2>👧 3D Аватар Mirai</h2>
    <p>Текущая эмоция: {emotion}</p>
    <p>3D аватар загружается...</p>
  </div>
);

const DiaryPlaceholder = ({ userId, onEmotionChange }) => (
  <div className="placeholder">
    <h2>📖 Дневник Mirai</h2>
    <p>Дневник загружается...</p>
  </div>
);

const MusicPlaceholder = ({ userId, onEmotionChange }) => (
  <div className="placeholder">
    <h2>🎵 Музыкальная студия</h2>
    <p>Музыкальная студия загружается...</p>
  </div>
);

const GamesPlaceholder = ({ userId, onEmotionChange }) => (
  <div className="placeholder">
    <h2>🎮 Игровой центр</h2>
    <p>Игры загружаются...</p>
  </div>
);

const CreativePlaceholder = ({ userId, onEmotionChange }) => (
  <div className="placeholder">
    <h2>🎨 Творческая студия</h2>
    <p>Творческая студия загружается...</p>
  </div>
);

const ProfilePage = ({ userId, miraiState }) => (
  <div className="profile-page">
    <h2>⚙️ Профиль и настройки</h2>
    <div className="profile-content">
      <div className="user-stats">
        <h3>Ваша статистика</h3>
        <div className="stat-grid">
          <div className="stat-item">
            <div className="stat-number">15</div>
            <div className="stat-label">Дней вместе</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">147</div>
            <div className="stat-label">Сообщений</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">8</div>
            <div className="stat-label">Проектов</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">92%</div>
            <div className="stat-label">Дружба</div>
          </div>
        </div>
      </div>
      
      <div className="settings">
        <h3>Настройки</h3>
        <div className="setting-item">
          <label>Язык интерфейса</label>
          <select>
            <option>Русский</option>
            <option>English</option>
            <option>日本語</option>
          </select>
        </div>
        <div className="setting-item">
          <label>Уведомления</label>
          <input type="checkbox" checked />
        </div>
        <div className="setting-item">
          <label>Голос Mirai</label>
          <select>
            <option>Kawaii</option>
            <option>Serious</option>
            <option>Playful</option>
          </select>
        </div>
      </div>
    </div>

    <style jsx>{`
      .profile-page {
        padding: 40px;
        max-width: 800px;
        margin: 0 auto;
        color: white;
      }

      .profile-page h2 {
        margin: 0 0 30px 0;
        font-size: 2.5em;
        background: linear-gradient(45deg, #ffd93d, #ff6b9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
      }

      .profile-content {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 30px;
      }

      .user-stats, .settings {
        background: rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 25px;
        backdrop-filter: blur(10px);
      }

      .user-stats h3, .settings h3 {
        margin: 0 0 20px 0;
        color: #ffd93d;
      }

      .stat-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 15px;
      }

      .stat-item {
        text-align: center;
        background: rgba(255,255,255,0.1);
        padding: 20px;
        border-radius: 10px;
      }

      .stat-number {
        font-size: 2em;
        font-weight: bold;
        color: #ff6b9d;
        margin-bottom: 5px;
      }

      .stat-label {
        font-size: 12px;
        opacity: 0.8;
        text-transform: uppercase;
      }

      .setting-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding: 15px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
      }

      .setting-item label {
        font-weight: bold;
      }

      .setting-item select,
      .setting-item input {
        background: rgba(255,255,255,0.2);
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
        color: white;
        outline: none;
      }

      @media (max-width: 768px) {
        .profile-content {
          grid-template-columns: 1fr;
        }
        
        .stat-grid {
          grid-template-columns: repeat(2, 1fr);
        }
      }
    `}</style>
  </div>
);