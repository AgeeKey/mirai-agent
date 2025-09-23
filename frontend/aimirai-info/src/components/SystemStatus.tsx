'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ClockIcon 
} from '@heroicons/react/24/outline';

export interface SystemStatus {
  api: 'online' | 'offline' | 'loading';
  trading: 'active' | 'inactive' | 'error';
  database: 'connected' | 'disconnected' | 'unknown';
  websocket: 'connected' | 'disconnected' | 'connecting';
  lastUpdate: Date;
}

export interface SystemStatusProps {
  onStatusChange?: (status: SystemStatus) => void;
}

export function SystemStatusIndicator({ onStatusChange }: SystemStatusProps) {
  const [status, setStatus] = useState<SystemStatus>({
    api: 'loading',
    trading: 'inactive',
    database: 'unknown',
    websocket: 'disconnected',
    lastUpdate: new Date(),
  });

  const checkSystemStatus = async () => {
    try {
      // Проверка API
      const apiResponse = await fetch('https://aimirai.online/health', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
      });

      const newStatus: SystemStatus = {
        api: apiResponse.ok ? 'online' : 'offline',
        trading: 'inactive', // Будет обновлено через WebSocket
        database: 'unknown', // Будет обновлено из API response
        websocket: 'disconnected', // Будет обновлено WebSocket manager
        lastUpdate: new Date(),
      };

      if (apiResponse.ok) {
        const data = await apiResponse.json();
        newStatus.database = data.database_status === 'ok' ? 'connected' : 'disconnected';
        newStatus.trading = data.trading_status === 'active' ? 'active' : 'inactive';
      }

      setStatus(newStatus);
      onStatusChange?.(newStatus);
    } catch (error) {
      const errorStatus: SystemStatus = {
        api: 'offline',
        trading: 'error',
        database: 'disconnected',
        websocket: 'disconnected',
        lastUpdate: new Date(),
      };
      setStatus(errorStatus);
      onStatusChange?.(errorStatus);
    }
  };

  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 30000); // Проверка каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (componentStatus: string) => {
    switch (componentStatus) {
      case 'online':
      case 'active':
      case 'connected':
        return 'text-green-400';
      case 'offline':
      case 'error':
      case 'disconnected':
        return 'text-red-400';
      case 'loading':
      case 'connecting':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusIcon = (componentStatus: string) => {
    switch (componentStatus) {
      case 'online':
      case 'active':
      case 'connected':
        return CheckCircleIcon;
      case 'offline':
      case 'error':
      case 'disconnected':
        return XCircleIcon;
      case 'loading':
      case 'connecting':
        return ClockIcon;
      default:
        return ExclamationTriangleIcon;
    }
  };

  const statusItems = [
    { label: 'API', status: status.api },
    { label: 'Trading', status: status.trading },
    { label: 'Database', status: status.database },
    { label: 'WebSocket', status: status.websocket },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-4"
    >
      <h3 className="text-sm font-medium text-gray-300 mb-3">Статус системы</h3>
      <div className="grid grid-cols-2 gap-3">
        {statusItems.map((item) => {
          const IconComponent = getStatusIcon(item.status);
          return (
            <div key={item.label} className="flex items-center space-x-2">
              <IconComponent className={`h-4 w-4 ${getStatusColor(item.status)}`} />
              <span className="text-xs text-gray-300">{item.label}</span>
              <span className={`text-xs font-medium ${getStatusColor(item.status)}`}>
                {item.status}
              </span>
            </div>
          );
        })}
      </div>
      <div className="mt-3 pt-3 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          Обновлено: {status.lastUpdate.toLocaleTimeString('ru-RU')}
        </div>
      </div>
    </motion.div>
  );
}

export function useSystemStatus() {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  return {
    status,
    setStatus,
    isOnline: status?.api === 'online',
    isTradingActive: status?.trading === 'active',
    isFullyOperational: 
      status?.api === 'online' && 
      status?.trading === 'active' && 
      status?.database === 'connected' &&
      status?.websocket === 'connected',
  };
}