import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { bookmarksApi } from '../services/api'
import { ExternalLink, Loader } from 'lucide-react'

const BookmarkCard = ({ bookmark }) => {
  const handleClick = () => {
    window.open(bookmark.url, '_blank', 'noopener,noreferrer')
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

  return (
    <div
      onClick={handleClick}
      className="bookmark-card cursor-pointer"
    >
      <div className="flex items-start gap-3">
        {/* Favicon */}
        <div className="flex-shrink-0">
          {bookmark.favicon ? (
            <img
              src={bookmark.favicon}
              alt=""
              className="w-8 h-8"
              onError={(e) => {
                e.target.style.display = 'none'
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
              {bookmark.tags.slice(0, 3).map((tag, idx) => (
                <span
                  key={idx}
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
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {bookmarks.map((bookmark) => (
        <BookmarkCard key={bookmark.id} bookmark={bookmark} />
      ))}
    </div>
  )
}

export default BookmarkGrid
