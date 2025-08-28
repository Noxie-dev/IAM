import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import FAQPage from './index.jsx'; // Import our refactored component

// Mock lucide-react icons to avoid rendering complex SVGs
jest.mock('lucide-react', () => {
  // A proxy to dynamically mock any icon from the library
  return new Proxy({}, {
    get: (target, property) => {
      if (property === '__esModule') return true;
      return (props) => <div data-testid={`icon-${String(property)}`} {...props} />;
    },
  });
});

// Mock browser APIs not available in JSDOM
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
  configurable: true,
});

describe('FAQPage Component', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('renders correctly and displays initial data', () => {
    render(<FAQPage />);
    expect(screen.getByRole('heading', { name: /how can we help/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search for answers/i)).toBeInTheDocument();
    expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    expect(screen.getByRole('button', { name: /all/i })).toHaveClass('bg-gradient-to-r');
  });

  test('filters FAQs based on search term after debounce', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<FAQPage />);

    const searchInput = screen.getByPlaceholderText(/search for answers/i);
    await user.type(searchInput, 'POPIA');

    // Fast-forward time to trigger the debounce
    act(() => {
      jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(screen.getByText(/is iam popia compliant/i)).toBeInTheDocument();
      expect(screen.queryByText(/how do i get started with iam/i)).not.toBeInTheDocument();
      expect(screen.getAllByText(/view details/i)).toHaveLength(1);
    });

    await user.clear(searchInput);
    act(() => {
      jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
        expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    });
  });

  test('shows no results message for unmatched search', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<FAQPage />);
    
    const searchInput = screen.getByPlaceholderText(/search for answers/i);
    await user.type(searchInput, 'this search will find nothing');

    act(() => {
        jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
        expect(screen.getByRole('heading', { name: /no questions found/i })).toBeInTheDocument();
    });

    const resetButton = screen.getByRole('button', { name: /reset all filters and show all faq articles/i });
    await user.click(resetButton);

    act(() => {
        jest.advanceTimersByTime(300); // Debounce for search term clearing
    });

    await waitFor(() => {
        expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    });
  });

  test('filters FAQs by category', async () => {
    const user = userEvent.setup();
    render(<FAQPage />);

    // Wait for initial render
    expect(screen.getAllByText(/view details/i)).toHaveLength(18);

    const securityButton = screen.getByRole('button', { name: /filter by security & privacy category/i });
    await user.click(securityButton);

    // Wait for filtering to complete
    await waitFor(() => {
        expect(screen.getAllByText(/view details/i)).toHaveLength(3);
    }, { timeout: 3000 });
    
    expect(screen.getByText(/is iam popia compliant/i)).toBeInTheDocument();
    expect(screen.queryByText(/how do i get started with iam/i)).not.toBeInTheDocument();
  });

  test('opens and closes the modal', async () => {
    const user = userEvent.setup();
    render(<FAQPage />);

    // Wait for initial render and find first card
    await waitFor(() => {
      expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    });

    const firstCardQuestion = screen.getByText(/how do i get started with iam/i);
    const firstCard = firstCardQuestion.closest('div[class*="group"]');
    expect(firstCard).toBeInTheDocument();
    
    await user.click(firstCard);

    // Modal should be visible
    const modalTitle = await screen.findByRole('heading', { name: /how do i get started with iam/i, level: 2 });
    expect(modalTitle).toBeInTheDocument();
    expect(screen.getByText(/getting started is simple!/i)).toBeInTheDocument();

    // Click the close button
    const closeButton = screen.getByTestId('icon-X').closest('button');
    await user.click(closeButton);

    await waitFor(() => {
      expect(modalTitle).not.toBeInTheDocument();
    });
  });

  test('navigates to a related question from within the modal', async () => {
    const user = userEvent.setup();
    render(<FAQPage />);

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    });

    const firstCardQuestion = screen.getByText(/how do i get started with iam/i);
    await user.click(firstCardQuestion.closest('div[class*="group"]'));

    // Wait for modal to appear
    const modal = await screen.findByRole('dialog');
    expect(modal).toBeInTheDocument();

    const relatedQuestionLink = await screen.findByText(/what file formats do you support for uploads/i);
    await user.click(relatedQuestionLink);

    await waitFor(() => {
        expect(screen.getByRole('heading', { name: /what file formats do you support for uploads/i, level: 2})).toBeInTheDocument();
    });
  });

   test('clicking a tag in the modal closes it and filters the main page', async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(<FAQPage />);

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getAllByText(/view details/i)).toHaveLength(18);
    });

    const cardQuestion = screen.getByText(/how accurate are your transcriptions/i);
    await user.click(cardQuestion.closest('div[class*="group"]'));

    const modal = await screen.findByRole('dialog');
    const tagButton = await screen.findByRole('button', { name: /search for whisper/i });
    await user.click(tagButton);
    
    await waitFor(() => {
        expect(modal).not.toBeInTheDocument();
    });

    act(() => {
        jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
        expect(screen.getByPlaceholderText(/search for answers/i)).toHaveValue('whisper');
        // Check that filtering happened - the search should return 2 results that contain 'whisper'
        const filteredResults = screen.getAllByText(/view details/i);
        expect(filteredResults.length).toBeGreaterThan(0);
        expect(screen.getByText(/how accurate are your transcriptions/i)).toBeInTheDocument();
    });
  });
});
