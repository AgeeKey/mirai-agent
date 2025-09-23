'use client'

import React, { useState, useEffect } from 'react'
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react'

interface VoiceWidgetProps {
  onVoiceInput?: (text: string) => void
  onVoiceResponse?: (text: string) => void
}

export function VoiceWidget({ onVoiceInput, onVoiceResponse }: VoiceWidgetProps) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [recognition, setRecognition] = useState<any>(null)
  const [speechSynthesis, setSpeechSynthesis] = useState<any>(null)

  useEffect(() => {
    // Инициализация Web Speech API
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
      const speechSynth = window.speechSynthesis

      if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition()
        recognitionInstance.continuous = false
        recognitionInstance.interimResults = true
        recognitionInstance.lang = 'ru-RU'

        recognitionInstance.onstart = () => {
          setIsListening(true)
        }

        recognitionInstance.onresult = (event: any) => {
          const results = Array.from(event.results)
          const transcript = results
            .map((result: any) => result[0])
            .map((result: any) => result.transcript)
            .join('')

          setTranscript(transcript)
          
          if (event.results[0]?.isFinal) {
            setIsListening(false)
            onVoiceInput?.(transcript)
          }
        }

        recognitionInstance.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error)
          setIsListening(false)
        }

        recognitionInstance.onend = () => {
          setIsListening(false)
        }

        setRecognition(recognitionInstance)
      }

      if (speechSynth) {
        setSpeechSynthesis(speechSynth)
      }
    }
  }, [onVoiceInput])

  const startListening = () => {
    if (recognition && !isListening) {
      recognition.start()
    }
  }

  const stopListening = () => {
    if (recognition && isListening) {
      recognition.stop()
    }
  }

  const speak = (text: string) => {
    if (speechSynthesis && !isSpeaking) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'ru-RU'
      utterance.rate = 1
      utterance.pitch = 1
      utterance.volume = 1

      utterance.onstart = () => setIsSpeaking(true)
      utterance.onend = () => setIsSpeaking(false)
      utterance.onerror = () => setIsSpeaking(false)

      speechSynthesis.speak(utterance)
      onVoiceResponse?.(text)
    }
  }

  const stopSpeaking = () => {
    if (speechSynthesis && isSpeaking) {
      speechSynthesis.cancel()
      setIsSpeaking(false)
    }
  }

  const handleTestVoice = () => {
    const testMessage = "Привет! Я Мирай, твоя цифровая сестра. Система голосового взаимодействия активна!"
    speak(testMessage)
  }

  return (
    <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4">🎤 Голосовое взаимодействие</h3>
      
      {/* Voice Controls */}
      <div className="flex items-center space-x-4 mb-4">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`p-3 rounded-full transition-all duration-200 ${
            isListening 
              ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
          disabled={isSpeaking}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        <button
          onClick={isSpeaking ? stopSpeaking : handleTestVoice}
          className={`p-3 rounded-full transition-all duration-200 ${
            isSpeaking 
              ? 'bg-orange-500 hover:bg-orange-600 text-white animate-pulse' 
              : 'bg-green-500 hover:bg-green-600 text-white'
          }`}
          disabled={isListening}
        >
          {isSpeaking ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
        </button>

        <div className="flex-1">
          <div className="text-sm text-gray-400">
            {isListening && '🔴 Слушаю...'}
            {isSpeaking && '🔊 Говорю...'}
            {!isListening && !isSpeaking && '⏸️ Готов к работе'}
          </div>
        </div>
      </div>

      {/* Transcript Display */}
      {transcript && (
        <div className="bg-gray-800 rounded-lg p-3 mb-4">
          <p className="text-sm text-gray-300 mb-1">Распознанный текст:</p>
          <p className="text-white">{transcript}</p>
        </div>
      )}

      {/* Voice Status */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="text-center">
          <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
            isListening ? 'bg-red-400 animate-pulse' : 'bg-gray-600'
          }`}></div>
          <span className="text-gray-400">Распознавание</span>
        </div>
        <div className="text-center">
          <div className={`w-3 h-3 rounded-full mx-auto mb-2 ${
            isSpeaking ? 'bg-green-400 animate-pulse' : 'bg-gray-600'
          }`}></div>
          <span className="text-gray-400">Синтез речи</span>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-4 text-xs text-gray-500">
        <p>🎤 Нажмите микрофон для записи голоса</p>
        <p>🔊 Нажмите динамик для тестового воспроизведения</p>
      </div>
    </div>
  )
}

