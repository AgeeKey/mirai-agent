import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Конфигурация обработки уведомлений
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

export interface NotificationData {
  title: string;
  body: string;
  data?: any;
  sound?: boolean;
  badge?: number;
}

export interface TradingSignalNotification {
  symbol: string;
  type: 'BUY' | 'SELL';
  confidence: number;
  price: number;
  strategy: string;
}

export interface PortfolioUpdateNotification {
  totalValue: number;
  dailyPnl: number;
  changePercent: number;
}

class NotificationService {
  private expoPushToken: string | null = null;
  private notificationListener: any = null;
  private responseListener: any = null;

  /**
   * Инициализация сервиса уведомлений
   */
  async initialize(): Promise<boolean> {
    try {
      // Проверяем, что устройство поддерживает push уведомления
      if (!Device.isDevice) {
        console.warn('Push notifications только работают на физических устройствах');
        return false;
      }

      // Запрашиваем разрешения
      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.warn('Разрешение на уведомления не получено');
        return false;
      }

      // Получаем токен для push уведомлений
      this.expoPushToken = await this.getExpoPushToken();
      
      // Настраиваем каналы уведомлений для Android
      if (Platform.OS === 'android') {
        await this.setupAndroidChannels();
      }

      // Настраиваем слушатели
      this.setupListeners();

      console.log('NotificationService инициализирован успешно');
      return true;
    } catch (error) {
      console.error('Ошибка инициализации NotificationService:', error);
      return false;
    }
  }

  /**
   * Получение Expo Push Token
   */
  private async getExpoPushToken(): Promise<string> {
    try {
      const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
      
      if (!projectId) {
        throw new Error('Project ID не найден в конфигурации');
      }

      const token = await Notifications.getExpoPushTokenAsync({
        projectId,
      });
      
      console.log('Expo Push Token:', token.data);
      return token.data;
    } catch (error) {
      console.error('Ошибка получения Expo Push Token:', error);
      throw error;
    }
  }

  /**
   * Настройка каналов уведомлений для Android
   */
  private async setupAndroidChannels(): Promise<void> {
    // Канал для торговых сигналов
    await Notifications.setNotificationChannelAsync('trading-signals', {
      name: 'Торговые сигналы',
      description: 'Уведомления о новых AI торговых сигналах',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#60A5FA',
      sound: 'default',
      enableVibrate: true,
      enableLights: true,
    });

    // Канал для изменений портфеля
    await Notifications.setNotificationChannelAsync('portfolio-updates', {
      name: 'Обновления портфеля',
      description: 'Уведомления об изменениях в портфеле',
      importance: Notifications.AndroidImportance.DEFAULT,
      vibrationPattern: [0, 150, 150],
      lightColor: '#10B981',
      sound: 'default',
    });

    // Канал для системных уведомлений
    await Notifications.setNotificationChannelAsync('system-alerts', {
      name: 'Системные уведомления',
      description: 'Важные системные уведомления',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 500, 200, 500],
      lightColor: '#EF4444',
      sound: 'default',
      enableVibrate: true,
      enableLights: true,
    });
  }

  /**
   * Настройка слушателей уведомлений
   */
  private setupListeners(): void {
    // Слушатель получения уведомлений
    this.notificationListener = Notifications.addNotificationReceivedListener(notification => {
      console.log('Уведомление получено:', notification);
      
      // Можно добавить кастомную логику обработки
      const { title, body, data } = notification.request.content;
      
      if (data?.type === 'trading_signal') {
        this.handleTradingSignalReceived(data);
      } else if (data?.type === 'portfolio_update') {
        this.handlePortfolioUpdateReceived(data);
      }
    });

    // Слушатель нажатий на уведомления
    this.responseListener = Notifications.addNotificationResponseReceivedListener(response => {
      console.log('Уведомление нажато:', response);
      
      const { data } = response.notification.request.content;
      
      if (data?.type === 'trading_signal') {
        this.handleTradingSignalTapped(data);
      } else if (data?.type === 'portfolio_update') {
        this.handlePortfolioUpdateTapped(data);
      }
    });
  }

  /**
   * Отправка локального уведомления о торговом сигнале
   */
  async sendTradingSignalNotification(signal: TradingSignalNotification): Promise<void> {
    const confidencePercent = Math.round(signal.confidence * 100);
    const priceFormatted = signal.price.toFixed(2);
    
    await Notifications.scheduleNotificationAsync({
      content: {
        title: `🤖 ${signal.type} сигнал`,
        body: `${signal.symbol}: $${priceFormatted} | Уверенность: ${confidencePercent}%`,
        data: {
          type: 'trading_signal',
          signal: signal,
        },
        sound: 'default',
        badge: 1,
      },
      trigger: null, // Отправить немедленно
      identifier: `trading_signal_${Date.now()}`,
    });
  }

  /**
   * Отправка локального уведомления об обновлении портфеля
   */
  async sendPortfolioUpdateNotification(update: PortfolioUpdateNotification): Promise<void> {
    const changeSymbol = update.dailyPnl >= 0 ? '+' : '';
    const changeIcon = update.dailyPnl >= 0 ? '📈' : '📉';
    const totalFormatted = update.totalValue.toLocaleString();
    const pnlFormatted = update.dailyPnl.toFixed(2);
    
    await Notifications.scheduleNotificationAsync({
      content: {
        title: `${changeIcon} Обновление портфеля`,
        body: `Баланс: $${totalFormatted} | Сегодня: ${changeSymbol}$${pnlFormatted}`,
        data: {
          type: 'portfolio_update',
          update: update,
        },
        sound: 'default',
      },
      trigger: null,
      identifier: `portfolio_update_${Date.now()}`,
    });
  }

  /**
   * Отправка системного уведомления
   */
  async sendSystemNotification(title: string, body: string, data?: any): Promise<void> {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: `⚠️ ${title}`,
        body: body,
        data: {
          type: 'system_alert',
          ...data,
        },
        sound: 'default',
        badge: 1,
      },
      trigger: null,
      identifier: `system_alert_${Date.now()}`,
    });
  }

  /**
   * Планирование повторяющихся уведомлений (например, ежедневный отчет)
   */
  async scheduleDailyReport(): Promise<void> {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '📊 Ежедневный отчет',
        body: 'Посмотрите результаты торговли за сегодня',
        data: {
          type: 'daily_report',
        },
        sound: 'default',
      },
      trigger: {
        hour: 20, // 8 PM
        minute: 0,
        repeats: true,
      },
      identifier: 'daily_report',
    });
  }

  /**
   * Отмена всех запланированных уведомлений
   */
  async cancelAllNotifications(): Promise<void> {
    await Notifications.cancelAllScheduledNotificationsAsync();
  }

  /**
   * Отмена конкретного уведомления
   */
  async cancelNotification(identifier: string): Promise<void> {
    await Notifications.cancelScheduledNotificationAsync(identifier);
  }

  /**
   * Получение количества непрочитанных уведомлений
   */
  async getBadgeCount(): Promise<number> {
    return await Notifications.getBadgeCountAsync();
  }

  /**
   * Установка значка с количеством уведомлений
   */
  async setBadgeCount(count: number): Promise<void> {
    await Notifications.setBadgeCountAsync(count);
  }

  /**
   * Обработка получения торгового сигнала
   */
  private handleTradingSignalReceived(data: any): void {
    console.log('Получен торговый сигнал:', data);
    // Здесь можно добавить логику обработки, например обновление состояния приложения
  }

  /**
   * Обработка нажатия на уведомление о торговом сигнале
   */
  private handleTradingSignalTapped(data: any): void {
    console.log('Нажато уведомление о торговом сигнале:', data);
    // Здесь можно добавить навигацию к экрану торговых сигналов
  }

  /**
   * Обработка получения обновления портфеля
   */
  private handlePortfolioUpdateReceived(data: any): void {
    console.log('Получено обновление портфеля:', data);
  }

  /**
   * Обработка нажатия на уведомление об обновлении портфеля
   */
  private handlePortfolioUpdateTapped(data: any): void {
    console.log('Нажато уведомление об обновлении портфеля:', data);
    // Здесь можно добавить навигацию к экрану портфеля
  }

  /**
   * Получение токена для отправки на сервер
   */
  getExpoPushTokenForServer(): string | null {
    return this.expoPushToken;
  }

  /**
   * Очистка ресурсов
   */
  dispose(): void {
    if (this.notificationListener) {
      Notifications.removeNotificationSubscription(this.notificationListener);
    }
    if (this.responseListener) {
      Notifications.removeNotificationSubscription(this.responseListener);
    }
  }
}

// Экспортируем singleton instance
export const notificationService = new NotificationService();

// Экспортируем типы для использования в других компонентах
export { Notifications };
export default NotificationService;