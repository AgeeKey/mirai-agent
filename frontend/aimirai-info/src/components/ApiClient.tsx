'use client';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface TradingSignal {
  id: string;
  symbol: string;
  signal: 'BUY' | 'SELL';
  confidence: number;
  price: number;
  timestamp: string;
  reason?: string;
}

export interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  status: 'OPEN' | 'CLOSED' | 'PARTIAL';
  timestamp: string;
}

export interface PortfolioStats {
  total_balance: number;
  available_balance: number;
  total_pnl: number;
  total_pnl_percent: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  active_positions: number;
  ai_score: number;
}

export interface ApiConfig {
  baseUrl: string;
  wsUrl: string;
  timeout: number;
}

const DEFAULT_CONFIG: ApiConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE || 'https://aimirai.online',
  wsUrl: process.env.NEXT_PUBLIC_API_BASE?.replace('https', 'wss') + '/ws' || 'wss://aimirai.online/ws',
  timeout: 10000,
};

class ApiClient {
  private config: ApiConfig;

  constructor(config: Partial<ApiConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.config.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: AbortSignal.timeout(this.config.timeout),
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || data.message || `HTTP ${response.status}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Неизвестная ошибка',
      };
    }
  }

  // Auth endpoints
  async login(username: string, password: string): Promise<ApiResponse<{ token: string; user: any }>> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(username: string, email: string, password: string): Promise<ApiResponse<{ message: string }>> {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  // Portfolio endpoints
  async getPortfolioStats(): Promise<ApiResponse<PortfolioStats>> {
    return this.request('/portfolio/stats');
  }

  async getPositions(): Promise<ApiResponse<Position[]>> {
    return this.request('/portfolio/positions');
  }

  // Trading endpoints
  async getTradingSignals(limit: number = 10): Promise<ApiResponse<TradingSignal[]>> {
    return this.request(`/trading/signals?limit=${limit}`);
  }

  async setTradingStatus(enabled: boolean): Promise<ApiResponse<{ status: string }>> {
    return this.request('/trading/status', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  async getTradingStatus(): Promise<ApiResponse<{ enabled: boolean; status: string }>> {
    return this.request('/trading/status');
  }

  // Settings endpoints
  async getSettings(): Promise<ApiResponse<any>> {
    return this.request('/settings');
  }

  async updateSettings(settings: any): Promise<ApiResponse<{ message: string }>> {
    return this.request('/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.request('/health');
  }
}

// Singleton instance
export const apiClient = new ApiClient();

// Custom hooks for API calls
export function useApi() {
  return {
    client: apiClient,
    
    // Wrapper functions with error handling
    async login(username: string, password: string) {
      const response = await apiClient.login(username, password);
      if (response.success && response.data?.token) {
        // Store token in localStorage
        localStorage.setItem('auth_token', response.data.token);
      }
      return response;
    },

    async register(username: string, email: string, password: string) {
      return apiClient.register(username, email, password);
    },

    async logout() {
      localStorage.removeItem('auth_token');
      window.location.href = '/';
    },

    getAuthToken() {
      if (typeof window !== 'undefined') {
        return localStorage.getItem('auth_token');
      }
      return null;
    },

    isAuthenticated() {
      return !!this.getAuthToken();
    },
  };
}