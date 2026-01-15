import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App, { formatInterval } from './App';

// Mock the API calls
vi.mock('./services/api', () => ({
  generateSolution: vi.fn().mockResolvedValue({}),
  getApplicationStatus: vi.fn().mockResolvedValue({ status: 'running', active_agents: 0 }),
  getRecentActivities: vi.fn().mockResolvedValue({ activities: [] }),
  getAgentHierarchy: vi.fn().mockResolvedValue({ hierarchy: {} }),
  getAllAgentStates: vi.fn().mockResolvedValue({ agent_states: {} }),
  getPendingQuestions: vi.fn().mockResolvedValue({ questions: {} }),
  answerQuestion: vi.fn().mockResolvedValue({}),
  getGeneratedFiles: vi.fn().mockResolvedValue({ files: [] })
}));

describe('App', () => {
  describe('Header Title', () => {
    it('renders the application title as "Willow says Hi"', () => {
      /**
       * Test that the header displays the new title "🎭 Willow says Hi"
       * instead of the old title "🎭 Ensemble AI"
       */
      render(<App />);

      const title = screen.getByRole('heading', { level: 4 });
      expect(title).toHaveTextContent('🎭 Willow says Hi');
    });

    it('does not render the old "Ensemble AI" title', () => {
      /**
       * Verify the old title "Ensemble AI" is no longer present
       */
      render(<App />);

      const oldTitle = screen.queryByText(/Ensemble AI/i);
      expect(oldTitle).not.toBeInTheDocument();
    });
  });

  describe('Activity Feed Card Header', () => {
    it('does not render a dropdown filter (Form.Select) for activity filtering', () => {
      /**
       * Test that the activity filter dropdown has been removed from
       * the Activity Feed card header. The filtering is now handled
       * inside the ActivityFeed component with tabs.
       */
      render(<App />);

      // The old dropdown would have options like "All Activities", "Agent Spawned", etc.
      const activityFilterDropdown = screen.queryByRole('combobox', { name: /activity/i });
      expect(activityFilterDropdown).toBeNull();
      
      // Also check there's no select with activity filter options
      const allActivitiesOption = screen.queryByRole('option', { name: /All Activities/i });
      expect(allActivitiesOption).not.toBeInTheDocument();
    });

    it('passes all activities to ActivityFeed without pre-filtering', async () => {
      /**
       * Verify that App.jsx passes all activities to the ActivityFeed component
       * without filtering them first (the old filteredActivities logic should be removed)
       */
      // Import mocked API to set up test data
      const { getRecentActivities } = await import('./services/api');
      getRecentActivities.mockResolvedValue({
        activities: [
          { activity_type: 'agent_started', agent_name: 'test1', timestamp: new Date().toISOString(), data: {} },
          { activity_type: 'agent_completed', agent_name: 'test2', timestamp: new Date().toISOString(), data: {} },
          { activity_type: 'agent_spawned', agent_name: 'test3', timestamp: new Date().toISOString(), data: {} }
        ]
      });

      render(<App />);

      // Wait for activities to load
      await waitFor(() => {
        // All 3 activities should be visible (since ActivityFeed receives all of them)
        // The badge should show total count, not filtered count
        const badge = screen.getByText(/3 activities/i);
        expect(badge).toBeInTheDocument();
      });
    });

    it('shows total activity count in badge without filtering indicator', () => {
      /**
       * Test that the activity feed badge shows just the total count
       * (e.g., "3 activities") not "3 / 5 activities" format
       */
      render(<App />);

      // Should NOT find the old format with "X / Y activities"
      const oldFormatBadge = screen.queryByText(/\d+ \/ \d+ activities/i);
      expect(oldFormatBadge).not.toBeInTheDocument();
    });
  });

  describe('Activity Feed Rendering', () => {
    it('renders ActivityFeed component in the middle column', () => {
      /**
       * Verify that the ActivityFeed component is rendered
       */
      render(<App />);

      // ActivityFeed shows "No activities yet" message when empty
      const emptyMessage = screen.getByText(/No activities yet/i);
      expect(emptyMessage).toBeInTheDocument();
    });
  });
});

describe('Interval Formatting', () => {
  describe('formatInterval function', () => {
    it('formats 1000ms as "1s"', () => {
      const result = formatInterval(1000);
      expect(result).toBe('1s');
    });

    it('formats 60000ms as "1m"', () => {
      const result = formatInterval(60000);
      expect(result).toBe('1m');
    });

    it('formats 300000ms as "5m"', () => {
      const result = formatInterval(300000);
      expect(result).toBe('5m');
    });

    it('formats non-standard intervals in milliseconds', () => {
      const result = formatInterval(2500);
      expect(result).toBe('2500ms');
    });
  });

  describe('interval button labels', () => {
    it('displays interval buttons with formatted labels', () => {
      render(<App />);

      const oneSecondButton = screen.getByRole('button', { name: /^1s$/i });
      const oneMinuteButton = screen.getByRole('button', { name: /^1m$/i });
      const fiveMinuteButton = screen.getByRole('button', { name: /^5m$/i });

      expect(oneSecondButton).toBeInTheDocument();
      expect(oneMinuteButton).toBeInTheDocument();
      expect(fiveMinuteButton).toBeInTheDocument();
    });

    it('does not display buttons with raw millisecond values', () => {
      render(<App />);

      const rawThousandButton = screen.queryByRole('button', { name: /^1000$/i });
      const rawSixtyKButton = screen.queryByRole('button', { name: /^60000$/i });
      const rawThreeHundredKButton = screen.queryByRole('button', { name: /^300000$/i });

      expect(rawThousandButton).not.toBeInTheDocument();
      expect(rawSixtyKButton).not.toBeInTheDocument();
      expect(rawThreeHundredKButton).not.toBeInTheDocument();
    });

    it('does not have old interval buttons for 500ms and 2s', () => {
      render(<App />);

      const fiveHundredMsButton = screen.queryByRole('button', { name: /^500ms$/i });
      const twoSecondsButton = screen.queryByRole('button', { name: /^2s$/i });

      expect(fiveHundredMsButton).not.toBeInTheDocument();
      expect(twoSecondsButton).not.toBeInTheDocument();
    });
  });

  describe('interval button click behavior', () => {
    it('displays "1s" in the interval display area when 1s button is clicked', async () => {
      const user = userEvent.setup();
      render(<App />);

      const oneSecondButton = screen.getByRole('button', { name: /^1s$/i });
      await user.click(oneSecondButton);

      const intervalDisplay = screen.getByText(/1s/i, { 
        selector: ':not(button)'
      });
      expect(intervalDisplay).toBeInTheDocument();
    });

    it('displays "1m" in the interval display area when 1m button is clicked', async () => {
      const user = userEvent.setup();
      render(<App />);

      const oneMinuteButton = screen.getByRole('button', { name: /^1m$/i });
      await user.click(oneMinuteButton);

      const intervalDisplay = screen.getByText(/1m/i, { 
        selector: ':not(button)'
      });
      expect(intervalDisplay).toBeInTheDocument();
    });

    it('displays "5m" in the interval display area when 5m button is clicked', async () => {
      const user = userEvent.setup();
      render(<App />);

      const fiveMinuteButton = screen.getByRole('button', { name: /^5m$/i });
      await user.click(fiveMinuteButton);

      const intervalDisplay = screen.getByText(/5m/i, { 
        selector: ':not(button)'
      });
      expect(intervalDisplay).toBeInTheDocument();
    });
  });
});
