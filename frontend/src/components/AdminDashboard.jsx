import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Users,
  Bookmark,
  LayoutGrid,
  Save,
  X,
  Trash2,
  Edit2,
  Settings,
  Layers,
  Target,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../services/api';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('users');
  const [editingUser, setEditingUser] = useState(null);
  const [editingBookmark, setEditingBookmark] = useState(null);
  const [editingWidget, setEditingWidget] = useState(null);
  const [editingSection, setEditingSection] = useState(null);
  const [editingHabit, setEditingHabit] = useState(null);
  const [editingPreference, setEditingPreference] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [bookmarkEditForm, setBookmarkEditForm] = useState({});
  const [widgetEditForm, setWidgetEditForm] = useState({});
  const [sectionEditForm, setSectionEditForm] = useState({});
  const [habitEditForm, setHabitEditForm] = useState({});
  const [preferenceEditForm, setPreferenceEditForm] = useState({});
  const [selectedUserId, setSelectedUserId] = useState(null);

  // Fetch users
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const response = await adminApi.getUsers();
      return response.data;
    },
  });

  // Fetch bookmarks
  const { data: bookmarks = [], isLoading: bookmarksLoading } = useQuery({
    queryKey: ['admin-bookmarks', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getBookmarks(selectedUserId);
      return response.data;
    },
    enabled: activeTab === 'bookmarks',
  });

  // Fetch widgets
  const { data: widgets = [], isLoading: widgetsLoading } = useQuery({
    queryKey: ['admin-widgets', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getWidgets(selectedUserId);
      return response.data;
    },
    enabled: activeTab === 'widgets',
  });

  // Fetch preferences
  const { data: preferences = [], isLoading: preferencesLoading } = useQuery({
    queryKey: ['admin-preferences', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getPreferences(selectedUserId);
      return response.data;
    },
    enabled: activeTab === 'settings',
  });

  // Fetch sections
  const { data: sections = [], isLoading: sectionsLoading } = useQuery({
    queryKey: ['admin-sections', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getSections(selectedUserId);
      return response.data;
    },
    enabled: activeTab === 'sections',
  });

  // Fetch habits
  const { data: habits = [], isLoading: habitsLoading } = useQuery({
    queryKey: ['admin-habits', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getHabits(selectedUserId);
      return response.data;
    },
    enabled: activeTab === 'habits',
  });

  // Update user mutation
  const updateUserMutation = useMutation({
    mutationFn: ({ userId, data }) => adminApi.updateUser(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      setEditingUser(null);
      setEditForm({});
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: userId => adminApi.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
    },
  });

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

  // Delete widget mutation
  const deleteWidgetMutation = useMutation({
    mutationFn: widgetId => adminApi.deleteWidget(widgetId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-widgets'] });
    },
  });

  // Update widget mutation
  const updateWidgetMutation = useMutation({
    mutationFn: ({ widgetId, data }) => adminApi.updateWidget(widgetId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-widgets'] });
      setEditingWidget(null);
      setWidgetEditForm({});
    },
  });

  // Delete preference mutation
  const deletePreferenceMutation = useMutation({
    mutationFn: preferenceId => adminApi.deletePreference(preferenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-preferences'] });
    },
  });

  // Update preference mutation
  const updatePreferenceMutation = useMutation({
    mutationFn: ({ preferenceId, data }) => adminApi.updatePreference(preferenceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-preferences'] });
      setEditingPreference(null);
      setPreferenceEditForm({});
    },
  });

  // Section mutations
  const updateSectionMutation = useMutation({
    mutationFn: ({ sectionId, data }) => adminApi.updateSection(sectionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sections'] });
      setEditingSection(null);
      setSectionEditForm({});
    },
  });

  const deleteSectionMutation = useMutation({
    mutationFn: sectionId => adminApi.deleteSection(sectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-sections'] });
    },
  });

  // Habit mutations
  const updateHabitMutation = useMutation({
    mutationFn: ({ habitId, data }) => adminApi.updateHabit(habitId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-habits'] });
      setEditingHabit(null);
      setHabitEditForm({});
    },
  });

  const deleteHabitMutation = useMutation({
    mutationFn: habitId => adminApi.deleteHabit(habitId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-habits'] });
    },
  });

  const handleEditUser = user => {
    setEditingUser(user.id);
    setEditForm({
      name: user.name || '',
      role: user.role,
      is_active: user.is_active,
    });
  };

  const handleSaveUser = () => {
    updateUserMutation.mutate({
      userId: editingUser,
      data: editForm,
    });
  };

  const handleCancelEdit = () => {
    setEditingUser(null);
    setEditForm({});
  };

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

  const handleDeleteWidget = widgetId => {
    if (window.confirm('Are you sure you want to delete this widget?')) {
      deleteWidgetMutation.mutate(widgetId);
    }
  };

  const handleEditWidget = widget => {
    setEditingWidget(widget.id);
    setWidgetEditForm({
      enabled: widget.enabled,
      refresh_interval: widget.refresh_interval,
      // Use existing position or default to row 0, col 0 with 1x1 size for new widgets
      position: widget.position || { row: 0, col: 0, width: 1, height: 1 },
    });
  };

  const handleSaveWidget = () => {
    updateWidgetMutation.mutate({
      widgetId: editingWidget,
      data: widgetEditForm,
    });
  };

  const handleCancelWidgetEdit = () => {
    setEditingWidget(null);
    setWidgetEditForm({});
  };

  const handleDeletePreference = preferenceId => {
    if (window.confirm('Are you sure you want to delete this preference?')) {
      deletePreferenceMutation.mutate(preferenceId);
    }
  };

  const handleEditPreference = preference => {
    setEditingPreference(preference.id);
    setPreferenceEditForm({
      value: preference.value || '',
    });
  };

  const handleSavePreference = () => {
    updatePreferenceMutation.mutate({
      preferenceId: editingPreference,
      data: preferenceEditForm,
    });
  };

  const handleCancelPreferenceEdit = () => {
    setEditingPreference(null);
    setPreferenceEditForm({});
  };

  // Section handlers
  const handleEditSection = section => {
    setEditingSection(section.id);
    setSectionEditForm({
      title: section.title || '',
      position: section.position || 0,
      enabled: section.enabled,
    });
  };

  const handleSaveSection = () => {
    updateSectionMutation.mutate({
      sectionId: editingSection,
      data: sectionEditForm,
    });
  };

  const handleCancelSectionEdit = () => {
    setEditingSection(null);
    setSectionEditForm({});
  };

  const handleDeleteSection = sectionId => {
    if (window.confirm('Are you sure you want to delete this section?')) {
      deleteSectionMutation.mutate(sectionId);
    }
  };

  // Habit handlers
  const handleEditHabit = habit => {
    setEditingHabit(habit.id);
    setHabitEditForm({
      name: habit.name || '',
      description: habit.description || '',
      active: habit.active,
    });
  };

  const handleSaveHabit = () => {
    updateHabitMutation.mutate({
      habitId: editingHabit,
      data: habitEditForm,
    });
  };

  const handleCancelHabitEdit = () => {
    setEditingHabit(null);
    setHabitEditForm({});
  };

  const handleDeleteHabit = habitId => {
    if (window.confirm('Are you sure you want to delete this habit? All completions will also be deleted.')) {
      deleteHabitMutation.mutate(habitId);
    }
  };

  // User delete handler
  const handleDeleteUser = userId => {
    if (window.confirm('Are you sure you want to delete this user? All their data will be permanently deleted.')) {
      deleteUserMutation.mutate(userId);
    }
  };

  const getUserName = userId => {
    const user = users.find(u => u.id === userId);
    return user ? user.name || user.email : `User ${userId}`;
  };

  // Format preference value for display (handles JSON objects)
  const formatPreferenceValue = value => {
    try {
      const parsed = JSON.parse(value);
      if (typeof parsed === 'object') {
        return JSON.stringify(parsed, null, 2);
      }
      return String(parsed);
    } catch {
      return value;
    }
  };

  const tabs = [
    { id: 'users', label: 'Users', icon: Users },
    { id: 'bookmarks', label: 'Bookmarks', icon: Bookmark },
    { id: 'widgets', label: 'Widgets', icon: LayoutGrid },
    { id: 'sections', label: 'Sections', icon: Layers },
    { id: 'habits', label: 'Habits', icon: Target },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8 bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/')}
          className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
          aria-label="Back to Dashboard"
        >
          <ArrowLeft size={24} />
        </button>
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">Administration</h1>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-[var(--border-color)]">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-[var(--accent-color)] text-[var(--accent-color)]'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon size={18} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* User filter for bookmarks, widgets, sections, habits and settings */}
      {(activeTab === 'bookmarks' || activeTab === 'widgets' || activeTab === 'sections' || activeTab === 'habits' || activeTab === 'settings') && (
        <div className="mb-4">
          <label className="block text-sm text-[var(--text-secondary)] mb-1">Filter by User</label>
          <select
            value={selectedUserId || ''}
            onChange={e => setSelectedUserId(e.target.value ? Number(e.target.value) : null)}
            className="px-3 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-secondary)] text-[var(--text-primary)]"
          >
            <option value="">All Users</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>
                {user.name || user.email}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
          {usersLoading ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">Loading users...</div>
          ) : (
            <table className="w-full">
              <thead className="bg-[var(--bg-primary)] border-b border-[var(--border-color)]">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Role
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Last Login
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr
                    key={user.id}
                    className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
                  >
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{user.id}</td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{user.email}</td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {editingUser === user.id ? (
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        />
                      ) : (
                        user.name || '-'
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {editingUser === user.id ? (
                        <select
                          value={editForm.role}
                          onChange={e => setEditForm({ ...editForm, role: e.target.value })}
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        >
                          <option value="user">User</option>
                          <option value="admin">Admin</option>
                        </select>
                      ) : (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            user.role === 'admin'
                              ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          }`}
                        >
                          {user.role}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingUser === user.id ? (
                        <select
                          value={editForm.is_active ? 'active' : 'inactive'}
                          onChange={e =>
                            setEditForm({
                              ...editForm,
                              is_active: e.target.value === 'active',
                            })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        >
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      ) : (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            user.is_active
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}
                        >
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingUser === user.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveUser}
                            disabled={updateUserMutation.isPending}
                            className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                            title="Save"
                          >
                            <Save size={18} />
                          </button>
                          <button
                            onClick={handleCancelEdit}
                            className="p-1 text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditUser(user)}
                            className="p-1 text-blue-600 hover:text-blue-800"
                            title="Edit"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={deleteUserMutation.isPending}
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
      )}

      {/* Bookmarks Tab */}
      {activeTab === 'bookmarks' && (
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
      )}

      {/* Widgets Tab */}
      {activeTab === 'widgets' && (
        <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
          {widgetsLoading ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">Loading widgets...</div>
          ) : widgets.length === 0 ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">No widgets found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-[var(--bg-primary)] border-b border-[var(--border-color)]">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Position
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Refresh Interval
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {widgets.map(widget => (
                  <tr
                    key={widget.id}
                    className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
                  >
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{widget.id}</td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      <span className="px-2 py-1 bg-[var(--bg-primary)] rounded text-xs">
                        {widget.type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingWidget === widget.id ? (
                        <select
                          value={widgetEditForm.enabled ? 'enabled' : 'disabled'}
                          onChange={e =>
                            setWidgetEditForm({
                              ...widgetEditForm,
                              enabled: e.target.value === 'enabled',
                            })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        >
                          <option value="enabled">Enabled</option>
                          <option value="disabled">Disabled</option>
                        </select>
                      ) : (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            widget.enabled
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}
                        >
                          {widget.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {editingWidget === widget.id ? (
                        <div className="flex gap-1 items-center">
                          <span>R:</span>
                          <input
                            type="number"
                            min="0"
                            value={widgetEditForm.position?.row ?? 0}
                            onChange={e => {
                              const value = parseInt(e.target.value, 10);
                              setWidgetEditForm({
                                ...widgetEditForm,
                                position: {
                                  ...widgetEditForm.position,
                                  row: Number.isNaN(value) ? 0 : value,
                                },
                              });
                            }}
                            className="px-1 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-12"
                          />
                          <span>C:</span>
                          <input
                            type="number"
                            min="0"
                            value={widgetEditForm.position?.col ?? 0}
                            onChange={e => {
                              const value = parseInt(e.target.value, 10);
                              setWidgetEditForm({
                                ...widgetEditForm,
                                position: {
                                  ...widgetEditForm.position,
                                  col: Number.isNaN(value) ? 0 : value,
                                },
                              });
                            }}
                            className="px-1 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-12"
                          />
                        </div>
                      ) : (
                        <>
                          Row: {widget.position?.row}, Col: {widget.position?.col}
                        </>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {editingWidget === widget.id ? (
                        <input
                          type="number"
                          min="60"
                          max="86400"
                          value={widgetEditForm.refresh_interval}
                          onChange={e => {
                            const value = parseInt(e.target.value, 10);
                            setWidgetEditForm({
                              ...widgetEditForm,
                              refresh_interval: Number.isNaN(value) ? 60 : value,
                            });
                          }}
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-20"
                        />
                      ) : (
                        <>{widget.refresh_interval}s</>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingWidget === widget.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveWidget}
                            disabled={updateWidgetMutation.isPending}
                            className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                            title="Save"
                          >
                            <Save size={18} />
                          </button>
                          <button
                            onClick={handleCancelWidgetEdit}
                            className="p-1 text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditWidget(widget)}
                            className="p-1 text-blue-600 hover:text-blue-800"
                            title="Edit"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteWidget(widget.id)}
                            disabled={deleteWidgetMutation.isPending}
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
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
          {preferencesLoading ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">Loading settings...</div>
          ) : preferences.length === 0 ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">
              No user settings found
            </div>
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
                    Key
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Value
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {preferences.map(preference => (
                  <tr
                    key={preference.id}
                    className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
                  >
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {preference.id}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {getUserName(preference.user_id)}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      <span className="px-2 py-1 bg-[var(--bg-primary)] rounded text-xs font-mono">
                        {preference.key}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)] max-w-md">
                      {editingPreference === preference.id ? (
                        <textarea
                          value={preferenceEditForm.value}
                          onChange={e =>
                            setPreferenceEditForm({ ...preferenceEditForm, value: e.target.value })
                          }
                          className="w-full px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] font-mono text-xs"
                          rows={4}
                        />
                      ) : (
                        <pre className="whitespace-pre-wrap text-xs bg-[var(--bg-primary)] p-2 rounded overflow-x-auto">
                          {formatPreferenceValue(preference.value)}
                        </pre>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingPreference === preference.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSavePreference}
                            disabled={updatePreferenceMutation.isPending}
                            className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                            title="Save"
                          >
                            <Save size={18} />
                          </button>
                          <button
                            onClick={handleCancelPreferenceEdit}
                            className="p-1 text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditPreference(preference)}
                            className="p-1 text-blue-600 hover:text-blue-800"
                            title="Edit"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDeletePreference(preference.id)}
                            disabled={deletePreferenceMutation.isPending}
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
      )}

      {/* Sections Tab */}
      {activeTab === 'sections' && (
        <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
          {sectionsLoading ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">Loading sections...</div>
          ) : sections.length === 0 ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">No sections found</div>
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
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Title
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Position
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {sections.map(section => (
                  <tr
                    key={section.id}
                    className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
                  >
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{section.id}</td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {getUserName(section.user_id)}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      <span className="px-2 py-1 bg-[var(--bg-primary)] rounded text-xs font-mono">
                        {section.name}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {editingSection === section.id ? (
                        <input
                          type="text"
                          value={sectionEditForm.title}
                          onChange={e =>
                            setSectionEditForm({ ...sectionEditForm, title: e.target.value })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-full"
                        />
                      ) : (
                        section.title
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {editingSection === section.id ? (
                        <input
                          type="number"
                          min="0"
                          value={sectionEditForm.position}
                          onChange={e => {
                            const value = parseInt(e.target.value, 10);
                            setSectionEditForm({
                              ...sectionEditForm,
                              position: Number.isNaN(value) ? 0 : value,
                            });
                          }}
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-16"
                        />
                      ) : (
                        section.position
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingSection === section.id ? (
                        <select
                          value={sectionEditForm.enabled ? 'enabled' : 'disabled'}
                          onChange={e =>
                            setSectionEditForm({
                              ...sectionEditForm,
                              enabled: e.target.value === 'enabled',
                            })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        >
                          <option value="enabled">Enabled</option>
                          <option value="disabled">Disabled</option>
                        </select>
                      ) : (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            section.enabled
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}
                        >
                          {section.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingSection === section.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveSection}
                            disabled={updateSectionMutation.isPending}
                            className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                            title="Save"
                          >
                            <Save size={18} />
                          </button>
                          <button
                            onClick={handleCancelSectionEdit}
                            className="p-1 text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditSection(section)}
                            className="p-1 text-blue-600 hover:text-blue-800"
                            title="Edit"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteSection(section.id)}
                            disabled={deleteSectionMutation.isPending}
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
      )}

      {/* Habits Tab */}
      {activeTab === 'habits' && (
        <div className="bg-[var(--bg-secondary)] rounded-lg overflow-hidden">
          {habitsLoading ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">Loading habits...</div>
          ) : habits.length === 0 ? (
            <div className="p-8 text-center text-[var(--text-secondary)]">No habits found</div>
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
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Description
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-secondary)]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {habits.map(habit => (
                  <tr
                    key={habit.id}
                    className="border-b border-[var(--border-color)] hover:bg-[var(--bg-primary)]"
                  >
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      <span className="font-mono text-xs">{habit.id.substring(0, 8)}...</span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {getUserName(habit.user_id)}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-primary)]">
                      {editingHabit === habit.id ? (
                        <input
                          type="text"
                          value={habitEditForm.name}
                          onChange={e =>
                            setHabitEditForm({ ...habitEditForm, name: e.target.value })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)] w-full"
                        />
                      ) : (
                        habit.name
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)] max-w-xs">
                      {editingHabit === habit.id ? (
                        <textarea
                          value={habitEditForm.description}
                          onChange={e =>
                            setHabitEditForm({ ...habitEditForm, description: e.target.value })
                          }
                          className="w-full px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                          rows={2}
                        />
                      ) : (
                        <span className="truncate block">{habit.description || '-'}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingHabit === habit.id ? (
                        <select
                          value={habitEditForm.active ? 'active' : 'inactive'}
                          onChange={e =>
                            setHabitEditForm({
                              ...habitEditForm,
                              active: e.target.value === 'active',
                            })
                          }
                          className="px-2 py-1 border border-[var(--border-color)] rounded bg-[var(--bg-primary)] text-[var(--text-primary)]"
                        >
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      ) : (
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            habit.active
                              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                          }`}
                        >
                          {habit.active ? 'Active' : 'Inactive'}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                      {habit.created ? new Date(habit.created).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {editingHabit === habit.id ? (
                        <div className="flex gap-2">
                          <button
                            onClick={handleSaveHabit}
                            disabled={updateHabitMutation.isPending}
                            className="p-1 text-green-600 hover:text-green-800 disabled:opacity-50"
                            title="Save"
                          >
                            <Save size={18} />
                          </button>
                          <button
                            onClick={handleCancelHabitEdit}
                            className="p-1 text-gray-600 hover:text-gray-800"
                            title="Cancel"
                          >
                            <X size={18} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditHabit(habit)}
                            className="p-1 text-blue-600 hover:text-blue-800"
                            title="Edit"
                          >
                            <Edit2 size={18} />
                          </button>
                          <button
                            onClick={() => handleDeleteHabit(habit.id)}
                            disabled={deleteHabitMutation.isPending}
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
      )}
    </div>
  );
};

export default AdminDashboard;
