import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProblemInputForm from './ProblemInputForm';

describe('ProblemInputForm', () => {
  it('renders a textarea for problem description', () => {
    render(<ProblemInputForm onProblemSubmit={vi.fn()} />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    expect(textarea).toBeInTheDocument();
    expect(textarea.tagName).toBe('TEXTAREA');
  });

  it('renders a submit button with correct text', () => {
    render(<ProblemInputForm onProblemSubmit={vi.fn()} />);

    const button = screen.getByRole('button', { name: /generate solution/i });
    expect(button).toBeInTheDocument();
    expect(button.type).toBe('submit');
  });

  it('calls onProblemSubmit when form is submitted with valid input', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();

    render(<ProblemInputForm onProblemSubmit={mockSubmit} />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    // Type into textarea
    await user.type(textarea, 'Build a calculator app');

    // Submit form
    await user.click(button);

    expect(mockSubmit).toHaveBeenCalledTimes(1);
    expect(mockSubmit).toHaveBeenCalledWith('Build a calculator app');
  });

  it('does not call onProblemSubmit when input is empty', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();

    render(<ProblemInputForm onProblemSubmit={mockSubmit} />);

    const button = screen.getByRole('button', { name: /generate solution/i });

    // Submit without typing anything
    await user.click(button);

    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('does not call onProblemSubmit when input is only whitespace', async () => {
    const mockSubmit = vi.fn();
    const user = userEvent.setup();

    render(<ProblemInputForm onProblemSubmit={mockSubmit} />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    // Type only whitespace
    await user.type(textarea, '   ');
    await user.click(button);

    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('updates textarea value as user types', async () => {
    const user = userEvent.setup();

    render(<ProblemInputForm onProblemSubmit={vi.fn()} />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);

    expect(textarea.value).toBe('');

    await user.type(textarea, 'Test problem');

    expect(textarea.value).toBe('Test problem');
  });

  it('prevents default form submission behavior', () => {
    const mockSubmit = vi.fn();

    render(<ProblemInputForm onProblemSubmit={mockSubmit} />);

    const form = screen.getByRole('button', { name: /generate solution/i }).closest('form');
    const event = new Event('submit', { bubbles: true, cancelable: true });

    form.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
  });

  it('has accessible form structure', () => {
    render(<ProblemInputForm onProblemSubmit={vi.fn()} />);

    const textarea = screen.getByPlaceholderText(/describe your problem/i);
    const button = screen.getByRole('button', { name: /generate solution/i });

    // Check form contains both elements
    const form = button.closest('form');
    expect(form).toContainElement(textarea);
    expect(form).toContainElement(button);
  });
});
