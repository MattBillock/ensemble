import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';

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
