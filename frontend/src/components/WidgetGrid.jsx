import React, { useMemo, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { widgetsApi, sectionsApi, preferencesApi } from '../services/api';
import { Loader, Edit2, Trash2 } from 'lucide-react';
import WeatherWidget from './widgets/WeatherWidget';
import ExchangeRateWidget from './widgets/ExchangeRateWidget';
import NewsWidget from './widgets/NewsWidget';
import MarketWidget from './widgets/MarketWidget';
import HabitTrackingWidget from './widgets/HabitTrackingWidget';
import SectionHeader from './SectionHeader';
import BookmarkModal from './BookmarkModal';
import WidgetForm from './WidgetForm';

// Map widget types to components
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  news: NewsWidget,
  market: MarketWidget,
  habit_tracking: HabitTrackingWidget,
};

// Map widget types to section names
const WIDGET_TYPE_TO_SECTION = {
  weather: 'weather',
  exchange_rate: 'rates',
  market: 'markets',
  news: 'news',
  habit_tracking: 'habits',
};

// Widget Card wrapper with edit/delete buttons
const WidgetCard = ({ widget, widthMultiple }) => {
  const queryClient = useQueryClient();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const WidgetComponent = WIDGET_COMPONENTS[widget.type];

  const deleteMutation = useMutation({
    mutationFn: () => widgetsApi.delete(widget.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] });
    },
    onError: error => {
      console.error('Error deleting widget:', error);
      alert('Failed to delete widget');
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
    if (window.confirm('Are you sure you want to delete this widget?')) {
      setIsDeleting(true);
      deleteMutation.mutate();
    }
  };

  if (!WidgetComponent) {
    return (
      <div className={`grid-span-${widthMultiple}`}>
        <div className="widget-card">
          <p className="text-[var(--text-secondary)]">Unknown widget type: {widget.type}</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={`grid-span-${widthMultiple} relative group`}>
        {/* Action Buttons */}
        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
          <button
            onClick={handleEdit}
            className="p-1.5 bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] rounded border border-[var(--border-color)] shadow-sm"
            aria-label="Edit widget"
            title="Edit"
          >
            <Edit2 size={14} className="text-[var(--text-primary)]" />
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-1.5 bg-[var(--bg-primary)] hover:bg-red-50 dark:hover:bg-red-900/20 rounded border border-[var(--border-color)] shadow-sm disabled:opacity-50"
            aria-label="Delete widget"
            title="Delete"
          >
            {isDeleting ? (
              <Loader size={14} className="animate-spin text-red-500" />
            ) : (
              <Trash2 size={14} className="text-red-500" />
            )}
          </button>
        </div>

        <WidgetComponent widgetId={widget.id} config={widget.config} />
      </div>

      {/* Edit Modal */}
      <BookmarkModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Widget"
      >
        <WidgetForm
          widget={widget}
          onSuccess={() => setIsEditModalOpen(false)}
          onCancel={() => setIsEditModalOpen(false)}
        />
      </BookmarkModal>
    </>
  );
};

const WidgetGrid = () => {
  const queryClient = useQueryClient();
  const [collapsedSections, setCollapsedSections] = useState({});
  const [isLoadingPreference, setIsLoadingPreference] = useState(true);

  // Fetch widgets
  const {
    data: widgetsData,
    isLoading: widgetsLoading,
    error: widgetsError,
  } = useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll();
      return response.data;
    },
  });

  // Fetch sections
  const {
    data: sectionsData,
    isLoading: sectionsLoading,
    error: sectionsError,
  } = useQuery({
    queryKey: ['sections'],
    queryFn: async () => {
      const response = await sectionsApi.getAll();
      return response.data;
    },
  });

  // Load collapsed sections preference on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await preferencesApi.get('widget_sections_collapsed');
        if (response.data && response.data.value) {
          setCollapsedSections(response.data.value);
        }
      } catch (error) {
        console.error('Failed to load collapsed sections preference:', error);
      } finally {
        setIsLoadingPreference(false);
      }
    };
    loadPreferences();
  }, []);

  // Save collapsed sections preference when changed
  useEffect(() => {
    if (isLoadingPreference) return;

    const savePreference = async () => {
      try {
        await preferencesApi.set('widget_sections_collapsed', collapsedSections);
      } catch (error) {
        console.error('Failed to save collapsed sections preference:', error);
      }
    };
    savePreference();
  }, [collapsedSections, isLoadingPreference]);

  // Mutation for reordering sections
  const reorderMutation = useMutation({
    mutationFn: sections => sectionsApi.reorder(sections),
    onSuccess: () => {
      queryClient.invalidateQueries(['sections']);
    },
  });

  // Group widgets by section
  const widgetsBySection = useMemo(() => {
    if (!widgetsData || !sectionsData) return {};

    const grouped = {};

    // Initialize all sections with empty arrays
    sectionsData.forEach(section => {
      grouped[section.name] = [];
    });

    // Group widgets by their section
    widgetsData.forEach(widget => {
      const sectionName = WIDGET_TYPE_TO_SECTION[widget.type];
      if (sectionName && grouped[sectionName]) {
        grouped[sectionName].push(widget);
      }
    });

    return grouped;
  }, [widgetsData, sectionsData]);

  // Handle moving section up
  const handleMoveUp = section => {
    const currentIndex = sectionsData.findIndex(s => s.id === section.id);
    if (currentIndex <= 0) return;

    const newSections = [...sectionsData];
    const temp = newSections[currentIndex];
    newSections[currentIndex] = newSections[currentIndex - 1];
    newSections[currentIndex - 1] = temp;

    // Update positions
    const reorderData = newSections.map((section, index) => ({
      name: section.name,
      position: index,
    }));

    reorderMutation.mutate(reorderData);
  };

  // Handle moving section down
  const handleMoveDown = section => {
    const currentIndex = sectionsData.findIndex(s => s.id === section.id);
    if (currentIndex === -1 || currentIndex === sectionsData.length - 1) return;

    const newSections = [...sectionsData];
    const temp = newSections[currentIndex];
    newSections[currentIndex] = newSections[currentIndex + 1];
    newSections[currentIndex + 1] = temp;

    // Update positions
    const reorderData = newSections.map((section, index) => ({
      name: section.name,
      position: index,
    }));

    reorderMutation.mutate(reorderData);
  };

  // Handle toggling section collapse
  const handleToggleCollapse = sectionName => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName],
    }));
  };

  if (widgetsLoading || sectionsLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  if (widgetsError || sectionsError) {
    return (
      <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        {widgetsError && <div>Error loading widgets: {widgetsError.message}</div>}
        {sectionsError && <div>Error loading sections: {sectionsError.message}</div>}
      </div>
    );
  }

  if (!widgetsData || widgetsData.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No widgets configured. Add widgets in the configuration file.
      </div>
    );
  }

  if (!sectionsData || sectionsData.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No sections configured. Sections will be created automatically.
      </div>
    );
  }

  // Filter out sections with no widgets for display
  const visibleSections = sectionsData.filter(section => {
    const sectionWidgets = widgetsBySection[section.name] || [];
    return sectionWidgets.length > 0;
  });

  return (
    <div className="space-y-8">
      {visibleSections.map((section, displayIndex) => {
        let sectionWidgets = widgetsBySection[section.name] || [];

        // Sort weather widgets by country and then by city
        if (section.name === 'weather') {
          sectionWidgets = [...sectionWidgets].sort((a, b) => {
            // Parse location from config (format: "City, Country" or "City, CountryCode")
            const getLocationParts = widget => {
              const location = widget.config?.location || '';
              const parts = location.split(',').map(part => part.trim());
              return {
                city: parts[0] || '',
                country: parts[1] || '',
              };
            };

            const locA = getLocationParts(a);
            const locB = getLocationParts(b);

            // First compare by country
            const countryCompare = locA.country.localeCompare(locB.country);
            if (countryCompare !== 0) return countryCompare;

            // Then compare by city
            return locA.city.localeCompare(locB.city);
          });
        }

        // Find the actual index in the full sections array
        const actualIndex = sectionsData.findIndex(s => s.id === section.id);

        return (
          <section key={section.id} id={`section-${section.name}`}>
            <SectionHeader
              section={section}
              onMoveUp={() => handleMoveUp(section)}
              onMoveDown={() => handleMoveDown(section)}
              isFirst={actualIndex === 0}
              isLast={actualIndex === sectionsData.length - 1}
              onToggleCollapse={() => handleToggleCollapse(section.name)}
              isCollapsed={collapsedSections[section.name] || false}
            />
            {!collapsedSections[section.name] && (
              <div className="unified-grid">
                {sectionWidgets.map(widget => {
                  const widthMultiple = widget.position?.width || 1;
                  return (
                    <WidgetCard key={widget.id} widget={widget} widthMultiple={widthMultiple} />
                  );
                })}
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
};

export default WidgetGrid;
