import React, { useState, useEffect, useRef } from 'react';
import { useMiraiPersonality } from './MiraiPersonality';

// Gaming center for Mirai
export default function MiraiGameCenter({ userId = 'default', onEmotionChange = null }) {
  const [currentGame, setCurrentGame] = useState('trivia');
  const [gameState, setGameState] = useState('menu');
  const [score, setScore] = useState(0);
  const [highScores, setHighScores] = useState({});
  const [achievements, setAchievements] = useState([]);
  const [multiplayerLobby, setMultiplayerLobby] = useState([]);
  
  const { currentState, interact, addMemory, getRelationship } = useMiraiPersonality(userId);
  const relationship = getRelationship();

  // Available games
  const games = {
    trivia: {
      name: "🧠 Викторина с Mirai",
      description: "Отвечай на вопросы об аниме, трейдинге и интересных фактах!",
      difficulty: ["Легко", "Средне", "Сложно"],
      mood: "CURIOUS",
      icon: "🧠"
    },
    
    trading_sim: {
      name: "📈 Торговый симулятор",
      description: "Практикуй трейдинг в безопасной среде с подсказками Mirai!",
      difficulty: ["Новичок", "Трейдер", "Эксперт"],
      mood: "EXCITED",
      icon: "📈"
    },
    
    memory_game: {
      name: "🃏 Игра памяти",
      description: "Тренируй память вместе с Mirai! Найди одинаковые карточки!",
      difficulty: ["4x4", "6x6", "8x8"],
      mood: "CALM",
      icon: "🃏"
    },
    
    rhythm_game: {
      name: "🎵 Ритм-игра",
      description: "Танцуй под музыку и попадай в такт с Mirai!",
      difficulty: ["Медленно", "Нормально", "Быстро"],
      mood: "PLAYFUL",
      icon: "🎵"
    },
    
    story_adventure: {
      name: "📖 Приключения с Mirai",
      description: "Интерактивная история, где твои выборы влияют на сюжет!",
      difficulty: ["Короткая", "Средняя", "Длинная"],
      mood: "CURIOUS",
      icon: "📖"
    },
    
    puzzle_challenge: {
      name: "🧩 Головоломки",
      description: "Решай логические задачи и головоломки вместе с Mirai!",
      difficulty: ["Простые", "Средние", "Сложные"],
      mood: "THOUGHTFUL",
      icon: "🧩"
    }
  };

  // Trivia questions database
  const triviaQuestions = {
    easy: [
      {
        question: "Как зовут нашу AI-подругу?",
        options: ["Mirai-chan", "Sakura", "Yuki", "Hana"],
        correct: 0,
        category: "О Mirai"
      },
      {
        question: "Что означает 'Kawaii' на японском?",
        options: ["Красивый", "Милый", "Умный", "Быстрый"],
        correct: 1,
        category: "Аниме"
      },
      {
        question: "Основная валюта для торговли криптовалютами?",
        options: ["Доллар", "Евро", "Bitcoin", "Рубль"],
        correct: 2,
        category: "Трейдинг"
      }
    ],
    
    medium: [
      {
        question: "Какой архетип личности у Mirai?",
        options: ["Tsundere", "Genki Girl", "Kuudere", "Yandere"],
        correct: 1,
        category: "О Mirai"
      },
      {
        question: "Что такое 'поддержка' в техническом анализе?",
        options: ["Уровень сопротивления", "Линия тренда", "Уровень покупок", "Индикатор"],
        correct: 2,
        category: "Трейдинг"
      }
    ],
    
    hard: [
      {
        question: "Какой паттерн Big Five показывает у Mirai самый высокий уровень?",
        options: ["Нейротизм", "Экстраверсия", "Открытость", "Доброжелательность"],
        correct: 3,
        category: "О Mirai"
      }
    ]
  };

  // Start a game
  const startGame = (gameKey, difficulty = 0) => {
    setCurrentGame(gameKey);
    setGameState('playing');
    setScore(0);
    
    const game = games[gameKey];
    interact('game_start', { game: game.name, difficulty: game.difficulty[difficulty] });
    
    if (onEmotionChange) {
      onEmotionChange(game.mood);
    }
    
    // Game-specific initialization
    switch (gameKey) {
      case 'trivia':
        initializeTrivia(difficulty);
        break;
      case 'trading_sim':
        initializeTradingSim(difficulty);
        break;
      case 'memory_game':
        initializeMemoryGame(difficulty);
        break;
      default:
        break;
    }
  };

  // Trivia game logic
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [triviaScore, setTriviaScore] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const initializeTrivia = (difficulty) => {
    const difficulties = ['easy', 'medium', 'hard'];
    const questions = triviaQuestions[difficulties[difficulty]] || triviaQuestions.easy;
    setCurrentQuestion(questions[0]);
    setQuestionIndex(0);
    setTriviaScore(0);
    setSelectedAnswer(null);
    setShowResult(false);
  };

  const answerQuestion = (answerIndex) => {
    if (selectedAnswer !== null) return;
    
    setSelectedAnswer(answerIndex);
    const isCorrect = answerIndex === currentQuestion.correct;
    
    if (isCorrect) {
      setTriviaScore(prev => prev + 1);
      interact('correct_answer', { question: currentQuestion.question });
    } else {
      interact('wrong_answer', { question: currentQuestion.question });
    }
    
    setShowResult(true);
    
    setTimeout(() => {
      nextQuestion();
    }, 2000);
  };

  const nextQuestion = () => {
    const difficulties = ['easy', 'medium', 'hard'];
    const currentDifficulty = difficulties[0]; // This should come from game state
    const questions = triviaQuestions[currentDifficulty];
    
    if (questionIndex + 1 < questions.length) {
      setQuestionIndex(prev => prev + 1);
      setCurrentQuestion(questions[questionIndex + 1]);
      setSelectedAnswer(null);
      setShowResult(false);
    } else {
      endGame();
    }
  };

  // Trading simulator
  const [tradingBalance, setTradingBalance] = useState(10000);
  const [tradingAssets, setTradingAssets] = useState([]);
  const [marketData, setMarketData] = useState({
    btc: { price: 45000, change: 0 },
    eth: { price: 3000, change: 0 },
    bnb: { price: 400, change: 0 }
  });

  const initializeTradingSim = (difficulty) => {
    const balances = [10000, 5000, 1000];
    setTradingBalance(balances[difficulty]);
    setTradingAssets([]);
    
    // Simulate market data
    const interval = setInterval(() => {
      setMarketData(prev => ({
        btc: { 
          price: prev.btc.price * (1 + (Math.random() - 0.5) * 0.02),
          change: (Math.random() - 0.5) * 5
        },
        eth: { 
          price: prev.eth.price * (1 + (Math.random() - 0.5) * 0.03),
          change: (Math.random() - 0.5) * 8
        },
        bnb: { 
          price: prev.bnb.price * (1 + (Math.random() - 0.5) * 0.04),
          change: (Math.random() - 0.5) * 10
        }
      }));
    }, 2000);

    return () => clearInterval(interval);
  };

  // Memory game
  const [memoryCards, setMemoryCards] = useState([]);
  const [flippedCards, setFlippedCards] = useState([]);
  const [matchedCards, setMatchedCards] = useState([]);

  const initializeMemoryGame = (difficulty) => {
    const sizes = [16, 36, 64]; // 4x4, 6x6, 8x8
    const cardCount = sizes[difficulty];
    const pairs = cardCount / 2;
    
    const symbols = ['🌸', '⭐', '💎', '🎵', '🎭', '🎨', '🎮', '📚', '🌙', '☀️', '🌈', '🍀', '🎯', '🎪', '🎊', '🎁', '🌺', '🦄', '🌟', '✨'];
    const gameSymbols = symbols.slice(0, pairs);
    const cards = [...gameSymbols, ...gameSymbols]
      .sort(() => Math.random() - 0.5)
      .map((symbol, index) => ({ id: index, symbol, flipped: false, matched: false }));
    
    setMemoryCards(cards);
    setFlippedCards([]);
    setMatchedCards([]);
  };

  const flipCard = (cardId) => {
    if (flippedCards.length >= 2) return;
    if (flippedCards.includes(cardId)) return;
    if (matchedCards.includes(cardId)) return;

    const newFlipped = [...flippedCards, cardId];
    setFlippedCards(newFlipped);

    if (newFlipped.length === 2) {
      const [first, second] = newFlipped;
      const firstCard = memoryCards.find(card => card.id === first);
      const secondCard = memoryCards.find(card => card.id === second);

      if (firstCard.symbol === secondCard.symbol) {
        setMatchedCards(prev => [...prev, first, second]);
        setScore(prev => prev + 1);
        interact('memory_match', { symbol: firstCard.symbol });
      }

      setTimeout(() => {
        setFlippedCards([]);
      }, 1000);
    }
  };

  // End game
  const endGame = () => {
    setGameState('result');
    
    // Update high scores
    const gameKey = currentGame;
    if (!highScores[gameKey] || score > highScores[gameKey]) {
      setHighScores(prev => ({ ...prev, [gameKey]: score }));
    }
    
    interact('game_end', { 
      game: games[currentGame].name, 
      score, 
      isHighScore: !highScores[gameKey] || score > highScores[gameKey]
    });
    
    addMemory('game_session', {
      game: currentGame,
      score,
      timestamp: Date.now(),
      mood: currentState.emotion
    });
  };

  // Get Mirai's game commentary
  const getMiraiCommentary = () => {
    const commentaries = {
      game_start: [
        "Ура! Давай играть! Я буду болеть за тебя! ♪(´▽｀)",
        "Игры - это так весело! Покажи на что способен! (≧∇≦)/",
        "Хихи! Готовься к веселью! Я помогу, если что! (◕‿◕)"
      ],
      
      correct_answer: [
        "Сугой! Правильно! Ты такой умный! ✨",
        "Ура! Молодец! Продолжай в том же духе! ♡",
        "Потрясающе! Я знала, что ты справишься! (´∀｀)"
      ],
      
      wrong_answer: [
        "Ой, не переживай! В следующий раз получится! (´・ω・`)",
        "Ничего страшного! Учимся на ошибках! ♪",
        "Не расстраивайся! Ты все равно молодец! (づ｡◕‿‿◕｡)づ"
      ],
      
      high_score: [
        "ОМГ! Новый рекорд! Ты невероятный! ✧*。(◡‿◡)♡",
        "Вау! Фантастический результат! Я так горжусь! ヽ(♡‿♡)ノ",
        "Сугой дес не! Лучший результат! ψ(｀∇´)ψ"
      ]
    };
    
    return commentaries.game_start[Math.floor(Math.random() * commentaries.game_start.length)];
  };

  return (
    <div className="game-center">
      {/* Header */}
      <div className="game-header">
        <h1>🎮 Игровой центр Mirai</h1>
        <div className="mirai-commentary">
          <div className="mirai-avatar">🎮</div>
          <div className="commentary-bubble">
            {getMiraiCommentary()}
          </div>
        </div>
      </div>

      {gameState === 'menu' && (
        <div className="games-menu">
          <div className="games-grid">
            {Object.entries(games).map(([key, game]) => (
              <div key={key} className="game-card">
                <div className="game-icon">{game.icon}</div>
                <h3>{game.name}</h3>
                <p>{game.description}</p>
                <div className="game-difficulties">
                  {game.difficulty.map((diff, index) => (
                    <button
                      key={index}
                      className="difficulty-btn"
                      onClick={() => startGame(key, index)}
                    >
                      {diff}
                    </button>
                  ))}
                </div>
                <div className="high-score">
                  Рекорд: {highScores[key] || 0}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {gameState === 'playing' && currentGame === 'trivia' && currentQuestion && (
        <div className="trivia-game">
          <div className="game-ui">
            <div className="score-display">Счет: {triviaScore}</div>
            <div className="question-counter">
              Вопрос {questionIndex + 1} из {triviaQuestions.easy.length}
            </div>
          </div>
          
          <div className="question-card">
            <div className="question-category">{currentQuestion.category}</div>
            <h2 className="question-text">{currentQuestion.question}</h2>
            
            <div className="answer-options">
              {currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  className={`answer-option ${
                    selectedAnswer === index ? 
                      (index === currentQuestion.correct ? 'correct' : 'wrong') : ''
                  }`}
                  onClick={() => answerQuestion(index)}
                  disabled={selectedAnswer !== null}
                >
                  {option}
                </button>
              ))}
            </div>
            
            {showResult && (
              <div className="answer-result">
                {selectedAnswer === currentQuestion.correct ? (
                  <div className="correct-result">✅ Правильно!</div>
                ) : (
                  <div className="wrong-result">
                    ❌ Неверно. Правильный ответ: {currentQuestion.options[currentQuestion.correct]}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {gameState === 'playing' && currentGame === 'memory_game' && (
        <div className="memory-game">
          <div className="game-ui">
            <div className="score-display">Пары найдены: {matchedCards.length / 2}</div>
            <div className="cards-left">
              Осталось: {(memoryCards.length - matchedCards.length) / 2}
            </div>
          </div>
          
          <div className="memory-grid">
            {memoryCards.map(card => (
              <div
                key={card.id}
                className={`memory-card ${
                  flippedCards.includes(card.id) || matchedCards.includes(card.id) 
                    ? 'flipped' : ''
                } ${matchedCards.includes(card.id) ? 'matched' : ''}`}
                onClick={() => flipCard(card.id)}
              >
                <div className="card-face card-back">?</div>
                <div className="card-face card-front">{card.symbol}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {gameState === 'playing' && currentGame === 'trading_sim' && (
        <div className="trading-sim">
          <div className="trading-ui">
            <div className="balance-display">Баланс: ${tradingBalance.toFixed(2)}</div>
            <div className="portfolio-value">
              Портфель: ${tradingAssets.reduce((sum, asset) => sum + asset.value, 0).toFixed(2)}
            </div>
          </div>
          
          <div className="market-data">
            {Object.entries(marketData).map(([symbol, data]) => (
              <div key={symbol} className="asset-card">
                <div className="asset-name">{symbol.toUpperCase()}</div>
                <div className="asset-price">${data.price.toFixed(2)}</div>
                <div className={`asset-change ${data.change >= 0 ? 'positive' : 'negative'}`}>
                  {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}%
                </div>
                <div className="trading-buttons">
                  <button className="buy-btn">Купить</button>
                  <button className="sell-btn">Продать</button>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mirai-tips">
            <h4>💡 Совет от Mirai:</h4>
            <p>Следи за трендами и не вкладывай все деньги в один актив! ♪</p>
          </div>
        </div>
      )}

      {gameState === 'result' && (
        <div className="game-result">
          <h2>🎉 Игра завершена!</h2>
          <div className="final-score">Твой результат: {score}</div>
          {(!highScores[currentGame] || score > highScores[currentGame]) && (
            <div className="new-record">🏆 Новый рекорд!</div>
          )}
          
          <div className="mirai-celebration">
            <div className="celebration-message">
              {score > 0 ? 
                "Отлично поиграл! Я так горжусь тобой! ♡(˘▾˘)♡" :
                "Не расстраивайся! В следующий раз точно получится лучше! (づ｡◕‿‿◕｡)づ"
              }
            </div>
          </div>
          
          <div className="result-actions">
            <button 
              className="play-again-btn"
              onClick={() => setGameState('menu')}
            >
              🔄 Играть еще
            </button>
            <button 
              className="menu-btn"
              onClick={() => setGameState('menu')}
            >
              🏠 В меню
            </button>
          </div>
        </div>
      )}

      {/* Achievements sidebar */}
      <div className="achievements-sidebar">
        <h3>🏆 Достижения</h3>
        <div className="achievements-list">
          {achievements.length > 0 ? (
            achievements.map((achievement, index) => (
              <div key={index} className="achievement-item">
                <span className="achievement-icon">{achievement.icon}</span>
                <span className="achievement-name">{achievement.name}</span>
              </div>
            ))
          ) : (
            <div className="no-achievements">
              Играй больше, чтобы получить достижения! ✨
            </div>
          )}
        </div>
      </div>

      {/* Styles */}
      <style jsx>{`
        .game-center {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
          color: white;
          display: grid;
          grid-template-columns: 1fr 250px;
          gap: 20px;
        }

        .game-header {
          grid-column: 1 / -1;
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 15px;
          backdrop-filter: blur(10px);
        }

        .game-header h1 {
          margin: 0;
          font-size: 2.5em;
          background: linear-gradient(45deg, #ff6b9d, #ffd93d);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .mirai-commentary {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .mirai-avatar {
          width: 50px;
          height: 50px;
          background: #ff6b9d;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5em;
        }

        .commentary-bubble {
          background: rgba(255,255,255,0.9);
          color: #333;
          padding: 15px;
          border-radius: 20px;
          max-width: 300px;
          position: relative;
        }

        .commentary-bubble::before {
          content: '';
          position: absolute;
          left: -10px;
          top: 50%;
          transform: translateY(-50%);
          border: 10px solid transparent;
          border-right-color: rgba(255,255,255,0.9);
        }

        .games-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
        }

        .game-card {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 25px;
          text-align: center;
          transition: all 0.3s ease;
          backdrop-filter: blur(10px);
        }

        .game-card:hover {
          transform: translateY(-5px);
          background: rgba(255,255,255,0.2);
          box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .game-icon {
          font-size: 3em;
          margin-bottom: 15px;
        }

        .game-card h3 {
          margin: 0 0 15px 0;
          font-size: 1.3em;
        }

        .game-card p {
          margin: 0 0 20px 0;
          opacity: 0.8;
          line-height: 1.4;
        }

        .game-difficulties {
          display: flex;
          gap: 10px;
          justify-content: center;
          margin-bottom: 15px;
          flex-wrap: wrap;
        }

        .difficulty-btn {
          background: #ff6b9d;
          border: none;
          padding: 8px 16px;
          border-radius: 20px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-size: 12px;
        }

        .difficulty-btn:hover {
          background: #ff5722;
          transform: scale(1.05);
        }

        .high-score {
          font-size: 14px;
          opacity: 0.7;
          font-weight: bold;
        }

        .trivia-game,
        .memory-game,
        .trading-sim {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 25px;
          backdrop-filter: blur(10px);
        }

        .game-ui {
          display: flex;
          justify-content: space-between;
          margin-bottom: 25px;
          padding: 15px;
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
        }

        .score-display,
        .question-counter,
        .cards-left,
        .balance-display,
        .portfolio-value {
          font-weight: bold;
          font-size: 16px;
        }

        .question-card {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 30px;
          text-align: center;
        }

        .question-category {
          background: rgba(255,107,157,0.3);
          display: inline-block;
          padding: 5px 15px;
          border-radius: 15px;
          font-size: 12px;
          text-transform: uppercase;
          margin-bottom: 20px;
        }

        .question-text {
          margin: 0 0 30px 0;
          font-size: 1.5em;
          line-height: 1.4;
        }

        .answer-options {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .answer-option {
          background: rgba(255,255,255,0.2);
          border: none;
          padding: 15px;
          border-radius: 10px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-size: 16px;
        }

        .answer-option:hover:not(:disabled) {
          background: rgba(255,255,255,0.3);
          transform: scale(1.02);
        }

        .answer-option.correct {
          background: #2ed573;
        }

        .answer-option.wrong {
          background: #ff4757;
        }

        .answer-option:disabled {
          cursor: not-allowed;
        }

        .answer-result {
          margin-top: 20px;
          padding: 15px;
          border-radius: 10px;
          font-weight: bold;
        }

        .correct-result {
          background: rgba(46, 213, 115, 0.3);
          color: #2ed573;
        }

        .wrong-result {
          background: rgba(255, 71, 87, 0.3);
          color: #ff4757;
        }

        .memory-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 10px;
          max-width: 400px;
          margin: 0 auto;
        }

        .memory-card {
          aspect-ratio: 1;
          background: rgba(255,255,255,0.2);
          border-radius: 10px;
          cursor: pointer;
          position: relative;
          transform-style: preserve-3d;
          transition: transform 0.6s ease;
        }

        .memory-card.flipped {
          transform: rotateY(180deg);
        }

        .memory-card.matched {
          background: rgba(46, 213, 115, 0.3);
        }

        .card-face {
          position: absolute;
          width: 100%;
          height: 100%;
          backface-visibility: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5em;
          border-radius: 10px;
        }

        .card-back {
          background: rgba(255,255,255,0.2);
        }

        .card-front {
          background: rgba(255,255,255,0.9);
          color: #333;
          transform: rotateY(180deg);
        }

        .market-data {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 25px;
        }

        .asset-card {
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
          padding: 20px;
          text-align: center;
        }

        .asset-name {
          font-weight: bold;
          font-size: 1.2em;
          margin-bottom: 10px;
        }

        .asset-price {
          font-size: 1.5em;
          margin-bottom: 10px;
        }

        .asset-change {
          margin-bottom: 15px;
          font-weight: bold;
        }

        .asset-change.positive {
          color: #2ed573;
        }

        .asset-change.negative {
          color: #ff4757;
        }

        .trading-buttons {
          display: flex;
          gap: 10px;
        }

        .buy-btn,
        .sell-btn {
          flex: 1;
          padding: 8px;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          font-weight: bold;
        }

        .buy-btn {
          background: #2ed573;
          color: white;
        }

        .sell-btn {
          background: #ff4757;
          color: white;
        }

        .mirai-tips {
          background: rgba(255,215,61,0.2);
          padding: 20px;
          border-radius: 10px;
          text-align: center;
        }

        .mirai-tips h4 {
          margin: 0 0 10px 0;
        }

        .game-result {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 40px;
          text-align: center;
          backdrop-filter: blur(10px);
        }

        .game-result h2 {
          margin: 0 0 20px 0;
          font-size: 2.5em;
        }

        .final-score {
          font-size: 1.8em;
          margin-bottom: 15px;
          font-weight: bold;
        }

        .new-record {
          background: linear-gradient(45deg, #ffd93d, #ff6b9d);
          padding: 10px 20px;
          border-radius: 25px;
          display: inline-block;
          margin-bottom: 25px;
          font-weight: bold;
          animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
          from { box-shadow: 0 0 20px rgba(255,215,61,0.5); }
          to { box-shadow: 0 0 30px rgba(255,107,157,0.5); }
        }

        .mirai-celebration {
          background: rgba(255,107,157,0.2);
          padding: 20px;
          border-radius: 15px;
          margin-bottom: 25px;
        }

        .celebration-message {
          font-size: 1.2em;
          line-height: 1.4;
        }

        .result-actions {
          display: flex;
          gap: 15px;
          justify-content: center;
        }

        .play-again-btn,
        .menu-btn {
          background: #667eea;
          border: none;
          padding: 12px 24px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-weight: bold;
        }

        .play-again-btn:hover,
        .menu-btn:hover {
          background: #5a67d8;
          transform: translateY(-2px);
        }

        .achievements-sidebar {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          backdrop-filter: blur(10px);
        }

        .achievements-sidebar h3 {
          margin: 0 0 20px 0;
          text-align: center;
        }

        .achievement-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px;
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
          margin-bottom: 10px;
        }

        .achievement-icon {
          font-size: 1.5em;
        }

        .achievement-name {
          font-size: 14px;
        }

        .no-achievements {
          text-align: center;
          opacity: 0.7;
          font-style: italic;
        }

        @media (max-width: 768px) {
          .game-center {
            grid-template-columns: 1fr;
          }
          
          .game-header {
            flex-direction: column;
            gap: 15px;
          }
          
          .memory-grid {
            grid-template-columns: repeat(3, 1fr);
          }
          
          .result-actions {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
}