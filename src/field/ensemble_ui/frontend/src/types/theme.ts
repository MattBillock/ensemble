/**
 * TypeScript theme type definitions and predefined theme objects
 */

export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  text: string;
  border: string;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
}

// Light Theme - bright background, dark text
export const lightTheme: Theme = {
  name: 'Light',
  colors: {
    primary: '#007bff',
    secondary: '#6c757d',
    background: '#ffffff',
    text: '#333333',
    border: '#dee2e6'
  }
};

// Dark Theme - dark background, light text
export const darkTheme: Theme = {
  name: 'Dark',
  colors: {
    primary: '#4dabf7',
    secondary: '#adb5bd',
    background: '#212529',
    text: '#f8f9fa',
    border: '#495057'
  }
};

// High Contrast Theme - maximum contrast for accessibility
export const highContrastTheme: Theme = {
  name: 'High Contrast',
  colors: {
    primary: '#0000ff',
    secondary: '#800080',
    background: '#ffffff',
    text: '#000000',
    border: '#000000'
  }
};