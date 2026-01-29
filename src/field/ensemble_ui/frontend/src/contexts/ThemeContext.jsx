import React, { createContext, useState, useEffect } from 'react';

const STORAGE_KEY = 'ensemble_theme';
const DEFAULT_THEME = 'dark';

export const availableThemes = [
  { name: 'dark', label: 'Dark', icon: '🌙' },
  { name: 'light', label: 'Light', icon: '☀️' },
  { name: 'high-contrast', label: 'High Contrast', icon: '👁️' }
];

export const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [themeName, setThemeNameState] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored && availableThemes.some(t => t.name === stored) ? stored : DEFAULT_THEME;
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem(STORAGE_KEY, themeName);
  }, [themeName]);

  const setTheme = (name) => {
    if (availableThemes.some(t => t.name === name)) {
      setThemeNameState(name);
    }
  };

  return (
    <ThemeContext.Provider value={{ themeName, setTheme, availableThemes }}>
      {children}
    </ThemeContext.Provider>
  );
}
