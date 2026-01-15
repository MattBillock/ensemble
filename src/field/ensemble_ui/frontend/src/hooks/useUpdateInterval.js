import { useState, useEffect, useRef, useCallback } from 'react';

const STORAGE_KEY = 'ensemble_poll_interval';
const DEFAULT_INTERVAL = 1000;
const MIN_INTERVAL = 200;
const MAX_INTERVAL = 300000;
const FAST_THRESHOLD = 500;
const SLOW_THRESHOLD = 5000;
const DEBOUNCE_DELAY = 300;

/**
 * Custom hook for managing polling interval configuration with validation,
 * warnings, localStorage persistence, and debounced input handling.
 */
const useUpdateInterval = () => {
  // Initialize interval from localStorage or default
  const getInitialInterval = () => {
    const storedValue = localStorage.getItem(STORAGE_KEY);
    if (storedValue) {
      const parsed = parseInt(storedValue, 10);
      if (!isNaN(parsed)) {
        return parsed;
      }
    }
    return DEFAULT_INTERVAL;
  };

  const [interval, setIntervalState] = useState(getInitialInterval);
  const [isPaused, setIsPaused] = useState(false);
  const [customInput, setCustomInput] = useState('');
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  
  const debounceTimerRef = useRef(null);

  // Validate interval and set error/warning messages
  const validateInterval = useCallback((value) => {
    if (value < MIN_INTERVAL) {
      setError('Interval too low - minimum is 200ms');
      setWarning('');
      return false;
    } else if (value > MAX_INTERVAL) {
      setError('Interval too high - maximum is 300000ms');
      setWarning('');
      return false;
    } else {
      setError('');
      
      if (value < FAST_THRESHOLD) {
        setWarning('Fast polling may impact performance');
      } else if (value > SLOW_THRESHOLD) {
        setWarning('Slow polling may miss rapid updates');
      } else {
        setWarning('');
      }
      return true;
    }
  }, []);

  // Set interval with validation - memoized to prevent infinite loops
  const setInterval = useCallback((value) => {
    validateInterval(value);
    setIntervalState(value);
    localStorage.setItem(STORAGE_KEY, String(value));
  }, [validateInterval]);

  // Reset to default state
  const reset = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setIntervalState(DEFAULT_INTERVAL);
    setError('');
    setWarning('');
    setCustomInput('');
  }, []);

  // Handle debounced customInput changes
  // CRITICAL: Only depends on customInput to avoid circular dependency
  useEffect(() => {
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Only process if customInput has a value
    if (customInput !== '') {
      debounceTimerRef.current = setTimeout(() => {
        const parsed = parseInt(customInput, 10);
        if (!isNaN(parsed)) {
          // Directly update state and localStorage without calling setInterval
          // This breaks the circular dependency chain
          setIntervalState(parsed);
          
          // Validate and set error/warning states
          if (parsed < MIN_INTERVAL) {
            setError('Interval too low - minimum is 200ms');
            setWarning('');
          } else if (parsed > MAX_INTERVAL) {
            setError('Interval too high - maximum is 300000ms');
            setWarning('');
          } else {
            setError('');
            
            if (parsed < FAST_THRESHOLD) {
              setWarning('Fast polling may impact performance');
            } else if (parsed > SLOW_THRESHOLD) {
              setWarning('Slow polling may miss rapid updates');
            } else {
              setWarning('');
            }
          }
          
          // Write directly to localStorage
          localStorage.setItem(STORAGE_KEY, String(parsed));
        }
      }, DEBOUNCE_DELAY);
    }

    // Cleanup on unmount or customInput change
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [customInput]); // Only depends on customInput - no circular dependency

  return {
    interval,
    setInterval,
    isPaused,
    setIsPaused,
    customInput,
    setCustomInput,
    error,
    warning,
    reset
  };
};

export default useUpdateInterval;