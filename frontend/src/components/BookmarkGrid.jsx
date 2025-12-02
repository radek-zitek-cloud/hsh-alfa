import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bookmarksApi, preferencesApi } from '../services/api';
import { ExternalLink, Loader, Edit2, Trash2 } from 'lucide-react';
import BookmarkModal from './BookmarkModal';
import BookmarkForm from './BookmarkForm';

const BookmarkCard = ({ bookmark }) => {
  const queryClient = useQueryClient();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [faviconError, setFaviconError] = useState(false);

  const trackClickMutation = useMutation({
    mutationFn: () => bookmarksApi.trackClick(bookmark.id),
    onSuccess: () => {
      queryClient.invalidateQueries(['bookmarks']);
    },
  });

  const handleClick = () => {
    // Track the click
    trackClickMutation.mutate();
    // Open the bookmark
    window.open(bookmark.url, '_blank', 'noopener,noreferrer');
  };

  const deleteMutation = useMutation({
    mutationFn: () => bookmarksApi.delete(bookmark.id),
    onSuccess: () => {
      queryClient.invalidateQueries(['bookmarks']);
    },
    onError: error => {
      console.error('Error deleting bookmark:', error);
      alert('Failed to delete bookmark');
    },
    onSettled: () => {
      setIsDeleting(false);
    },
  });

  const handleEdit = e => {
    e.stopPropagation();
    setIsEditModalOpen(true);
  };

  const handleDelete = e => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete "${bookmark.title}"?`)) {
      setIsDeleting(true);
      deleteMutation.mutate();
    }
  };

  // Extract domain from URL for fallback
  const getDomain = url => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch (e) {
      return '';
    }
  };

  // Get proxied favicon URL to avoid CORS issues
  const getFaviconUrl = faviconUrl => {
    if (!faviconUrl) return null;
    // Use proxy endpoint to serve favicons through backend
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
    return `${apiBaseUrl}/bookmarks/favicon/proxy?url=${encodeURIComponent(faviconUrl)}`;
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <>
      <div
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        className="bookmark-card cursor-pointer relative group"
        aria-label={`Open ${bookmark.title} at ${getDomain(bookmark.url)}`}
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
                  setFaviconError(true);
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
            <h3 className="font-semibold text-[var(--text-primary)] truncate">{bookmark.title}</h3>
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
                {bookmark.tags.slice(0, 3).map(tag => (
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
  );
};

const BookmarkGrid = () => {
  const [sortBy, setSortBy] = useState('position');
  const [groupByCategory, setGroupByCategory] = useState(false);
  const [isLoadingPreference, setIsLoadingPreference] = useState(true);

  // Load saved preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const [sortResponse, groupResponse] = await Promise.all([
          preferencesApi.get('bookmarks_sort_order').catch(() => ({ data: null })),
          preferencesApi.get('bookmarks_group_by_category').catch(() => ({ data: null })),
        ]);

        if (sortResponse.data && sortResponse.data.value) {
          setSortBy(sortResponse.data.value);
        }

        if (groupResponse.data && groupResponse.data.value !== undefined) {
          // Parse the string value back to boolean
          const groupValue = groupResponse.data.value;
          setGroupByCategory(groupValue === 'true' || groupValue === true);
        }
      } catch (error) {
        console.debug('Error loading preferences:', error);
      } finally {
        setIsLoadingPreference(false);
      }
    };
    loadPreferences();
  }, []);

  // Save sort preference whenever it changes
  useEffect(() => {
    // Skip saving during initial load
    if (isLoadingPreference) return;

    const saveSortPreference = async () => {
      try {
        await preferencesApi.set('bookmarks_sort_order', sortBy);
      } catch (error) {
        console.debug('Failed to save sort preference:', error);
      }
    };
    saveSortPreference();
  }, [sortBy, isLoadingPreference]);

  // Save group by category preference whenever it changes
  useEffect(() => {
    // Skip saving during initial load
    if (isLoadingPreference) return;

    const saveGroupPreference = async () => {
      try {
        // Convert boolean to string for storage
        await preferencesApi.set('bookmarks_group_by_category', String(groupByCategory));
      } catch (error) {
        console.debug('Failed to save group preference:', error);
      }
    };
    saveGroupPreference();
  }, [groupByCategory, isLoadingPreference]);

  const {
    data: bookmarks,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['bookmarks', sortBy],
    queryFn: async () => {
      const response = await bookmarksApi.getAll(null, sortBy === 'position' ? null : sortBy);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        Error loading bookmarks: {error.message}
      </div>
    );
  }

  if (!bookmarks || bookmarks.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No bookmarks yet. Add your first bookmark!
      </div>
    );
  }

  return (
    <div>
      {/* Sorting Controls */}
      <div className="mb-4 flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-[var(--text-primary)]">Sort by:</label>
          <div className="flex gap-2">
            <button
              onClick={() => setSortBy('position')}
              className={`px-3 py-1.5 text-sm rounded border transition-colors ${
                sortBy === 'position'
                  ? 'bg-[var(--accent-color)] text-white border-[var(--accent-color)]'
                  : 'bg-[var(--bg-primary)] text-[var(--text-primary)] border-[var(--border-color)] hover:bg-[var(--bg-secondary)]'
              }`}
            >
              Default
            </button>
            <button
              onClick={() => setSortBy('alphabetical')}
              className={`px-3 py-1.5 text-sm rounded border transition-colors ${
                sortBy === 'alphabetical'
                  ? 'bg-[var(--accent-color)] text-white border-[var(--accent-color)]'
                  : 'bg-[var(--bg-primary)] text-[var(--text-primary)] border-[var(--border-color)] hover:bg-[var(--bg-secondary)]'
              }`}
            >
              Alphabetical
            </button>
            <button
              onClick={() => setSortBy('clicks')}
              className={`px-3 py-1.5 text-sm rounded border transition-colors ${
                sortBy === 'clicks'
                  ? 'bg-[var(--accent-color)] text-white border-[var(--accent-color)]'
                  : 'bg-[var(--bg-primary)] text-[var(--text-primary)] border-[var(--border-color)] hover:bg-[var(--bg-secondary)]'
              }`}
            >
              Most Clicked
            </button>
          </div>
        </div>

        {/* Category Sections Toggle */}
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="groupByCategory"
            checked={groupByCategory}
            onChange={e => setGroupByCategory(e.target.checked)}
            className="w-4 h-4 rounded border-[var(--border-color)] text-[var(--accent-color)] focus:ring-2 focus:ring-[var(--accent-color)] cursor-pointer"
          />
          <label
            htmlFor="groupByCategory"
            className="text-sm font-medium text-[var(--text-primary)] cursor-pointer"
          >
            Group by Category
          </label>
        </div>
      </div>

      {/* Bookmarks Grid */}
      {groupByCategory ? (
        // Group bookmarks by category
        (() => {
          // Group bookmarks by category
          const groupedBookmarks = bookmarks.reduce((groups, bookmark) => {
            const category = bookmark.category || 'Uncategorized';
            if (!groups[category]) {
              groups[category] = [];
            }
            groups[category].push(bookmark);
            return groups;
          }, {});

          // Sort categories alphabetically, but put Uncategorized last
          const sortedCategories = Object.keys(groupedBookmarks).sort((a, b) => {
            if (a === 'Uncategorized') return 1;
            if (b === 'Uncategorized') return -1;
            return a.localeCompare(b);
          });

          return (
            <div className="space-y-6">
              {sortedCategories.map(category => (
                <div key={category}>
                  {/* Category Header */}
                  <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3 pb-2 border-b border-[var(--border-color)]">
                    {category}
                  </h2>
                  {/* Category Bookmarks */}
                  <div className="unified-grid">
                    {groupedBookmarks[category].map(bookmark => (
                      <BookmarkCard key={bookmark.id} bookmark={bookmark} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          );
        })()
      ) : (
        // Show all bookmarks without grouping
        <div className="unified-grid">
          {bookmarks.map(bookmark => (
            <BookmarkCard key={bookmark.id} bookmark={bookmark} />
          ))}
        </div>
      )}
    </div>
  );
};

export default BookmarkGrid;
