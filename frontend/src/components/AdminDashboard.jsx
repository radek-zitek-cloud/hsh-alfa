import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Users,
  Bookmark,
  LayoutGrid,
  Settings,
  Layers,
  Target,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../services/api';
import {
  AdminUsersTab,
  AdminBookmarksTab,
  AdminWidgetsTab,
  AdminSectionsTab,
  AdminHabitsTab,
  AdminSettingsTab,
} from './admin';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('users');
  const [selectedUserId, setSelectedUserId] = useState(null);

  // Fetch users
  const { data: users = [], isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const response = await adminApi.getUsers();
      return response.data.items;
    },
  });

  // Fetch bookmarks
  const { data: bookmarks = [], isLoading: bookmarksLoading } = useQuery({
    queryKey: ['admin-bookmarks', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getBookmarks(selectedUserId);
      return response.data.items;
    },
    enabled: activeTab === 'bookmarks',
  });

  // Fetch widgets
  const { data: widgets = [], isLoading: widgetsLoading } = useQuery({
    queryKey: ['admin-widgets', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getWidgets(selectedUserId);
      return response.data.items;
    },
    enabled: activeTab === 'widgets',
  });

  // Fetch preferences
  const { data: preferences = [], isLoading: preferencesLoading } = useQuery({
    queryKey: ['admin-preferences', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getPreferences(selectedUserId);
      return response.data.items;
    },
    enabled: activeTab === 'settings',
  });

  // Fetch sections
  const { data: sections = [], isLoading: sectionsLoading } = useQuery({
    queryKey: ['admin-sections', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getSections(selectedUserId);
      return response.data.items;
    },
    enabled: activeTab === 'sections',
  });

  // Fetch habits
  const { data: habits = [], isLoading: habitsLoading } = useQuery({
    queryKey: ['admin-habits', selectedUserId],
    queryFn: async () => {
      const response = await adminApi.getHabits(selectedUserId);
      return response.data.items;
    },
    enabled: activeTab === 'habits',
  });

  const tabs = [
    { id: 'users', label: 'Users', icon: Users },
    { id: 'bookmarks', label: 'Bookmarks', icon: Bookmark },
    { id: 'widgets', label: 'Widgets', icon: LayoutGrid },
    { id: 'sections', label: 'Sections', icon: Layers },
    { id: 'habits', label: 'Habits', icon: Target },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'users':
        return <AdminUsersTab users={users} usersLoading={usersLoading} />;
      case 'bookmarks':
        return (
          <AdminBookmarksTab
            bookmarks={bookmarks}
            bookmarksLoading={bookmarksLoading}
            users={users}
          />
        );
      case 'widgets':
        return <AdminWidgetsTab widgets={widgets} widgetsLoading={widgetsLoading} />;
      case 'sections':
        return (
          <AdminSectionsTab
            sections={sections}
            sectionsLoading={sectionsLoading}
            users={users}
          />
        );
      case 'habits':
        return (
          <AdminHabitsTab
            habits={habits}
            habitsLoading={habitsLoading}
            users={users}
          />
        );
      case 'settings':
        return (
          <AdminSettingsTab
            preferences={preferences}
            preferencesLoading={preferencesLoading}
            users={users}
          />
        );
      default:
        return null;
    }
  };

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

      {/* Tab Content */}
      {renderTabContent()}
    </div>
  );
};

export default AdminDashboard;
