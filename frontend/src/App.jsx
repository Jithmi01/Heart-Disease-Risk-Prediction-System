import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import Dashboard from './pages/Dashboard';
import PredictionForm from './pages/PredictionForm';
import UserProfile from './pages/UserProfile';

function AppContent() {
  const [currentPage, setCurrentPage] = useState('home');
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Not logged in - show public pages
  if (!token) {
    if (currentPage === 'login') {
      return <LoginPage onNavigate={setCurrentPage} />;
    }
    if (currentPage === 'register') {
      return <RegisterPage onNavigate={setCurrentPage} />;
    }
    return <HomePage onNavigate={setCurrentPage} />;
  }

  // Logged in - show protected pages
  if (currentPage === 'profile') {
    return <UserProfile onNavigate={setCurrentPage} />;
  }
  if (currentPage === 'predict') {
    return <PredictionForm onNavigate={setCurrentPage} />;
  }
  return <Dashboard onNavigate={setCurrentPage} />;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
