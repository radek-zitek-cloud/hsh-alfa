import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import DateHeader from '../DateHeader';

// Mock the wikipediaService
vi.mock('../../services/wikipediaService', () => ({
  getRandomOnThisDayEvent: vi.fn(),
  getRandomFallbackFact: vi.fn(),
}));

import {
  getRandomOnThisDayEvent,
  getRandomFallbackFact,
} from '../../services/wikipediaService';

describe('DateHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getRandomOnThisDayEvent.mockResolvedValue('In 1215, King John sealed Magna Carta');
    getRandomFallbackFact.mockReturnValue('Interesting fallback fact');
  });

  it('renders the date header container', async () => {
    await act(async () => {
      render(<DateHeader />);
    });

    // The component should have rendered with some date text
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toBeInTheDocument();
  });

  it('shows loading state initially', async () => {
    // Delay the mock to capture loading state
    getRandomOnThisDayEvent.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve('Historical event'), 100))
    );

    await act(async () => {
      render(<DateHeader />);
    });

    // Loading state should appear initially
    expect(screen.getByText(/loading historical event/i)).toBeInTheDocument();
  });

  it('displays the historical event after loading', async () => {
    await act(async () => {
      render(<DateHeader />);
    });

    await waitFor(() => {
      expect(screen.getByText(/on this day:/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/magna carta/i)).toBeInTheDocument();
  });

  it('displays fallback fact when API fails', async () => {
    getRandomOnThisDayEvent.mockRejectedValue(new Error('API error'));

    // Suppress the console warning for this test
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {});

    await act(async () => {
      render(<DateHeader />);
    });

    await waitFor(() => {
      expect(screen.getByText(/interesting fallback fact/i)).toBeInTheDocument();
    });

    consoleWarn.mockRestore();
  });

  it('calls getRandomOnThisDayEvent on mount', async () => {
    await act(async () => {
      render(<DateHeader />);
    });

    await waitFor(() => {
      expect(getRandomOnThisDayEvent).toHaveBeenCalled();
    });
  });
});
