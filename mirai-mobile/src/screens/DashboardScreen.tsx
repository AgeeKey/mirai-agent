import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  Alert,
  SafeAreaView,
  RefreshControl,
} from 'react-native';
import { buildUrl, API_CONFIG } from '../config/api';
import { useNotifications } from '../hooks/useNotifications';

interface DashboardScreenProps {
  onLogout: () => void;
  onShowAnalytics: () => void;
  onShowNotificationSettings: () => void;
  token: string;
}

interface PortfolioStats {
  totalBalance: string;
  todayProfit: string;
  activePositions: number;
  aiScore: number;
}

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: string;
  pnl: string;
  pnlPercent: string;
}

interface AISignal {
  time: string;
  symbol: string;
  signal: 'BUY' | 'SELL';
  confidence: string;
  price: string;
}

export default function DashboardScreen({ onLogout, onShowAnalytics, onShowNotificationSettings, token }: DashboardScreenProps) {
  const [portfolioStats, setPortfolioStats] = useState<PortfolioStats>({
    totalBalance: '125,840.50',
    todayProfit: '+2,384.20',
    activePositions: 7,
    aiScore: 94.2,
  });

  const [positions, setPositions] = useState<Position[]>([]);
  const [aiSignals, setAiSignals] = useState<AISignal[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  // Интегрируем уведомления
  const {
    notificationCount,
    sendTradingSignal,
    sendPortfolioUpdate,
    resetBadgeCount
  } = useNotifications();

  useEffect(() => {
    loadData();
  }, []);

    const loadData = async () => {
    try {
      setRefreshing(true);
      
      // Load portfolio stats
      const portfolioResponse = await fetch(buildUrl(API_CONFIG.ENDPOINTS.PORTFOLIO), {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (portfolioResponse.ok) {
        const portfolioData = await portfolioResponse.json();
        setPortfolioStats({
          totalBalance: portfolioData.total_value.toLocaleString(),
          todayProfit: `${portfolioData.daily_pnl >= 0 ? '+' : ''}${portfolioData.daily_pnl.toFixed(2)}`,
          activePositions: portfolioData.positions.length,
          aiScore: 94.2,
        });
        
        // Устанавливаем позиции из данных портфолио
        setPositions(portfolioData.positions.map((pos: any) => ({
          symbol: pos.symbol,
          side: 'LONG',
          size: pos.size.toString(),
          pnl: `${pos.value.toFixed(2)}`,
          pnlPercent: `+2.5%`,
        })));
        
        // Отправляем уведомление об обновлении портфолио
        sendPortfolioUpdate({
          totalValue: portfolioData.total_value,
          dailyPnl: portfolioData.daily_pnl,
          changePercent: portfolioData.daily_pnl > 0 ? 2.5 : -1.2
        });
      }

      // Загружаем AI сигналы
      const signalsResponse = await fetch(buildUrl(API_CONFIG.ENDPOINTS.SIGNALS), {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (signalsResponse.ok) {
        const signalsData = await signalsResponse.json();
        setAiSignals(signalsData.signals.map((signal: any) => ({
          time: new Date(signal.timestamp).toLocaleTimeString('ru', { 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          symbol: signal.symbol,
          signal: signal.type,
          confidence: `${Math.round(signal.confidence * 100)}%`,
          price: signal.price.toFixed(2),
        })));
        
        // Отправляем уведомление о новых торговых сигналах
        if (signalsData.signals.length > 0) {
          const latestSignal = signalsData.signals[0];
          sendTradingSignal({
            symbol: latestSignal.symbol,
            type: latestSignal.type.toUpperCase() as 'BUY' | 'SELL',
            price: latestSignal.price,
            confidence: Math.round(latestSignal.confidence * 100),
            strategy: 'AI Trading'
          });
        }
      }
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleTradeAction = (symbol: string, action: string) => {
    Alert.alert(
      'Подтверждение сделки',
      `${action} ${symbol}?`,
      [
        { text: 'Отмена', style: 'cancel' },
        { 
          text: 'Подтвердить', 
          onPress: async () => {
            try {
              const response = await fetch('http://localhost:8001/trading/execute-trade', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  symbol,
                  side: action,
                  quantity: 0.1, // Default quantity
                }),
              });

              if (response.ok) {
                Alert.alert('Успех', 'Сделка выполнена');
                loadData(); // Refresh data
              } else {
                Alert.alert('Ошибка', 'Не удалось выполнить сделку');
              }
            } catch (error) {
              Alert.alert('Ошибка', 'Сетевая ошибка');
            }
          }
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Mirai AI Trading</Text>
          <Text style={styles.headerSubtitle}>Мобильный терминал</Text>
        </View>
        <TouchableOpacity onPress={onLogout} style={styles.logoutButton}>
          <Text style={styles.logoutText}>Выйти</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Portfolio Stats */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Портфель</Text>
          
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Общий баланс</Text>
              <Text style={styles.statValue}>${portfolioStats.totalBalance}</Text>
              <Text style={styles.statCurrency}>USDT</Text>
            </View>
            
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Прибыль сегодня</Text>
              <Text style={[styles.statValue, styles.profit]}>
                {portfolioStats.todayProfit}
              </Text>
              <Text style={styles.statCurrency}>USDT</Text>
            </View>
            
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Активных позиций</Text>
              <Text style={styles.statValue}>{portfolioStats.activePositions}</Text>
            </View>
            
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>AI Score</Text>
              <Text style={[styles.statValue, styles.aiScore]}>
                {portfolioStats.aiScore}%
              </Text>
            </View>
          </View>
        </View>

        {/* Active Positions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Активные позиции</Text>
          
          {positions.length > 0 ? positions.map((position, index) => (
            <View key={index} style={styles.positionCard}>
              <View style={styles.positionHeader}>
                <Text style={styles.positionSymbol}>{position.symbol}</Text>
                <View style={[
                  styles.positionSide,
                  position.side === 'LONG' ? styles.long : styles.short
                ]}>
                  <Text style={styles.positionSideText}>{position.side}</Text>
                </View>
              </View>
              
              <View style={styles.positionDetails}>
                <Text style={styles.positionSize}>Размер: {position.size}</Text>
                <View style={styles.positionPnl}>
                  <Text style={[styles.pnlValue, styles.profit]}>{position.pnl}</Text>
                  <Text style={[styles.pnlPercent, styles.profit]}>
                    {position.pnlPercent}
                  </Text>
                </View>
              </View>
            </View>
          )) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>Нет активных позиций</Text>
            </View>
          )}
        </View>

        {/* AI Signals */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI Сигналы</Text>
          
          {aiSignals.length > 0 ? aiSignals.map((signal, index) => (
            <View key={index} style={styles.signalCard}>
              <View style={styles.signalHeader}>
                <Text style={styles.signalTime}>{signal.time}</Text>
                <Text style={styles.signalSymbol}>{signal.symbol}</Text>
                <View style={[
                  styles.signalAction,
                  signal.signal === 'BUY' ? styles.buy : styles.sell
                ]}>
                  <Text style={styles.signalActionText}>{signal.signal}</Text>
                </View>
              </View>
              
              <View style={styles.signalDetails}>
                <Text style={styles.signalConfidence}>
                  Уверенность: {signal.confidence}
                </Text>
                <Text style={styles.signalPrice}>${signal.price}</Text>
              </View>
              
              <View style={styles.signalActions}>
                <TouchableOpacity
                  style={[styles.actionButton, styles.buyButton]}
                  onPress={() => handleTradeAction(signal.symbol, 'BUY')}
                >
                  <Text style={styles.actionButtonText}>BUY</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[styles.actionButton, styles.sellButton]}
                  onPress={() => handleTradeAction(signal.symbol, 'SELL')}
                >
                  <Text style={styles.actionButtonText}>SELL</Text>
                </TouchableOpacity>
              </View>
            </View>
          )) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>Нет новых сигналов</Text>
            </View>
          )}
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Быстрые действия</Text>
          
          <View style={styles.quickActions}>
            <TouchableOpacity style={styles.quickAction} onPress={onShowAnalytics}>
              <Text style={styles.quickActionText}>📊</Text>
              <Text style={styles.quickActionLabel}>Аналитика</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.quickAction}>
              <Text style={styles.quickActionText}>🤖</Text>
              <Text style={styles.quickActionLabel}>AI Настройки</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.quickAction}>
              <Text style={styles.quickActionText}>🛡️</Text>
              <Text style={styles.quickActionLabel}>Риск-менеджмент</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.quickAction} onPress={onShowNotificationSettings}>
              <Text style={styles.quickActionText}>🔔</Text>
              <Text style={styles.quickActionLabel}>Уведомления</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.quickAction}>
              <Text style={styles.quickActionText}>⚙️</Text>
              <Text style={styles.quickActionLabel}>Настройки</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
    backgroundColor: '#1F2937',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  logoutButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#EF4444',
  },
  logoutText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  statCard: {
    width: '48%',
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: '1%',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#374151',
  },
  statLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  statCurrency: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  profit: {
    color: '#10B981',
  },
  aiScore: {
    color: '#8B5CF6',
  },
  positionCard: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  positionSide: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  long: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
  },
  short: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  positionSideText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  positionDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  positionSize: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  positionPnl: {
    alignItems: 'flex-end',
  },
  pnlValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  pnlPercent: {
    fontSize: 12,
  },
  signalCard: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  signalTime: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  signalSymbol: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  signalAction: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  buy: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
  },
  sell: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  signalActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  signalDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  signalConfidence: {
    fontSize: 12,
    color: '#8B5CF6',
  },
  signalPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  signalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    marginHorizontal: 4,
    alignItems: 'center',
  },
  buyButton: {
    backgroundColor: '#10B981',
  },
  sellButton: {
    backgroundColor: '#EF4444',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -8,
  },
  quickAction: {
    width: '23%',
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: '1%',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#374151',
  },
  quickActionText: {
    fontSize: 24,
    marginBottom: 8,
  },
  quickActionLabel: {
    fontSize: 10,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  emptyState: {
    backgroundColor: '#1F2937',
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#374151',
  },
  emptyText: {
    color: '#6B7280',
    fontSize: 14,
  },
});