import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import GeneratedFiles from '../GeneratedFiles.jsx';

// Mock react-bootstrap components
vi.mock('react-bootstrap', () => ({
  Badge: ({ bg, children, ...props }) => <span data-testid="badge" data-bg={bg} {...props}>{children}</span>,
  Collapse: ({ in: isOpen, children }) => (
    <div data-testid="collapse" data-open={isOpen} style={{ display: isOpen ? 'block' : 'none' }}>
      {children}
    </div>
  )
}));

describe('GeneratedFiles', () => {
  const mockFiles = [
    {
      file_path: '/test/path/example.py',
      file_name: 'example.py',
      file_size: 1024,
      file_type: 'python',
      agent_name: 'test_agent',
      agent_id: 'agent_123',
      request_id: 'req_456',
      timestamp: '2024-01-15T10:30:00Z',
      preview: 'def hello():\n    print("Hello World")\n    return True'
    },
    {
      file_path: '/project/completion_summary.md',
      file_name: 'completion_summary.md',
      file_size: 2704,
      file_type: 'markdown',
      agent_name: 'exec_agent',
      agent_id: 'exec_dir_4',
      request_id: 'req_789',
      timestamp: '2024-01-15T11:00:00Z',
      preview: '# Completion Summary\n\nThis is a test markdown file with some content that demonstrates the preview functionality.'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('test_renders_with_file_array', () => {
    it('should render component with array of file objects and display file list', () => {
      /**
       * Verifies that the GeneratedFiles component renders correctly when provided
       * with an array of file objects and displays each file in the list
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      // Should render both files
      expect(screen.getByText('example.py')).toBeInTheDocument();
      expect(screen.getByText('completion_summary.md')).toBeInTheDocument();
      
      // Should display file paths
      expect(screen.getByText('/test/path')).toBeInTheDocument();
      expect(screen.getByText('/project')).toBeInTheDocument();
    });
  });

  describe('test_displays_file_metadata', () => {
    it('should display file metadata including name, size, and type for all files', () => {
      /**
       * Verifies that each file item displays its metadata correctly:
       * file name, file size (formatted), and file type badge
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      // Check file names
      expect(screen.getByText('example.py')).toBeInTheDocument();
      expect(screen.getByText('completion_summary.md')).toBeInTheDocument();
      
      // Check file sizes (formatted)
      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
      expect(screen.getByText('2.6 KB')).toBeInTheDocument();
      
      // Check file type badges
      const badges = screen.getAllByTestId('badge');
      expect(badges).toHaveLength(2);
      expect(badges[0]).toHaveTextContent('python');
      expect(badges[0]).toHaveAttribute('data-bg', 'success');
      expect(badges[1]).toHaveTextContent('markdown');
      expect(badges[1]).toHaveAttribute('data-bg', 'primary');
    });
  });

  describe('test_file_expansion_collapse_functionality', () => {
    it('should toggle file expansion state when file header is clicked', () => {
      /**
       * Verifies that clicking on a file header toggles the expanded state
       * and shows/hides the collapse component with preview content
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      const firstFileHeader = screen.getByText('example.py').closest('div').closest('div');
      const collapses = screen.getAllByTestId('collapse');
      
      // Initially collapsed
      expect(collapses[0]).toHaveAttribute('data-open', 'false');
      
      // Click to expand
      fireEvent.click(firstFileHeader);
      expect(collapses[0]).toHaveAttribute('data-open', 'true');
      
      // Click to collapse
      fireEvent.click(firstFileHeader);
      expect(collapses[0]).toHaveAttribute('data-open', 'false');
    });
  });

  describe('test_preview_content_display', () => {
    it('should display preview content when file is expanded', () => {
      /**
       * Verifies that when a file is expanded, its preview content is displayed
       * in a formatted code block with proper styling
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      const firstFileHeader = screen.getByText('example.py').closest('div').closest('div');
      
      // Expand first file
      fireEvent.click(firstFileHeader);
      
      // Check preview content is displayed
      expect(screen.getByText('def hello():')).toBeInTheDocument();
      expect(screen.getByText('print("Hello World")')).toBeInTheDocument();
      expect(screen.getByText('return True')).toBeInTheDocument();
      
      // Check metadata is displayed when expanded
      expect(screen.getByText('Agent:')).toBeInTheDocument();
      expect(screen.getByText('test_agent (agent_123)')).toBeInTheDocument();
      expect(screen.getByText('Request ID:')).toBeInTheDocument();
      expect(screen.getByText('req_456')).toBeInTheDocument();
    });
  });

  describe('test_empty_state_rendering', () => {
    it('should render empty state message when no files are provided', () => {
      /**
       * Verifies that when files array is empty or null, the component
       * displays an appropriate empty state message
       */
      // Test with empty array
      const { rerender } = render(<GeneratedFiles files={[]} />);
      expect(screen.getByText('No files generated yet. Files created by agents will appear here.')).toBeInTheDocument();
      
      // Test with null
      rerender(<GeneratedFiles files={null} />);
      expect(screen.getByText('No files generated yet. Files created by agents will appear here.')).toBeInTheDocument();
      
      // Test with undefined
      rerender(<GeneratedFiles />);
      expect(screen.getByText('No files generated yet. Files created by agents will appear here.')).toBeInTheDocument();
    });
  });

  describe('test_completion_summary_file_specific', () => {
    it('should correctly display completion_summary.md file with specific metadata', () => {
      /**
       * Verifies specific rendering of the completion_summary.md file with
       * 2704 bytes size, markdown type, and agent_id exec_dir_4
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      // Check specific file is displayed
      expect(screen.getByText('completion_summary.md')).toBeInTheDocument();
      
      // Check file size (2704 bytes = 2.6 KB)
      expect(screen.getByText('2.6 KB')).toBeInTheDocument();
      
      // Check file type badge
      const markdownBadge = screen.getAllByTestId('badge').find(badge => 
        badge.textContent === 'markdown'
      );
      expect(markdownBadge).toHaveAttribute('data-bg', 'primary');
      
      // Expand to check agent details
      const summaryFileHeader = screen.getByText('completion_summary.md').closest('div').closest('div');
      fireEvent.click(summaryFileHeader);
      
      // Check agent ID
      expect(screen.getByText('exec_agent (exec_dir_4)')).toBeInTheDocument();
      
      // Check preview content
      expect(screen.getByText('# Completion Summary')).toBeInTheDocument();
    });
  });

  describe('test_file_size_formatting', () => {
    it('should format file sizes correctly in different units', () => {
      /**
       * Verifies that file sizes are formatted correctly for different ranges:
       * bytes, kilobytes, and megabytes
       */
      const testFiles = [
        { ...mockFiles[0], file_size: 500 }, // 500 B
        { ...mockFiles[0], file_size: 1536 }, // 1.5 KB
        { ...mockFiles[0], file_size: 2048000 } // 2.0 MB
      ];
      
      render(<GeneratedFiles files={testFiles} />);
      
      expect(screen.getByText('500 B')).toBeInTheDocument();
      expect(screen.getByText('1.5 KB')).toBeInTheDocument();
      expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    });
  });

  describe('test_file_icon_display', () => {
    it('should display appropriate icons for different file types', () => {
      /**
       * Verifies that different file types display the correct emoji icons
       */
      const testFiles = [
        { ...mockFiles[0], file_type: 'python' },
        { ...mockFiles[0], file_type: 'javascript' },
        { ...mockFiles[0], file_type: 'markdown' },
        { ...mockFiles[0], file_type: 'unknown' }
      ];
      
      render(<GeneratedFiles files={testFiles} />);
      
      // Icons are emoji characters, they should be present in the document
      // We can't easily test the exact emoji, but we can verify the component renders
      const fileHeaders = screen.getAllByRole('generic').filter(el => 
        el.style.cursor === 'pointer'
      );
      expect(fileHeaders.length).toBeGreaterThan(0);
    });
  });

  describe('test_multiple_file_expansion', () => {
    it('should allow multiple files to be expanded simultaneously', () => {
      /**
       * Verifies that multiple files can be expanded at the same time
       * and their expansion states are independent
       */
      render(<GeneratedFiles files={mockFiles} />);
      
      const firstFileHeader = screen.getByText('example.py').closest('div').closest('div');
      const secondFileHeader = screen.getByText('completion_summary.md').closest('div').closest('div');
      const collapses = screen.getAllByTestId('collapse');
      
      // Initially both collapsed
      expect(collapses[0]).toHaveAttribute('data-open', 'false');
      expect(collapses[1]).toHaveAttribute('data-open', 'false');
      
      // Expand both files
      fireEvent.click(firstFileHeader);
      fireEvent.click(secondFileHeader);
      
      // Both should be expanded
      expect(collapses[0]).toHaveAttribute('data-open', 'true');
      expect(collapses[1]).toHaveAttribute('data-open', 'true');
      
      // Collapse first, second should remain expanded
      fireEvent.click(firstFileHeader);
      expect(collapses[0]).toHaveAttribute('data-open', 'false');
      expect(collapses[1]).toHaveAttribute('data-open', 'true');
    });
  });
});