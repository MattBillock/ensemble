import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import ThemeSwitcher from './ThemeSwitcher';
import { ThemeProvider } from '../contexts/ThemeContext';

describe('ThemeSwitcher', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  const renderWithProvider = () =>
    render(
      <ThemeProvider>
        <ThemeSwitcher />
      </ThemeProvider>
    );

  it('should render dropdown toggle', () => {
    renderWithProvider();
    expect(screen.getByRole('button', { name: /dark/i })).toBeInTheDocument();
  });

  it('should display all theme options when opened', () => {
    renderWithProvider();
    fireEvent.click(screen.getByRole('button', { name: /dark/i }));
    expect(screen.getByText(/Light/)).toBeInTheDocument();
    expect(screen.getByText(/High Contrast/)).toBeInTheDocument();
  });

  it('should change data-theme attribute when theme is selected', () => {
    renderWithProvider();
    fireEvent.click(screen.getByRole('button', { name: /dark/i }));
    fireEvent.click(screen.getByText(/Light/));
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });
});
