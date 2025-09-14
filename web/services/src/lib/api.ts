// API client for Mirai Agent
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

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
    const url = `${API_BASE}${endpoint}`;
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

  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
    const response = await this.request<AuthResponse>('/auth/login', {
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

  async getStatus(): Promise<ApiResponse> {
    return this.request('/status');
  }

  async get<T = any>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint);
  }

  async patch<T = any>(endpoint: string, data: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async getMetrics(): Promise<ApiResponse> {
    return this.request('/metrics');
  }

  async getRiskConfig(): Promise<ApiResponse> {
    return this.request('/risk');
  }

  async updateRiskConfig(config: any): Promise<ApiResponse> {
    return this.request('/risk', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async getOrders(): Promise<ApiResponse> {
    return this.request('/orders');
  }

  async killSwitch(): Promise<ApiResponse> {
    return this.request('/kill-switch', {
      method: 'POST',
    });
  }

  logout() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }
}

export const api = new ApiClient();
export const apiClient = api;
