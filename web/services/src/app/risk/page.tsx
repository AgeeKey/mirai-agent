'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/Card';
import { apiClient } from '@/lib/api';
import Link from 'next/link';

interface RiskConfig {
  MAX_TRADES_PER_DAY: number;
  COOLDOWN_SEC: number;
  DAILY_MAX_LOSS_USDT: number;
  DAILY_TRAIL_DRAWDOWN: number;
  ADVISOR_THRESHOLD: number;
}

export default function RiskPage() {
  const [config, setConfig] = useState<RiskConfig | null>(null);
  const [editedConfig, setEditedConfig] = useState<RiskConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const data = await apiClient.get('/risk/config');
        setConfig(data.data);
        setEditedConfig(data.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch config');
      } finally {
        setIsLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const handleSave = async () => {
    if (!editedConfig) return;

    setIsSaving(true);
    setError('');
    setSuccessMessage('');

    try {
      const updatedConfig = await apiClient.patch('/risk/config', editedConfig);
      setConfig(updatedConfig.data);
      setEditedConfig(updatedConfig.data);
      setSuccessMessage('Risk configuration updated successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update config');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setEditedConfig(config);
    setError('');
    setSuccessMessage('');
  };

  const handleChange = (key: keyof RiskConfig, value: number) => {
    if (!editedConfig) return;
    setEditedConfig({ ...editedConfig, [key]: value });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading risk configuration...</p>
        </div>
      </div>
    );
  }

  const hasChanges = JSON.stringify(config) !== JSON.stringify(editedConfig);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-2xl font-bold text-gray-900">Risk Configuration</h1>
            <div className="flex space-x-4">
              <Link href="/dashboard" className="text-indigo-600 hover:text-indigo-800">
                ← Dashboard
              </Link>
              <Link href="/orders" className="text-indigo-600 hover:text-indigo-800">
                Orders
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
            {successMessage}
          </div>
        )}

        <Card title="Risk Management Settings">
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Trades Per Day
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={editedConfig?.MAX_TRADES_PER_DAY || 0}
                  onChange={(e) => handleChange('MAX_TRADES_PER_DAY', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Maximum number of trades allowed per day
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cooldown Period (seconds)
                </label>
                <input
                  type="number"
                  min="0"
                  value={editedConfig?.COOLDOWN_SEC || 0}
                  onChange={(e) => handleChange('COOLDOWN_SEC', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Minimum time between trades
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Max Loss (USDT)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={editedConfig?.DAILY_MAX_LOSS_USDT || 0}
                  onChange={(e) => handleChange('DAILY_MAX_LOSS_USDT', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Maximum loss allowed per day in USDT
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Daily Trail Drawdown
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={editedConfig?.DAILY_TRAIL_DRAWDOWN || 0}
                  onChange={(e) => handleChange('DAILY_TRAIL_DRAWDOWN', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Maximum trailing drawdown (0.05 = 5%)
                </p>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Advisor Threshold
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={editedConfig?.ADVISOR_THRESHOLD || 0}
                  onChange={(e) => handleChange('ADVISOR_THRESHOLD', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Minimum advisor score required for trade execution (0.6 = 60%)
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                onClick={handleReset}
                disabled={!hasChanges || isSaving}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || isSaving}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>
        </Card>

        <div className="mt-8">
          <Card title="Current Configuration Summary">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 rounded">
                <div className="text-2xl font-bold text-blue-600">{config?.MAX_TRADES_PER_DAY}</div>
                <div className="text-sm text-gray-600">Max Daily Trades</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">${config?.DAILY_MAX_LOSS_USDT}</div>
                <div className="text-sm text-gray-600">Max Daily Loss</div>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded">
                <div className="text-2xl font-bold text-purple-600">{((config?.ADVISOR_THRESHOLD || 0) * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-600">Advisor Threshold</div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}