import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Try to get theme from localStorage, fallback to 'light'
    try {
      const savedTheme = localStorage.getItem('theme');
      return savedTheme === 'dark' ? 'dark' : 'light';
    } catch {
      return 'light';
    }
  });

  // Update data attribute and localStorage when theme changes
  useEffect(() => {
    // Set data attribute on document element for CSS styling
    document.documentElement.setAttribute('data-theme', theme);
    
    // Persist theme to localStorage
    try {
      localStorage.setItem('theme', theme);
    } catch {
      // Ignore localStorage errors (e.g., in private mode)
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  const isDarkMode = theme === 'dark';

  const value = {
    theme,
    isDarkMode,
    toggleTheme
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};