import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import {
  generateCSSVariables,
  applyCSSVariables,
  getCSSVariableValue
} from './cssVariables';

describe('CSS Variables Utility Functions', () => {
  // Mock theme objects for testing
  const validTheme = {
    primary: '#3b82f6',
    secondary: '#64748b',
    background: '#ffffff',
    text: '#1f2937',
    accent: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    success: '#22c55e'
  };

  const nestedTheme = {
    colors: {
      primary: '#3b82f6',
      secondary: '#64748b'
    },
    spacing: {
      small: '8px',
      medium: '16px',
      large: '24px'
    },
    typography: {
      fontSize: {
        base: '16px',
        large: '18px'
      }
    }
  };

  beforeEach(() => {
    // Set up jsdom environment
    const dom = new JSDOM('<!DOCTYPE html><html><head></head><body></body></html>');
    global.document = dom.window.document;
    global.window = dom.window as any;
    
    // Clear any existing CSS variables
    document.documentElement.style.cssText = '';
  });

  describe('generateCSSVariables', () => {
    it('should convert flat theme object to CSS variables string', () => {
      /**
       * Test that generateCSSVariables converts a flat theme object
       * to properly formatted CSS custom properties string
       */
      const result = generateCSSVariables(validTheme);
      
      expect(result).toContain('--theme-primary: #3b82f6;');
      expect(result).toContain('--theme-secondary: #64748b;');
      expect(result).toContain('--theme-background: #ffffff;');
      expect(result).toContain('--theme-text: #1f2937;');
      expect(result).toContain('--theme-accent: #10b981;');
      expect(result).toContain('--theme-error: #ef4444;');
      expect(result).toContain('--theme-warning: #f59e0b;');
      expect(result).toContain('--theme-success: #22c55e;');
    });

    it('should handle nested theme objects with proper naming convention', () => {
      /**
       * Test that generateCSSVariables handles nested objects
       * and creates proper CSS variable names with kebab-case
       */
      const result = generateCSSVariables(nestedTheme);
      
      expect(result).toContain('--theme-colors-primary: #3b82f6;');
      expect(result).toContain('--theme-colors-secondary: #64748b;');
      expect(result).toContain('--theme-spacing-small: 8px;');
      expect(result).toContain('--theme-spacing-medium: 16px;');
      expect(result).toContain('--theme-spacing-large: 24px;');
      expect(result).toContain('--theme-typography-font-size-base: 16px;');
      expect(result).toContain('--theme-typography-font-size-large: 18px;');
    });

    it('should handle empty theme object', () => {
      /**
       * Test that generateCSSVariables handles empty theme gracefully
       */
      const result = generateCSSVariables({});
      
      expect(result).toBe('');
    });

    it('should handle theme with special characters in keys', () => {
      /**
       * Test that generateCSSVariables properly sanitizes keys with special characters
       */
      const specialTheme = {
        'primary-color': '#3b82f6',
        'background_color': '#ffffff',
        'text.color': '#1f2937'
      };
      
      const result = generateCSSVariables(specialTheme);
      
      expect(result).toContain('--theme-primary-color: #3b82f6;');
      expect(result).toContain('--theme-background-color: #ffffff;');
      expect(result).toContain('--theme-text-color: #1f2937;');
    });

    it('should throw error for null or undefined theme', () => {
      /**
       * Test that generateCSSVariables throws appropriate error for invalid input
       */
      expect(() => generateCSSVariables(null as any)).toThrow('Theme must be a valid object');
      expect(() => generateCSSVariables(undefined as any)).toThrow('Theme must be a valid object');
    });

    it('should throw error for non-object theme', () => {
      /**
       * Test that generateCSSVariables throws error for primitive values
       */
      expect(() => generateCSSVariables('string' as any)).toThrow('Theme must be a valid object');
      expect(() => generateCSSVariables(123 as any)).toThrow('Theme must be a valid object');
      expect(() => generateCSSVariables([] as any)).toThrow('Theme must be a valid object');
    });

    it('should handle numeric and boolean values', () => {
      /**
       * Test that generateCSSVariables converts different value types to strings
       */
      const mixedTheme = {
        opacity: 0.8,
        isVisible: true,
        zIndex: 100
      };
      
      const result = generateCSSVariables(mixedTheme);
      
      expect(result).toContain('--theme-opacity: 0.8;');
      expect(result).toContain('--theme-is-visible: true;');
      expect(result).toContain('--theme-z-index: 100;');
    });
  });

  describe('applyCSSVariables', () => {
    it('should apply CSS variables to document.documentElement.style', () => {
      /**
       * Test that applyCSSVariables properly sets CSS custom properties
       * on the document root element
       */
      applyCSSVariables(validTheme);
      
      const rootStyle = document.documentElement.style;
      expect(rootStyle.getPropertyValue('--theme-primary')).toBe('#3b82f6');
      expect(rootStyle.getPropertyValue('--theme-secondary')).toBe('#64748b');
      expect(rootStyle.getPropertyValue('--theme-background')).toBe('#ffffff');
      expect(rootStyle.getPropertyValue('--theme-text')).toBe('#1f2937');
    });

    it('should handle nested theme objects in DOM application', () => {
      /**
       * Test that applyCSSVariables works with nested theme structures
       */
      applyCSSVariables(nestedTheme);
      
      const rootStyle = document.documentElement.style;
      expect(rootStyle.getPropertyValue('--theme-colors-primary')).toBe('#3b82f6');
      expect(rootStyle.getPropertyValue('--theme-spacing-small')).toBe('8px');
      expect(rootStyle.getPropertyValue('--theme-typography-font-size-base')).toBe('16px');
    });

    it('should update existing CSS variables', () => {
      /**
       * Test that applyCSSVariables updates previously set variables
       */
      // Apply initial theme
      applyCSSVariables(validTheme);
      expect(document.documentElement.style.getPropertyValue('--theme-primary')).toBe('#3b82f6');
      
      // Apply updated theme
      const updatedTheme = { primary: '#ff0000', background: '#000000' };
      applyCSSVariables(updatedTheme);
      
      expect(document.documentElement.style.getPropertyValue('--theme-primary')).toBe('#ff0000');
      expect(document.documentElement.style.getPropertyValue('--theme-background')).toBe('#000000');
    });

    it('should handle empty theme without errors', () => {
      /**
       * Test that applyCSSVariables handles empty theme gracefully
       */
      expect(() => applyCSSVariables({})).not.toThrow();
    });

    it('should throw error for invalid theme objects', () => {
      /**
       * Test that applyCSSVariables throws appropriate errors for invalid input
       */
      expect(() => applyCSSVariables(null as any)).toThrow('Theme must be a valid object');
      expect(() => applyCSSVariables(undefined as any)).toThrow('Theme must be a valid object');
      expect(() => applyCSSVariables('invalid' as any)).toThrow('Theme must be a valid object');
    });

    it('should handle document.documentElement being null', () => {
      /**
       * Test error handling when document.documentElement is not available
       */
      const originalDocumentElement = document.documentElement;
      (document as any).documentElement = null;
      
      expect(() => applyCSSVariables(validTheme)).toThrow('Document element not available');
      
      // Restore original documentElement
      (document as any).documentElement = originalDocumentElement;
    });
  });

  describe('getCSSVariableValue', () => {
    beforeEach(() => {
      // Set up some CSS variables for testing
      applyCSSVariables(validTheme);
    });

    it('should retrieve existing CSS variable value', () => {
      /**
       * Test that getCSSVariableValue returns the correct value for existing variables
       */
      const primaryValue = getCSSVariableValue('--theme-primary');
      const backgroundValue = getCSSVariableValue('--theme-background');
      
      expect(primaryValue).toBe('#3b82f6');
      expect(backgroundValue).toBe('#ffffff');
    });

    it('should handle CSS variable names without -- prefix', () => {
      /**
       * Test that getCSSVariableValue works with variable names missing -- prefix
       */
      const primaryValue = getCSSVariableValue('theme-primary');
      const backgroundValue = getCSSVariableValue('theme-background');
      
      expect(primaryValue).toBe('#3b82f6');
      expect(backgroundValue).toBe('#ffffff');
    });

    it('should return empty string for non-existent variables', () => {
      /**
       * Test that getCSSVariableValue returns empty string for undefined variables
       */
      const nonExistentValue = getCSSVariableValue('--theme-nonexistent');
      
      expect(nonExistentValue).toBe('');
    });

    it('should handle empty or invalid variable names', () => {
      /**
       * Test that getCSSVariableValue handles edge cases gracefully
       */
      expect(getCSSVariableValue('')).toBe('');
      expect(getCSSVariableValue('   ')).toBe('');
    });

    it('should throw error for null or undefined variable names', () => {
      /**
       * Test that getCSSVariableValue throws error for invalid input
       */
      expect(() => getCSSVariableValue(null as any)).toThrow('Variable name must be a string');
      expect(() => getCSSVariableValue(undefined as any)).toThrow('Variable name must be a string');
    });

    it('should handle document.documentElement being null', () => {
      /**
       * Test error handling when document.documentElement is not available
       */
      const originalDocumentElement = document.documentElement;
      (document as any).documentElement = null;
      
      expect(() => getCSSVariableValue('--theme-primary')).toThrow('Document element not available');
      
      // Restore original documentElement
      (document as any).documentElement = originalDocumentElement;
    });

    it('should trim whitespace from retrieved values', () => {
      /**
       * Test that getCSSVariableValue properly trims whitespace
       */
      // Manually set a variable with whitespace
      document.documentElement.style.setProperty('--test-spacing', '  16px  ');
      
      const value = getCSSVariableValue('--test-spacing');
      expect(value).toBe('16px');
    });

    it('should handle computed styles from getComputedStyle', () => {
      /**
       * Test that getCSSVariableValue works with computed styles
       * when variables are not directly set on element.style
       */
      // Create a style element with CSS variables
      const styleEl = document.createElement('style');
      styleEl.textContent = ':root { --computed-var: #123456; }';
      document.head.appendChild(styleEl);
      
      const value = getCSSVariableValue('--computed-var');
      expect(value).toBe('#123456');
      
      // Cleanup
      document.head.removeChild(styleEl);
    });
  });

  describe('Integration Tests', () => {
    it('should work together: generate -> apply -> retrieve', () => {
      /**
       * Test the complete workflow of CSS variables utilities
       */
      const theme = {
        primary: '#007bff',
        secondary: '#6c757d',
        success: '#28a745'
      };
      
      // Generate CSS variables string
      const cssString = generateCSSVariables(theme);
      expect(cssString).toContain('--theme-primary: #007bff;');
      
      // Apply to DOM
      applyCSSVariables(theme);
      
      // Retrieve values
      expect(getCSSVariableValue('--theme-primary')).toBe('#007bff');
      expect(getCSSVariableValue('--theme-secondary')).toBe('#6c757d');
      expect(getCSSVariableValue('--theme-success')).toBe('#28a745');
    });

    it('should handle theme updates correctly', () => {
      /**
       * Test that theme updates work correctly across all utilities
       */
      const initialTheme = { primary: '#initial' };
      const updatedTheme = { primary: '#updated', secondary: '#new' };
      
      // Apply initial theme
      applyCSSVariables(initialTheme);
      expect(getCSSVariableValue('--theme-primary')).toBe('#initial');
      
      // Update theme
      applyCSSVariables(updatedTheme);
      expect(getCSSVariableValue('--theme-primary')).toBe('#updated');
      expect(getCSSVariableValue('--theme-secondary')).toBe('#new');
    });

    it('should maintain consistency between generate and apply functions', () => {
      /**
       * Test that generateCSSVariables and applyCSSVariables produce consistent results
       */
      const theme = { primary: '#test', background: '#ffffff' };
      
      const generatedCSS = generateCSSVariables(theme);
      applyCSSVariables(theme);
      
      // Check that generated CSS contains the same variables that were applied
      expect(generatedCSS).toContain('--theme-primary: #test;');
      expect(generatedCSS).toContain('--theme-background: #ffffff;');
      expect(getCSSVariableValue('--theme-primary')).toBe('#test');
      expect(getCSSVariableValue('--theme-background')).toBe('#ffffff');
    });
  });
});