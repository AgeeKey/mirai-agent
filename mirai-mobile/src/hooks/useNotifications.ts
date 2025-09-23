import { useEffect, useState, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { notificationService, TradingSignalNotification, PortfolioUpdateNotification } from '../services/notifications';

export interface NotificationSettings {
  tradingSignals: boolean;
  portfolioUpdates: boolean;
  systemAlerts: boolean;
  dailyReports: boolean;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
}

export const useNotifications = () => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [permissionGranted, setPermissionGranted] = useState(false);
  const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [settings, setSettings] = useState<NotificationSettings>({
    tradingSignals: true,
    portfolioUpdates: true,
    systemAlerts: true,
    dailyReports: false,
    soundEnabled: true,
    vibrationEnabled: true,
  });

  const appState = useRef(AppState.currentState);

  /**
   * Инициализация уведомлений при монтировании компонента
   */
  useEffect(() => {
    initializeNotifications();
    
    // Слушаем изменения состояния приложения
    const subscription = AppState.addEventListener('change', handleAppStateChange);
    
    return () => {
      subscription?.remove();
      notificationService.dispose();
    };
  }, []);

  /**
   * Обновляем badge count при изменении количества уведомлений
   */
  useEffect(() => {
    if (isInitialized) {
      notificationService.setBadgeCount(notificationCount);
    }
  }, [notificationCount, isInitialized]);

  /**
   * Инициализация сервиса уведомлений
   */
  const initializeNotifications = async (): Promise<void> => {
    try {
      const success = await notificationService.initialize();
      
      if (success) {
        setIsInitialized(true);
        setPermissionGranted(true);
        
        const token = notificationService.getExpoPushTokenForServer();
        setExpoPushToken(token);
        
        // Получаем текущее количество badge
        const currentBadgeCount = await notificationService.getBadgeCount();
        setNotificationCount(currentBadgeCount);
        
        console.log('Notifications hook инициализирован успешно');
      } else {
        setPermissionGranted(false);
        console.warn('Не удалось инициализировать уведомления');
      }
    } catch (error) {
      console.error('Ошибка инициализации уведомлений:', error);
      setPermissionGranted(false);
    }
  };

  /**
   * Обработка изменения состояния приложения
   */
  const handleAppStateChange = (nextAppState: AppStateStatus): void => {
    if (appState.current.match(/inactive|background/) && nextAppState === 'active') {
      // Приложение стало активным - обновляем badge count
      updateBadgeCount();
    }
    appState.current = nextAppState;
  };

  /**
   * Обновление количества непрочитанных уведомлений
   */
  const updateBadgeCount = async (): Promise<void> => {
    if (isInitialized) {
      const count = await notificationService.getBadgeCount();
      setNotificationCount(count);
    }
  };

  /**
   * Отправка уведомления о торговом сигнале
   */
  const sendTradingSignal = async (signal: TradingSignalNotification): Promise<void> => {
    if (!isInitialized || !settings.tradingSignals) return;
    
    try {
      await notificationService.sendTradingSignalNotification(signal);
      setNotificationCount(prev => prev + 1);
    } catch (error) {
      console.error('Ошибка отправки уведомления о торговом сигнале:', error);
    }
  };

  /**
   * Отправка уведомления об обновлении портфеля
   */
  const sendPortfolioUpdate = async (update: PortfolioUpdateNotification): Promise<void> => {
    if (!isInitialized || !settings.portfolioUpdates) return;
    
    try {
      await notificationService.sendPortfolioUpdateNotification(update);
      // Не увеличиваем badge для обновлений портфеля (менее критично)
    } catch (error) {
      console.error('Ошибка отправки уведомления об обновлении портфеля:', error);
    }
  };

  /**
   * Отправка системного уведомления
   */
  const sendSystemAlert = async (title: string, body: string, data?: any): Promise<void> => {
    if (!isInitialized || !settings.systemAlerts) return;
    
    try {
      await notificationService.sendSystemNotification(title, body, data);
      setNotificationCount(prev => prev + 1);
    } catch (error) {
      console.error('Ошибка отправки системного уведомления:', error);
    }
  };

  /**
   * Планирование ежедневного отчета
   */
  const scheduleDailyReport = async (): Promise<void> => {
    if (!isInitialized || !settings.dailyReports) return;
    
    try {
      await notificationService.scheduleDailyReport();
      console.log('Ежедневный отчет запланирован');
    } catch (error) {
      console.error('Ошибка планирования ежедневного отчета:', error);
    }
  };

  /**
   * Отмена ежедневного отчета
   */
  const cancelDailyReport = async (): Promise<void> => {
    if (!isInitialized) return;
    
    try {
      await notificationService.cancelNotification('daily_report');
      console.log('Ежедневный отчет отменен');
    } catch (error) {
      console.error('Ошибка отмены ежедневного отчета:', error);
    }
  };

  /**
   * Очистка всех уведомлений
   */
  const clearAllNotifications = async (): Promise<void> => {
    if (!isInitialized) return;
    
    try {
      await notificationService.cancelAllNotifications();
      await notificationService.setBadgeCount(0);
      setNotificationCount(0);
      console.log('Все уведомления очищены');
    } catch (error) {
      console.error('Ошибка очистки уведомлений:', error);
    }
  };

  /**
   * Обновление настроек уведомлений
   */
  const updateSettings = (newSettings: Partial<NotificationSettings>): void => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      
      // Если ежедневные отчеты включены - планируем, если выключены - отменяем
      if (newSettings.dailyReports !== undefined) {
        if (newSettings.dailyReports) {
          scheduleDailyReport();
        } else {
          cancelDailyReport();
        }
      }
      
      return updated;
    });
  };

  /**
   * Сброс счетчика badge
   */
  const resetBadgeCount = async (): Promise<void> => {
    if (!isInitialized) return;
    
    try {
      await notificationService.setBadgeCount(0);
      setNotificationCount(0);
    } catch (error) {
      console.error('Ошибка сброса badge count:', error);
    }
  };

  /**
   * Проверка разрешений на уведомления
   */
  const checkPermissions = async (): Promise<boolean> => {
    try {
      const { status } = await notificationService.getPermissionsAsync();
      const granted = status === 'granted';
      setPermissionGranted(granted);
      return granted;
    } catch (error) {
      console.error('Ошибка проверки разрешений:', error);
      return false;
    }
  };

  return {
    // Состояние
    isInitialized,
    permissionGranted,
    expoPushToken,
    notificationCount,
    settings,
    
    // Методы для отправки уведомлений
    sendTradingSignal,
    sendPortfolioUpdate,
    sendSystemAlert,
    
    // Управление уведомлениями
    scheduleDailyReport,
    cancelDailyReport,
    clearAllNotifications,
    resetBadgeCount,
    
    // Настройки
    updateSettings,
    
    // Утилиты
    checkPermissions,
    updateBadgeCount,
    
    // Переинициализация (например, после изменения разрешений)
    reinitialize: initializeNotifications,
  };
};