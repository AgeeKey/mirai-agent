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
  Dimensions,
} from 'react-native';
import { buildUrl, API_CONFIG } from '../config/api';

interface AnalyticsScreenProps {
  token: string;
  onBack: () => void;
}

interface PerformanceMetrics {
  total_return: number;
  annualized_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_trade_return: number;
}

interface RiskMetrics {
  value_at_risk: number;
  expected_shortfall: number;
  beta: number;
  volatility: number;
  correlation_btc: number;
}

interface StrategyPerformance {
  name: string;
  performance: number;
  trades: number;
  win_rate: number;
  status: string;
  allocation: number;
  sharpe_ratio: number;
  max_drawdown: number;
}

interface BacktestResult {
  period: string;
  initial_capital: number;
  final_capital: number;
  return: number;
  sharpe: number;
  max_drawdown: number;
  trades_count: number;
  win_rate: number;
}

const { width } = Dimensions.get('window');

export default function AnalyticsScreen({ token, onBack }: AnalyticsScreenProps) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('30d');
  
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [strategies, setStrategies] = useState<StrategyPerformance[]>([]);
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([]);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      // Загружаем детальный отчет
      const response = await fetch(buildUrl(`${API_CONFIG.ENDPOINTS.DETAILED_REPORT}?period=${selectedPeriod}`), {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
      });

      if (response.ok) {
        const data = await response.json();
        
        setPerformanceMetrics(data.performance_summary);
        setRiskMetrics(data.risk_metrics);
        setStrategies(data.strategy_performance);
        setBacktestResults(data.backtesting_results);
      } else {
        Alert.alert('Ошибка', 'Не удалось загрузить данные аналитики');
      }
    } catch (error) {
      Alert.alert('Ошибка сети', 'Проверьте подключение к интернету');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAnalyticsData();
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  if (loading && !refreshing) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Загружаем аналитику...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backButtonText}>← Назад</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Аналитика</Text>
        <View style={styles.placeholder} />
      </View>

      {/* Period Selector */}
      <View style={styles.periodSelector}>
        {['7d', '30d', '90d', '1y'].map((period) => (
          <TouchableOpacity
            key={period}
            style={[
              styles.periodButton,
              selectedPeriod === period && styles.periodButtonActive
            ]}
            onPress={() => setSelectedPeriod(period)}
          >
            <Text style={[
              styles.periodButtonText,
              selectedPeriod === period && styles.periodButtonTextActive
            ]}>
              {period}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Performance Summary */}
        {performanceMetrics && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>📊 Показатели эффективности</Text>
            <View style={styles.metricsGrid}>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Общий доход</Text>
                <Text style={[styles.metricValue, { color: performanceMetrics.total_return >= 0 ? '#10B981' : '#EF4444' }]}>
                  {formatPercent(performanceMetrics.total_return)}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Коэф. Шарпа</Text>
                <Text style={styles.metricValue}>
                  {performanceMetrics.sharpe_ratio.toFixed(2)}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Макс. просадка</Text>
                <Text style={[styles.metricValue, { color: '#EF4444' }]}>
                  {formatPercent(performanceMetrics.max_drawdown)}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <Text style={styles.metricLabel}>Винрейт</Text>
                <Text style={styles.metricValue}>
                  {formatPercent(performanceMetrics.win_rate)}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Risk Metrics */}
        {riskMetrics && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>⚠️ Метрики риска</Text>
            <View style={styles.riskCard}>
              <View style={styles.riskRow}>
                <Text style={styles.riskLabel}>Value at Risk (95%)</Text>
                <Text style={[styles.riskValue, { color: '#EF4444' }]}>
                  {formatPercent(riskMetrics.value_at_risk)}
                </Text>
              </View>
              <View style={styles.riskRow}>
                <Text style={styles.riskLabel}>Волатильность</Text>
                <Text style={styles.riskValue}>
                  {riskMetrics.volatility.toFixed(1)}%
                </Text>
              </View>
              <View style={styles.riskRow}>
                <Text style={styles.riskLabel}>Бета</Text>
                <Text style={styles.riskValue}>
                  {riskMetrics.beta.toFixed(2)}
                </Text>
              </View>
              <View style={styles.riskRow}>
                <Text style={styles.riskLabel}>Корреляция с BTC</Text>
                <Text style={styles.riskValue}>
                  {riskMetrics.correlation_btc.toFixed(2)}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Strategy Performance */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>🤖 Производительность стратегий</Text>
          {strategies.map((strategy, index) => (
            <View key={index} style={styles.strategyCard}>
              <View style={styles.strategyHeader}>
                <Text style={styles.strategyName}>{strategy.name}</Text>
                <View style={[
                  styles.statusBadge,
                  { backgroundColor: strategy.status === 'active' ? '#10B981' : '#6B7280' }
                ]}>
                  <Text style={styles.statusText}>
                    {strategy.status === 'active' ? 'Активна' : 'Пауза'}
                  </Text>
                </View>
              </View>
              <View style={styles.strategyMetrics}>
                <View style={styles.strategyMetric}>
                  <Text style={styles.strategyMetricLabel}>Доходность</Text>
                  <Text style={[
                    styles.strategyMetricValue,
                    { color: strategy.performance >= 0 ? '#10B981' : '#EF4444' }
                  ]}>
                    {formatPercent(strategy.performance)}
                  </Text>
                </View>
                <View style={styles.strategyMetric}>
                  <Text style={styles.strategyMetricLabel}>Сделки</Text>
                  <Text style={styles.strategyMetricValue}>{strategy.trades}</Text>
                </View>
                <View style={styles.strategyMetric}>
                  <Text style={styles.strategyMetricLabel}>Винрейт</Text>
                  <Text style={styles.strategyMetricValue}>
                    {strategy.win_rate.toFixed(1)}%
                  </Text>
                </View>
                <View style={styles.strategyMetric}>
                  <Text style={styles.strategyMetricLabel}>Аллокация</Text>
                  <Text style={styles.strategyMetricValue}>
                    {strategy.allocation.toFixed(0)}%
                  </Text>
                </View>
              </View>
            </View>
          ))}
        </View>

        {/* Backtesting Results */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📈 Результаты бэктестирования</Text>
          {backtestResults.map((result, index) => (
            <View key={index} style={styles.backtestCard}>
              <View style={styles.backtestHeader}>
                <Text style={styles.backtestPeriod}>{result.period}</Text>
                <Text style={[
                  styles.backtestReturn,
                  { color: result.return >= 0 ? '#10B981' : '#EF4444' }
                ]}>
                  {formatPercent(result.return)}
                </Text>
              </View>
              <View style={styles.backtestDetails}>
                <Text style={styles.backtestDetail}>
                  Начальный капитал: {formatCurrency(result.initial_capital)}
                </Text>
                <Text style={styles.backtestDetail}>
                  Итоговый капитал: {formatCurrency(result.final_capital)}
                </Text>
                <Text style={styles.backtestDetail}>
                  Коэф. Шарпа: {result.sharpe.toFixed(2)}
                </Text>
                <Text style={styles.backtestDetail}>
                  Макс. просадка: {formatPercent(result.max_drawdown)}
                </Text>
                <Text style={styles.backtestDetail}>
                  Сделки: {result.trades_count} | Винрейт: {result.win_rate.toFixed(1)}%
                </Text>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1F2937',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#9CA3AF',
    fontSize: 16,
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
  periodSelector: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 15,
    gap: 10,
  },
  periodButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#374151',
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: '#60A5FA',
  },
  periodButtonText: {
    color: '#9CA3AF',
    fontSize: 14,
    fontWeight: '600',
  },
  periodButtonTextActive: {
    color: 'white',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metricCard: {
    width: (width - 50) / 2,
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
    alignItems: 'center',
  },
  metricLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    marginBottom: 5,
    textAlign: 'center',
  },
  metricValue: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  riskCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
  },
  riskRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#4B5563',
  },
  riskLabel: {
    color: '#9CA3AF',
    fontSize: 14,
  },
  riskValue: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  strategyCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  strategyName: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  strategyMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 15,
  },
  strategyMetric: {
    alignItems: 'center',
  },
  strategyMetricLabel: {
    color: '#9CA3AF',
    fontSize: 12,
    marginBottom: 3,
  },
  strategyMetricValue: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  backtestCard: {
    backgroundColor: '#374151',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
  },
  backtestHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  backtestPeriod: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  backtestReturn: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  backtestDetails: {
    gap: 5,
  },
  backtestDetail: {
    color: '#9CA3AF',
    fontSize: 13,
  },
});