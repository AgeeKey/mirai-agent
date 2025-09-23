import React, { useState, useEffect } from 'react';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import NotificationSettingsScreen from './src/screens/NotificationSettingsScreen';
import { Text, View, StyleSheet } from 'react-native';

type Screen = 'login' | 'register' | 'dashboard' | 'analytics' | 'notifications';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('login');
  const [authToken, setAuthToken] = useState<string | null>(null);

  const handleLogin = (token: string) => {
    setAuthToken(token);
    setCurrentScreen('dashboard');
  };

  const handleRegister = (token: string) => {
    setAuthToken(token);
    setCurrentScreen('dashboard');
  };

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentScreen('login');
  };

  const showRegister = () => {
    setCurrentScreen('register');
  };

  const showLogin = () => {
    setCurrentScreen('login');
  };

  const showNotificationSettings = () => {
    setCurrentScreen('notifications');
  };

  const showAnalytics = () => {
    setCurrentScreen('analytics');
  };

  const showDashboard = () => {
    setCurrentScreen('dashboard');
  };

  if (currentScreen === 'notifications' && authToken) {
    return <NotificationSettingsScreen onBack={showDashboard} />;
  }

  if (currentScreen === 'analytics' && authToken) {
    return <AnalyticsScreen token={authToken} onBack={showDashboard} />;
  }

  if (currentScreen === 'dashboard' && authToken) {
    return (
      <DashboardScreen 
        onLogout={handleLogout} 
        onShowAnalytics={showAnalytics} 
        onShowNotificationSettings={showNotificationSettings}
        token={authToken} 
      />
    );
  }

  if (currentScreen === 'register') {
    return (
      <RegisterScreen 
        onRegister={handleRegister}
        onBack={showLogin}
      />
    );
  }

  return (
    <LoginScreen 
      onLogin={handleLogin}
      onShowRegister={showRegister}
    />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
});