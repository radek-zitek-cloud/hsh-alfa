import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import BookmarkForm from '../BookmarkForm'
import { bookmarksApi } from '../../services/api'

// Mock the API
vi.mock('../../services/api', () => ({
  bookmarksApi: {
    create: vi.fn(),
    update: vi.fn(),
  },
}))

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('BookmarkForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Validation', () => {
    it('should show error when title is empty', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Title is required')).toBeInTheDocument()
      })
    })

    it('should show error when URL is empty', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      fireEvent.change(titleInput, { target: { value: 'Test Bookmark' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('URL is required')).toBeInTheDocument()
      })
    })

    it('should show error for invalid URL format', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'not-a-valid-url' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/Invalid URL format/i)).toBeInTheDocument()
      })
    })

    it('should block dangerous URL schemes (javascript:)', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Malicious' } })
      fireEvent.change(urlInput, { target: { value: 'javascript:alert("xss")' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/URL scheme not allowed/i)).toBeInTheDocument()
      })
    })

    it('should block dangerous URL schemes (data:)', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Malicious' } })
      fireEvent.change(urlInput, { target: { value: 'data:text/html,<script>alert("xss")</script>' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/URL scheme not allowed/i)).toBeInTheDocument()
      })
    })

    it('should validate favicon URL for dangerous schemes', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)
      const faviconInput = screen.getByLabelText(/favicon url/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })
      fireEvent.change(faviconInput, { target: { value: 'javascript:void(0)' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText(/Favicon URL scheme not allowed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Tags Processing', () => {
    it('should convert comma-separated tags string to array', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockResolvedValue({ data: { id: 1 } })

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)
      const tagsInput = screen.getByLabelText(/tags/i)

      fireEvent.change(titleInput, { target: { value: 'Test Bookmark' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })
      fireEvent.change(tagsInput, { target: { value: 'tag1, tag2, tag3' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(bookmarksApi.create).toHaveBeenCalledWith(
          expect.objectContaining({
            tags: ['tag1', 'tag2', 'tag3'],
          })
        )
      })
    })

    it('should trim whitespace from tags', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockResolvedValue({ data: { id: 1 } })

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)
      const tagsInput = screen.getByLabelText(/tags/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })
      fireEvent.change(tagsInput, { target: { value: '  tag1  ,  tag2  ,  tag3  ' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(bookmarksApi.create).toHaveBeenCalledWith(
          expect.objectContaining({
            tags: ['tag1', 'tag2', 'tag3'],
          })
        )
      })
    })

    it('should filter out empty tags', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockResolvedValue({ data: { id: 1 } })

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)
      const tagsInput = screen.getByLabelText(/tags/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })
      fireEvent.change(tagsInput, { target: { value: 'tag1, , tag2, ,,' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(bookmarksApi.create).toHaveBeenCalledWith(
          expect.objectContaining({
            tags: ['tag1', 'tag2'],
          })
        )
      })
    })
  })

  describe('API Error Handling', () => {
    it('should display error message on API failure', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockRejectedValue({
        response: { data: { detail: 'Server error occurred' } },
      })

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Server error occurred')).toBeInTheDocument()
      })
    })

    it('should display generic error message when API error has no detail', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockRejectedValue(new Error('Network error'))

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Failed to create bookmark')).toBeInTheDocument()
      })
    })
  })

  describe('Loading States', () => {
    it('should disable form inputs during submission', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      // Mock slow API response
      bookmarksApi.create.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ data: { id: 1 } }), 100))
      )

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      // Check inputs are disabled during loading
      expect(titleInput).toBeDisabled()
      expect(urlInput).toBeDisabled()
      expect(submitButton).toBeDisabled()

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled()
      })
    })

    it('should show loading indicator during submission', async () => {
      const onSuccess = vi.fn()
      const onCancel = vi.fn()

      bookmarksApi.create.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ data: { id: 1 } }), 100))
      )

      render(
        <BookmarkForm onSuccess={onSuccess} onCancel={onCancel} />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      const urlInput = screen.getByLabelText(/^URL/i)

      fireEvent.change(titleInput, { target: { value: 'Test' } })
      fireEvent.change(urlInput, { target: { value: 'https://example.com' } })

      const submitButton = screen.getByRole('button', { name: /create bookmark/i })
      fireEvent.click(submitButton)

      // Loading spinner should be visible
      expect(screen.getByRole('button', { name: /create bookmark/i })).toContainElement(
        document.querySelector('.animate-spin')
      )

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled()
      })
    })
  })

  describe('Update Mode', () => {
    it('should populate form with existing bookmark data', () => {
      const existingBookmark = {
        id: 1,
        title: 'Existing Bookmark',
        url: 'https://existing.com',
        description: 'A description',
        category: 'Work',
        tags: ['tag1', 'tag2'],
        favicon: 'https://existing.com/favicon.ico',
      }

      render(
        <BookmarkForm
          bookmark={existingBookmark}
          onSuccess={vi.fn()}
          onCancel={vi.fn()}
        />,
        { wrapper: createWrapper() }
      )

      expect(screen.getByLabelText(/title/i)).toHaveValue('Existing Bookmark')
      expect(screen.getByLabelText(/^URL/i)).toHaveValue('https://existing.com')
      expect(screen.getByLabelText(/description/i)).toHaveValue('A description')
      expect(screen.getByLabelText(/category/i)).toHaveValue('Work')
      expect(screen.getByLabelText(/tags/i)).toHaveValue('tag1, tag2')
      expect(screen.getByLabelText(/favicon url/i)).toHaveValue('https://existing.com/favicon.ico')
    })

    it('should call update API when editing existing bookmark', async () => {
      const existingBookmark = {
        id: 1,
        title: 'Existing',
        url: 'https://existing.com',
        tags: ['tag1'],
      }

      bookmarksApi.update.mockResolvedValue({ data: { id: 1 } })

      render(
        <BookmarkForm
          bookmark={existingBookmark}
          onSuccess={vi.fn()}
          onCancel={vi.fn()}
        />,
        { wrapper: createWrapper() }
      )

      const titleInput = screen.getByLabelText(/title/i)
      fireEvent.change(titleInput, { target: { value: 'Updated Title' } })

      const submitButton = screen.getByRole('button', { name: /update bookmark/i })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(bookmarksApi.update).toHaveBeenCalledWith(
          1,
          expect.objectContaining({
            title: 'Updated Title',
          })
        )
      })
    })
  })
})
