'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

export interface WebSocketManagerProps {
  url?: string;
  onMessage?: (data: any) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export function useWebSocket({
  url = process.env.NEXT_PUBLIC_API_BASE?.replace('https', 'wss') + '/ws',
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: WebSocketManagerProps = {}) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    if (!url) return;

    const ws = new WebSocket(url);
    
    ws.onopen = () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
      onDisconnect?.();
    };

    ws.onerror = (error) => {
      setConnectionStatus('disconnected');
      onError?.(error);
    };

    setSocket(ws);
    setConnectionStatus('connecting');

    return () => {
      ws.close();
    };
  }, [url, onMessage, onConnect, onDisconnect, onError]);

  const sendMessage = (data: any) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(data));
    }
  };

  return {
    socket,
    isConnected,
    connectionStatus,
    sendMessage,
  };
}

export interface WebSocketStatusProps {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

export function WebSocketStatus({ isConnected, connectionStatus }: WebSocketStatusProps) {
  const statusColors = {
    connecting: 'bg-yellow-500',
    connected: 'bg-green-500',
    disconnected: 'bg-red-500',
  };

  const statusText = {
    connecting: 'Подключение...',
    connected: 'Подключено',
    disconnected: 'Отключено',
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex items-center space-x-2 text-sm"
    >
      <div className={`w-2 h-2 rounded-full ${statusColors[connectionStatus]}`} />
      <span className="text-gray-400">{statusText[connectionStatus]}</span>
    </motion.div>
  );
}