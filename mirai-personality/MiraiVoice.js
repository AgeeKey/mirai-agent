import { useState, useEffect, useRef } from 'react';

// Voice synthesis system for Mirai
class MiraiVoiceSystem {
  constructor() {
    this.ttsEnabled = true;
    this.sttEnabled = true;
    this.currentVoice = null;
    this.speechRate = 0.9;
    this.speechPitch = 1.1; // Slightly higher pitch for anime character
    this.speechVolume = 0.8;
    
    // Voice characteristics for different emotions
    this.emotionVoiceSettings = {
      'HAPPY': { rate: 1.0, pitch: 1.2, volume: 0.9 },
      'EXCITED': { rate: 1.2, pitch: 1.3, volume: 1.0 },
      'CURIOUS': { rate: 0.9, pitch: 1.1, volume: 0.8 },
      'CALM': { rate: 0.7, pitch: 1.0, volume: 0.7 },
      'PLAYFUL': { rate: 1.1, pitch: 1.25, volume: 0.9 },
      'THOUGHTFUL': { rate: 0.8, pitch: 0.95, volume: 0.7 },
      'AFFECTIONATE': { rate: 0.85, pitch: 1.05, volume: 0.8 }
    };
    
    this.initializeVoices();
    this.initializeSpeechRecognition();
  }

  async initializeVoices() {
    if (!('speechSynthesis' in window)) {
      console.warn('Speech synthesis not supported');
      this.ttsEnabled = false;
      return;
    }

    // Wait for voices to load
    const loadVoices = () => {
      const voices = speechSynthesis.getVoices();
      
      // Prefer female voices, especially with Japanese or anime-like characteristics
      const preferredVoices = [
        'Google русский', // Russian female
        'Microsoft Irina - Russian (Russia)',
        'Google UK English Female',
        'Microsoft Zira - English (United States)',
        'Google 日本語', // Japanese
        'Microsoft Haruka - Japanese (Japan)'
      ];

      for (const preferredName of preferredVoices) {
        const voice = voices.find(v => v.name.includes(preferredName));
        if (voice) {
          this.currentVoice = voice;
          break;
        }
      }

      // Fallback to any female voice
      if (!this.currentVoice) {
        this.currentVoice = voices.find(v => 
          v.name.toLowerCase().includes('female') || 
          v.name.toLowerCase().includes('woman') ||
          v.name.toLowerCase().includes('zira') ||
          v.name.toLowerCase().includes('irina')
        ) || voices[0];
      }
    };

    loadVoices();
    speechSynthesis.addEventListener('voiceschanged', loadVoices);
  }

  initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn('Speech recognition not supported');
      this.sttEnabled = false;
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.recognition.continuous = true;
    this.recognition.interimResults = true;
    this.recognition.lang = 'ru-RU'; // Primary language
    this.recognition.maxAlternatives = 3;
  }

  // Text-to-Speech with emotion
  speak(text, emotion = 'HAPPY', onStart = null, onEnd = null) {
    if (!this.ttsEnabled || !text.trim()) return;

    // Cancel any ongoing speech
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance();
    
    // Process text for better pronunciation
    utterance.text = this.preprocessText(text);
    utterance.voice = this.currentVoice;
    
    // Apply emotion-based voice settings
    const emotionSettings = this.emotionVoiceSettings[emotion] || this.emotionVoiceSettings['HAPPY'];
    utterance.rate = emotionSettings.rate * this.speechRate;
    utterance.pitch = emotionSettings.pitch * this.speechPitch;
    utterance.volume = emotionSettings.volume * this.speechVolume;

    // Add slight randomization for more natural speech
    utterance.rate += (Math.random() - 0.5) * 0.1;
    utterance.pitch += (Math.random() - 0.5) * 0.1;

    // Event handlers
    utterance.onstart = () => {
      if (onStart) onStart();
    };

    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error);
      if (onEnd) onEnd();
    };

    speechSynthesis.speak(utterance);
    return utterance;
  }

  // Preprocess text for better TTS pronunciation
  preprocessText(text) {
    let processed = text;

    // Handle emoji and special characters
    processed = processed.replace(/[♡♪✨⭐]/g, ''); // Remove decorative characters
    processed = processed.replace(/\(.*?\)/g, ''); // Remove text in parentheses (emoticons)
    processed = processed.replace(/[（）]/g, ''); // Remove Japanese parentheses
    
    // Japanese phrase pronunciation hints
    const japaneseMap = {
      'сугой': 'су-гой',
      'кавай': 'ка-вай', 
      'арига': 'а-ри-га',
      'гомен': 'го-мен',
      'охайо': 'о-хай-о',
      'коннитива': 'кон-ни-ти-ва',
      'ня': 'ня-я'
    };

    Object.entries(japaneseMap).forEach(([japanese, pronunciation]) => {
      const regex = new RegExp(japanese, 'gi');
      processed = processed.replace(regex, pronunciation);
    });

    // Add pauses for better delivery
    processed = processed.replace(/[.!?]/g, '$&... ');
    processed = processed.replace(/,/g, ', ');

    return processed;
  }

  // Start listening for speech input
  startListening(onResult = null, onError = null, onEnd = null) {
    if (!this.sttEnabled) return false;

    try {
      this.recognition.onresult = (event) => {
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

        if (onResult) {
          onResult({
            final: finalTranscript,
            interim: interimTranscript,
            confidence: event.results[event.results.length - 1][0].confidence
          });
        }
      };

      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (onError) onError(event.error);
      };

      this.recognition.onend = () => {
        if (onEnd) onEnd();
      };

      this.recognition.start();
      return true;
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      return false;
    }
  }

  // Stop listening
  stopListening() {
    if (this.recognition) {
      this.recognition.stop();
    }
  }

  // Stop speaking
  stopSpeaking() {
    speechSynthesis.cancel();
  }

  // Change language
  setLanguage(language) {
    if (this.recognition) {
      this.recognition.lang = language;
    }
  }

  // Get available voices
  getAvailableVoices() {
    return speechSynthesis.getVoices();
  }

  // Set specific voice
  setVoice(voiceName) {
    const voices = this.getAvailableVoices();
    const voice = voices.find(v => v.name === voiceName);
    if (voice) {
      this.currentVoice = voice;
      return true;
    }
    return false;
  }
}

// React hook for voice functionality
export function useMiraiVoice() {
  const [voiceSystem] = useState(() => new MiraiVoiceSystem());
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);

  // Speak text with emotion
  const speak = (text, emotion = 'HAPPY') => {
    return voiceSystem.speak(
      text, 
      emotion,
      () => setIsSpeaking(true),
      () => setIsSpeaking(false)
    );
  };

  // Start voice recognition
  const startListening = () => {
    const success = voiceSystem.startListening(
      (result) => {
        setTranscript(result.final || result.interim);
        setConfidence(result.confidence || 0);
      },
      (error) => {
        console.error('Voice recognition error:', error);
        setIsListening(false);
      },
      () => {
        setIsListening(false);
      }
    );
    
    if (success) {
      setIsListening(true);
      setTranscript('');
    }
    
    return success;
  };

  // Stop voice recognition
  const stopListening = () => {
    voiceSystem.stopListening();
    setIsListening(false);
  };

  // Stop speaking
  const stopSpeaking = () => {
    voiceSystem.stopSpeaking();
    setIsSpeaking(false);
  };

  return {
    speak,
    startListening,
    stopListening,
    stopSpeaking,
    isListening,
    isSpeaking,
    transcript,
    confidence,
    voiceSystem
  };
}

// Voice command processor
export class VoiceCommandProcessor {
  constructor() {
    this.commands = new Map();
    this.setupDefaultCommands();
  }

  setupDefaultCommands() {
    // Navigation commands
    this.addCommand(['привет', 'hello', 'хай'], () => ({ action: 'greet' }));
    this.addCommand(['чат', 'поговорим', 'talk', 'chat'], () => ({ action: 'open_chat' }));
    this.addCommand(['музыка', 'music', 'песня'], () => ({ action: 'open_music' }));
    this.addCommand(['игра', 'играть', 'game', 'play'], () => ({ action: 'open_games' }));
    this.addCommand(['дневник', 'diary'], () => ({ action: 'open_diary' }));
    this.addCommand(['помощь', 'help'], () => ({ action: 'show_help' }));
    
    // Emotion commands
    this.addCommand(['улыбнись', 'smile'], () => ({ action: 'emotion', emotion: 'HAPPY' }));
    this.addCommand(['успокойся', 'calm'], () => ({ action: 'emotion', emotion: 'CALM' }));
    this.addCommand(['радость', 'excited'], () => ({ action: 'emotion', emotion: 'EXCITED' }));
    
    // Trading commands
    this.addCommand(['рынок', 'market', 'торговля'], () => ({ action: 'open_trading' }));
    this.addCommand(['анализ', 'analysis'], () => ({ action: 'market_analysis' }));
    this.addCommand(['портфель', 'portfolio'], () => ({ action: 'show_portfolio' }));
    
    // Control commands
    this.addCommand(['стоп', 'stop', 'замолчи'], () => ({ action: 'stop_speaking' }));
    this.addCommand(['повтори', 'repeat'], () => ({ action: 'repeat' }));
    this.addCommand(['громче', 'louder'], () => ({ action: 'volume_up' }));
    this.addCommand(['тише', 'quieter'], () => ({ action: 'volume_down' }));
  }

  addCommand(triggers, action) {
    triggers.forEach(trigger => {
      this.commands.set(trigger.toLowerCase(), action);
    });
  }

  processCommand(text) {
    const normalizedText = text.toLowerCase().trim();
    
    // Check for exact matches first
    if (this.commands.has(normalizedText)) {
      return this.commands.get(normalizedText)();
    }

    // Check for partial matches
    for (const [trigger, action] of this.commands.entries()) {
      if (normalizedText.includes(trigger)) {
        return action();
      }
    }

    // No command found, treat as conversation
    return { action: 'conversation', text: text };
  }
}

// Audio effects for Mirai's voice
export class VoiceEffects {
  constructor() {
    this.audioContext = null;
    this.initializeAudioContext();
  }

  async initializeAudioContext() {
    try {
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    } catch (error) {
      console.warn('Web Audio API not supported:', error);
    }
  }

  // Add reverb effect for certain emotions
  addReverb(audioBuffer, intensity = 0.3) {
    if (!this.audioContext) return audioBuffer;

    const convolver = this.audioContext.createConvolver();
    const impulseBuffer = this.createReverbImpulse(intensity);
    convolver.buffer = impulseBuffer;

    return convolver;
  }

  createReverbImpulse(intensity) {
    const length = this.audioContext.sampleRate * 2; // 2 seconds
    const impulse = this.audioContext.createBuffer(2, length, this.audioContext.sampleRate);
    
    for (let channel = 0; channel < 2; channel++) {
      const channelData = impulse.getChannelData(channel);
      for (let i = 0; i < length; i++) {
        channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, 2) * intensity;
      }
    }
    
    return impulse;
  }

  // Add pitch modulation for emotional expression
  modulatePitch(frequency, emotion) {
    const modulations = {
      'HAPPY': frequency * 1.1,
      'EXCITED': frequency * 1.2,
      'SAD': frequency * 0.9,
      'CALM': frequency * 0.95,
      'PLAYFUL': frequency * (1 + Math.sin(Date.now() * 0.01) * 0.1)
    };

    return modulations[emotion] || frequency;
  }
}

export default MiraiVoiceSystem;