import React from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  SafeAreaView,
} from 'react-native';
import { useNotifications, NotificationSettings } from '../hooks/useNotifications';

interface NotificationSettingsScreenProps {
  onBack: () => void;
}

export default function NotificationSettingsScreen({ onBack }: NotificationSettingsScreenProps) {
  const {
    isInitialized,
    permissionGranted,
    expoPushToken,
    notificationCount,
    settings,
    updateSettings,
    clearAllNotifications,
    resetBadgeCount,
    checkPermissions,
    reinitialize,
    sendTradingSignal,
    sendPortfolioUpdate,
    sendSystemAlert,
  } = useNotifications();

  const handleToggleSetting = (key: keyof NotificationSettings, value: boolean) => {
    updateSettings({ [key]: value });
  };

  const handleTestTradingSignal = async () => {
    if (!permissionGranted) {
      Alert.alert('Ошибка', 'Разрешения на уведомления не предоставлены');
      return;
    }

    await sendTradingSignal({
      symbol: 'BTC/USDT',
      type: 'BUY',
      confidence: 0.87,
      price: 45250.00,
      strategy: 'AI Trend Following'
    });

    Alert.alert('Тест', 'Тестовое уведомление о торговом сигнале отправлено');
  };

  const handleTestPortfolioUpdate = async () => {
    if (!permissionGranted) {
      Alert.alert('Ошибка', 'Разрешения на уведомления не предоставлены');
      return;
    }

    await sendPortfolioUpdate({
      totalValue: 125840.50,
      dailyPnl: 2384.20,
      changePercent: 1.95
    });

    Alert.alert('Тест', 'Тестовое уведомление об обновлении портфеля отправлено');
  };

  const handleTestSystemAlert = async () => {
    if (!permissionGranted) {
      Alert.alert('Ошибка', 'Разрешения на уведомления не предоставлены');
      return;
    }

    await sendSystemAlert(
      'Тестовое системное уведомление',
      'Это тестовое сообщение для проверки системных уведомлений'
    );

    Alert.alert('Тест', 'Тестовое системное уведомление отправлено');
  };

  const handleClearAllNotifications = () => {
    Alert.alert(
      'Очистить уведомления',
      'Вы уверены, что хотите отменить все запланированные уведомления?',
      [
        { text: 'Отмена', style: 'cancel' },
        {
          text: 'Очистить',
          style: 'destructive',
          onPress: async () => {
            await clearAllNotifications();
            Alert.alert('Готово', 'Все уведомления очищены');
          }
        }
      ]
    );
  };

  const handleRequestPermissions = async () => {
    const granted = await checkPermissions();
    if (granted) {
      await reinitialize();
      Alert.alert('Успех', 'Разрешения предоставлены');
    } else {
      Alert.alert(
        'Разрешения не предоставлены',
        'Для получения уведомлений необходимо предоставить разрешения в настройках устройства'
      );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Уведомления</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView style={styles.content}>
        {/* Статус */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📱 Статус</Text>
          
          <View style={styles.statusCard}>
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Инициализированы</Text>
              <View style={[styles.statusIndicator, { backgroundColor: isInitialized ? '#10B981' : '#EF4444' }]} />
            </View>
            
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Разрешения</Text>
              <View style={[styles.statusIndicator, { backgroundColor: permissionGranted ? '#10B981' : '#EF4444' }]} />
            </View>
            
            <View style={styles.statusRow}>
              <Text style={styles.statusLabel}>Непрочитанных</Text>
              <View style={styles.badgeCount}>
                <Text style={styles.badgeText}>{notificationCount}</Text>
              </View>
            </View>
          </View>

          {!permissionGranted && (
            <TouchableOpacity style={styles.permissionButton} onPress={handleRequestPermissions}>
              <Text style={styles.permissionButtonText}>🔔 Запросить разрешения</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Настройки типов уведомлений */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚙️ Настройки</Text>
          
          <View style={styles.settingsCard}>
            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>🤖 Торговые сигналы</Text>
                <Text style={styles.settingDescription}>Уведомления о новых AI сигналах</Text>
              </View>
              <Switch
                value={settings.tradingSignals}
                onValueChange={(value) => handleToggleSetting('tradingSignals', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.tradingSignals ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>💰 Обновления портфеля</Text>
                <Text style={styles.settingDescription}>Изменения баланса и P&L</Text>
              </View>
              <Switch
                value={settings.portfolioUpdates}
                onValueChange={(value) => handleToggleSetting('portfolioUpdates', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.portfolioUpdates ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>⚠️ Системные уведомления</Text>
                <Text style={styles.settingDescription}>Важные системные события</Text>
              </View>
              <Switch
                value={settings.systemAlerts}
                onValueChange={(value) => handleToggleSetting('systemAlerts', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.systemAlerts ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>📊 Ежедневные отчеты</Text>
                <Text style={styles.settingDescription}>Отчеты в 20:00 каждый день</Text>
              </View>
              <Switch
                value={settings.dailyReports}
                onValueChange={(value) => handleToggleSetting('dailyReports', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.dailyReports ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>
          </View>
        </View>

        {/* Настройки звука и вибрации */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🔊 Звук и вибрация</Text>
          
          <View style={styles.settingsCard}>
            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>🔔 Звуковые уведомления</Text>
                <Text style={styles.settingDescription}>Воспроизводить звук</Text>
              </View>
              <Switch
                value={settings.soundEnabled}
                onValueChange={(value) => handleToggleSetting('soundEnabled', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.soundEnabled ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>

            <View style={styles.settingRow}>
              <View style={styles.settingInfo}>
                <Text style={styles.settingLabel}>📳 Вибрация</Text>
                <Text style={styles.settingDescription}>Вибрация при уведомлениях</Text>
              </View>
              <Switch
                value={settings.vibrationEnabled}
                onValueChange={(value) => handleToggleSetting('vibrationEnabled', value)}
                trackColor={{ false: '#374151', true: '#60A5FA' }}
                thumbColor={settings.vibrationEnabled ? '#FFFFFF' : '#9CA3AF'}
              />
            </View>
          </View>
        </View>

        {/* Тестирование */}
        {permissionGranted && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🧪 Тестирование</Text>
            
            <View style={styles.testButtons}>
              <TouchableOpacity style={styles.testButton} onPress={handleTestTradingSignal}>
                <Text style={styles.testButtonText}>🤖 Тест торгового сигнала</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.testButton} onPress={handleTestPortfolioUpdate}>
                <Text style={styles.testButtonText}>💰 Тест обновления портфеля</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.testButton} onPress={handleTestSystemAlert}>
                <Text style={styles.testButtonText}>⚠️ Тест системного уведомления</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Управление */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🛠 Управление</Text>
          
          <View style={styles.actionButtons}>
            <TouchableOpacity style={styles.actionButton} onPress={resetBadgeCount}>
              <Text style={styles.actionButtonText}>🔄 Сбросить счетчик</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={[styles.actionButton, styles.destructiveButton]} onPress={handleClearAllNotifications}>
              <Text style={[styles.actionButtonText, styles.destructiveButtonText]}>🗑 Очистить все</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Техническая информация */}
        {expoPushToken && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>🔧 Техническая информация</Text>
            
            <View style={styles.techInfo}>
              <Text style={styles.techLabel}>Expo Push Token:</Text>
              <Text style={styles.techValue} numberOfLines={3} ellipsizeMode="middle">
                {expoPushToken}
              </Text>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1F2937',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  backButton: {
    padding: 5,
  },
  backButtonText: {
    color: '#60A5FA',
    fontSize: 16,
    fontWeight: '600',
  },
  headerTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  placeholder: {
    width: 60,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginVertical: 15,
  },
  sectionTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  statusCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  statusLabel: {
    color: '#9CA3AF',
    fontSize: 16,
  },
  statusIndicator: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  badgeCount: {
    backgroundColor: '#EF4444',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  permissionButton: {
    backgroundColor: '#60A5FA',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  permissionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  settingsCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#4B5563',
  },
  settingInfo: {
    flex: 1,
    marginRight: 15,
  },
  settingLabel: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  settingDescription: {
    color: '#9CA3AF',
    fontSize: 14,
    marginTop: 2,
  },
  testButtons: {
    gap: 10,
  },
  testButton: {
    backgroundColor: '#4B5563',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
  },
  testButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  actionButtons: {
    gap: 10,
  },
  actionButton: {
    backgroundColor: '#4B5563',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  destructiveButton: {
    backgroundColor: '#EF4444',
  },
  destructiveButtonText: {
    color: 'white',
  },
  techInfo: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
  },
  techLabel: {
    color: '#9CA3AF',
    fontSize: 14,
    marginBottom: 5,
  },
  techValue: {
    color: 'white',
    fontSize: 12,
    fontFamily: 'monospace',
  },
});