import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminBookmarksTab = ({ bookmarks, bookmarksLoading, users }) => {
  const queryClient = useQueryClient();
  const [editingBookmark, setEditingBookmark] = useState(null);
  const [bookmarkEditForm, setBookmarkEditForm] = useState({});

  // Delete bookmark mutation
  const deleteBookmarkMutation = useMutation({
    mutationFn: bookmarkId => adminApi.deleteBookmark(bookmarkId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-bookmarks'] });
    },
  });

  // Update bookmark mutation
  const updateBookmarkMutation = useMutation({
    mutationFn: ({ bookmarkId, data }) => adminApi.updateBookmark(bookmarkId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-bookmarks'] });
      setEditingBookmark(null);
      setBookmarkEditForm({});
    },
  });

  const handleDeleteBookmark = bookmarkId => {
    if (window.confirm('Are you sure you want to delete this bookmark?')) {
      deleteBookmarkMutation.mutate(bookmarkId);
    }
  };

  const handleEditBookmark = bookmark => {
    setEditingBookmark(bookmark.id);
    setBookmarkEditForm({
      title: bookmark.title || '',
      url: bookmark.url || '',
      category: bookmark.category || '',
      description: bookmark.description || '',
    });
  };

  const handleSaveBookmark = () => {
    updateBookmarkMutation.mutate({
      bookmarkId: editingBookmark,
      data: bookmarkEditForm,
    });
  };

  const handleCancelBookmarkEdit = () => {
    setEditingBookmark(null);
    setBookmarkEditForm({});
  };

  const getUserName = userId => {
    const user = users.find(u => u.id === userId);
    return user ? user.name || user.email : `User ${userId}`;
  };

  return (
    <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
      {bookmarksLoading ? (
        <div className="p-8 text-center text-[var(--text-secondary)]">Loading bookmarks...</div>
      ) : bookmarks.length === 0 ? (
        <div className="p-8 text-center text-[var(--text-secondary)]">No bookmarks found</div>
      ) : (
        <table className="w-full">
          <thead className="bg-[var(--bg-primary)] border-b border-[var(--border-color)]">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                ID
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                User
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                Title
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                URL
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                Category
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                Clicks
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {bookmarks.map(bookmark => (
              <tr
                key={bookmark.id}
                className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
              >
                <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{bookmark.id}</td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                  {getUserName(bookmark.user_id)}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                  {editingBookmark === bookmark.id ? (
                    <input
                      type="text"
                      value={bookmarkEditForm.title}
                      onChange={e =>
                        setBookmarkEditForm({ ...bookmarkEditForm, title: e.target.value })
                      }
                      className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-full"
                    />
                  ) : (
                    <div className="flex items-center gap-2">
                      {bookmark.favicon && (
                        <img src={bookmark.favicon} alt="" className="w-4 h-4" />
                      )}
                      {bookmark.title}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-secondary)] max-w-xs">
                  {editingBookmark === bookmark.id ? (
                    <input
                      type="text"
                      value={bookmarkEditForm.url}
                      onChange={e =>
                        setBookmarkEditForm({ ...bookmarkEditForm, url: e.target.value })
                      }
                      className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-full"
                    />
                  ) : (
                    <a
                      href={bookmark.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-[var(--accent-color)] truncate block"
                    >
                      {bookmark.url}
                    </a>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                  {editingBookmark === bookmark.id ? (
                    <input
                      type="text"
                      value={bookmarkEditForm.category}
                      onChange={e =>
                        setBookmarkEditForm({ ...bookmarkEditForm, category: e.target.value })
                      }
                      className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-full"
                    />
                  ) : (
                    bookmark.category || '-'
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                  {bookmark.clicks}
                </td>
                <td className="px-4 py-3 text-sm">
                  {editingBookmark === bookmark.id ? (
                    <div className="flex gap-2">
                      <button
                        onClick={handleSaveBookmark}
                        disabled={updateBookmarkMutation.isPending}
                        className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                        title="Save"
                      >
                        <Save size={18} />
                      </button>
                      <button
                        onClick={handleCancelBookmarkEdit}
                        className="p-1 text-gray-600 hover:text-gray-800"
                        title="Cancel"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditBookmark(bookmark)}
                        className="p-1 text-blue-600 hover:text-blue-800"
                        title="Edit"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDeleteBookmark(bookmark.id)}
                        disabled={deleteBookmarkMutation.isPending}
                        className="p-1 text-red-600 hover:text-red-800 disabled:opacity-50"
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default AdminBookmarksTab;
