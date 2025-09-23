// API Configuration
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8002',
  ENDPOINTS: {
    // Auth
    LOGIN: '/auth/login',
    REGISTER: '/auth/register', 
    ME: '/auth/me',
    
    // Trading
    PORTFOLIO: '/trading/portfolio',
    SIGNALS: '/trading/signals',
    
    // Analytics
    PERFORMANCE: '/analytics/performance',
    RISK: '/analytics/risk',
    STRATEGIES: '/analytics/strategies',
    BACKTESTING: '/analytics/backtesting',
    DETAILED_REPORT: '/analytics/detailed-report'
  }
};

// Helper function to build full URL
export const buildUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};