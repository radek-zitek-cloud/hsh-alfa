import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Sun,
  Moon,
  Plus,
  LogOut,
  Database,
  Cloud,
  DollarSign,
  TrendingUp,
  Newspaper,
  Shield,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { sectionsApi, widgetsApi } from '../services/api';
import BookmarkGrid from './BookmarkGrid';
import WidgetGrid from './WidgetGrid';
import BookmarkModal from './BookmarkModal';
import BookmarkForm from './BookmarkForm';
import WidgetForm from './WidgetForm';
import ExportImportModal from './ExportImportModal';
import DateHeader from './DateHeader';

// Map section names to icons
const SECTION_ICONS = {
  weather: Cloud,
  rates: DollarSign,
  markets: TrendingUp,
  news: Newspaper,
};

// Map widget types to section names (matching WidgetGrid)
const WIDGET_TYPE_TO_SECTION = {
  weather: 'weather',
  exchange_rate: 'rates',
  market: 'markets',
  news: 'news',
};

const Dashboard = ({ theme, toggleTheme }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isAddWidgetModalOpen, setIsAddWidgetModalOpen] = useState(false);
  const [isExportImportModalOpen, setIsExportImportModalOpen] = useState(false);

  const isAdmin = user?.role === 'admin';

  // Fetch sections for navigation
  const { data: sectionsData } = useQuery({
    queryKey: ['sections'],
    queryFn: async () => {
      const response = await sectionsApi.getAll();
      return response.data;
    },
  });

  // Fetch widgets to determine which sections have content
  const { data: widgetsData } = useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll();
      return response.data;
    },
  });

  // Determine which sections have widgets
  const visibleSections = useMemo(() => {
    if (!sectionsData || !widgetsData) return [];

    const widgetsBySection = {};
    sectionsData.forEach(section => {
      widgetsBySection[section.name] = [];
    });

    widgetsData.forEach(widget => {
      const sectionName = WIDGET_TYPE_TO_SECTION[widget.type];
      if (sectionName && widgetsBySection[sectionName]) {
        widgetsBySection[sectionName].push(widget);
      }
    });

    return sectionsData.filter(section => widgetsBySection[section.name]?.length > 0);
  }, [sectionsData, widgetsData]);

  const scrollToSection = sectionName => {
    const element = document.getElementById(`section-${sectionName}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <DateHeader />
        <div className="flex items-center gap-4">
          {/* Section Navigation Icons */}
          {visibleSections.map(section => {
            const IconComponent = SECTION_ICONS[section.name];
            if (!IconComponent) return null;
            return (
              <button
                key={section.id}
                onClick={() => scrollToSection(section.name)}
                className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
                aria-label={`Jump to ${section.title}`}
                title={`Jump to ${section.title}`}
              >
                <IconComponent size={24} />
              </button>
            );
          })}

          {/* Divider between navigation and action icons */}
          {visibleSections.length > 0 && <div className="h-6 w-px bg-[var(--border-color)]" />}

          <button
            onClick={() => setIsExportImportModalOpen(true)}
            className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
            aria-label="Export/Import Data"
            title="Export/Import Database"
          >
            <Database size={24} />
          </button>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
            aria-label="Toggle theme"
          >
            {theme === 'light' ? <Moon size={24} /> : <Sun size={24} />}
          </button>
          <button
            onClick={handleLogout}
            className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
            aria-label="Logout"
            title="Logout"
          >
            <LogOut size={24} />
          </button>
          {user && (
            <div className="flex items-center gap-3">
              {/* Admin Icon - Only visible to admins */}
              {isAdmin && (
                <button
                  onClick={() => navigate('/admin')}
                  className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900 hover:bg-purple-200 dark:hover:bg-purple-800 transition-colors"
                  aria-label="Administration"
                  title="Administration"
                >
                  <Shield size={24} className="text-purple-600 dark:text-purple-300" />
                </button>
              )}
              {user.picture && (
                <img
                  src={user.picture}
                  alt={user.name || user.email}
                  className="w-8 h-8 rounded-full"
                />
              )}
              <span className="text-sm text-[var(--text-secondary)] hidden sm:inline">
                {user.name || user.email}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Bookmarks Section */}
      <section className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Bookmarks</h2>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus size={18} />
            Add Bookmark
          </button>
        </div>
        <BookmarkGrid />
      </section>

      {/* Widgets Section */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">Widgets</h2>
          <button
            onClick={() => setIsAddWidgetModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus size={18} />
            Add Widget
          </button>
        </div>
        <WidgetGrid />
      </section>

      {/* Add Bookmark Modal */}
      <BookmarkModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Bookmark"
      >
        <BookmarkForm
          onSuccess={() => setIsAddModalOpen(false)}
          onCancel={() => setIsAddModalOpen(false)}
        />
      </BookmarkModal>

      {/* Add Widget Modal */}
      <BookmarkModal
        isOpen={isAddWidgetModalOpen}
        onClose={() => setIsAddWidgetModalOpen(false)}
        title="Add New Widget"
      >
        <WidgetForm
          onSuccess={() => setIsAddWidgetModalOpen(false)}
          onCancel={() => setIsAddWidgetModalOpen(false)}
        />
      </BookmarkModal>

      {/* Export/Import Modal */}
      <ExportImportModal
        isOpen={isExportImportModalOpen}
        onClose={() => setIsExportImportModalOpen(false)}
      />
    </div>
  );
};

export default Dashboard;
