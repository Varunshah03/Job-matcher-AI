// App.tsx
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/toaster';

// Import your existing components with correct paths
import Index from './pages/Index'; // Your main homepage
import Profile from './components/Profile'; // Profile component
import AuthForms from './components/AuthForms'; // Auth component
import NotFound from './pages/NotFound'; // 404 page

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return currentUser ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route Component (redirects to home if already authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentUser, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return currentUser ? <Navigate to="/" replace /> : <>{children}</>;
};

// Main App Routes Component
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route 
        path="/login" 
        element={
          <PublicRoute>
            <AuthForms />
          </PublicRoute>
        } 
      />
      <Route 
        path="/register" 
        element={
          <PublicRoute>
            <AuthForms />
          </PublicRoute>
        } 
      />
      <Route 
        path="/signup" 
        element={<Navigate to="/register" replace />} 
      />

      {/* Protected Routes */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <Index />
          </ProtectedRoute>
        } 
      />
      <Route 
        path="/home" 
        element={<Navigate to="/" replace />} 
      />
      <Route 
        path="/dashboard" 
        element={<Navigate to="/" replace />} 
      />
      <Route 
        path="/profile" 
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        } 
      />

      {/* 404 Not Found - keep this as the last route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

// Main App Component
const App: React.FC = () => {
  return (
    <AuthProvider>
      <div className="App min-h-screen bg-gray-50">
        <AppRoutes />
        
        {/* Toast notifications */}
        <Toaster />
      </div>
    </AuthProvider>
  );
};

export default App;