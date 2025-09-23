import React, { useState, useEffect, useRef } from 'react';
import { useMiraiPersonality } from './MiraiPersonality';

// Music Studio component for Mirai
export default function MiraiMusicStudio({ userId = 'default', onEmotionChange = null }) {
  const [currentTrack, setCurrentTrack] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentPlaylist, setCurrentPlaylist] = useState('mirai_favorites');
  const [volume, setVolume] = useState(0.7);
  const [showKaraoke, setShowKaraoke] = useState(false);
  const [showCreator, setShowCreator] = useState(false);
  const [listeningTogether, setListeningTogether] = useState([]);
  
  const audioRef = useRef(null);
  const { currentState, interact, addMemory } = useMiraiPersonality(userId);

  // Mirai's curated playlists
  const playlists = {
    mirai_favorites: {
      name: "💕 Любимые треки Mirai",
      description: "Мои самые любимые песни для хорошего настроения!",
      mood: "HAPPY",
      tracks: [
        {
          id: 1,
          title: "Lo-fi Dreams",
          artist: "Mirai's Collection",
          duration: "3:24",
          url: "/music/lofi-dreams.mp3",
          mood: "CALM",
          anime: false
        },
        {
          id: 2,
          title: "Trading Victory",
          artist: "Motivational Beats",
          duration: "2:45",
          url: "/music/trading-victory.mp3",
          mood: "EXCITED",
          anime: false
        },
        {
          id: 3,
          title: "Anime Opening Medley",
          artist: "Various Artists",
          duration: "4:12",
          url: "/music/anime-medley.mp3",
          mood: "EXCITED",
          anime: true
        }
      ]
    },
    
    study_session: {
      name: "📚 Для учебы с Mirai",
      description: "Спокойная музыка для изучения трейдинга и концентрации",
      mood: "CALM",
      tracks: [
        {
          id: 4,
          title: "Focus Flow",
          artist: "Study Beats",
          duration: "5:30",
          url: "/music/focus-flow.mp3",
          mood: "CALM"
        },
        {
          id: 5,
          title: "Market Analysis",
          artist: "Chill Instrumentals",
          duration: "4:45",
          url: "/music/market-analysis.mp3",
          mood: "THOUGHTFUL"
        }
      ]
    },
    
    anime_vibes: {
      name: "🌸 Аниме Vibes",
      description: "Лучшие треки из любимых аниме!",
      mood: "EXCITED",
      tracks: [
        {
          id: 6,
          title: "Kawaii Desu Ne",
          artist: "Anime OST",
          duration: "3:33",
          url: "/music/kawaii-desu.mp3",
          mood: "PLAYFUL",
          anime: true
        },
        {
          id: 7,
          title: "Friendship Power",
          artist: "J-Pop Mix",
          duration: "4:18",
          url: "/music/friendship-power.mp3",
          mood: "HAPPY",
          anime: true
        }
      ]
    },
    
    chill_together: {
      name: "🌙 Расслабляемся вместе",
      description: "Для спокойных вечеров и размышлений",
      mood: "CALM",
      tracks: [
        {
          id: 8,
          title: "Moonlight Serenade",
          artist: "Night Ambient",
          duration: "6:20",
          url: "/music/moonlight-serenade.mp3",
          mood: "CALM"
        },
        {
          id: 9,
          title: "Gentle Rain",
          artist: "Nature Sounds",
          duration: "8:00",
          url: "/music/gentle-rain.mp3",
          mood: "CALM"
        }
      ]
    }
  };

  // Initialize with Mirai's favorite playlist
  useEffect(() => {
    setCurrentTrack(playlists[currentPlaylist].tracks[0]);
    interact('music_activity', { playlist: currentPlaylist });
  }, []);

  // Handle track selection
  const selectTrack = (track) => {
    setCurrentTrack(track);
    setIsPlaying(false);
    
    // Mirai reacts to music choice
    interact('music_selection', { track: track.title, mood: track.mood });
    addMemory('music_preference', { track, timestamp: Date.now() });
    
    if (onEmotionChange && track.mood) {
      onEmotionChange(track.mood);
    }
  };

  // Play/pause functionality
  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
        interact('music_paused');
      } else {
        audioRef.current.play();
        interact('music_playing', { track: currentTrack?.title });
      }
      setIsPlaying(!isPlaying);
    }
  };

  // Handle playlist change
  const switchPlaylist = (playlistKey) => {
    setCurrentPlaylist(playlistKey);
    setCurrentTrack(playlists[playlistKey].tracks[0]);
    setIsPlaying(false);
    
    const playlist = playlists[playlistKey];
    interact('playlist_change', { playlist: playlist.name, mood: playlist.mood });
    
    if (onEmotionChange) {
      onEmotionChange(playlist.mood);
    }
  };

  // Mirai's music recommendations based on mood
  const getMiraiRecommendation = () => {
    const recommendations = {
      'HAPPY': "Давай послушаем что-то веселое! Попробуй мои любимые треки! ♪(´▽｀)",
      'EXCITED': "Сугой! Энергичная музыка для бодрого настроения! ヽ(>∀<☆)ノ",
      'CALM': "Хм, может что-то спокойное для расслабления? (｡◕‿◕｡)",
      'CURIOUS': "А что если попробуем что-то новое? Я нашла интересные треки! ◉_◉",
      'THOUGHTFUL': "Музыка для размышлений... идеально для анализа рынка ˘_˘",
      'PLAYFUL': "Хихи! Давай что-то игривое и милое! (｡◕‿‿◕｡)",
      'AFFECTIONATE': "Что-то теплое и душевное для нашей дружбы... ♡(˘▾˘)♡"
    };
    
    return recommendations[currentState.emotion] || recommendations['HAPPY'];
  };

  // Generate AI music (placeholder for future implementation)
  const generateAIMusic = async (prompt) => {
    // This would integrate with AI music generation APIs like Stable Audio
    console.log('Generating AI music with prompt:', prompt);
    interact('ai_music_creation', { prompt });
    
    return {
      id: Date.now(),
      title: `AI Generated: ${prompt}`,
      artist: "Mirai & AI",
      duration: "3:00",
      url: "/music/ai-generated.mp3",
      mood: currentState.emotion,
      isAIGenerated: true
    };
  };

  return (
    <div className="music-studio">
      {/* Studio Header */}
      <div className="studio-header">
        <div className="studio-title">
          <h1>🎵 Музыкальная студия Mirai</h1>
          <p>Давай создадим прекрасную атмосферу вместе! ♪</p>
        </div>
        
        <div className="mirai-recommendation">
          <div className="mirai-avatar-small">🎧</div>
          <div className="recommendation-bubble">
            {getMiraiRecommendation()}
          </div>
        </div>
      </div>

      {/* Main Player */}
      <div className="main-player">
        {currentTrack && (
          <>
            <div className="track-artwork">
              <div className="artwork-container">
                <div className={`vinyl-record ${isPlaying ? 'spinning' : ''}`}>
                  <div className="vinyl-center"></div>
                </div>
                {currentTrack.anime && (
                  <div className="anime-badge">🌸 Anime</div>
                )}
              </div>
            </div>
            
            <div className="track-info">
              <h2>{currentTrack.title}</h2>
              <p>{currentTrack.artist}</p>
              <div className="track-mood">Настроение: {currentTrack.mood}</div>
            </div>
            
            <div className="player-controls">
              <button className="control-btn" onClick={() => {/* Previous track */}}>
                ⏮️
              </button>
              
              <button 
                className="play-pause-btn"
                onClick={togglePlayback}
              >
                {isPlaying ? '⏸️' : '▶️'}
              </button>
              
              <button className="control-btn" onClick={() => {/* Next track */}}>
                ⏭️
              </button>
            </div>
            
            <div className="volume-control">
              <span>🔊</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={volume}
                onChange={(e) => setVolume(parseFloat(e.target.value))}
                className="volume-slider"
              />
            </div>

            <audio
              ref={audioRef}
              src={currentTrack.url}
              volume={volume}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </>
        )}
      </div>

      {/* Playlists Section */}
      <div className="playlists-section">
        <h3>🎶 Плейлисты Mirai</h3>
        <div className="playlists-grid">
          {Object.entries(playlists).map(([key, playlist]) => (
            <div 
              key={key}
              className={`playlist-card ${currentPlaylist === key ? 'active' : ''}`}
              onClick={() => switchPlaylist(key)}
            >
              <div className="playlist-header">
                <h4>{playlist.name}</h4>
                <div className="playlist-mood">{playlist.mood}</div>
              </div>
              <p>{playlist.description}</p>
              <div className="track-count">
                {playlist.tracks.length} треков
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Track List */}
      <div className="track-list">
        <h3>📋 {playlists[currentPlaylist].name}</h3>
        <div className="tracks">
          {playlists[currentPlaylist].tracks.map((track, index) => (
            <div 
              key={track.id}
              className={`track-item ${currentTrack?.id === track.id ? 'current' : ''}`}
              onClick={() => selectTrack(track)}
            >
              <div className="track-number">{index + 1}</div>
              <div className="track-details">
                <div className="track-title">{track.title}</div>
                <div className="track-artist">{track.artist}</div>
              </div>
              <div className="track-duration">{track.duration}</div>
              <div className="track-mood-indicator">{track.mood}</div>
              {track.anime && <span className="anime-icon">🌸</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Features */}
      <div className="interactive-features">
        <div className="feature-buttons">
          <button 
            className="feature-btn karaoke"
            onClick={() => setShowKaraoke(!showKaraoke)}
          >
            🎤 Караоке с Mirai
          </button>
          
          <button 
            className="feature-btn creator"
            onClick={() => setShowCreator(!showCreator)}
          >
            🎨 Создать музыку с AI
          </button>
          
          <button className="feature-btn social">
            👥 Слушать вместе ({listeningTogether.length})
          </button>
        </div>

        {/* Karaoke Mode */}
        {showKaraoke && (
          <div className="karaoke-mode">
            <h4>🎤 Режим караоке</h4>
            <p>Пой вместе с Mirai! Она будет подпевать и поддерживать тебя! ♪</p>
            <div className="karaoke-controls">
              <button className="karaoke-btn">Начать караоке</button>
              <div className="vocal-effects">
                <label>
                  <input type="checkbox" /> Эхо
                </label>
                <label>
                  <input type="checkbox" /> Автотюн
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Music Creator */}
        {showCreator && (
          <div className="music-creator">
            <h4>🎨 Создание музыки с AI</h4>
            <p>Опиши, какую музыку хочешь, и Mirai поможет создать её с помощью AI!</p>
            <div className="creator-form">
              <input 
                type="text" 
                placeholder="Например: 'Спокойная lo-fi музыка для изучения трейдинга'"
                className="prompt-input"
              />
              <button 
                className="generate-btn"
                onClick={() => generateAIMusic("Lo-fi study music")}
              >
                ✨ Создать с Mirai
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Mirai's Musical Reactions */}
      <div className="mirai-reactions">
        <div className="reaction-bubble">
          {isPlaying ? (
            <span>Миrai танцует под музыку! ♪(´▽｀) </span>
          ) : (
            <span>Выбери трек, и я буду подпевать! (◕‿◕)</span>
          )}
        </div>
        
        {currentTrack?.anime && (
          <div className="anime-reaction">
            <span>Сугой! Обожаю аниме музыку! ✨</span>
          </div>
        )}
      </div>

      {/* Styles */}
      <style jsx>{`
        .music-studio {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 20px;
          color: white;
        }

        .studio-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          padding: 20px;
          background: rgba(255,255,255,0.1);
          border-radius: 20px;
          backdrop-filter: blur(10px);
        }

        .studio-title h1 {
          margin: 0;
          font-size: 2.5em;
          background: linear-gradient(45deg, #ff6b9d, #ffd93d);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .mirai-recommendation {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .mirai-avatar-small {
          width: 50px;
          height: 50px;
          background: #ff6b9d;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5em;
        }

        .recommendation-bubble {
          background: rgba(255,255,255,0.9);
          color: #333;
          padding: 15px;
          border-radius: 20px;
          max-width: 300px;
          position: relative;
          font-size: 14px;
        }

        .recommendation-bubble::before {
          content: '';
          position: absolute;
          left: -10px;
          top: 50%;
          transform: translateY(-50%);
          border: 10px solid transparent;
          border-right-color: rgba(255,255,255,0.9);
        }

        .main-player {
          background: rgba(255,255,255,0.1);
          border-radius: 25px;
          padding: 30px;
          margin-bottom: 30px;
          display: flex;
          align-items: center;
          gap: 30px;
          backdrop-filter: blur(10px);
        }

        .track-artwork {
          position: relative;
        }

        .artwork-container {
          width: 150px;
          height: 150px;
          position: relative;
        }

        .vinyl-record {
          width: 150px;
          height: 150px;
          background: radial-gradient(circle, #333 30%, #111 100%);
          border-radius: 50%;
          position: relative;
          transition: transform 0.3s ease;
        }

        .vinyl-record.spinning {
          animation: spin 3s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .vinyl-center {
          width: 40px;
          height: 40px;
          background: #ff6b9d;
          border-radius: 50%;
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }

        .anime-badge {
          position: absolute;
          top: -10px;
          right: -10px;
          background: #ff6b9d;
          color: white;
          padding: 5px 10px;
          border-radius: 15px;
          font-size: 12px;
          font-weight: bold;
        }

        .track-info {
          flex: 1;
        }

        .track-info h2 {
          margin: 0 0 10px 0;
          font-size: 2em;
        }

        .track-info p {
          margin: 0 0 10px 0;
          opacity: 0.8;
        }

        .track-mood {
          background: rgba(255,107,157,0.3);
          padding: 5px 15px;
          border-radius: 15px;
          display: inline-block;
          font-size: 12px;
          text-transform: uppercase;
        }

        .player-controls {
          display: flex;
          gap: 15px;
          align-items: center;
        }

        .control-btn {
          background: rgba(255,255,255,0.2);
          border: none;
          width: 50px;
          height: 50px;
          border-radius: 50%;
          color: white;
          font-size: 1.2em;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .control-btn:hover {
          background: rgba(255,255,255,0.3);
          transform: scale(1.1);
        }

        .play-pause-btn {
          background: #ff6b9d;
          border: none;
          width: 70px;
          height: 70px;
          border-radius: 50%;
          color: white;
          font-size: 1.8em;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .play-pause-btn:hover {
          background: #ff5722;
          transform: scale(1.1);
        }

        .volume-control {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .volume-slider {
          width: 100px;
          height: 5px;
          background: rgba(255,255,255,0.3);
          border-radius: 5px;
          outline: none;
          cursor: pointer;
        }

        .playlists-section {
          margin-bottom: 30px;
        }

        .playlists-section h3 {
          margin-bottom: 20px;
          font-size: 1.8em;
        }

        .playlists-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
        }

        .playlist-card {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
          backdrop-filter: blur(10px);
        }

        .playlist-card:hover,
        .playlist-card.active {
          background: rgba(255,107,157,0.3);
          transform: translateY(-5px);
          box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }

        .playlist-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .playlist-header h4 {
          margin: 0;
          font-size: 1.2em;
        }

        .playlist-mood {
          background: rgba(255,255,255,0.2);
          padding: 3px 8px;
          border-radius: 10px;
          font-size: 10px;
          text-transform: uppercase;
        }

        .track-count {
          margin-top: 10px;
          font-size: 12px;
          opacity: 0.7;
        }

        .track-list {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          margin-bottom: 30px;
          backdrop-filter: blur(10px);
        }

        .track-list h3 {
          margin-bottom: 20px;
        }

        .track-item {
          display: flex;
          align-items: center;
          gap: 15px;
          padding: 15px;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .track-item:hover,
        .track-item.current {
          background: rgba(255,107,157,0.2);
        }

        .track-number {
          width: 30px;
          text-align: center;
          font-weight: bold;
        }

        .track-details {
          flex: 1;
        }

        .track-title {
          font-weight: bold;
          margin-bottom: 5px;
        }

        .track-artist {
          opacity: 0.7;
          font-size: 14px;
        }

        .track-duration,
        .track-mood-indicator {
          font-size: 12px;
          opacity: 0.8;
        }

        .anime-icon {
          font-size: 16px;
        }

        .interactive-features {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          margin-bottom: 30px;
          backdrop-filter: blur(10px);
        }

        .feature-buttons {
          display: flex;
          gap: 15px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }

        .feature-btn {
          background: #ff6b9d;
          border: none;
          padding: 12px 24px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
          font-weight: bold;
        }

        .feature-btn:hover {
          background: #ff5722;
          transform: translateY(-3px);
        }

        .karaoke-mode,
        .music-creator {
          background: rgba(255,255,255,0.1);
          padding: 20px;
          border-radius: 15px;
          margin-top: 15px;
        }

        .karaoke-controls,
        .creator-form {
          display: flex;
          gap: 15px;
          align-items: center;
          flex-wrap: wrap;
        }

        .prompt-input {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 25px;
          background: rgba(255,255,255,0.9);
          color: #333;
          min-width: 300px;
        }

        .generate-btn,
        .karaoke-btn {
          background: #667eea;
          border: none;
          padding: 12px 24px;
          border-radius: 25px;
          color: white;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .generate-btn:hover,
        .karaoke-btn:hover {
          background: #5a67d8;
          transform: translateY(-2px);
        }

        .vocal-effects {
          display: flex;
          gap: 15px;
        }

        .vocal-effects label {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 14px;
        }

        .mirai-reactions {
          background: rgba(255,255,255,0.1);
          border-radius: 15px;
          padding: 20px;
          text-align: center;
          backdrop-filter: blur(10px);
        }

        .reaction-bubble,
        .anime-reaction {
          background: rgba(255,107,157,0.3);
          padding: 15px 25px;
          border-radius: 25px;
          display: inline-block;
          margin: 5px;
          font-size: 16px;
        }

        .anime-reaction {
          background: rgba(255,215,61,0.3);
        }

        @media (max-width: 768px) {
          .main-player {
            flex-direction: column;
            text-align: center;
          }
          
          .playlists-grid {
            grid-template-columns: 1fr;
          }
          
          .feature-buttons {
            flex-direction: column;
          }
          
          .karaoke-controls,
          .creator-form {
            flex-direction: column;
          }
          
          .prompt-input {
            min-width: 100%;
          }
        }
      `}</style>
    </div>
  );
}