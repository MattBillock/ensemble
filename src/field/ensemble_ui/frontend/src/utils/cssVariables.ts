/**
 * CSS Variable utility functions for theme management.
 * Generates, applies, and retrieves CSS custom properties from theme objects.
 */

function isValidTheme(theme: unknown): theme is Record<string, unknown> {
  return theme !== null && theme !== undefined && typeof theme === 'object' && !Array.isArray(theme);
}

/**
 * Convert camelCase to kebab-case
 */
function toKebabCase(str: string): string {
  return str
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[_.]/g, '-')
    .toLowerCase();
}

/**
 * Flatten a nested theme object into CSS variable entries.
 * Keys are joined with `-` and converted to kebab-case.
 */
function flattenTheme(obj: Record<string, unknown>, prefix: string = '--theme'): Array<[string, string]> {
  const entries: Array<[string, string]> = [];

  for (const [key, value] of Object.entries(obj)) {
    const varName = `${prefix}-${toKebabCase(key)}`;
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      entries.push(...flattenTheme(value as Record<string, unknown>, varName));
    } else {
      entries.push([varName, String(value)]);
    }
  }

  return entries;
}

/**
 * Convert a theme object to a CSS variables string with `--theme-` prefix.
 */
export function generateCSSVariables(theme: Record<string, unknown>): string {
  if (!isValidTheme(theme)) {
    throw new Error('Theme must be a valid object');
  }

  const entries = flattenTheme(theme);
  return entries.map(([name, value]) => `${name}: ${value};`).join('\n');
}

/**
 * Apply theme variables to document.documentElement.style.
 */
export function applyCSSVariables(theme: Record<string, unknown>): void {
  if (!isValidTheme(theme)) {
    throw new Error('Theme must be a valid object');
  }
  if (!document.documentElement) {
    throw new Error('Document element not available');
  }

  const entries = flattenTheme(theme);
  for (const [name, value] of entries) {
    document.documentElement.style.setProperty(name, value);
  }
}

/**
 * Get the current value of a CSS variable from the document root.
 */
export function getCSSVariableValue(name: unknown): string {
  if (typeof name !== 'string') {
    throw new Error('Variable name must be a string');
  }
  if (!document.documentElement) {
    throw new Error('Document element not available');
  }

  const trimmed = name.trim();
  if (!trimmed) return '';

  const varName = trimmed.startsWith('--') ? trimmed : `--${trimmed}`;

  // Try inline style first, then computed style
  const inlineValue = document.documentElement.style.getPropertyValue(varName).trim();
  if (inlineValue) return inlineValue;

  const computedValue = window.getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  return computedValue;
}
