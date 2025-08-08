// Component to protect routes that require authentication
import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import AuthForms from './AuthForms';

const ProtectedRoute = ({ children }) => {
  const { currentUser } = useAuth();

  // If user is authenticated, show the protected content
  // If not authenticated, show the authentication forms
  return currentUser ? children : <AuthForms />;
};

export default ProtectedRoute;