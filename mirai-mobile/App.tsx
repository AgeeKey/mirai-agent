import React, { useState, useEffect } from 'react';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import { Text, View, StyleSheet } from 'react-native';

type Screen = 'login' | 'register' | 'dashboard';

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

  if (currentScreen === 'dashboard' && authToken) {
    return <DashboardScreen onLogout={handleLogout} token={authToken} />;
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
