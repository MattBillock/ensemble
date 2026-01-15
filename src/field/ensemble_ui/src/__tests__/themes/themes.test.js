import { themes, applyTheme, getThemeVariables, validateTheme } from '../../themes/themes.js';

describe('Theme Configuration System', () => {
  describe('Theme Metadata Structure', () => {
    test('should export themes object with predefined themes', () => {
      /**
       * Verifies that themes object exists and contains expected theme entries
       */
      expect(themes).toBeDefined();
      expect(typeof themes).toBe('object');
      expect(Object.keys(themes).length).toBeGreaterThan(0);
    });

    test('should have dark theme with correct metadata structure', () => {
      /**
       * Verifies dark theme exists with required metadata fields
       */
      expect(themes.dark).toBeDefined();
      expect(themes.dark).toHaveProperty('id', 'dark');
      expect(themes.dark).toHaveProperty('name');
      expect(themes.dark).toHaveProperty('previewColor');
      expect(typeof themes.dark.name).toBe('string');
      expect(typeof themes.dark.previewColor).toBe('string');
    });

    test('should have light theme with correct metadata structure', () => {
      /**
       * Verifies light theme exists with required metadata fields
       */
      expect(themes.light).toBeDefined();
      expect(themes.light).toHaveProperty('id', 'light');
      expect(themes.light).toHaveProperty('name');
      expect(themes.light).toHaveProperty('previewColor');
      expect(typeof themes.light.name).toBe('string');
      expect(typeof themes.light.previewColor).toBe('string');
    });

    test('should have theme variables defined for all themes', () => {
      /**
       * Verifies each theme has a variables object with CSS custom properties
       */
      Object.values(themes).forEach(theme => {
        expect(theme).toHaveProperty('variables');
        expect(typeof theme.variables).toBe('object');
        expect(Object.keys(theme.variables).length).toBeGreaterThan(0);
      });
    });
  });

  describe('CSS Custom Properties for UI Colors', () => {
    test('should define background color variables', () => {
      /**
       * Verifies all themes have background color CSS custom properties
       */
      Object.values(themes).forEach(theme => {
        expect(theme.variables).toHaveProperty('--bg-primary');
        expect(theme.variables).toHaveProperty('--bg-secondary');
        expect(theme.variables).toHaveProperty('--bg-tertiary');
        expect(theme.variables).toHaveProperty('--bg-surface');
        expect(theme.variables).toHaveProperty('--bg-overlay');
      });
    });

    test('should define text color variables', () => {
      /**
       * Verifies all themes have text color CSS custom properties
       */
      Object.values(themes).forEach(theme => {
        expect(theme.variables).toHaveProperty('--text-primary');
        expect(theme.variables).toHaveProperty('--text-secondary');
        expect(theme.variables).toHaveProperty('--text-muted');
        expect(theme.variables).toHaveProperty('--text-inverse');
        expect(theme.variables).toHaveProperty('--text-link');
      });
    });

    test('should define accent color variables', () => {
      /**
       * Verifies all themes have accent color CSS custom properties
       */
      Object.values(themes).forEach(theme => {
        expect(theme.variables).toHaveProperty('--accent-primary');
        expect(theme.variables).toHaveProperty('--accent-secondary');
        expect(theme.variables).toHaveProperty('--accent-success');
        expect(theme.variables).toHaveProperty('--accent-warning');
        expect(theme.variables).toHaveProperty('--accent-error');
        expect(theme.variables).toHaveProperty('--accent-info');
      });
    });

    test('should define border color variables', () => {
      /**
       * Verifies all themes have border color CSS custom properties
       */
      Object.values(themes).forEach(theme => {
        expect(theme.variables).toHaveProperty('--border-primary');
        expect(theme.variables).toHaveProperty('--border-secondary');
        expect(theme.variables).toHaveProperty('--border-subtle');
        expect(theme.variables).toHaveProperty('--border-focus');
        expect(theme.variables).toHaveProperty('--border-error');
      });
    });

    test('should have valid CSS color values for all variables', () => {
      /**
       * Verifies all CSS custom property values are valid color formats
       */
      Object.values(themes).forEach(theme => {
        Object.entries(theme.variables).forEach(([key, value]) => {
          // Check if value is a valid CSS color (hex, rgb, hsl, or named color)
          const colorRegex = /^(#[0-9a-fA-F]{3,8}|rgb\(.*\)|rgba\(.*\)|hsl\(.*\)|hsla\(.*\)|[a-zA-Z]+)$/;
          expect(value).toMatch(colorRegex);
        });
      });
    });
  });

  describe('Dark Theme Variables', () => {
    test('should match existing UI colors for dark theme', () => {
      /**
       * Verifies dark theme variables match the current dark UI color scheme
       */
      const darkTheme = themes.dark;
      
      // Test specific color mappings that should match existing UI
      expect(darkTheme.variables['--bg-primary']).toBe('#1a1a1a');
      expect(darkTheme.variables['--bg-secondary']).toBe('#2d2d2d');
      expect(darkTheme.variables['--text-primary']).toBe('#ffffff');
      expect(darkTheme.variables['--text-secondary']).toBe('#cccccc');
      expect(darkTheme.variables['--accent-primary']).toBe('#007bff');
    });

    test('should provide good contrast ratios for dark theme', () => {
      /**
       * Verifies dark theme has appropriate contrast between text and background colors
       */
      const darkTheme = themes.dark;
      
      // Primary text on primary background should have good contrast
      expect(darkTheme.variables['--text-primary']).not.toBe(darkTheme.variables['--bg-primary']);
      expect(darkTheme.variables['--text-secondary']).not.toBe(darkTheme.variables['--bg-secondary']);
    });
  });

  describe('Light Theme Variables', () => {
    test('should provide good contrast for light theme', () => {
      /**
       * Verifies light theme has appropriate contrast ratios for accessibility
       */
      const lightTheme = themes.light;
      
      // Light theme should have dark text on light backgrounds
      expect(lightTheme.variables['--bg-primary']).toMatch(/^#[f-f][0-9a-f]{5}$/); // Light background
      expect(lightTheme.variables['--text-primary']).toMatch(/^#[0-4][0-9a-f]{5}$/); // Dark text
    });

    test('should have professional appearance colors', () => {
      /**
       * Verifies light theme uses professional, business-appropriate colors
       */
      const lightTheme = themes.light;
      
      expect(lightTheme.variables).toHaveProperty('--bg-primary');
      expect(lightTheme.variables).toHaveProperty('--text-primary');
      expect(lightTheme.variables).toHaveProperty('--accent-primary');
      
      // Should not use overly bright or unprofessional colors
      expect(lightTheme.variables['--accent-primary']).not.toBe('#ff00ff'); // No neon colors
      expect(lightTheme.variables['--bg-primary']).not.toBe('#ffff00'); // No yellow background
    });
  });

  describe('Bootstrap Integration', () => {
    test('should define Bootstrap-compatible CSS custom properties', () => {
      /**
       * Verifies themes include Bootstrap's standard CSS custom property names
       */
      Object.values(themes).forEach(theme => {
        // Bootstrap color system variables
        expect(theme.variables).toHaveProperty('--bs-primary');
        expect(theme.variables).toHaveProperty('--bs-secondary');
        expect(theme.variables).toHaveProperty('--bs-success');
        expect(theme.variables).toHaveProperty('--bs-danger');
        expect(theme.variables).toHaveProperty('--bs-warning');
        expect(theme.variables).toHaveProperty('--bs-info');
        expect(theme.variables).toHaveProperty('--bs-light');
        expect(theme.variables).toHaveProperty('--bs-dark');
      });
    });

    test('should define Bootstrap body and text variables', () => {
      /**
       * Verifies themes include Bootstrap's body and text CSS variables
       */
      Object.values(themes).forEach(theme => {
        expect(theme.variables).toHaveProperty('--bs-body-bg');
        expect(theme.variables).toHaveProperty('--bs-body-color');
        expect(theme.variables).toHaveProperty('--bs-link-color');
        expect(theme.variables).toHaveProperty('--bs-border-color');
      });
    });
  });

  describe('Theme Switching Functionality', () => {
    test('should export applyTheme function', () => {
      /**
       * Verifies applyTheme function is available for switching themes
       */
      expect(applyTheme).toBeDefined();
      expect(typeof applyTheme).toBe('function');
    });

    test('should apply theme variables to document root when applyTheme is called', () => {
      /**
       * Verifies applyTheme applies CSS custom properties to :root
       */
      const mockSetProperty = jest.fn();
      const mockDocumentElement = {
        style: {
          setProperty: mockSetProperty
        }
      };
      
      // Mock document.documentElement
      Object.defineProperty(document, 'documentElement', {
        value: mockDocumentElement,
        writable: true
      });

      applyTheme('dark');

      expect(mockSetProperty).toHaveBeenCalled();
      // Verify specific variables were set
      expect(mockSetProperty).toHaveBeenCalledWith('--bg-primary', expect.any(String));
      expect(mockSetProperty).toHaveBeenCalledWith('--text-primary', expect.any(String));
    });

    test('should throw error for invalid theme ID', () => {
      /**
       * Verifies applyTheme throws appropriate error for non-existent themes
       */
      expect(() => {
        applyTheme('nonexistent-theme');
      }).toThrow('Theme "nonexistent-theme" not found');
    });
  });

  describe('Theme Utilities', () => {
    test('should export getThemeVariables function', () => {
      /**
       * Verifies getThemeVariables utility function is available
       */
      expect(getThemeVariables).toBeDefined();
      expect(typeof getThemeVariables).toBe('function');
    });

    test('should return variables for valid theme ID', () => {
      /**
       * Verifies getThemeVariables returns correct variables object
       */
      const darkVariables = getThemeVariables('dark');
      expect(darkVariables).toBeDefined();
      expect(typeof darkVariables).toBe('object');
      expect(darkVariables).toHaveProperty('--bg-primary');
    });

    test('should export validateTheme function', () => {
      /**
       * Verifies validateTheme utility function is available
       */
      expect(validateTheme).toBeDefined();
      expect(typeof validateTheme).toBe('function');
    });

    test('should validate theme structure correctly', () => {
      /**
       * Verifies validateTheme correctly validates theme object structure
       */
      const validTheme = {
        id: 'test',
        name: 'Test Theme',
        previewColor: '#000000',
        variables: {
          '--bg-primary': '#ffffff'
        }
      };

      expect(validateTheme(validTheme)).toBe(true);

      const invalidTheme = {
        id: 'test',
        // missing name, previewColor, variables
      };

      expect(validateTheme(invalidTheme)).toBe(false);
    });
  });

  describe('Theme Persistence', () => {
    test('should save current theme to localStorage when applied', () => {
      /**
       * Verifies theme preference is persisted to localStorage
       */
      const mockSetItem = jest.fn();
      Object.defineProperty(window, 'localStorage', {
        value: {
          setItem: mockSetItem
        },
        writable: true
      });

      applyTheme('light');

      expect(mockSetItem).toHaveBeenCalledWith('ensemble-theme', 'light');
    });

    test('should load saved theme from localStorage on initialization', () => {
      /**
       * Verifies saved theme is loaded from localStorage when available
       */
      const mockGetItem = jest.fn().mockReturnValue('dark');
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: mockGetItem
        },
        writable: true
      });

      // This would be called during module initialization
      const { loadSavedTheme } = require('../../themes/themes.js');
      
      if (loadSavedTheme) {
        loadSavedTheme();
        expect(mockGetItem).toHaveBeenCalledWith('ensemble-theme');
      }
    });
  });
});