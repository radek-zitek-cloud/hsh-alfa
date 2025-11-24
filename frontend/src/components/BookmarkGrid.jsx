import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bookmarksApi } from '../services/api'
import { ExternalLink, Loader, Edit2, Trash2 } from 'lucide-react'
import BookmarkModal from './BookmarkModal'
import BookmarkForm from './BookmarkForm'

const BookmarkCard = ({ bookmark }) => {
  const queryClient = useQueryClient()
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [faviconError, setFaviconError] = useState(false)

  const handleClick = () => {
    window.open(bookmark.url, '_blank', 'noopener,noreferrer')
  }

  const deleteMutation = useMutation({
    mutationFn: () => bookmarksApi.delete(bookmark.id),
    onSuccess: () => {
      queryClient.invalidateQueries(['bookmarks'])
    },
    onError: (error) => {
      console.error('Error deleting bookmark:', error)
      alert('Failed to delete bookmark')
    },
    onSettled: () => {
      setIsDeleting(false)
    },
  })

  const handleEdit = (e) => {
    e.stopPropagation()
    setIsEditModalOpen(true)
  }

  const handleDelete = (e) => {
    e.stopPropagation()
    if (window.confirm(`Are you sure you want to delete "${bookmark.title}"?`)) {
      setIsDeleting(true)
      deleteMutation.mutate()
    }
  }

  // Extract domain from URL for fallback
  const getDomain = (url) => {
    try {
      const urlObj = new URL(url)
      return urlObj.hostname
    } catch (e) {
      return ''
    }
  }

  // Get proxied favicon URL to avoid CORS issues
  const getFaviconUrl = (faviconUrl) => {
    if (!faviconUrl) return null
    // Use proxy endpoint to serve favicons through backend
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
    return `${apiBaseUrl}/bookmarks/favicon/proxy?url=${encodeURIComponent(faviconUrl)}`
  }

  return (
    <>
      <div
        onClick={handleClick}
        className="bookmark-card cursor-pointer relative group"
      >
        {/* Action Buttons */}
        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={handleEdit}
            className="p-1.5 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] rounded border border-[var(--border-color)] shadow-sm"
            aria-label="Edit bookmark"
            title="Edit"
          >
            <Edit2 size={14} className="text-[var(--text-primary)]" />
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-1.5 bg-[var(--bg-primary)] hover:bg-red-50 dark:hover:bg-red-900/20 rounded border border-[var(--border-color)] shadow-sm disabled:opacity-50"
            aria-label="Delete bookmark"
            title="Delete"
          >
            {isDeleting ? (
              <Loader size={14} className="animate-spin text-red-500" />
            ) : (
              <Trash2 size={14} className="text-red-500" />
            )}
          </button>
        </div>

        <div className="flex items-start gap-3">
          {/* Favicon */}
          <div className="flex-shrink-0">
            {bookmark.favicon && !faviconError ? (
              <img
                src={getFaviconUrl(bookmark.favicon)}
                alt=""
                className="w-8 h-8 object-contain"
                onError={() => {
                  setFaviconError(true)
                }}
              />
            ) : (
              <div className="w-8 h-8 bg-[var(--accent-color)] rounded flex items-center justify-center text-white font-bold">
                {bookmark.title.charAt(0).toUpperCase()}
              </div>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-[var(--text-primary)] truncate">
              {bookmark.title}
            </h3>
            {bookmark.description && (
              <p className="text-sm text-[var(--text-secondary)] mt-1 line-clamp-2">
                {bookmark.description}
              </p>
            )}
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-[var(--text-secondary)] truncate">
                {getDomain(bookmark.url)}
              </span>
              <ExternalLink size={12} className="text-[var(--text-secondary)]" />
            </div>
            {bookmark.tags && bookmark.tags.length > 0 && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {bookmark.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Edit Modal */}
      <BookmarkModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Bookmark"
      >
        <BookmarkForm
          bookmark={bookmark}
          onSuccess={() => setIsEditModalOpen(false)}
          onCancel={() => setIsEditModalOpen(false)}
        />
      </BookmarkModal>
    </>
  )
}

const BookmarkGrid = () => {
  const { data: bookmarks, isLoading, error } = useQuery({
    queryKey: ['bookmarks'],
    queryFn: async () => {
      const response = await bookmarksApi.getAll()
      return response.data
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        Error loading bookmarks: {error.message}
      </div>
    )
  }

  if (!bookmarks || bookmarks.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No bookmarks yet. Add your first bookmark!
      </div>
    )
  }

  return (
    <div className="unified-grid">
      {bookmarks.map((bookmark) => (
        <BookmarkCard key={bookmark.id} bookmark={bookmark} />
      ))}
    </div>
  )
}

export default BookmarkGrid
