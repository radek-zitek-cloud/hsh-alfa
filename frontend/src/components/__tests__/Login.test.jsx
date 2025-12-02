import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login from '../Login';

// Mock the AuthContext
const mockGetAuthUrl = vi.fn();

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    getAuthUrl: mockGetAuthUrl,
  }),
}));

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetAuthUrl.mockResolvedValue('https://accounts.google.com/oauth2/auth?...');
  });

  it('renders the login page with title and description', () => {
    render(<Login />);

    expect(screen.getByRole('heading', { name: /home sweet home/i })).toBeInTheDocument();
    expect(
      screen.getByText(/your personal homepage with bookmarks and widgets/i)
    ).toBeInTheDocument();
  });

  it('renders the Google sign-in button', () => {
    render(<Login />);

    expect(screen.getByRole('button', { name: /sign in with google/i })).toBeInTheDocument();
  });

  it('shows loading state when login button is clicked', async () => {
    const user = userEvent.setup();
    // Keep the promise pending to test loading state
    mockGetAuthUrl.mockImplementation(() => new Promise(() => {}));

    render(<Login />);

    const button = screen.getByRole('button', { name: /sign in with google/i });
    await user.click(button);

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('calls getAuthUrl when login button is clicked', async () => {
    const user = userEvent.setup();

    // Use jsdom location mock
    const originalLocation = window.location;
    delete window.location;
    window.location = { href: '' };

    render(<Login />);

    const button = screen.getByRole('button', { name: /sign in with google/i });
    await user.click(button);

    await waitFor(() => {
      expect(mockGetAuthUrl).toHaveBeenCalled();
    });

    // Restore location
    window.location = originalLocation;
  });

  it('displays error message when login fails', async () => {
    const user = userEvent.setup();
    mockGetAuthUrl.mockRejectedValue(new Error('Auth failed'));

    render(<Login />);

    const button = screen.getByRole('button', { name: /sign in with google/i });
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByText(/failed to initiate login/i)).toBeInTheDocument();
    });
  });

  it('renders the footer text', () => {
    render(<Login />);

    expect(screen.getByText(/sign in to access your personalized homepage/i)).toBeInTheDocument();
  });

  it('disables the button while loading', async () => {
    const user = userEvent.setup();
    mockGetAuthUrl.mockImplementation(() => new Promise(() => {}));

    render(<Login />);

    const button = screen.getByRole('button', { name: /sign in with google/i });
    await user.click(button);

    // Button should be disabled after click
    expect(button).toBeDisabled();
  });
});
