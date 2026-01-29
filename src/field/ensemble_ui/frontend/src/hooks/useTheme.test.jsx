import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { useTheme } from './useTheme';
import { ThemeProvider } from '../contexts/ThemeContext';

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>;

  it('should return dark theme by default', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    expect(result.current.themeName).toBe('dark');
  });

  it('should load theme from localStorage', () => {
    localStorage.setItem('ensemble_theme', 'light');
    const { result } = renderHook(() => useTheme(), { wrapper });
    expect(result.current.themeName).toBe('light');
  });

  it('should persist theme to localStorage on change', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    act(() => {
      result.current.setTheme('high-contrast');
    });
    expect(result.current.themeName).toBe('high-contrast');
    expect(localStorage.getItem('ensemble_theme')).toBe('high-contrast');
  });

  it('should set data-theme attribute on documentElement', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    act(() => {
      result.current.setTheme('light');
    });
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('should provide availableThemes', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    expect(result.current.availableThemes).toHaveLength(3);
    expect(result.current.availableThemes.map(t => t.name)).toEqual(['dark', 'light', 'high-contrast']);
  });

  it('should ignore invalid theme names', () => {
    const { result } = renderHook(() => useTheme(), { wrapper });
    act(() => {
      result.current.setTheme('invalid-theme');
    });
    expect(result.current.themeName).toBe('dark');
  });

  it('should throw when used outside ThemeProvider', () => {
    expect(() => {
      renderHook(() => useTheme());
    }).toThrow('useTheme must be used within a ThemeProvider');
  });
});
