import React from 'react';
import { Dropdown } from 'react-bootstrap';
import { useTheme } from '../hooks/useTheme';

function ThemeSwitcher() {
  const { themeName, setTheme, availableThemes } = useTheme();

  const currentTheme = availableThemes.find(t => t.name === themeName) || availableThemes[0];

  return (
    <Dropdown>
      <Dropdown.Toggle
        variant="outline-secondary"
        size="sm"
        id="theme-switcher-dropdown"
      >
        {currentTheme.icon} {currentTheme.label}
      </Dropdown.Toggle>
      <Dropdown.Menu style={{ backgroundColor: 'var(--color-bg-secondary)', border: '1px solid var(--color-border-primary)' }}>
        {availableThemes.map((theme) => (
          <Dropdown.Item
            key={theme.name}
            onClick={() => setTheme(theme.name)}
            active={themeName === theme.name}
            style={{ color: themeName === theme.name ? '#fff' : 'var(--color-text-secondary)' }}
          >
            {theme.icon} {theme.label}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}

export default ThemeSwitcher;
