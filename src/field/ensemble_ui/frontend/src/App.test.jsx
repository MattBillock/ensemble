import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App, { formatInterval } from './App';

describe('App', () => {
  it('renders the application title', () => {
    render(<App />);

    const title = screen.getByRole('heading', { name: /ensemble agent system/i });
    expect(title).toBeInTheDocument();
  });

  it('renders the ProblemInputForm component', () => {
    render(<App />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    expect(textarea).toBeInTheDocument();
    expect(button).toBeInTheDocument();
  });

  it('does not show problem description section initially', () => {
    render(<App />);

    // Should not show the heading when no problem submitted
    const problemHeading = screen.queryByRole('heading', { name: /problem description/i });
    expect(problemHeading).not.toBeInTheDocument();
  });

  it('displays submitted problem description after form submission', async () => {
    const user = userEvent.setup();

    render(<App />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    // Submit a problem
    await user.type(textarea, 'Build a todo list app');
    await user.click(button);

    // Should now show the problem description section
    const problemHeading = screen.getByRole('heading', { name: /problem description/i });
    expect(problemHeading).toBeInTheDocument();

    // Should display the submitted text in a paragraph (not the textarea)
    const problemSection = problemHeading.closest('div');
    expect(problemSection).toHaveTextContent('Build a todo list app');
  });

  it('updates displayed problem when submitting multiple times', async () => {
    const user = userEvent.setup();

    render(<App />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    // Submit first problem
    await user.type(textarea, 'First problem');
    await user.click(button);

    let problemHeading = screen.getByRole('heading', { name: /problem description/i });
    let problemSection = problemHeading.closest('div');
    expect(problemSection).toHaveTextContent('First problem');

    // Clear and submit second problem
    await user.clear(textarea);
    await user.type(textarea, 'Second problem');
    await user.click(button);

    problemHeading = screen.getByRole('heading', { name: /problem description/i });
    problemSection = problemHeading.closest('div');

    // Should show new problem in the display section
    expect(problemSection).toHaveTextContent('Second problem');
    expect(problemSection).not.toHaveTextContent('First problem');
  });

  it('has responsive layout classes', () => {
    const { container } = render(<App />);

    // Check for responsive padding classes
    const mainDiv = container.firstChild;
    expect(mainDiv.className).toMatch(/px-4|sm:px-6|lg:px-8/);
  });

  it('maintains layout structure', () => {
    render(<App />);

    // Should have centered max-width container
    const title = screen.getByRole('heading', { name: /ensemble agent system/i });
    const container = title.closest('.max-w-xl');

    expect(container).toBeInTheDocument();
  });

  it('logs problem to console when submitted', async () => {
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    const user = userEvent.setup();

    render(<App />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    await user.type(textarea, 'Test console log');
    await user.click(button);

    expect(consoleSpy).toHaveBeenCalledWith('Problem submitted:', 'Test console log');

    consoleSpy.mockRestore();
  });
});

describe('Interval Formatting', () => {
  describe('formatInterval function', () => {
    it('formats 1000ms as "1s"', () => {
      /**
       * Verify that formatInterval converts 1000 milliseconds to "1s"
       * Expected: formatInterval(1000) returns '1s'
       */
      const result = formatInterval(1000);
      expect(result).toBe('1s');
    });

    it('formats 60000ms as "1m"', () => {
      /**
       * Verify that formatInterval converts 60000 milliseconds (1 minute) to "1m"
       * Expected: formatInterval(60000) returns '1m'
       */
      const result = formatInterval(60000);
      expect(result).toBe('1m');
    });

    it('formats 300000ms as "5m"', () => {
      /**
       * Verify that formatInterval converts 300000 milliseconds (5 minutes) to "5m"
       * Expected: formatInterval(300000) returns '5m'
       */
      const result = formatInterval(300000);
      expect(result).toBe('5m');
    });

    it('formats non-standard intervals in milliseconds', () => {
      /**
       * Verify that formatInterval displays values that don't convert cleanly
       * to seconds or minutes as milliseconds (e.g., 2500ms)
       * Expected: formatInterval(2500) returns '2500ms'
       */
      const result = formatInterval(2500);
      expect(result).toBe('2500ms');
    });
  });

  describe('interval button labels', () => {
    it('displays interval buttons with formatted labels', () => {
      /**
       * Verify that interval buttons show user-friendly formatted labels
       * instead of raw millisecond values
       * Expected: Buttons display '1s', '1m', '5m' instead of '1000', '60000', '300000'
       */
      render(<App />);

      const oneSecondButton = screen.getByRole('button', { name: /^1s$/i });
      const oneMinuteButton = screen.getByRole('button', { name: /^1m$/i });
      const fiveMinuteButton = screen.getByRole('button', { name: /^5m$/i });

      expect(oneSecondButton).toBeInTheDocument();
      expect(oneMinuteButton).toBeInTheDocument();
      expect(fiveMinuteButton).toBeInTheDocument();
    });

    it('does not display buttons with raw millisecond values', () => {
      /**
       * Verify that buttons no longer show raw millisecond values like '1000', '60000', '300000'
       * Expected: No buttons with these numeric labels should exist
       */
      render(<App />);

      const rawThousandButton = screen.queryByRole('button', { name: /^1000$/i });
      const rawSixtyKButton = screen.queryByRole('button', { name: /^60000$/i });
      const rawThreeHundredKButton = screen.queryByRole('button', { name: /^300000$/i });

      expect(rawThousandButton).not.toBeInTheDocument();
      expect(rawSixtyKButton).not.toBeInTheDocument();
      expect(rawThreeHundredKButton).not.toBeInTheDocument();
    });

    it('does not have old interval buttons for 500ms and 2s', () => {
      /**
       * Verify that the old interval options (500ms and 2s) have been removed
       * and replaced with the new intervals (1s, 1m, 5m)
       * Expected: No buttons labeled '500ms' or '2s' should exist
       */
      render(<App />);

      const fiveHundredMsButton = screen.queryByRole('button', { name: /^500ms$/i });
      const twoSecondsButton = screen.queryByRole('button', { name: /^2s$/i });

      expect(fiveHundredMsButton).not.toBeInTheDocument();
      expect(twoSecondsButton).not.toBeInTheDocument();
    });
  });

  describe('interval button click behavior', () => {
    it('displays "1s" in the interval display area when 1s button is clicked', async () => {
      /**
       * Verify that clicking the '1s' interval button updates the display
       * to show the formatted interval value '1s'
       * Expected: After clicking '1s' button, display shows '1s'
       */
      const user = userEvent.setup();
      render(<App />);

      const oneSecondButton = screen.getByRole('button', { name: /^1s$/i });
      await user.click(oneSecondButton);

      // Look for the interval display - it should show '1s'
      const intervalDisplay = screen.getByText(/1s/i, { 
        selector: ':not(button)' // Exclude the button itself
      });
      expect(intervalDisplay).toBeInTheDocument();
    });

    it('displays "1m" in the interval display area when 1m button is clicked', async () => {
      /**
       * Verify that clicking the '1m' interval button updates the display
       * to show the formatted interval value '1m'
       * Expected: After clicking '1m' button, display shows '1m'
       */
      const user = userEvent.setup();
      render(<App />);

      const oneMinuteButton = screen.getByRole('button', { name: /^1m$/i });
      await user.click(oneMinuteButton);

      // Look for the interval display - it should show '1m'
      const intervalDisplay = screen.getByText(/1m/i, { 
        selector: ':not(button)' // Exclude the button itself
      });
      expect(intervalDisplay).toBeInTheDocument();
    });

    it('displays "5m" in the interval display area when 5m button is clicked', async () => {
      /**
       * Verify that clicking the '5m' interval button updates the display
       * to show the formatted interval value '5m'
       * Expected: After clicking '5m' button, display shows '5m'
       */
      const user = userEvent.setup();
      render(<App />);

      const fiveMinuteButton = screen.getByRole('button', { name: /^5m$/i });
      await user.click(fiveMinuteButton);

      // Look for the interval display - it should show '5m'
      const intervalDisplay = screen.getByText(/5m/i, { 
        selector: ':not(button)' // Exclude the button itself
      });
      expect(intervalDisplay).toBeInTheDocument();
    });
  });
});
