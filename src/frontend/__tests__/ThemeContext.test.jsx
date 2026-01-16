import React from 'react';
import { render, renderHook, act } from '@testing-library/react';
import { ThemeProvider, useTheme } from '../contexts/ThemeContext';

describe('ThemeContext', () => {
  // Test initial theme state
  test('initial theme state should be default light theme', () => {
    const { result } = renderHook(() => useTheme(), { 
      wrapper: ({ children }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )
    });

    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
  });

  // Test theme switching mechanism
  test('toggleTheme should switch between light and dark themes', () => {
    const { result } = renderHook(() => useTheme(), { 
      wrapper: ({ children }) => (
        <ThemeProvider>{children}</ThemeProvider>
      )
    });

    // Initial state check
    expect(result.current.theme).toBe('light');

    // Switch to dark theme
    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDarkMode).toBe(true);

    // Switch back to light theme
    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('light');
    expect(result.current.isDarkMode).toBe(false);
  });

  // Test theme persistence
  test('theme should persist across component re-renders', () => {
    const TestComponent = () => {
      const { theme, toggleTheme } = useTheme();
      return (
        <div>
          <span data-testid="current-theme">{theme}</span>
          <button onClick={toggleTheme}>Toggle Theme</button>
        </div>
      );
    };

    const { getByTestId, getByText } = render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    );

    // Initial theme check
    expect(getByTestId('current-theme').textContent).toBe('light');

    // Toggle theme
    act(() => {
      getByText('Toggle Theme').click();
    });

    // Verify theme change persists
    expect(getByTestId('current-theme').textContent).toBe('dark');
  });

  // Validate ThemeProvider component
  test('ThemeProvider should provide complete theme context', () => {
    const TestConsumer = () => {
      const themeContext = useTheme();
      
      expect(themeContext).toHaveProperty('theme');
      expect(themeContext).toHaveProperty('isDarkMode');
      expect(themeContext).toHaveProperty('toggleTheme');
      
      return null;
    };

    render(
      <ThemeProvider>
        <TestConsumer />
      </ThemeProvider>
    );
  });

  // Ensure correct context consumption
  test('multiple components can consume theme context simultaneously', () => {
    const ComponentA = () => {
      const { theme } = useTheme();
      return <div data-testid="component-a-theme">{theme}</div>;
    };

    const ComponentB = () => {
      const { isDarkMode } = useTheme();
      return <div data-testid="component-b-mode">{isDarkMode.toString()}</div>;
    };

    const { getByTestId } = render(
      <ThemeProvider>
        <ComponentA />
        <ComponentB />
      </ThemeProvider>
    );

    expect(getByTestId('component-a-theme').textContent).toBe('light');
    expect(getByTestId('component-b-mode').textContent).toBe('false');
  });
});