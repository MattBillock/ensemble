import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import useUpdateInterval from './useUpdateInterval';

describe('useUpdateInterval', () => {
  // Mock localStorage
  const localStorageMock = (() => {
    let store = {};
    return {
      getItem: vi.fn((key) => store[key] || null),
      setItem: vi.fn((key, value) => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key) => {
        delete store[key];
      }),
      clear: vi.fn(() => {
        store = {};
      })
    };
  })();

  beforeEach(() => {
    // Replace global localStorage with mock
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true
    });
    
    // Clear all mocks and storage before each test
    localStorageMock.clear();
    vi.clearAllMocks();
    
    // Use fake timers for debounce testing
    vi.useFakeTimers();
  });

  afterEach(() => {
    // Restore real timers
    vi.useRealTimers();
  });

  it('test_returns_default_interval_1000ms_when_localStorage_empty', () => {
    /**
     * Verify that the hook returns a default interval of 1000ms
     * when localStorage is empty (no saved value exists).
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    expect(result.current.interval).toBe(1000);
    expect(localStorageMock.getItem).toHaveBeenCalledWith('ensemble_poll_interval');
  });

  it('test_reads_initial_value_from_localStorage', () => {
    /**
     * Verify that the hook reads the initial interval value
     * from localStorage key 'ensemble_poll_interval' if it exists.
     */
    const savedInterval = '2500';
    localStorageMock.getItem.mockReturnValueOnce(savedInterval);
    
    const { result } = renderHook(() => useUpdateInterval());
    
    expect(localStorageMock.getItem).toHaveBeenCalledWith('ensemble_poll_interval');
    expect(result.current.interval).toBe(2500);
  });

  it('test_interval_below_200ms_produces_error_message', () => {
    /**
     * Verify that setting an interval below 200ms
     * produces an appropriate error message.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(150);
    });
    
    expect(result.current.error).toBeTruthy();
    expect(result.current.error).toMatch(/200ms|minimum|too low|below/i);
  });

  it('test_interval_above_30000ms_produces_error_message', () => {
    /**
     * Verify that setting an interval above 30000ms
     * produces an appropriate error message.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(35000);
    });
    
    expect(result.current.error).toBeTruthy();
    expect(result.current.error).toMatch(/30000ms|maximum|too high|above/i);
  });

  it('test_warning_fast_polling_below_500ms', () => {
    /**
     * Verify that setting an interval below 500ms (but above 200ms minimum)
     * produces a warning message about fast polling impacting performance.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(300);
    });
    
    expect(result.current.warning).toBeTruthy();
    expect(result.current.warning).toMatch(/fast polling|performance/i);
    expect(result.current.error).toBeFalsy();
  });

  it('test_warning_slow_polling_above_5000ms', () => {
    /**
     * Verify that setting an interval above 5000ms (but below 30000ms maximum)
     * produces a warning message about slow polling missing rapid updates.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(6000);
    });
    
    expect(result.current.warning).toBeTruthy();
    expect(result.current.warning).toMatch(/slow polling|miss.*updates|rapid updates/i);
    expect(result.current.error).toBeFalsy();
  });

  it('test_reset_clears_localStorage_and_resets_to_1000ms', () => {
    /**
     * Verify that calling reset() clears the localStorage entry
     * and resets the interval back to the default 1000ms.
     */
    // Set up initial state with custom interval
    localStorageMock.getItem.mockReturnValueOnce('3000');
    const { result } = renderHook(() => useUpdateInterval());
    
    expect(result.current.interval).toBe(3000);
    
    act(() => {
      result.current.reset();
    });
    
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('ensemble_poll_interval');
    expect(result.current.interval).toBe(1000);
  });

  it('test_customInput_debounced_300ms_before_applying', async () => {
    /**
     * Verify that changes to customInput are debounced by 300ms
     * before being applied to the interval value.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    // Set customInput to a new value
    act(() => {
      result.current.setCustomInput('2000');
    });
    
    // Immediately after setting, interval should not have changed yet
    expect(result.current.customInput).toBe('2000');
    expect(result.current.interval).toBe(1000);
    
    // Advance timers by 200ms (not enough)
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current.interval).toBe(1000);
    
    // Advance timers by another 100ms (total 300ms)
    act(() => {
      vi.advanceTimersByTime(100);
    });
    
    // Now interval should be updated
    await waitFor(() => {
      expect(result.current.interval).toBe(2000);
    });
  });

  it('test_localStorage_updated_when_interval_changes', () => {
    /**
     * Verify that localStorage is updated with the new value
     * whenever the interval changes.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(3500);
    });
    
    expect(localStorageMock.setItem).toHaveBeenCalledWith('ensemble_poll_interval', '3500');
  });

  it('test_setIsPaused_updates_isPaused_state', () => {
    /**
     * Verify that calling setIsPaused properly updates
     * the isPaused state value.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    // Initial state should be false (not paused)
    expect(result.current.isPaused).toBe(false);
    
    // Pause
    act(() => {
      result.current.setIsPaused(true);
    });
    expect(result.current.isPaused).toBe(true);
    
    // Unpause
    act(() => {
      result.current.setIsPaused(false);
    });
    expect(result.current.isPaused).toBe(false);
  });

  it('test_hook_returns_all_required_properties', () => {
    /**
     * Verify that the hook returns an object with all required properties:
     * interval, setInterval, isPaused, setIsPaused, customInput, 
     * setCustomInput, error, warning, reset
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    expect(result.current).toHaveProperty('interval');
    expect(result.current).toHaveProperty('setInterval');
    expect(result.current).toHaveProperty('isPaused');
    expect(result.current).toHaveProperty('setIsPaused');
    expect(result.current).toHaveProperty('customInput');
    expect(result.current).toHaveProperty('setCustomInput');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('warning');
    expect(result.current).toHaveProperty('reset');
    
    // Verify function types
    expect(typeof result.current.setInterval).toBe('function');
    expect(typeof result.current.setIsPaused).toBe('function');
    expect(typeof result.current.setCustomInput).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  it('test_no_warning_or_error_for_valid_interval', () => {
    /**
     * Verify that a valid interval (between 500ms and 5000ms)
     * produces neither warnings nor errors.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    act(() => {
      result.current.setInterval(1500);
    });
    
    expect(result.current.error).toBeFalsy();
    expect(result.current.warning).toBeFalsy();
  });

  it('test_customInput_debounce_cancels_previous_timer', async () => {
    /**
     * Verify that rapidly changing customInput cancels previous
     * debounce timers, only applying the final value after 300ms.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    // First change
    act(() => {
      result.current.setCustomInput('2000');
    });
    
    // Advance 200ms
    act(() => {
      vi.advanceTimersByTime(200);
    });
    
    // Second change before first debounce completes
    act(() => {
      result.current.setCustomInput('3000');
    });
    
    // Advance 200ms (not enough from second change)
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current.interval).toBe(1000); // Still default
    
    // Advance another 100ms (300ms from second change)
    act(() => {
      vi.advanceTimersByTime(100);
    });
    
    // Should apply the final value (3000), not the first (2000)
    await waitFor(() => {
      expect(result.current.interval).toBe(3000);
    });
  });

  it('test_invalid_localStorage_value_falls_back_to_default', () => {
    /**
     * Verify that if localStorage contains an invalid value (non-numeric),
     * the hook falls back to the default 1000ms interval.
     */
    localStorageMock.getItem.mockReturnValueOnce('invalid_value');
    
    const { result } = renderHook(() => useUpdateInterval());
    
    expect(result.current.interval).toBe(1000);
  });

  it('test_reset_clears_warnings_and_errors', () => {
    /**
     * Verify that calling reset() clears any existing
     * warnings or errors.
     */
    const { result } = renderHook(() => useUpdateInterval());
    
    // Set an interval that produces a warning
    act(() => {
      result.current.setInterval(300);
    });
    expect(result.current.warning).toBeTruthy();
    
    // Reset
    act(() => {
      result.current.reset();
    });
    
    expect(result.current.warning).toBeFalsy();
    expect(result.current.error).toBeFalsy();
  });
});
