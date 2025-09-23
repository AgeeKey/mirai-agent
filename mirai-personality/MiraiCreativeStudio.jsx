import React, { useState, useEffect, useRef } from 'react';
import { useMiraiPersonality } from './MiraiPersonality';

// Mirai's creative studio for collaborative art and content creation
export default function MiraiCreativeStudio({ userId = 'default', onEmotionChange = null }) {
  const [activeProject, setActiveProject] = useState(null);
  const [viewMode, setViewMode] = useState('gallery'); // 'gallery', 'create', 'collaborate'
  const [artStyle, setArtStyle] = useState('anime');
  const [creativeMode, setCreativeMode] = useState('draw'); // 'draw', 'write', 'music', 'video'
  const [collaborationLevel, setCollaborationLevel] = useState('guided'); // 'guided', 'freestyle', 'ai-lead'
  
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [brushSize, setBrushSize] = useState(5);
  const [brushColor, setBrushColor] = useState('#ff6b9d');
  const [currentStory, setCurrentStory] = useState('');
  const [storyPrompt, setStoryPrompt] = useState('');
  
  const { currentState, addMemory, getRelationship } = useMiraiPersonality(userId);
  const relationship = getRelationship();

  // Creative projects gallery
  const [projects] = useState([
    {
      id: 1,
      type: 'drawing',
      title: 'Sunset Over Crypto Markets',
      description: 'Совместное арт-произведение: золотой закат с графиками трейдинга как облаками',
      collaborators: ['User', 'Mirai'],
      mood: 'CALM',
      dateCreated: '2025-09-20',
      thumbnail: '🎨',
      tags: ['природа', 'трейдинг', 'закат'],
      difficulty: 'medium',
      completionTime: '45 минут',
      miraiContribution: 'Цветовая палитра и композиция',
      userContribution: 'Основные формы и детали'
    },
    {
      id: 2,
      type: 'story',
      title: 'Приключения в DeFi-лесу',
      description: 'Интерактивная сказка о путешествии через волшебный лес децентрализованных финансов',
      collaborators: ['User', 'Mirai'],
      mood: 'PLAYFUL',
      dateCreated: '2025-09-19',
      thumbnail: '📚',
      tags: ['сказка', 'DeFi', 'приключения'],
      difficulty: 'easy',
      completionTime: '30 минут',
      miraiContribution: 'Персонажи и диалоги',
      userContribution: 'Сюжетные повороты'
    },
    {
      id: 3,
      type: 'music',
      title: 'Мелодия Торговой Сессии',
      description: 'Ambient композиция, отражающая ритм рынка - от спокойного открытия до динамичного закрытия',
      collaborators: ['User', 'Mirai'],
      mood: 'EXCITED',
      dateCreated: '2025-09-18',
      thumbnail: '🎵',
      tags: ['ambient', 'трейдинг', 'ритм'],
      difficulty: 'hard',
      completionTime: '2 часа',
      miraiContribution: 'Базовая мелодия и аранжировка',
      userContribution: 'Ритм-секция и эффекты'
    },
    {
      id: 4,
      type: 'video',
      title: 'Объяснение Блокчейна через Аниме',
      description: 'Короткое обучающее видео в стиле аниме о том, как работает блокчейн',
      collaborators: ['User', 'Mirai'],
      mood: 'CURIOUS',
      dateCreated: '2025-09-17',
      thumbnail: '🎬',
      tags: ['обучение', 'блокчейн', 'аниме'],
      difficulty: 'hard',
      completionTime: '3 часа',
      miraiContribution: 'Сценарий и озвучка',
      userContribution: 'Анимация и монтаж'
    }
  ]);

  // Drawing prompts based on mood and trading context
  const getDrawingPrompts = () => {
    const prompts = {
      'HAPPY': [
        'Нарисуем радужного единорога, считающего прибыль! 🦄💰',
        'Давай создадим солнечный пейзаж с зелеными свечами! ☀️📈',
        'Как насчет счастливого кота-трейдера? 😺💹'
      ],
      'EXCITED': [
        'Создадим взрывной фейерверк из золотых монет! 🎆💰',
        'Нарисуем ракету, летящую к луне! 🚀🌙',
        'Давай изобразим танцующие графики! 💃📊'
      ],
      'CALM': [
        'Нарисуем тихий дзен-сад с камнями-монетами 🪨💎',
        'Создадим спокойное озеро с отражением гор-графиков 🏔️💧',
        'Как насчет медитирующего трейдера под сакурой? 🌸🧘'
      ],
      'PLAYFUL': [
        'Нарисуем забавных покемонов-криптовалют! ⚡💰',
        'Создадим карамельную землю из сладостей и монеток! 🍭💰',
        'Давай изобразим котиков, играющих с пузырями-графиками! 🐱💭'
      ]
    };
    
    return prompts[currentState.mood] || prompts['HAPPY'];
  };

  // Story prompts
  const getStoryPrompts = () => {
    const prompts = [
      'Жила-была маленькая криптомонета, которая мечтала стать биткоином...',
      'В далекой галактике, где вместо звезд светились экраны с графиками...',
      'Однажды Mirai обнаружила тайную дверь в мир, где числа ожили...',
      'В аниме-академии трейдинга новый семестр начался с загадочного урока...',
      'Котенок по имени Hodl отправился в путешествие через Блокчейн-лес...'
    ];
    
    return prompts[Math.floor(Math.random() * prompts.length)];
  };

  // Music creation prompts
  const getMusicPrompts = () => {
    const prompts = [
      'Создадим мелодию восходящего тренда - начинаем тихо и нарастаем!',
      'Сочиним ритм дневной торговли - быстрый, энергичный, с паузами',
      'Давай напишем спокойную композицию для ночного анализа рынка',
      'Как насчет драматической темы для крупных движений рынка?',
      'Создадим веселую мелодию для празднования прибыли!'
    ];
    
    return prompts[Math.floor(Math.random() * prompts.length)];
  };

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#f8f9fa';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
  }, []);

  // Drawing functions
  const startDrawing = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setIsDrawing(true);
    const ctx = canvas.getContext('2d');
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const draw = (e) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvas.getContext('2d');
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.strokeStyle = brushColor;
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  // Add Mirai's creative input
  const addMiraiInput = () => {
    const inputs = [
      'Oooh! А что если добавить больше ярких цветов? ✨',
      'Попробуй сделать этот уголок более округлым! (◕‿◕)',
      'Мне кажется, здесь не хватает маленьких деталей! 💫',
      'А давай добавим немного магии в этом месте? ✨',
      'Это выглядит потрясающе! Продолжай! (◡ ‿ ◡)'
    ];
    
    const randomInput = inputs[Math.floor(Math.random() * inputs.length)];
    
    addMemory('creative_collaboration', {
      type: creativeMode,
      miraiSuggestion: randomInput,
      userResponse: 'positive'
    });

    return randomInput;
  };

  // Generate collaborative story
  const generateStorySegment = () => {
    const segments = [
      'Внезапно главный герой понял, что...',
      'Но тут появился загадочный незнакомец и сказал...',
      'В этот момент магическая сила рынка...',
      'Неожиданно все графики ожили и...',
      'А тем временем Mirai думала про...'
    ];
    
    return segments[Math.floor(Math.random() * segments.length)];
  };

  // Get project type icon
  const getProjectIcon = (type) => {
    const icons = {
      'drawing': '🎨',
      'story': '📚',
      'music': '🎵',
      'video': '🎬'
    };
    return icons[type] || '🎨';
  };

  // Get difficulty color
  const getDifficultyColor = (difficulty) => {
    const colors = {
      'easy': '#4CAF50',
      'medium': '#FF9800',
      'hard': '#F44336'
    };
    return colors[difficulty] || '#4CAF50';
  };

  // Get mood color
  const getMoodColor = (mood) => {
    const colors = {
      'HAPPY': '#FFD700',
      'EXCITED': '#FF6B9D',
      'CALM': '#87CEEB',
      'PLAYFUL': '#FF69B4',
      'CURIOUS': '#DDA0DD'
    };
    return colors[mood] || '#FFD700';
  };

  // Handle project creation
  const createNewProject = () => {
    const newProject = {
      id: Date.now(),
      type: creativeMode,
      title: `Новый ${creativeMode === 'draw' ? 'рисунок' : creativeMode === 'story' ? 'рассказ' : creativeMode === 'music' ? 'музыка' : 'видео'}`,
      description: 'Совместный проект в процессе создания...',
      collaborators: ['User', 'Mirai'],
      mood: currentState.mood,
      dateCreated: new Date().toISOString().split('T')[0],
      thumbnail: getProjectIcon(creativeMode),
      tags: ['новый', 'в процессе'],
      difficulty: 'medium',
      completionTime: 'В процессе...',
      miraiContribution: 'Идеи и вдохновение',
      userContribution: 'Воплощение и детали'
    };
    
    setActiveProject(newProject);
    setViewMode('create');
    
    if (onEmotionChange) {
      onEmotionChange('EXCITED');
    }

    addMemory('project_started', {
      type: creativeMode,
      mood: currentState.mood,
      collaboration: collaborationLevel
    });
  };

  return (
    <div className="creative-studio">
      {/* Header */}
      <div className="studio-header">
        <h1>🎨 Творческая Студия Mirai</h1>
        <div className="header-stats">
          <div className="collaboration-level">
            Совместность: {Math.round(relationship.friendship * 100)}%
          </div>
          <div className="current-mood" style={{ color: getMoodColor(currentState.mood) }}>
            Настроение: {currentState.mood}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="studio-nav">
        <button 
          className={`nav-btn ${viewMode === 'gallery' ? 'active' : ''}`}
          onClick={() => setViewMode('gallery')}
        >
          🖼️ Галерея
        </button>
        
        <button 
          className={`nav-btn ${viewMode === 'create' ? 'active' : ''}`}
          onClick={() => setViewMode('create')}
        >
          ✨ Создать
        </button>
        
        <button 
          className={`nav-btn ${viewMode === 'collaborate' ? 'active' : ''}`}
          onClick={() => setViewMode('collaborate')}
        >
          🤝 Коллаборация
        </button>
      </div>

      {/* Creative Mode Selector */}
      {(viewMode === 'create' || viewMode === 'collaborate') && (
        <div className="mode-selector">
          <button 
            className={`mode-btn ${creativeMode === 'draw' ? 'active' : ''}`}
            onClick={() => setCreativeMode('draw')}
          >
            🎨 Рисование
          </button>
          
          <button 
            className={`mode-btn ${creativeMode === 'write' ? 'active' : ''}`}
            onClick={() => setCreativeMode('write')}
          >
            ✍️ Написание
          </button>
          
          <button 
            className={`mode-btn ${creativeMode === 'music' ? 'active' : ''}`}
            onClick={() => setCreativeMode('music')}
          >
            🎵 Музыка
          </button>
          
          <button 
            className={`mode-btn ${creativeMode === 'video' ? 'active' : ''}`}
            onClick={() => setCreativeMode('video')}
          >
            🎬 Видео
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="studio-content">
        {viewMode === 'gallery' && (
          <div className="gallery-mode">
            <div className="gallery-header">
              <h3>🖼️ Наши Совместные Работы</h3>
              <button className="create-new-btn" onClick={createNewProject}>
                ➕ Создать новый проект
              </button>
            </div>
            
            <div className="projects-grid">
              {projects.map(project => (
                <div 
                  key={project.id}
                  className="project-card"
                  onClick={() => setActiveProject(project)}
                >
                  <div className="project-thumbnail">
                    <div className="project-icon">{project.thumbnail}</div>
                    <div 
                      className="project-mood-indicator"
                      style={{ backgroundColor: getMoodColor(project.mood) }}
                    ></div>
                  </div>
                  
                  <div className="project-info">
                    <h4>{project.title}</h4>
                    <p>{project.description}</p>
                    
                    <div className="project-meta">
                      <div className="project-type">{project.type}</div>
                      <div 
                        className="project-difficulty"
                        style={{ color: getDifficultyColor(project.difficulty) }}
                      >
                        {project.difficulty}
                      </div>
                      <div className="project-time">{project.completionTime}</div>
                    </div>
                    
                    <div className="project-tags">
                      {project.tags.map(tag => (
                        <span key={tag} className="tag">#{tag}</span>
                      ))}
                    </div>
                    
                    <div className="collaborators">
                      <div className="collaboration-detail">
                        <strong>Mirai:</strong> {project.miraiContribution}
                      </div>
                      <div className="collaboration-detail">
                        <strong>Ты:</strong> {project.userContribution}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {viewMode === 'create' && (
          <div className="create-mode">
            <div className="creation-header">
              <h3>✨ Создаем Вместе!</h3>
              <div className="mirai-mood">
                Mirai сейчас {currentState.mood.toLowerCase()} и готова к творчеству! 
                {currentState.mood === 'EXCITED' && ' (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧'}
                {currentState.mood === 'HAPPY' && ' (◡ ‿ ◡)'}
                {currentState.mood === 'CALM' && ' ˘_˘'}
                {currentState.mood === 'PLAYFUL' && ' ヽ(°〇°)ﾉ'}
              </div>
            </div>

            {creativeMode === 'draw' && (
              <div className="drawing-workspace">
                <div className="drawing-tools">
                  <div className="tool-group">
                    <label>Размер кисти:</label>
                    <input 
                      type="range" 
                      min="1" 
                      max="20" 
                      value={brushSize}
                      onChange={(e) => setBrushSize(e.target.value)}
                    />
                    <span>{brushSize}px</span>
                  </div>
                  
                  <div className="tool-group">
                    <label>Цвет:</label>
                    <input 
                      type="color" 
                      value={brushColor}
                      onChange={(e) => setBrushColor(e.target.value)}
                    />
                  </div>
                  
                  <button className="mirai-suggest-btn" onClick={addMiraiInput}>
                    💡 Совет от Mirai
                  </button>
                </div>
                
                <div className="canvas-container">
                  <canvas
                    ref={canvasRef}
                    width={600}
                    height={400}
                    onMouseDown={startDrawing}
                    onMouseMove={draw}
                    onMouseUp={stopDrawing}
                    onMouseLeave={stopDrawing}
                    className="drawing-canvas"
                  />
                </div>
                
                <div className="drawing-prompts">
                  <h4>💡 Идеи от Mirai:</h4>
                  <div className="prompts-list">
                    {getDrawingPrompts().map((prompt, index) => (
                      <div key={index} className="prompt-item">
                        {prompt}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {creativeMode === 'write' && (
              <div className="writing-workspace">
                <div className="story-prompt">
                  <h4>📖 Начало истории от Mirai:</h4>
                  <div className="prompt-text">{storyPrompt || getStoryPrompts()}</div>
                  <button onClick={() => setStoryPrompt(getStoryPrompts())}>
                    🔄 Новая идея
                  </button>
                </div>
                
                <div className="story-editor">
                  <textarea
                    value={currentStory}
                    onChange={(e) => setCurrentStory(e.target.value)}
                    placeholder="Продолжи историю... Mirai добавит свои идеи! ✨"
                    className="story-textarea"
                  />
                </div>
                
                <div className="story-actions">
                  <button onClick={() => setCurrentStory(currentStory + '\n\n' + generateStorySegment())}>
                    🤖 Добавить идею Mirai
                  </button>
                  <button>💾 Сохранить историю</button>
                </div>
              </div>
            )}

            {creativeMode === 'music' && (
              <div className="music-workspace">
                <div className="music-prompt">
                  <h4>🎵 Музыкальная идея от Mirai:</h4>
                  <div className="prompt-text">{getMusicPrompts()}</div>
                </div>
                
                <div className="virtual-keyboard">
                  <div className="keyboard-row">
                    {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].map(note => (
                      <button 
                        key={note}
                        className={`key ${note.includes('#') ? 'black' : 'white'}`}
                        onClick={() => console.log(`Play ${note}`)}
                      >
                        {note}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div className="music-controls">
                  <button>▶️ Воспроизвести</button>
                  <button>⏹️ Остановить</button>
                  <button>🔄 Очистить</button>
                  <button>💾 Сохранить мелодию</button>
                </div>
              </div>
            )}

            {creativeMode === 'video' && (
              <div className="video-workspace">
                <div className="video-storyboard">
                  <h4>🎬 Создаем сториборд:</h4>
                  <div className="storyboard-frames">
                    {[1, 2, 3, 4].map(frame => (
                      <div key={frame} className="storyboard-frame">
                        <div className="frame-number">Кадр {frame}</div>
                        <div className="frame-content">
                          <div className="frame-placeholder">
                            🎭 Добавить сцену
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="video-script">
                  <h4>📝 Сценарий:</h4>
                  <textarea 
                    placeholder="Опиши сцены видео... Mirai поможет с идеями!"
                    className="script-textarea"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {viewMode === 'collaborate' && (
          <div className="collaborate-mode">
            <div className="collaboration-settings">
              <h3>🤝 Настройки Совместной Работы</h3>
              
              <div className="setting-group">
                <label>Уровень участия Mirai:</label>
                <select 
                  value={collaborationLevel}
                  onChange={(e) => setCollaborationLevel(e.target.value)}
                  className="collaboration-select"
                >
                  <option value="guided">Направляющий (подсказки и советы)</option>
                  <option value="freestyle">Свободный (равное участие)</option>
                  <option value="ai-lead">AI-ведущий (Mirai главная)</option>
                </select>
              </div>
              
              <div className="setting-group">
                <label>Стиль творчества:</label>
                <select 
                  value={artStyle}
                  onChange={(e) => setArtStyle(e.target.value)}
                  className="style-select"
                >
                  <option value="anime">Аниме стиль</option>
                  <option value="kawaii">Кавай стиль</option>
                  <option value="minimalist">Минимализм</option>
                  <option value="cyberpunk">Киберпанк</option>
                  <option value="traditional">Традиционный</option>
                </select>
              </div>
            </div>
            
            <div className="collaboration-tips">
              <h4>💫 Советы для лучшей совместной работы:</h4>
              <div className="tips-list">
                <div className="tip-item">
                  🎨 <strong>Для рисования:</strong> Начни с грубых форм, Mirai поможет с деталями
                </div>
                <div className="tip-item">
                  ✍️ <strong>Для писательства:</strong> Пиши по очереди - абзац ты, абзац Mirai
                </div>
                <div className="tip-item">
                  🎵 <strong>Для музыки:</strong> Создавай основу, Mirai добавит гармонии
                </div>
                <div className="tip-item">
                  🎬 <strong>Для видео:</strong> Планируй вместе, воплощай поэтапно
                </div>
              </div>
            </div>
            
            <div className="collaboration-history">
              <h4>📊 История Совместных Проектов:</h4>
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-number">{projects.length}</div>
                  <div className="stat-label">Проектов создано</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{Math.round(relationship.friendship * 100)}%</div>
                  <div className="stat-label">Творческая синергия</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">
                    {projects.reduce((acc, p) => acc + (p.type === 'drawing' ? 1 : 0), 0)}
                  </div>
                  <div className="stat-label">Рисунков</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">
                    {projects.reduce((acc, p) => acc + (p.type === 'story' ? 1 : 0), 0)}
                  </div>
                  <div className="stat-label">Историй</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Active Project Modal */}
      {activeProject && (
        <div className="project-modal" onClick={() => setActiveProject(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{activeProject.title}</h3>
              <button 
                className="close-btn"
                onClick={() => setActiveProject(null)}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              <div className="project-details">
                <div className="detail-row">
                  <strong>Тип:</strong> {activeProject.type}
                </div>
                <div className="detail-row">
                  <strong>Настроение:</strong> 
                  <span style={{ color: getMoodColor(activeProject.mood) }}>
                    {activeProject.mood}
                  </span>
                </div>
                <div className="detail-row">
                  <strong>Сложность:</strong>
                  <span style={{ color: getDifficultyColor(activeProject.difficulty) }}>
                    {activeProject.difficulty}
                  </span>
                </div>
                <div className="detail-row">
                  <strong>Время создания:</strong> {activeProject.completionTime}
                </div>
                <div className="detail-row">
                  <strong>Дата:</strong> {activeProject.dateCreated}
                </div>
              </div>
              
              <div className="project-description">
                <h4>Описание:</h4>
                <p>{activeProject.description}</p>
              </div>
              
              <div className="project-contributions">
                <h4>Вклад участников:</h4>
                <div className="contribution-item">
                  <strong>🤖 Mirai:</strong> {activeProject.miraiContribution}
                </div>
                <div className="contribution-item">
                  <strong>👤 Ты:</strong> {activeProject.userContribution}
                </div>
              </div>
              
              <div className="project-tags-modal">
                <h4>Теги:</h4>
                {activeProject.tags.map(tag => (
                  <span key={tag} className="tag-modal">#{tag}</span>
                ))}
              </div>
            </div>
            
            <div className="modal-actions">
              <button className="continue-btn">✏️ Продолжить работу</button>
              <button className="share-btn">📤 Поделиться</button>
              <button className="duplicate-btn">📋 Создать похожий</button>
            </div>
          </div>
        </div>
      )}

      {/* Styles */}
      <style jsx>{`
        .creative-studio {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
          color: white;
        }

        .studio-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255,255,255,0.1);
          padding: 25px;
          border-radius: 15px;
          margin-bottom: 20px;
          backdrop-filter: blur(10px);
        }

        .studio-header h1 {
          margin: 0;
          font-size: 2.5em;
          background: linear-gradient(45deg, #ff6b9d, #ffd93d);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .header-stats {
          display: flex;
          flex-direction: column;
          gap: 8px;
          font-size: 14px;
        }

        .collaboration-level {
          background: rgba(255,107,157,0.3);
          padding: 5px 12px;
          border-radius: 10px;
        }

        .current-mood {
          font-weight: bold;
          text-align: right;
        }

        .studio-nav, .mode-selector {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }

        .nav-btn, .mode-btn {
          background: rgba(255,255,255,0.2);
          border: none;
          padding: 12px 24px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-weight: bold;
        }

        .nav-btn:hover, .mode-btn:hover,
        .nav-btn.active, .mode-btn.active {
          background: #ff6b9d;
          transform: translateY(-2px);
        }

        .studio-content {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 25px;
          backdrop-filter: blur(10px);
          min-height: 70vh;
        }

        .gallery-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 25px;
        }

        .gallery-header h3 {
          margin: 0;
          font-size: 1.5em;
        }

        .create-new-btn {
          background: #ffd93d;
          border: none;
          padding: 12px 20px;
          border-radius: 25px;
          color: #333;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.3s ease;
        }

        .create-new-btn:hover {
          background: #ffed4e;
          transform: scale(1.05);
        }

        .projects-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 20px;
        }

        .project-card {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .project-card:hover {
          background: rgba(255,255,255,0.2);
          transform: translateY(-5px);
          box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .project-thumbnail {
          position: relative;
          text-align: center;
          margin-bottom: 15px;
        }

        .project-icon {
          font-size: 3em;
          margin-bottom: 10px;
        }

        .project-mood-indicator {
          position: absolute;
          top: 0;
          right: 0;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          border: 2px solid white;
        }

        .project-info h4 {
          margin: 0 0 10px 0;
          font-size: 1.3em;
          color: #ffd93d;
        }

        .project-info p {
          margin: 0 0 15px 0;
          line-height: 1.4;
          opacity: 0.9;
        }

        .project-meta {
          display: flex;
          justify-content: space-between;
          margin-bottom: 15px;
          font-size: 12px;
        }

        .project-type {
          background: rgba(255,255,255,0.3);
          padding: 4px 8px;
          border-radius: 8px;
          text-transform: uppercase;
        }

        .project-difficulty {
          font-weight: bold;
          text-transform: capitalize;
        }

        .project-time {
          opacity: 0.7;
        }

        .project-tags {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 15px;
        }

        .tag {
          background: rgba(255,107,157,0.3);
          padding: 4px 8px;
          border-radius: 12px;
          font-size: 11px;
        }

        .collaborators {
          border-top: 1px solid rgba(255,255,255,0.2);
          padding-top: 15px;
        }

        .collaboration-detail {
          font-size: 12px;
          margin-bottom: 5px;
          opacity: 0.8;
        }

        .creation-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .creation-header h3 {
          margin: 0 0 15px 0;
          font-size: 2em;
          color: #ffd93d;
        }

        .mirai-mood {
          font-size: 1.1em;
          opacity: 0.9;
        }

        .drawing-workspace {
          display: grid;
          grid-template-columns: 1fr 2fr 1fr;
          gap: 25px;
          align-items: start;
        }

        .drawing-tools {
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 10px;
        }

        .tool-group {
          margin-bottom: 20px;
        }

        .tool-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: bold;
        }

        .tool-group input {
          width: 100%;
          margin-bottom: 5px;
        }

        .mirai-suggest-btn {
          background: #ffd93d;
          border: none;
          padding: 10px 15px;
          border-radius: 20px;
          color: #333;
          cursor: pointer;
          font-weight: bold;
          width: 100%;
        }

        .canvas-container {
          text-align: center;
        }

        .drawing-canvas {
          border: 3px solid #ff6b9d;
          border-radius: 10px;
          background: white;
          cursor: crosshair;
        }

        .drawing-prompts {
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 10px;
        }

        .drawing-prompts h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .prompt-item {
          background: rgba(255,107,157,0.2);
          padding: 10px;
          border-radius: 8px;
          margin-bottom: 10px;
          font-size: 14px;
        }

        .writing-workspace {
          max-width: 800px;
          margin: 0 auto;
        }

        .story-prompt {
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 10px;
          margin-bottom: 20px;
          text-align: center;
        }

        .story-prompt h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .prompt-text {
          font-style: italic;
          font-size: 1.1em;
          margin-bottom: 15px;
          padding: 15px;
          background: rgba(255,107,157,0.2);
          border-radius: 8px;
        }

        .story-textarea {
          width: 100%;
          min-height: 300px;
          background: rgba(255,255,255,0.9);
          border: none;
          border-radius: 10px;
          padding: 20px;
          font-size: 16px;
          color: #333;
          resize: vertical;
          outline: none;
        }

        .story-actions {
          display: flex;
          gap: 15px;
          margin-top: 20px;
          justify-content: center;
        }

        .story-actions button {
          background: #ff6b9d;
          border: none;
          padding: 12px 20px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.3s ease;
        }

        .story-actions button:hover {
          background: #ff8fb3;
          transform: scale(1.05);
        }

        .music-workspace {
          text-align: center;
        }

        .music-prompt {
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 10px;
          margin-bottom: 30px;
        }

        .music-prompt h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .virtual-keyboard {
          background: rgba(255,255,255,0.1);
          padding: 30px;
          border-radius: 15px;
          margin-bottom: 30px;
        }

        .keyboard-row {
          display: flex;
          justify-content: center;
          gap: 5px;
        }

        .key {
          width: 50px;
          height: 100px;
          border: none;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.1s ease;
        }

        .key.white {
          background: white;
          color: #333;
          border-radius: 0 0 8px 8px;
        }

        .key.black {
          background: #333;
          color: white;
          height: 60px;
          width: 30px;
          margin: 0 -15px;
          z-index: 1;
          position: relative;
          border-radius: 0 0 4px 4px;
        }

        .key:hover {
          transform: translateY(2px);
        }

        .key:active {
          transform: translateY(4px);
        }

        .music-controls {
          display: flex;
          gap: 15px;
          justify-content: center;
        }

        .music-controls button {
          background: #ff6b9d;
          border: none;
          padding: 12px 20px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.3s ease;
        }

        .music-controls button:hover {
          background: #ff8fb3;
          transform: scale(1.05);
        }

        .video-workspace {
          max-width: 900px;
          margin: 0 auto;
        }

        .video-storyboard {
          margin-bottom: 30px;
        }

        .video-storyboard h4 {
          margin: 0 0 20px 0;
          color: #ffd93d;
          text-align: center;
        }

        .storyboard-frames {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .storyboard-frame {
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
          padding: 15px;
          text-align: center;
        }

        .frame-number {
          font-weight: bold;
          margin-bottom: 10px;
          color: #ffd93d;
        }

        .frame-content {
          background: rgba(255,255,255,0.05);
          height: 120px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .frame-placeholder {
          opacity: 0.7;
          font-size: 14px;
        }

        .video-script h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .script-textarea {
          width: 100%;
          min-height: 200px;
          background: rgba(255,255,255,0.9);
          border: none;
          border-radius: 10px;
          padding: 20px;
          font-size: 16px;
          color: #333;
          resize: vertical;
          outline: none;
        }

        .collaboration-settings {
          background: rgba(255,255,255,0.1);
          padding: 25px;
          border-radius: 15px;
          margin-bottom: 25px;
        }

        .collaboration-settings h3 {
          margin: 0 0 20px 0;
          color: #ffd93d;
        }

        .setting-group {
          margin-bottom: 20px;
        }

        .setting-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: bold;
        }

        .collaboration-select, .style-select {
          width: 100%;
          padding: 10px;
          border: none;
          border-radius: 8px;
          background: rgba(255,255,255,0.9);
          color: #333;
          outline: none;
        }

        .collaboration-tips {
          background: rgba(255,255,255,0.1);
          padding: 25px;
          border-radius: 15px;
          margin-bottom: 25px;
        }

        .collaboration-tips h4 {
          margin: 0 0 20px 0;
          color: #ffd93d;
        }

        .tip-item {
          background: rgba(255,107,157,0.2);
          padding: 15px;
          border-radius: 10px;
          margin-bottom: 10px;
          line-height: 1.4;
        }

        .collaboration-history {
          background: rgba(255,255,255,0.1);
          padding: 25px;
          border-radius: 15px;
        }

        .collaboration-history h4 {
          margin: 0 0 20px 0;
          color: #ffd93d;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
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
          color: #ffd93d;
          margin-bottom: 5px;
        }

        .stat-label {
          font-size: 12px;
          opacity: 0.8;
          text-transform: uppercase;
        }

        .project-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 20px;
        }

        .modal-content {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 20px;
          max-width: 600px;
          width: 100%;
          max-height: 80vh;
          overflow-y: auto;
          color: white;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 25px;
          border-bottom: 1px solid rgba(255,255,255,0.2);
        }

        .modal-header h3 {
          margin: 0;
          font-size: 1.8em;
          color: #ffd93d;
        }

        .close-btn {
          background: none;
          border: none;
          color: white;
          font-size: 1.5em;
          cursor: pointer;
          padding: 5px;
          border-radius: 50%;
          width: 35px;
          height: 35px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .close-btn:hover {
          background: rgba(255,255,255,0.2);
        }

        .modal-body {
          padding: 25px;
        }

        .project-details {
          margin-bottom: 20px;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 10px;
          padding: 8px 0;
          border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .project-description {
          margin-bottom: 20px;
        }

        .project-description h4 {
          margin: 0 0 10px 0;
          color: #ffd93d;
        }

        .project-contributions {
          margin-bottom: 20px;
        }

        .project-contributions h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .contribution-item {
          background: rgba(255,255,255,0.1);
          padding: 10px;
          border-radius: 8px;
          margin-bottom: 8px;
        }

        .project-tags-modal h4 {
          margin: 0 0 15px 0;
          color: #ffd93d;
        }

        .tag-modal {
          background: rgba(255,107,157,0.3);
          padding: 6px 12px;
          border-radius: 15px;
          font-size: 12px;
          margin-right: 8px;
          margin-bottom: 8px;
          display: inline-block;
        }

        .modal-actions {
          display: flex;
          gap: 15px;
          padding: 25px;
          border-top: 1px solid rgba(255,255,255,0.2);
          justify-content: center;
        }

        .modal-actions button {
          background: #ff6b9d;
          border: none;
          padding: 12px 20px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          font-weight: bold;
          transition: all 0.3s ease;
        }

        .modal-actions button:hover {
          background: #ff8fb3;
          transform: scale(1.05);
        }

        @media (max-width: 768px) {
          .studio-header {
            flex-direction: column;
            gap: 15px;
            text-align: center;
          }
          
          .studio-nav, .mode-selector {
            flex-wrap: wrap;
            justify-content: center;
          }
          
          .projects-grid {
            grid-template-columns: 1fr;
          }
          
          .drawing-workspace {
            grid-template-columns: 1fr;
            gap: 20px;
          }
          
          .drawing-canvas {
            width: 100%;
            max-width: 400px;
            height: 250px;
          }
          
          .keyboard-row {
            flex-wrap: wrap;
          }
          
          .key {
            width: 40px;
            height: 80px;
          }
          
          .key.black {
            width: 25px;
            height: 50px;
          }
          
          .storyboard-frames {
            grid-template-columns: repeat(2, 1fr);
          }
          
          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }
          
          .modal-content {
            margin: 20px;
            max-height: 90vh;
          }
          
          .modal-actions {
            flex-wrap: wrap;
          }
        }
      `}</style>
    </div>
  );
}