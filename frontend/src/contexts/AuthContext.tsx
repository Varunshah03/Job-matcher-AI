// AuthContext.tsx - Global authentication context for managing user state
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { onAuthStateChanged, signOut, User } from 'firebase/auth';
import { auth } from '../firebase/config';

// Define the shape of our auth context
interface AuthContextType {
  currentUser: User | null;
  logout: () => Promise<void>;
  loading: boolean;
}

// Create the authentication context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use the auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Props for the AuthProvider component
interface AuthProviderProps {
  children: ReactNode;
}

// Authentication provider component that wraps the entire app
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User | null>(null); // Current authenticated user
  const [loading, setLoading] = useState(true); // Loading state during auth check

  useEffect(() => {
    // Listen for authentication state changes
    // This runs whenever user logs in, logs out, or page refreshes
    const unsubscribe = onAuthStateChanged(auth, (user: User | null) => {
      setCurrentUser(user); // Set the current user (null if not authenticated)
      setLoading(false); // Authentication check is complete
    });

    // Cleanup subscription on unmount
    return unsubscribe;
  }, []);

  // Function to log out the current user
  const logout = async (): Promise<void> => {
    await signOut(auth);
  };

  // Values provided to all components that use this context
  const value: AuthContextType = {
    currentUser,    // Current user object or null
    logout,         // Function to log out
    loading         // Loading state
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children} {/* Only render children when auth check is complete */}
    </AuthContext.Provider>
  );
};