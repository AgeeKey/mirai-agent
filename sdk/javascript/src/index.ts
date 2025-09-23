/**
 * Mirai Trading SDK for JavaScript/TypeScript
 * Official client library for the Mirai Trading System
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import { EventEmitter } from 'eventemitter3';
import WebSocket from 'ws';

// Type definitions
export interface MiraiConfig {
    apiUrl?: string;
    apiKey?: string;
    timeout?: number;
    maxRetries?: number;
    retryDelay?: number;
    enableLogging?: boolean;
}

export interface TradingStatus {
    is_active: boolean;
    mode: string;
    balance: {
        total: number;
        available: number;
        used: number;
    };
    daily_pnl: number;
    win_rate: number;
    risk_level: string;
    ai_confidence: number;
    strategies: Record<string, {
        status: string;
        win_rate: number;
    }>;
}

export interface Trade {
    id: number;
    symbol: string;
    action: string;
    price: number;
    quantity: number;
    pnl: number;
    timestamp: string;
    strategy: string;
}

export interface Position {
    symbol: string;
    side: string;
    size: number;
    entry_price: number;
    current_price: number;
    unrealized_pnl: number;
    margin_used: number;
    leverage: number;
}

export interface AISignal {
    symbol: string;
    direction: string;
    strength: number;
    confidence: number;
    strategy: string;
    timestamp: string;
    reasoning?: string;
}

export interface Order {
    symbol: string;
    side: string;
    type: string;
    quantity: number;
    price?: number;
    stop_loss?: number;
    take_profit?: number;
}

export interface OrderResult {
    order_id: string;
    status: string;
    symbol: string;
    side: string;
    executed_price?: number;
    executed_quantity: number;
    timestamp: string;
}

export interface Alert {
    id: string;
    type: string;
    severity: string;
    message: string;
    timestamp: string;
    symbol?: string;
}

export interface PerformanceSummary {
    connection_pools: Record<string, any>;
    cache_performance: {
        hit_rate: number;
        total_requests: number;
        memory_items: number;
    };
    task_management: {
        active_tasks: number;
        completed_tasks: number;
        success_rate: number;
    };
}

// Custom error classes
export class MiraiError extends Error {
    public readonly errorCode?: string;
    public readonly statusCode?: number;

    constructor(message: string, errorCode?: string, statusCode?: number) {
        super(message);
        this.name = 'MiraiError';
        this.errorCode = errorCode;
        this.statusCode = statusCode;
    }
}

export class MiraiAPIError extends MiraiError {
    constructor(message: string, errorCode?: string, statusCode?: number) {
        super(message, errorCode, statusCode);
        this.name = 'MiraiAPIError';
    }
}

export class MiraiConnectionError extends MiraiError {
    constructor(message: string) {
        super(message);
        this.name = 'MiraiConnectionError';
    }
}

export class MiraiRateLimitError extends MiraiError {
    constructor(message: string) {
        super(message);
        this.name = 'MiraiRateLimitError';
    }
}

// WebSocket client for real-time data
export class MiraiWebSocketClient extends EventEmitter {
    private ws: WebSocket | null = null;
    private wsUrl: string;
    private reconnectDelay = 1000;
    private maxReconnectDelay = 30000;
    private running = false;

    constructor(wsUrl: string) {
        super();
        this.wsUrl = wsUrl;
    }

    public connect(): Promise<void> {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.wsUrl);
                this.running = true;

                this.ws.on('open', () => {
                    this.reconnectDelay = 1000; // Reset delay on successful connection
                    this.emit('connected');
                    resolve();
                });

                this.ws.on('message', (data: WebSocket.Data) => {
                    try {
                        const message = JSON.parse(data.toString());
                        this.emit('message', message);

                        // Emit specific event types
                        if (message.type) {
                            this.emit(message.type, message.data || message);
                        }
                    } catch (error) {
                        this.emit('error', new Error(`Invalid JSON received: ${error}`));
                    }
                });

                this.ws.on('close', () => {
                    this.emit('disconnected');
                    if (this.running) {
                        this.reconnect();
                    }
                });

                this.ws.on('error', (error) => {
                    this.emit('error', error);
                    reject(error);
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    private reconnect(): void {
        if (!this.running) return;

        setTimeout(() => {
            this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
            this.connect().catch(() => {
                // Connection failed, will retry again
            });
        }, this.reconnectDelay);
    }

    public disconnect(): void {
        this.running = false;
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    public send(data: any): void {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

// Main Mirai client
export class MiraiClient {
    private config: Required<MiraiConfig>;
    private httpClient: AxiosInstance;
    private wsClient: MiraiWebSocketClient;

    constructor(config: MiraiConfig = {}) {
        // Default configuration
        this.config = {
            apiUrl: config.apiUrl || 'http://localhost:8001',
            apiKey: config.apiKey || '',
            timeout: config.timeout || 30000,
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 1000,
            enableLogging: config.enableLogging !== false,
        };

        // Setup HTTP client
        this.httpClient = axios.create({
            baseURL: this.config.apiUrl,
            timeout: this.config.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'MiraiSDK/1.0.0 (JavaScript)',
                ...(this.config.apiKey && { Authorization: `Bearer ${this.config.apiKey}` }),
            },
        });

        // Setup request/response interceptors
        this.setupInterceptors();

        // Setup WebSocket client
        const wsUrl = this.config.apiUrl.replace(/^http/, 'ws') + '/ws';
        this.wsClient = new MiraiWebSocketClient(wsUrl);

        if (this.config.enableLogging) {
            console.log('Mirai SDK initialized (JavaScript/TypeScript v1.0.0)');
        }
    }

    private setupInterceptors(): void {
        // Request interceptor
        this.httpClient.interceptors.request.use(
            (config) => {
                if (this.config.enableLogging) {
                    console.log(`Making request: ${config.method?.toUpperCase()} ${config.url}`);
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor
        this.httpClient.interceptors.response.use(
            (response) => response,
            async (error: AxiosError) => {
                const originalRequest = error.config as any;

                // Handle rate limiting
                if (error.response?.status === 429 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    const retryAfter = parseInt(error.response.headers['retry-after'] || '60', 10);

                    if (this.config.enableLogging) {
                        console.warn(`Rate limited, retrying in ${retryAfter}s`);
                    }

                    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
                    return this.httpClient(originalRequest);
                }

                // Handle other errors with retry
                if (!originalRequest._retry && this.shouldRetry(error)) {
                    originalRequest._retry = true;
                    originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

                    if (originalRequest._retryCount <= this.config.maxRetries) {
                        const delay = this.config.retryDelay * Math.pow(2, originalRequest._retryCount - 1);

                        if (this.config.enableLogging) {
                            console.warn(`Request failed, retrying in ${delay}ms`);
                        }

                        await new Promise(resolve => setTimeout(resolve, delay));
                        return this.httpClient(originalRequest);
                    }
                }

                return Promise.reject(this.createError(error));
            }
        );
    }

    private shouldRetry(error: AxiosError): boolean {
        // Retry on network errors or 5xx status codes
        return !error.response || (error.response.status >= 500);
    }

    private createError(error: AxiosError): MiraiError {
        if (!error.response) {
            return new MiraiConnectionError(`Connection failed: ${error.message}`);
        }

        const status = error.response.status;
        const data = error.response.data as any;

        if (status === 429) {
            return new MiraiRateLimitError('Rate limit exceeded');
        }

        const message = data?.error?.message || `HTTP ${status}`;
        const errorCode = data?.error?.code;

        return new MiraiAPIError(message, errorCode, status);
    }

    // Health & Status Methods
    public async getHealth(): Promise<{ status: string; timestamp: string }> {
        const response = await this.httpClient.get('/api/health');
        return response.data;
    }

    public async getTradingStatus(): Promise<TradingStatus> {
        const response = await this.httpClient.get('/api/trading/status');
        return response.data;
    }

    // Trading Data Methods
    public async getPerformanceData(): Promise<{ performance: Array<any> }> {
        const response = await this.httpClient.get('/api/trading/performance');
        return response.data;
    }

    public async getRecentTrades(options: {
        limit?: number;
        symbol?: string;
        strategy?: string;
    } = {}): Promise<{ trades: Trade[] }> {
        const response = await this.httpClient.get('/api/trading/trades', {
            params: options,
        });
        return response.data;
    }

    public async getPositions(): Promise<{ positions: Position[] }> {
        const response = await this.httpClient.get('/api/trading/positions');
        return response.data;
    }

    // Order Management Methods
    public async placeOrder(order: Order): Promise<OrderResult> {
        const response = await this.httpClient.post('/api/trading/order', order);
        return response.data;
    }

    public async placeMarketOrder(params: {
        symbol: string;
        side: string;
        quantity: number;
        stopLoss?: number;
        takeProfit?: number;
    }): Promise<OrderResult> {
        const order: Order = {
            symbol: params.symbol,
            side: params.side,
            type: 'MARKET',
            quantity: params.quantity,
            stop_loss: params.stopLoss,
            take_profit: params.takeProfit,
        };
        return this.placeOrder(order);
    }

    public async placeLimitOrder(params: {
        symbol: string;
        side: string;
        quantity: number;
        price: number;
        stopLoss?: number;
        takeProfit?: number;
    }): Promise<OrderResult> {
        const order: Order = {
            symbol: params.symbol,
            side: params.side,
            type: 'LIMIT',
            quantity: params.quantity,
            price: params.price,
            stop_loss: params.stopLoss,
            take_profit: params.takeProfit,
        };
        return this.placeOrder(order);
    }

    // AI & Analysis Methods
    public async getAISignals(): Promise<{ signals: AISignal[] }> {
        const response = await this.httpClient.get('/api/ai/signals');
        return response.data;
    }

    public async getAIAnalysis(symbol: string): Promise<any> {
        const response = await this.httpClient.get(`/api/ai/analysis/${symbol}`);
        return response.data;
    }

    // Monitoring Methods
    public async getMetrics(): Promise<string> {
        const response = await this.httpClient.get('/api/metrics');
        return response.data;
    }

    public async getAlerts(): Promise<{ alerts: Alert[] }> {
        const response = await this.httpClient.get('/api/alerts');
        return response.data;
    }

    // Performance Methods
    public async getPerformanceSummary(): Promise<{ status: string; data: PerformanceSummary }> {
        const response = await this.httpClient.get('/api/performance/summary');
        return response.data;
    }

    public async getCacheStats(): Promise<any> {
        const response = await this.httpClient.get('/api/performance/cache/stats');
        return response.data;
    }

    public async invalidateCache(pattern: string): Promise<{ status: string; message: string }> {
        const response = await this.httpClient.post('/api/performance/cache/invalidate', {
            pattern,
        });
        return response.data;
    }

    // WebSocket Methods
    public async connectWebSocket(): Promise<void> {
        return this.wsClient.connect();
    }

    public disconnectWebSocket(): void {
        this.wsClient.disconnect();
    }

    public subscribeTrades(callback: (data: any) => void): void {
        this.wsClient.on('trade_update', callback);
    }

    public subscribePrices(callback: (data: any) => void): void {
        this.wsClient.on('price_update', callback);
    }

    public subscribeSignals(callback: (data: any) => void): void {
        this.wsClient.on('ai_signal', callback);
    }

    public subscribeAll(callback: (data: any) => void): void {
        this.wsClient.on('message', callback);
    }

    public unsubscribeTrades(callback: (data: any) => void): void {
        this.wsClient.off('trade_update', callback);
    }

    public unsubscribePrices(callback: (data: any) => void): void {
        this.wsClient.off('price_update', callback);
    }

    public unsubscribeSignals(callback: (data: any) => void): void {
        this.wsClient.off('ai_signal', callback);
    }

    // Utility Methods
    public async waitForOrder(orderId: string, timeout: number = 60000): Promise<Trade | null> {
        const startTime = Date.now();

        while (Date.now() - startTime < timeout) {
            try {
                const { trades } = await this.getRecentTrades({ limit: 10 });
                const trade = trades.find(t => (t as any).order_id === orderId);

                if (trade) {
                    return trade;
                }

                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch (error) {
                if (this.config.enableLogging) {
                    console.warn(`Error polling for order ${orderId}:`, error);
                }
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        }

        return null;
    }

    // Configuration
    public setApiKey(apiKey: string): void {
        this.config.apiKey = apiKey;
        this.httpClient.defaults.headers['Authorization'] = `Bearer ${apiKey}`;
    }

    public getConfig(): Readonly<Required<MiraiConfig>> {
        return { ...this.config };
    }
}

// Convenience functions
export function createClient(config?: MiraiConfig): MiraiClient {
    return new MiraiClient(config);
}

// Default export
export default MiraiClient;