import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import IntervalSelector from '../components/IntervalSelector';
import PropTypes from 'prop-types';

describe('IntervalSelector Component', () => {
  // Test 1: Rendering with default props
  test('renders IntervalSelector with default intervals', () => {
    const mockOnChange = jest.fn();
    
    render(<IntervalSelector 
      currentInterval="1s" 
      intervals={['1s', '1m', '5m']} 
      onChange={mockOnChange} 
    />);
    
    // Check that all specified intervals are rendered
    const intervalButtons = screen.getAllByRole('button');
    expect(intervalButtons).toHaveLength(3);
    expect(intervalButtons.map(btn => btn.textContent)).toEqual(['1s', '1m', '5m']);
  });

  // Test 2: Interval selection triggers change handler
  test('calls onChange handler with selected interval', () => {
    const mockOnChange = jest.fn();
    
    render(<IntervalSelector 
      currentInterval="1s" 
      intervals={['1s', '1m', '5m']} 
      onChange={mockOnChange} 
    />);
    
    // Click on '1m' interval
    const oneMinuteButton = screen.getByText('1m');
    fireEvent.click(oneMinuteButton);
    
    // Verify change handler was called with correct interval
    expect(mockOnChange).toHaveBeenCalledWith('1m');
  });

  // Test 3: Millisecond mapping validation
  test('converts intervals to correct millisecond values', () => {
    const millisecondMap = {
      '1s': 1000,
      '1m': 60000,
      '5m': 300000
    };
    
    const mockOnChange = jest.fn();
    const { container } = render(<IntervalSelector 
      currentInterval="1s" 
      intervals={['1s', '1m', '5m']} 
      onChange={mockOnChange} 
    />);
    
    // Check each interval button for data attribute with correct milliseconds
    const buttons = container.querySelectorAll('button');
    buttons.forEach(button => {
      const interval = button.textContent;
      expect(button).toHaveAttribute('data-ms', millisecondMap[interval].toString());
    });
  });

  // Test 4: Current interval is highlighted
  test('highlights currently selected interval', () => {
    render(<IntervalSelector 
      currentInterval="1m" 
      intervals={['1s', '1m', '5m']} 
      onChange={jest.fn()} 
    />);
    
    const oneMinuteButton = screen.getByText('1m');
    expect(oneMinuteButton).toHaveClass('selected');
  });

  // Test 5: Prop type validation
  test('validates prop types', () => {
    const originalError = console.error;
    console.error = jest.fn();

    try {
      // Test invalid prop types
      expect(() => {
        PropTypes.checkPropTypes(
          IntervalSelector.propTypes, 
          {
            currentInterval: 123, // should be string
            intervals: 'not an array', // should be array
            onChange: 'not a function' // should be function
          }, 
          'prop', 
          'IntervalSelector'
        );
      }).toThrow();
    } finally {
      console.error = originalError;
    }
  });

  // Test 6: Edge case - empty intervals array
  test('handles empty intervals array gracefully', () => {
    const mockOnChange = jest.fn();
    
    render(<IntervalSelector 
      currentInterval="1s" 
      intervals={[]} 
      onChange={mockOnChange} 
    />);
    
    // Should render without errors, no buttons
    const intervalButtons = screen.queryAllByRole('button');
    expect(intervalButtons).toHaveLength(0);
  });

  // Test 7: Disabled state when current interval not in list
  test('disables interval selection when current interval not in list', () => {
    const mockOnChange = jest.fn();
    
    render(<IntervalSelector 
      currentInterval="10s" 
      intervals={['1s', '1m', '5m']} 
      onChange={mockOnChange} 
    />);
    
    // Should not throw error, and no interval should be selected
    const selectedButton = screen.queryByClassName('selected');
    expect(selectedButton).toBeNull();
  });
});