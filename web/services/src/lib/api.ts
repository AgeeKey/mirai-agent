// API client for Mirai Agent
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Trading interfaces
export interface TradingPosition {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  unrealizedPnl: number;
  margin: number;
  leverage: number;
  createdAt: string;
  updatedAt: string;
}

export interface TradingOrder {
  id: string;
  symbol: string;
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
  stopPrice?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  createdAt: string;
  updatedAt: string;
}

export interface PortfolioMetrics {
  totalBalance: number;
  availableBalance: number;
  unrealizedPnl: number;
  totalPnl: number;
  totalPnlPercent: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
  equity: number;
  drawdown: number;
  maxDrawdown: number;
  exposure: number;
  leverage: number;
  portfolioHealth: number;
  riskScore: number;
  lastUpdate: string;
}

export interface RiskMetrics {
  drawdown: number;
  maxDrawdown: number;
  exposure: number;
  leverage: number;
  portfolioHealth: number;
  riskScore: number;
  shieldLevel: 1 | 2 | 3 | 4 | 5;
  lastUpdate: Date;
}

export interface TradingStrategy {
  id: string;
  name: string;
  description: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  performance: {
    winRate: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    totalTrades: number;
    averageReturn: number;
  };
  parameters: Record<string, any>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Studio interfaces
export interface StudioProduct {
  id: string;
  type: 'strategy' | 'subscription' | 'nft' | 'course';
  name: string;
  description: string;
  price: number;
  currency: 'USD' | 'ETH' | 'BTC';
  rarity?: 'common' | 'rare' | 'epic' | 'legendary';
  performance?: any;
  tags: string[];
  isActive: boolean;
  sales: number;
  rating: number;
  createdAt: string;
  updatedAt: string;
}

export interface StudioSale {
  id: string;
  productId: string;
  buyerId: string;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  transactionHash?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StudioAnalytics {
  totalRevenue: number;
  monthlyRevenue: number;
  totalSales: number;
  monthlySales: number;
  topProducts: StudioProduct[];
  revenueByMonth: Array<{ month: string; revenue: number; sales: number }>;
  productPerformance: Array<{ productId: string; revenue: number; sales: number }>;
}

// Analytics interfaces
export interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  changePercent24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  marketCap?: number;
  lastUpdate: string;
}

export interface TechnicalIndicator {
  symbol: string;
  timeframe: string;
  indicator: string;
  value: number;
  signal: 'buy' | 'sell' | 'neutral';
  confidence: number;
  lastUpdate: string;
}

export interface AIAnalysis {
  symbol: string;
  prediction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  timeframe: string;
  reasoning: string;
  supportLevels: number[];
  resistanceLevels: number[];
  targetPrice: number;
  stopLoss: number;
  lastUpdate: string;
}

class ApiClient {
  private token: string | null = null;
  
  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
  const url = `${API_BASE}/api${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      console.error('API request failed:', error);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
    const response = await this.request<AuthResponse>('/auth/login/form', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (response.success && response.data?.access_token) {
      this.token = response.data.access_token;
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', this.token);
      }
    }

    return response;
  }

  logout() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  // Basic HTTP methods
  async get<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint);
  }

  async post<T = any>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async patch<T = any>(endpoint: string, data: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async delete<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }

  // System methods
  async getStatus(): Promise<ApiResponse> {
    return this.request('/status');
  }

  async getMetrics(): Promise<ApiResponse<PortfolioMetrics>> {
    return this.request('/metrics');
  }

  async killSwitch(): Promise<ApiResponse> {
    return this.request('/kill-switch', {
      method: 'POST',
    });
  }

  // Trading methods
  async getPositions(): Promise<ApiResponse<TradingPosition[]>> {
    return this.request('/trading/positions');
  }

  async getOrders(): Promise<ApiResponse<TradingOrder[]>> {
    return this.request('/trading/orders');
  }

  async createOrder(order: Partial<TradingOrder>): Promise<ApiResponse<TradingOrder>> {
    return this.request('/trading/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    });
  }

  async cancelOrder(orderId: string): Promise<ApiResponse> {
    return this.request(`/trading/orders/${orderId}`, {
      method: 'DELETE',
    });
  }

  async closePosition(positionId: string): Promise<ApiResponse> {
    return this.request(`/trading/positions/${positionId}/close`, {
      method: 'POST',
    });
  }

  async getStrategies(): Promise<ApiResponse<TradingStrategy[]>> {
    return this.request('/trading/strategies');
  }

  async createStrategy(strategy: Partial<TradingStrategy>): Promise<ApiResponse<TradingStrategy>> {
    return this.request('/trading/strategies', {
      method: 'POST',
      body: JSON.stringify(strategy),
    });
  }

  async updateStrategy(strategyId: string, updates: Partial<TradingStrategy>): Promise<ApiResponse<TradingStrategy>> {
    return this.request(`/trading/strategies/${strategyId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteStrategy(strategyId: string): Promise<ApiResponse> {
    return this.request(`/trading/strategies/${strategyId}`, {
      method: 'DELETE',
    });
  }

  async activateStrategy(strategyId: string): Promise<ApiResponse> {
    return this.request(`/trading/strategies/${strategyId}/activate`, {
      method: 'POST',
    });
  }

  async deactivateStrategy(strategyId: string): Promise<ApiResponse> {
    return this.request(`/trading/strategies/${strategyId}/deactivate`, {
      method: 'POST',
    });
  }

  // Risk management methods
  async getRiskConfig(): Promise<ApiResponse> {
    return this.request('/risk/config');
  }

  async updateRiskConfig(config: any): Promise<ApiResponse> {
    return this.request('/risk/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async getRiskMetrics(): Promise<ApiResponse<RiskMetrics>> {
    return this.request('/risk/metrics');
  }

  async updateShieldLevel(level: number): Promise<ApiResponse> {
    return this.request('/risk/shield-level', {
      method: 'POST',
      body: JSON.stringify({ level }),
    });
  }

  async emergencyStop(): Promise<ApiResponse> {
    return this.request('/risk/emergency-stop', {
      method: 'POST',
    });
  }

  // Studio monetization methods
  async getStudioProducts(): Promise<ApiResponse<StudioProduct[]>> {
    return this.request('/studio/products');
  }

  async createStudioProduct(product: Partial<StudioProduct>): Promise<ApiResponse<StudioProduct>> {
    return this.request('/studio/products', {
      method: 'POST',
      body: JSON.stringify(product),
    });
  }

  async updateStudioProduct(productId: string, updates: Partial<StudioProduct>): Promise<ApiResponse<StudioProduct>> {
    return this.request(`/studio/products/${productId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteStudioProduct(productId: string): Promise<ApiResponse> {
    return this.request(`/studio/products/${productId}`, {
      method: 'DELETE',
    });
  }

  async getStudioSales(): Promise<ApiResponse<StudioSale[]>> {
    return this.request('/studio/sales');
  }

  async getStudioAnalytics(): Promise<ApiResponse<StudioAnalytics>> {
    return this.request('/studio/analytics');
  }

  async purchaseProduct(productId: string, paymentMethod: string): Promise<ApiResponse<StudioSale>> {
    return this.request('/studio/purchase', {
      method: 'POST',
      body: JSON.stringify({ productId, paymentMethod }),
    });
  }

  // Analytics methods
  async getMarketData(symbols?: string[]): Promise<ApiResponse<MarketData[]>> {
    const params = symbols ? `?symbols=${symbols.join(',')}` : '';
    return this.request(`/analytics/market-data${params}`);
  }

  async getTechnicalIndicators(symbol: string, timeframe: string): Promise<ApiResponse<TechnicalIndicator[]>> {
    return this.request(`/analytics/technical-indicators?symbol=${symbol}&timeframe=${timeframe}`);
  }

  async getAIAnalysis(symbol: string): Promise<ApiResponse<AIAnalysis>> {
    return this.request(`/analytics/ai-analysis?symbol=${symbol}`);
  }

  async getPerformanceAnalytics(period: string = '30d'): Promise<ApiResponse> {
    return this.request(`/analytics/performance?period=${period}`);
  }

  async getPortfolioAnalytics(): Promise<ApiResponse> {
    return this.request('/analytics/portfolio');
  }

  // WebSocket connection helper
  createWebSocket(endpoint: string): WebSocket | null {
    if (typeof window === 'undefined') return null;
    
    const wsUrl = `${API_BASE.replace('http', 'ws')}/ws${endpoint}`;
    const ws = new WebSocket(wsUrl);
    
    if (this.token) {
      ws.addEventListener('open', () => {
        ws.send(JSON.stringify({ type: 'auth', token: this.token }));
      });
    }
    
    return ws;
  }

  // Real-time trading data WebSocket
  connectTradingWebSocket(): WebSocket | null {
    return this.createWebSocket('/trading');
  }

  // Real-time market data WebSocket
  connectMarketWebSocket(): WebSocket | null {
    return this.createWebSocket('/market');
  }

  // Real-time analytics WebSocket
  connectAnalyticsWebSocket(): WebSocket | null {
    return this.createWebSocket('/analytics');
  }
}

export const api = new ApiClient();
export const apiClient = api;
