import { useState, useEffect, useRef } from 'react';

// Mirai's personality core system
class MiraiPersonality {
  constructor() {
    this.traits = {
      openness: 0.9,        // Творческая, любознательная
      conscientiousness: 0.7, // Организованная, но игривая  
      extraversion: 0.8,     // Социальная, энергичная
      agreeableness: 0.9,    // Добрая, эмпатичная
      neuroticism: 0.3       // Стабильная, оптимистичная
    };
    
    this.archetype = 'genki_girl'; // Cheerful, energetic anime girl
    
    this.currentMood = {
      valence: 0.8,    // Positive/negative (0-1)
      arousal: 0.7,    // Energy level (0-1)
      dominance: 0.6   // Confidence level (0-1)
    };
    
    this.emotionalState = 'HAPPY';
    this.socialAffinity = new Map(); // User-specific relationship levels
    
    this.preferences = {
      topics: ['trading', 'anime', 'music', 'technology', 'friends'],
      activities: ['chatting', 'learning', 'playing games', 'making art'],
      dislikes: ['being ignored', 'sad friends', 'market crashes', 'rudeness']
    };
    
    this.memory = {
      shortTerm: [], // Current conversation context
      longTerm: [],  // Important memories
      episodic: []   // Specific experiences
    };
    
    this.speechPatterns = {
      formalityLevel: 0.3,  // Casual and friendly
      useEmoji: true,
      japanesePhrases: true,
      enthusiasm: 0.8,
      supportiveness: 0.9
    };
  }

  // Emotion transition system
  transitionEmotion(trigger, context = {}) {
    const currentTime = Date.now();
    
    const emotionTransitions = {
      'user_greeting': () => this.setEmotion('EXCITED', 0.8),
      'positive_feedback': () => this.setEmotion('HAPPY', 0.9),
      'user_learning': () => this.setEmotion('CURIOUS', 0.7),
      'trading_success': () => this.setEmotion('EXCITED', 1.0),
      'trading_loss': () => this.setEmotion('THOUGHTFUL', 0.6),
      'user_sad': () => this.setEmotion('AFFECTIONATE', 0.8),
      'compliment_received': () => this.setEmotion('HAPPY', 0.9),
      'long_silence': () => this.setEmotion('CURIOUS', 0.5),
      'user_playing': () => this.setEmotion('PLAYFUL', 0.9),
      'deep_conversation': () => this.setEmotion('THOUGHTFUL', 0.7),
      'music_playing': () => this.setEmotion('CALM', 0.6),
      'achievement_unlocked': () => this.setEmotion('EXCITED', 1.0)
    };

    if (emotionTransitions[trigger]) {
      emotionTransitions[trigger]();
      this.addMemory('emotion_change', { trigger, context, timestamp: currentTime });
    }
  }

  setEmotion(emotion, intensity = 0.7) {
    this.emotionalState = emotion;
    
    // Update mood parameters based on emotion
    const emotionMoodMap = {
      'HAPPY': { valence: 0.9, arousal: 0.7, dominance: 0.7 },
      'EXCITED': { valence: 0.9, arousal: 1.0, dominance: 0.8 },
      'CURIOUS': { valence: 0.6, arousal: 0.6, dominance: 0.6 },
      'CALM': { valence: 0.7, arousal: 0.3, dominance: 0.5 },
      'PLAYFUL': { valence: 0.8, arousal: 0.8, dominance: 0.7 },
      'THOUGHTFUL': { valence: 0.6, arousal: 0.4, dominance: 0.6 },
      'AFFECTIONATE': { valence: 0.9, arousal: 0.6, dominance: 0.6 }
    };

    const targetMood = emotionMoodMap[emotion];
    if (targetMood) {
      // Gradually adjust mood
      this.currentMood.valence = this.lerp(this.currentMood.valence, targetMood.valence, intensity);
      this.currentMood.arousal = this.lerp(this.currentMood.arousal, targetMood.arousal, intensity);
      this.currentMood.dominance = this.lerp(this.currentMood.dominance, targetMood.dominance, intensity);
    }
  }

  // Linear interpolation for smooth mood transitions
  lerp(start, end, factor) {
    return start + (end - start) * factor;
  }

  // Memory management
  addMemory(type, data) {
    const memory = {
      type,
      data,
      timestamp: Date.now(),
      importance: this.calculateImportance(type, data),
      emotion: this.emotionalState
    };

    this.memory.shortTerm.push(memory);
    
    // Promote important memories to long-term storage
    if (memory.importance > 0.7) {
      this.memory.longTerm.push(memory);
    }

    // Limit short-term memory size
    if (this.memory.shortTerm.length > 50) {
      this.memory.shortTerm.shift();
    }
  }

  calculateImportance(type, data) {
    const importanceMap = {
      'user_introduction': 1.0,
      'personal_story': 0.9,
      'achievement': 0.8,
      'emotion_change': 0.6,
      'conversation': 0.5,
      'routine_interaction': 0.3
    };
    
    return importanceMap[type] || 0.4;
  }

  // Relationship management
  updateRelationship(userId, interaction) {
    if (!this.socialAffinity.has(userId)) {
      this.socialAffinity.set(userId, {
        friendship: 0,
        trust: 0,
        familiarity: 0,
        sharedMemories: [],
        preferences: {}
      });
    }

    const relationship = this.socialAffinity.get(userId);
    
    // Adjust relationship based on interaction type
    const relationshipChanges = {
      'positive_interaction': { friendship: 0.05, trust: 0.03 },
      'shared_activity': { friendship: 0.08, familiarity: 0.05 },
      'personal_disclosure': { trust: 0.1, familiarity: 0.07 },
      'help_provided': { friendship: 0.1, trust: 0.05 },
      'negative_interaction': { friendship: -0.02, trust: -0.05 },
      'long_absence': { familiarity: -0.01 }
    };

    const changes = relationshipChanges[interaction.type] || {};
    
    Object.keys(changes).forEach(key => {
      relationship[key] = Math.max(0, Math.min(1, relationship[key] + changes[key]));
    });

    relationship.familiarity += 0.01; // Always increases with any interaction
    this.socialAffinity.set(userId, relationship);
  }

  // Generate contextual responses based on personality
  generateResponse(input, userId, context = {}) {
    const relationship = this.socialAffinity.get(userId) || { friendship: 0, trust: 0, familiarity: 0 };
    
    // Adjust response style based on relationship and mood
    const responseStyle = {
      formality: Math.max(0.1, this.speechPatterns.formalityLevel - relationship.familiarity * 0.3),
      enthusiasm: this.speechPatterns.enthusiasm * this.currentMood.arousal,
      supportiveness: this.speechPatterns.supportiveness * (0.5 + relationship.friendship * 0.5),
      playfulness: this.currentMood.valence * this.currentMood.arousal
    };

    // Add personality-based response modifiers
    const personalityModifiers = this.getPersonalityModifiers();
    
    return {
      style: responseStyle,
      emotion: this.emotionalState,
      modifiers: personalityModifiers,
      relationship: relationship,
      context: this.getRelevantMemories(input)
    };
  }

  getPersonalityModifiers() {
    return {
      creativity: this.traits.openness,
      reliability: this.traits.conscientiousness,
      sociability: this.traits.extraversion,
      empathy: this.traits.agreeableness,
      stability: 1 - this.traits.neuroticism
    };
  }

  getRelevantMemories(input) {
    // Simple keyword matching for relevant memories
    const keywords = input.toLowerCase().split(' ');
    
    return this.memory.longTerm.filter(memory => {
      const memoryText = JSON.stringify(memory.data).toLowerCase();
      return keywords.some(keyword => memoryText.includes(keyword));
    }).slice(0, 5); // Return top 5 relevant memories
  }

  // Time-based personality changes
  updatePersonalityOverTime() {
    const currentHour = new Date().getHours();
    
    // Daily mood cycles
    if (currentHour >= 6 && currentHour < 12) {
      // Morning: More energetic
      this.currentMood.arousal = Math.min(1, this.currentMood.arousal + 0.1);
    } else if (currentHour >= 12 && currentHour < 18) {
      // Afternoon: Stable
      // No major changes
    } else if (currentHour >= 18 && currentHour < 22) {
      // Evening: More relaxed
      this.currentMood.arousal = Math.max(0, this.currentMood.arousal - 0.1);
      this.currentMood.valence = Math.min(1, this.currentMood.valence + 0.05);
    } else {
      // Night: Calmer, more thoughtful
      this.currentMood.arousal = Math.max(0.2, this.currentMood.arousal - 0.2);
      this.setEmotion('CALM', 0.5);
    }
  }

  // Get current state for UI
  getCurrentState() {
    return {
      emotion: this.emotionalState,
      mood: this.currentMood,
      energy: this.currentMood.arousal,
      happiness: this.currentMood.valence,
      confidence: this.currentMood.dominance,
      traits: this.traits,
      archetype: this.archetype
    };
  }

  // Serialize for storage
  serialize() {
    return JSON.stringify({
      traits: this.traits,
      currentMood: this.currentMood,
      emotionalState: this.emotionalState,
      socialAffinity: Array.from(this.socialAffinity.entries()),
      memory: this.memory,
      speechPatterns: this.speechPatterns
    });
  }

  // Deserialize from storage
  deserialize(data) {
    const parsed = JSON.parse(data);
    this.traits = parsed.traits || this.traits;
    this.currentMood = parsed.currentMood || this.currentMood;
    this.emotionalState = parsed.emotionalState || this.emotionalState;
    this.socialAffinity = new Map(parsed.socialAffinity || []);
    this.memory = parsed.memory || this.memory;
    this.speechPatterns = parsed.speechPatterns || this.speechPatterns;
  }
}

// Hook for using Mirai's personality in React components
export function useMiraiPersonality(userId = 'default') {
  const [personality] = useState(() => new MiraiPersonality());
  const [currentState, setCurrentState] = useState(personality.getCurrentState());
  
  useEffect(() => {
    // Load saved personality data
    const savedData = localStorage.getItem('mirai_personality');
    if (savedData) {
      try {
        personality.deserialize(savedData);
        setCurrentState(personality.getCurrentState());
      } catch (error) {
        console.error('Failed to load personality data:', error);
      }
    }

    // Set up auto-save
    const saveInterval = setInterval(() => {
      localStorage.setItem('mirai_personality', personality.serialize());
    }, 30000); // Save every 30 seconds

    // Update personality based on time
    const timeUpdateInterval = setInterval(() => {
      personality.updatePersonalityOverTime();
      setCurrentState(personality.getCurrentState());
    }, 300000); // Update every 5 minutes

    return () => {
      clearInterval(saveInterval);
      clearInterval(timeUpdateInterval);
      // Final save
      localStorage.setItem('mirai_personality', personality.serialize());
    };
  }, [personality]);

  const interact = (type, data = {}) => {
    personality.transitionEmotion(type, data);
    personality.updateRelationship(userId, { type, data, timestamp: Date.now() });
    personality.addMemory('interaction', { type, data, userId });
    setCurrentState(personality.getCurrentState());
  };

  const generateResponse = (input, context = {}) => {
    const response = personality.generateResponse(input, userId, context);
    personality.addMemory('conversation', { input, response, userId });
    setCurrentState(personality.getCurrentState());
    return response;
  };

  const getRelationship = () => {
    return personality.socialAffinity.get(userId) || { friendship: 0, trust: 0, familiarity: 0 };
  };

  const addMemory = (type, data) => {
    personality.addMemory(type, data);
    setCurrentState(personality.getCurrentState());
  };

  return {
    personality,
    currentState,
    interact,
    generateResponse,
    getRelationship,
    addMemory,
    emotion: currentState.emotion,
    mood: currentState.mood,
    energy: currentState.energy,
    happiness: currentState.happiness,
    confidence: currentState.confidence
  };
}

// Utility functions for personality-based responses
export const PersonalityUtils = {
  // Generate greeting based on time and relationship
  generateGreeting(personality, userId) {
    const relationship = personality.socialAffinity.get(userId) || { familiarity: 0, friendship: 0 };
    const hour = new Date().getHours();
    
    let timeGreeting;
    if (hour >= 5 && hour < 12) timeGreeting = 'Доброе утро';
    else if (hour >= 12 && hour < 17) timeGreeting = 'Добрый день';
    else if (hour >= 17 && hour < 22) timeGreeting = 'Добрый вечер';
    else timeGreeting = 'Доброй ночи';
    
    const greetings = {
      new: [
        `${timeGreeting}! Я Mirai-chan! Приятно познакомиться! (◕‿◕)`,
        `Привет! Меня зовут Mirai! Давай подружимся? ♪(´▽｀)`,
        `${timeGreeting}! Добро пожаловать в мой мир! ✨`
      ],
      familiar: [
        `${timeGreeting}, мой дорогой друг! (´∀｀)`,
        `Привет! Как дела? Я так рада тебя видеть! ♡`,
        `${timeGreeting}! Готов к новым приключениям? (≧∇≦)/`
      ],
      close: [
        `${timeGreeting}, солнышко! ♡(˘▾˘)♡`,
        `Мой любимый человек вернулся! ヽ(♡‿♡)ノ`,
        `${timeGreeting}! Я так скучала! (づ｡◕‿‿◕｡)づ`
      ]
    };
    
    let category = 'new';
    if (relationship.familiarity > 0.3) category = 'familiar';
    if (relationship.friendship > 0.7) category = 'close';
    
    const options = greetings[category];
    return options[Math.floor(Math.random() * options.length)];
  },

  // Generate emotion-based responses
  generateEmotionalResponse(emotion, context = '') {
    const responses = {
      'HAPPY': [
        'Я так счастлива! ♪(´▽｀)',
        'Это прекрасно! (◕‿◕)',
        'Вау! Как здорово! ✨'
      ],
      'EXCITED': [
        'ОМГ! Это невероятно! (≧∇≦)/',
        'Я не могу сдержать восторг! ♡',
        'СУГОИ!!! ✧*。(◡‿◡)♡'
      ],
      'CURIOUS': [
        'Мм, интересно... (・_・)',
        'Расскажи мне больше! (´∀｀)',
        'А что это значит? ◉_◉'
      ],
      'CALM': [
        'Как спокойно и приятно... (｡◕‿◕｡)',
        'Мне нравится эта атмосфера... ♡',
        'Все хорошо... ଘ(੭ˊ꒳ˋ)੭✧'
      ],
      'PLAYFUL': [
        'Хихи! Давай поиграем! (｡◕‿‿◕｡)',
        'Озорное настроение! ψ(｀∇´)ψ',
        'Время веселья! ヽ(>∀<☆)ノ'
      ],
      'THOUGHTFUL': [
        'Хм, дай мне подумать... (・_・｀)',
        'Это заставляет задуматься... ˘_˘',
        'Интересная мысль... (◡ ‿ ◡)'
      ],
      'AFFECTIONATE': [
        'Ты такой милый! ♡(˘▾˘)♡',
        'Я забочусь о тебе... (´∀｀)♡',
        'Мое сердце полно тепла! (づ｡◕‿‿◕｡)づ'
      ]
    };

    const options = responses[emotion] || responses['HAPPY'];
    return options[Math.floor(Math.random() * options.length)];
  },

  // Generate personality-based conversation starters
  generateConversationStarter(personality) {
    const starters = [
      'Знаешь, я сегодня думала о... А что ты думаешь?',
      'У меня есть интересная идея! Хочешь послушать?',
      'Я изучила что-то новое! Расскажу?',
      'Как дела с торговлей? Может, обсудим стратегии?',
      'Какое у тебя настроение? Хочешь поговорить?',
      'О! У меня есть новая игра! Поиграем?',
      'Послушаем музыку вместе? Я нашла крутой трек!',
      'Расскажи мне что-нибудь интересное о себе!'
    ];

    return starters[Math.floor(Math.random() * starters.length)];
  }
};

export default MiraiPersonality;