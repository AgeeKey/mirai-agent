import React, { useState, useEffect } from 'react';
import { AlertTriangle, Power, Shield, CheckCircle, XCircle } from 'lucide-react';
import './KillSwitch.css';

interface EmergencyState {
  trading_stopped: boolean;
  last_stop_time: string | null;
  stop_reason: string | null;
  stopped_by: string | null;
  active_positions_closed: boolean;
}

interface SystemStatus {
  trading_active: boolean;
  ai_active: boolean;
  positions_status: string;
  last_check: string;
}

interface EmergencyStatus {
  emergency_state: EmergencyState;
  system_status: SystemStatus;
}

const KillSwitch: React.FC = () => {
  const [emergencyStatus, setEmergencyStatus] = useState<EmergencyStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);

  // Проверяем статус каждые 5 секунд
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/emergency/status');
        const data = await response.json();
        setEmergencyStatus(data);
      } catch (error) {
        console.error('Ошибка получения статуса:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEmergencyStop = async (reason: string = 'Manual emergency stop') => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/emergency/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason, user: 'Web Interface' })
      });

      const result = await response.json();
      
      if (response.ok) {
        alert('🚨 Экстренная остановка инициирована! Проверьте статус через 30 секунд.');
        setShowConfirmation(false);
      } else {
        alert(`Ошибка: ${result.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      alert('Ошибка сети при выполнении экстренной остановки');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    const confirmation = prompt(
      'ВНИМАНИЕ! Это возобновит торговлю.\n\nВведите "CONFIRM_RESET" для подтверждения:'
    );

    if (confirmation !== 'CONFIRM_RESET') {
      alert('Сброс отменен. Неверное подтверждение.');
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/emergency/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          confirmation: 'CONFIRM_RESET',
          user: 'Web Interface'
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        alert('✅ Экстренное состояние сброшено. Торговля может быть возобновлена.');
      } else {
        alert(`Ошибка: ${result.detail || 'Неизвестная ошибка'}`);
      }
    } catch (error) {
      alert('Ошибка сети при сбросе состояния');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const runSystemTest = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/emergency/test', { method: 'POST' });
      const results = await response.json();
      setTestResults(results);
    } catch (error) {
      console.error('Ошибка тестирования:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await fetch('/api/emergency/logs?lines=20');
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Ошибка получения логов:', error);
    }
  };

  if (!emergencyStatus) {
    return (
      <div className="kill-switch-container loading">
        <div className="loading-spinner">⏳ Загрузка статуса...</div>
      </div>
    );
  }

  const isEmergencyStopped = emergencyStatus.emergency_state.trading_stopped;

  return (
    <div className="kill-switch-container">
      <div className="kill-switch-header">
        <h2>
          <Shield className="icon" />
          Система экстренной остановки
        </h2>
        <div className={`status-indicator ${isEmergencyStopped ? 'stopped' : 'active'}`}>
          {isEmergencyStopped ? (
            <>
              <XCircle className="icon" />
              ТОРГОВЛЯ ОСТАНОВЛЕНА
            </>
          ) : (
            <>
              <CheckCircle className="icon" />
              СИСТЕМА АКТИВНА
            </>
          )}
        </div>
      </div>

      <div className="status-grid">
        <div className="status-card">
          <h3>🤖 AI Orchestrator</h3>
          <div className={`status ${emergencyStatus.system_status.ai_active ? 'active' : 'inactive'}`}>
            {emergencyStatus.system_status.ai_active ? '✅ Активен' : '🛑 Остановлен'}
          </div>
        </div>

        <div className="status-card">
          <h3>📈 Торговля</h3>
          <div className={`status ${emergencyStatus.system_status.trading_active ? 'active' : 'inactive'}`}>
            {emergencyStatus.system_status.trading_active ? '✅ Активна' : '🛑 Остановлена'}
          </div>
        </div>

        <div className="status-card">
          <h3>💰 Позиции</h3>
          <div className={`status ${emergencyStatus.system_status.positions_status === 'active' ? 'active' : 'inactive'}`}>
            {emergencyStatus.system_status.positions_status === 'active' ? '📊 Открыты' : '💤 Закрыты'}
          </div>
        </div>

        <div className="status-card">
          <h3>⏰ Последняя проверка</h3>
          <div className="timestamp">
            {new Date(emergencyStatus.system_status.last_check).toLocaleTimeString('ru-RU')}
          </div>
        </div>
      </div>

      {isEmergencyStopped && (
        <div className="emergency-info">
          <h3>ℹ️ Информация об остановке</h3>
          <div className="info-grid">
            <div><strong>Время:</strong> {emergencyStatus.emergency_state.last_stop_time ? 
              new Date(emergencyStatus.emergency_state.last_stop_time).toLocaleString('ru-RU') : 'Неизвестно'}</div>
            <div><strong>Причина:</strong> {emergencyStatus.emergency_state.stop_reason || 'Не указана'}</div>
            <div><strong>Инициатор:</strong> {emergencyStatus.emergency_state.stopped_by || 'Неизвестен'}</div>
          </div>
        </div>
      )}

      <div className="action-buttons">
        {!isEmergencyStopped ? (
          <>
            <button 
              className="emergency-button"
              onClick={() => setShowConfirmation(true)}
              disabled={isLoading}
            >
              <AlertTriangle className="icon" />
              {isLoading ? 'Выполняется...' : 'ЭКСТРЕННАЯ ОСТАНОВКА'}
            </button>
            
            <button 
              className="test-button"
              onClick={runSystemTest}
              disabled={isLoading}
            >
              🧪 Тест системы
            </button>
          </>
        ) : (
          <button 
            className="reset-button"
            onClick={handleReset}
            disabled={isLoading}
          >
            <Power className="icon" />
            {isLoading ? 'Сбрасывается...' : 'СБРОС И ВОЗОБНОВЛЕНИЕ'}
          </button>
        )}

        <button 
          className="logs-button"
          onClick={fetchLogs}
        >
          📋 Показать логи
        </button>
      </div>

      {showConfirmation && (
        <div className="confirmation-modal">
          <div className="modal-content">
            <h3>⚠️ ПОДТВЕРЖДЕНИЕ ЭКСТРЕННОЙ ОСТАНОВКИ</h3>
            <p>Это действие немедленно:</p>
            <ul>
              <li>🛑 Остановит все торговые операции</li>
              <li>💰 Закроет все открытые позиции</li>
              <li>🤖 Отключит AI Orchestrator</li>
              <li>📱 Отправит уведомления</li>
            </ul>
            <p><strong>Продолжить?</strong></p>
            
            <div className="modal-buttons">
              <button 
                className="confirm-button"
                onClick={() => handleEmergencyStop()}
                disabled={isLoading}
              >
                ✅ ДА, ОСТАНОВИТЬ
              </button>
              <button 
                className="cancel-button"
                onClick={() => setShowConfirmation(false)}
              >
                ❌ Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {testResults && (
        <div className="test-results">
          <h3>🧪 Результаты тестирования</h3>
          <div className="test-grid">
            {Object.entries(testResults.tests).map(([test, result]) => (
              <div key={test} className="test-item">
                <strong>{test}:</strong> <span dangerouslySetInnerHTML={{__html: result as string}} />
              </div>
            ))}
          </div>
          <div className={`overall-result ${testResults.overall.includes('✅') ? 'success' : 'error'}`}>
            {testResults.overall}
          </div>
        </div>
      )}

      {logs.length > 0 && (
        <div className="logs-section">
          <h3>📋 Логи экстренной системы</h3>
          <div className="logs-container">
            {logs.map((log, index) => (
              <div key={index} className="log-line">
                {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KillSwitch;