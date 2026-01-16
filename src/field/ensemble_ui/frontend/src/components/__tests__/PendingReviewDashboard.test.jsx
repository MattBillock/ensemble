import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PendingReviewDashboard from '../PendingReviewDashboard';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  getPendingReviews: vi.fn(),
  getPendingReviewContent: vi.fn(),
  approvePendingReview: vi.fn(),
  rejectPendingReview: vi.fn(),
  scanForPendingReviews: vi.fn(),
}));

describe('PendingReviewDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Loading', () => {
    it('shows loading spinner while fetching reviews', () => {
      api.getPendingReviews.mockImplementation(() => new Promise(() => {}));

      render(<PendingReviewDashboard />);

      expect(screen.getByText(/loading pending reviews/i)).toBeInTheDocument();
    });

    it('renders empty state when no reviews', async () => {
      api.getPendingReviews.mockResolvedValue({ reviews: [], count: 0 });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/no pending reviews/i)).toBeInTheDocument();
      });
    });

    it('renders list of pending reviews', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/requirements.md',
          review_type: 'requirements',
          detection_method: 'auto',
          agent_name: 'Test Agent',
          created_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          file_path: 'src/output/architecture.md',
          review_type: 'architecture',
          detection_method: 'explicit',
          agent_name: 'Another Agent',
          created_at: '2024-01-02T00:00:00Z',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 2 });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('requirements.md')).toBeInTheDocument();
        expect(screen.getByText('architecture.md')).toBeInTheDocument();
      });
    });
  });

  describe('Review Selection', () => {
    it('shows content when a review is selected', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/requirements.md',
          review_type: 'requirements',
          detection_method: 'auto',
          action: 'start_implementation',
        },
      ];

      const mockContent = {
        review_id: 1,
        file_path: 'src/output/requirements.md',
        frontmatter: { review_type: 'requirements' },
        content: '# Test Requirements\n\nThis is the content.',
      };

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });
      api.getPendingReviewContent.mockResolvedValue(mockContent);

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('requirements.md')).toBeInTheDocument();
      });

      // Click on the review item
      fireEvent.click(screen.getByText('requirements.md'));

      await waitFor(() => {
        expect(screen.getByText(/test requirements/i)).toBeInTheDocument();
      });
    });

    it('shows approve and reject buttons when review selected', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/test.md',
          review_type: 'requirements',
          detection_method: 'auto',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });
      api.getPendingReviewContent.mockResolvedValue({
        content: '# Test',
        frontmatter: {},
      });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('test.md')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('test.md'));

      await waitFor(() => {
        expect(screen.getByText(/approve & execute/i)).toBeInTheDocument();
        expect(screen.getByText(/reject/i)).toBeInTheDocument();
      });
    });
  });

  describe('Review Actions', () => {
    it('calls approve API when approve button clicked', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/test.md',
          review_type: 'requirements',
          detection_method: 'auto',
          status: 'pending',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });
      api.getPendingReviewContent.mockResolvedValue({
        content: '# Test',
        frontmatter: {},
      });
      api.approvePendingReview.mockResolvedValue({
        success: true,
        result: { agent_id: 'exec_1' },
      });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('test.md')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('test.md'));

      await waitFor(() => {
        expect(screen.getByText(/approve & execute/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/approve & execute/i));

      await waitFor(() => {
        expect(api.approvePendingReview).toHaveBeenCalledWith(1);
      });
    });

    it('calls reject API when reject button clicked', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/test.md',
          review_type: 'requirements',
          detection_method: 'auto',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });
      api.getPendingReviewContent.mockResolvedValue({
        content: '# Test',
        frontmatter: {},
      });
      api.rejectPendingReview.mockResolvedValue({ success: true });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('test.md')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('test.md'));

      await waitFor(() => {
        expect(screen.getByText(/reject/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText(/reject/i));

      await waitFor(() => {
        expect(api.rejectPendingReview).toHaveBeenCalledWith(1);
      });
    });
  });

  describe('Scan Functionality', () => {
    it('calls scan API when scan button clicked', async () => {
      api.getPendingReviews.mockResolvedValue({ reviews: [], count: 0 });
      api.scanForPendingReviews.mockResolvedValue({
        scanned: true,
        new_reviews: 2,
      });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /scan for new files/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /scan for new files/i }));

      await waitFor(() => {
        expect(api.scanForPendingReviews).toHaveBeenCalled();
      });
    });

    it('shows success message after scan finds files', async () => {
      // Mock initial empty state
      api.getPendingReviews.mockResolvedValue({ reviews: [], count: 0 });
      api.scanForPendingReviews.mockResolvedValue({
        scanned: true,
        new_reviews: 3,
      });

      render(<PendingReviewDashboard />);

      // Wait for initial load to complete - use getByRole to find the button specifically
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /scan for new files/i })).toBeInTheDocument();
      });

      // Click scan button
      fireEvent.click(screen.getByRole('button', { name: /scan for new files/i }));

      // Wait for scan API to be called and success message to appear
      await waitFor(() => {
        expect(api.scanForPendingReviews).toHaveBeenCalled();
      });

      // Check for success message - using a more flexible matcher
      await waitFor(() => {
        const alert = screen.queryByRole('alert');
        expect(alert).toBeInTheDocument();
        expect(alert.textContent).toMatch(/found 3 new reviewable file/i);
      }, { timeout: 3000 });
    });
  });

  describe('Badge Display', () => {
    it('displays review type badges', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/requirements.md',
          review_type: 'requirements',
          detection_method: 'auto',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('requirements')).toBeInTheDocument();
      });
    });

    it('displays detection method badges for auto-detected files', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/auto.md',
          review_type: 'requirements',
          detection_method: 'auto',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Auto-detected')).toBeInTheDocument();
      });
    });

    it('displays detection method badges for explicitly reported files', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/explicit.md',
          review_type: 'architecture',
          detection_method: 'explicit',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Reported')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error message when fetch fails', async () => {
      api.getPendingReviews.mockRejectedValue(new Error('Network error'));

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/failed to load pending reviews/i)).toBeInTheDocument();
      });
    });

    it('shows error message when content fetch fails', async () => {
      const mockReviews = [
        {
          id: 1,
          file_path: 'src/output/test.md',
          review_type: 'requirements',
          detection_method: 'auto',
        },
      ];

      api.getPendingReviews.mockResolvedValue({ reviews: mockReviews, count: 1 });
      api.getPendingReviewContent.mockRejectedValue(new Error('Content error'));

      render(<PendingReviewDashboard />);

      await waitFor(() => {
        expect(screen.getByText('test.md')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('test.md'));

      await waitFor(() => {
        expect(screen.getByText(/failed to load file content/i)).toBeInTheDocument();
      });
    });
  });
});
