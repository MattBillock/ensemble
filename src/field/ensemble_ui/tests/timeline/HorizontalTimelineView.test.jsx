import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import HorizontalTimelineView from '../../components/timeline/HorizontalTimelineView';

// Mock the data provider
const mockDataProvider = {
  getData: jest.fn(),
  refreshData: jest.fn(),
  subscribe: jest.fn(),
  unsubscribe: jest.fn()
};

// Mock scroll methods
const mockScrollTo = jest.fn();
const mockScrollLeft = jest.fn();

// Setup DOM mocking for scroll behavior
beforeAll(() => {
  Object.defineProperty(Element.prototype, 'scrollTo', {
    writable: true,
    value: mockScrollTo
  });
  
  Object.defineProperty(Element.prototype, 'scrollLeft', {
    get: function() { return this._scrollLeft || 0; },
    set: function(value) { this._scrollLeft = value; }
  });
  
  Object.defineProperty(Element.prototype, 'scrollWidth', {
    writable: true,
    value: 2000
  });
  
  Object.defineProperty(Element.prototype, 'clientWidth', {
    writable: true,
    value: 800
  });
});

describe('HorizontalTimelineView - Scroll Position Preservation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockDataProvider.getData.mockResolvedValue([
      { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 10 },
      { id: 2, timestamp: '2024-01-02T00:00:00Z', value: 20 },
      { id: 3, timestamp: '2024-01-03T00:00:00Z', value: 15 }
    ]);
  });

  describe('test_scroll_position_maintained_during_data_refresh', () => {
    /**
     * Verifies that scroll position is preserved when data is refreshed
     * Tests the core requirement of maintaining scroll state during data updates
     */
    test('should maintain scroll position when data is refreshed', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      
      // Set initial scroll position
      const initialScrollLeft = 500;
      timelineContainer.scrollLeft = initialScrollLeft;
      fireEvent.scroll(timelineContainer);

      // Simulate data refresh
      const updatedData = [
        { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 12 },
        { id: 2, timestamp: '2024-01-02T00:00:00Z', value: 25 },
        { id: 3, timestamp: '2024-01-03T00:00:00Z', value: 18 },
        { id: 4, timestamp: '2024-01-04T00:00:00Z', value: 22 }
      ];
      
      mockDataProvider.getData.mockResolvedValue(updatedData);
      
      // Trigger data refresh
      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        expect(timelineContainer.scrollLeft).toBe(initialScrollLeft);
      });

      expect(mockDataProvider.getData).toHaveBeenCalledTimes(2);
    });
  });

  describe('test_component_state_preserved_across_updates', () => {
    /**
     * Ensures that component internal state is preserved during data updates
     * Tests zoom level, view settings, and selection state preservation
     */
    test('should preserve component state across data updates', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          initialZoom={1.5}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      // Set component state (zoom, selection, etc.)
      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      const zoomControls = screen.getByTestId('zoom-controls');
      
      // Simulate zoom change
      fireEvent.click(screen.getByTestId('zoom-in-button'));
      
      // Simulate item selection
      const timelineItem = screen.getByTestId('timeline-item-1');
      fireEvent.click(timelineItem);
      
      // Capture current state
      const currentZoom = screen.getByTestId('zoom-level').textContent;
      const selectedItem = screen.getByTestId('selected-item-indicator');
      
      // Trigger data refresh
      const updatedData = [
        { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 30 },
        { id: 2, timestamp: '2024-01-02T00:00:00Z', value: 35 }
      ];
      
      mockDataProvider.getData.mockResolvedValue(updatedData);
      
      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          initialZoom={1.5}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        // Verify zoom level preserved
        expect(screen.getByTestId('zoom-level').textContent).toBe(currentZoom);
        // Verify selection preserved (if item still exists)
        expect(screen.getByTestId('selected-item-indicator')).toBeInTheDocument();
      });
    });
  });

  describe('test_minimal_rerendering_during_refresh', () => {
    /**
     * Checks that unnecessary re-renders are minimized during data refresh
     * Tests React optimization and memoization effectiveness
     */
    test('should minimize unnecessary re-renders during data refresh', async () => {
      const renderSpy = jest.fn();
      
      const TestWrapper = (props) => {
        renderSpy();
        return <HorizontalTimelineView {...props} />;
      };

      const { rerender } = render(
        <TestWrapper 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const initialRenderCount = renderSpy.mock.calls.length;

      // Trigger data refresh with identical structure
      mockDataProvider.getData.mockResolvedValue([
        { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 10 },
        { id: 2, timestamp: '2024-01-02T00:00:00Z', value: 20 },
        { id: 3, timestamp: '2024-01-03T00:00:00Z', value: 15 }
      ]);

      rerender(
        <TestWrapper 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        const finalRenderCount = renderSpy.mock.calls.length;
        // Should only render once more for data refresh, not multiple times
        expect(finalRenderCount - initialRenderCount).toBeLessThanOrEqual(2);
      });

      // Verify memoization is working
      expect(screen.getByTestId('render-optimization-indicator')).toHaveAttribute('data-optimized', 'true');
    });
  });

  describe('test_scroll_preservation_different_positions', () => {
    /**
     * Tests scroll preservation with different initial scroll positions
     * Validates behavior at start, middle, and end positions
     */
    test('should preserve scroll position at different initial positions', async () => {
      const testPositions = [0, 250, 500, 750, 1000];
      
      for (const position of testPositions) {
        const { rerender, unmount } = render(
          <HorizontalTimelineView 
            dataProvider={mockDataProvider}
            height={400}
            width={800}
          />
        );

        await waitFor(() => {
          expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
        });

        const timelineContainer = screen.getByTestId('horizontal-timeline-container');
        
        // Set scroll position
        timelineContainer.scrollLeft = position;
        fireEvent.scroll(timelineContainer);

        // Trigger data refresh
        mockDataProvider.getData.mockResolvedValue([
          { id: 1, timestamp: '2024-01-01T00:00:00Z', value: Math.random() * 100 }
        ]);

        rerender(
          <HorizontalTimelineView 
            dataProvider={mockDataProvider}
            height={400}
            width={800}
            refreshTrigger={Date.now()}
          />
        );

        await waitFor(() => {
          expect(timelineContainer.scrollLeft).toBe(position);
        });

        unmount();
      }
    });
  });

  describe('test_scroll_behavior_various_data_scenarios', () => {
    /**
     * Validates scroll behavior with various data update scenarios
     * Tests data addition, removal, modification, and empty states
     */
    test('should handle scroll preservation during data addition', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      timelineContainer.scrollLeft = 300;
      fireEvent.scroll(timelineContainer);

      // Add more data items
      const expandedData = [
        { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 10 },
        { id: 2, timestamp: '2024-01-02T00:00:00Z', value: 20 },
        { id: 3, timestamp: '2024-01-03T00:00:00Z', value: 15 },
        { id: 4, timestamp: '2024-01-04T00:00:00Z', value: 25 },
        { id: 5, timestamp: '2024-01-05T00:00:00Z', value: 30 }
      ];

      mockDataProvider.getData.mockResolvedValue(expandedData);

      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        expect(timelineContainer.scrollLeft).toBe(300);
        expect(screen.getAllByTestId(/timeline-item-/)).toHaveLength(5);
      });
    });

    test('should handle scroll preservation during data removal', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      timelineContainer.scrollLeft = 400;
      fireEvent.scroll(timelineContainer);

      // Remove some data items
      const reducedData = [
        { id: 1, timestamp: '2024-01-01T00:00:00Z', value: 10 }
      ];

      mockDataProvider.getData.mockResolvedValue(reducedData);

      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        // Should preserve scroll position or adjust appropriately if content is shorter
        const maxScroll = timelineContainer.scrollWidth - timelineContainer.clientWidth;
        expect(timelineContainer.scrollLeft).toBeLessThanOrEqual(Math.max(400, maxScroll));
        expect(screen.getAllByTestId(/timeline-item-/)).toHaveLength(1);
      });
    });

    test('should handle scroll preservation with empty data', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      timelineContainer.scrollLeft = 200;
      fireEvent.scroll(timelineContainer);

      // Set empty data
      mockDataProvider.getData.mockResolvedValue([]);

      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('empty-timeline-message')).toBeInTheDocument();
        expect(timelineContainer.scrollLeft).toBe(0); // Should reset to 0 for empty data
      });
    });
  });

  describe('test_error_handling_during_scroll_preservation', () => {
    /**
     * Tests error handling scenarios while maintaining scroll position
     * Validates graceful degradation when data loading fails
     */
    test('should handle data loading errors gracefully while preserving scroll', async () => {
      const { rerender } = render(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
        />
      );

      await waitFor(() => {
        expect(screen.getByTestId('horizontal-timeline-container')).toBeInTheDocument();
      });

      const timelineContainer = screen.getByTestId('horizontal-timeline-container');
      timelineContainer.scrollLeft = 350;
      fireEvent.scroll(timelineContainer);

      // Simulate data loading error
      mockDataProvider.getData.mockRejectedValue(new Error('Data loading failed'));

      rerender(
        <HorizontalTimelineView 
          dataProvider={mockDataProvider}
          height={400}
          width={800}
          refreshTrigger={Date.now()}
        />
      );

      await waitFor(() => {
        // Should maintain scroll position even on error
        expect(timelineContainer.scrollLeft).toBe(350);
        // Should show error state
        expect(screen.getByTestId('error-message')).toBeInTheDocument();
      });
    });
  });
});