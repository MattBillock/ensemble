import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App, { formatInterval } from './App';

// Mock the API calls to prevent actual network requests
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

describe('formatInterval helper function', () => {
  it('formats 1000ms as 1s', () => {
    expect(formatInterval(1000)).toBe('1s');
  });

  it('formats 60000ms as 1m', () => {
    expect(formatInterval(60000)).toBe('1m');
  });

  it('formats 300000ms as 5m', () => {
    expect(formatInterval(300000)).toBe('5m');
  });

  it('formats other values with ms suffix', () => {
    expect(formatInterval(2500)).toBe('2500ms');
  });

  it('formats 500 as 500ms', () => {
    expect(formatInterval(500)).toBe('500ms');
  });
});

describe('Interval buttons', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders 1s interval button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: '1s' });
    expect(button).toBeInTheDocument();
  });

  it('renders 1m interval button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: '1m' });
    expect(button).toBeInTheDocument();
  });

  it('renders 5m interval button', () => {
    render(<App />);
    const button = screen.getByRole('button', { name: '5m' });
    expect(button).toBeInTheDocument();
  });

  it('does not render 500ms interval button', () => {
    render(<App />);
    const button = screen.queryByRole('button', { name: '500ms' });
    expect(button).not.toBeInTheDocument();
  });

  it('does not render 2s interval button', () => {
    render(<App />);
    const button = screen.queryByRole('button', { name: '2s' });
    expect(button).not.toBeInTheDocument();
  });
});

describe('Interval display text', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays formatted interval in status text', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Click 1m button and check display
    const oneMinButton = screen.getByRole('button', { name: '1m' });
    await user.click(oneMinButton);
    
    // Should show "Updates every 1m" not "Updates every 60000ms"
    expect(screen.getByText(/Updates every 1m/)).toBeInTheDocument();
  });

  it('displays 1s format when 1s interval selected', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const oneSecButton = screen.getByRole('button', { name: '1s' });
    await user.click(oneSecButton);
    
    expect(screen.getByText(/Updates every 1s/)).toBeInTheDocument();
  });

  it('displays 5m format when 5m interval selected', async () => {
    const user = userEvent.setup();
    render(<App />);
    
    const fiveMinButton = screen.getByRole('button', { name: '5m' });
    await user.click(fiveMinButton);
    
    expect(screen.getByText(/Updates every 5m/)).toBeInTheDocument();
  });
});
