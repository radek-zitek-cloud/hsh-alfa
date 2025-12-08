import { useState, useEffect, useMemo } from 'react';
import { widgetsApi, habitsApi } from '../services/api';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import {
  WeatherConfigFields,
  ExchangeRateConfigFields,
  NewsConfigFields,
  MarketConfigFields,
  HabitTrackingConfigFields,
} from './widget-config';

// Helper function to format error messages from API responses
const formatErrorMessage = error => {
  const detail = error.response?.data?.detail;

  // If detail is an array of validation errors (Pydantic format)
  if (Array.isArray(detail)) {
    return detail
      .map(err => {
        const field = err.loc?.join('.') || 'field';
        return `${field}: ${err.msg || 'Validation error'}`;
      })
      .join('; ');
  }

  // If detail is a string, return it directly
  if (typeof detail === 'string') {
    return detail;
  }

  // If detail is an object, try to stringify it
  if (detail && typeof detail === 'object') {
    return JSON.stringify(detail);
  }

  // Default fallback message
  return 'An error occurred';
};

const WidgetForm = ({ widget, onSuccess, onCancel }) => {
  const queryClient = useQueryClient();
  const isEditMode = !!widget;
  const isHabitTrackingWidget = widget?.type === 'habit_tracking' || false;
  const habitIdToEdit = isEditMode && isHabitTrackingWidget ? widget?.config?.habit_id : null;

  // Fetch available widget types
  const { data: typesData } = useQuery({
    queryKey: ['widgetTypes'],
    queryFn: async () => {
      const response = await widgetsApi.getTypes();
      return response.data;
    },
  });

  const widgetTypes = typesData?.widget_types || [];

  // Fetch available habits
  const { data: habitsData } = useQuery({
    queryKey: ['habits'],
    queryFn: async () => {
      const response = await habitsApi.getAll();
      return response.data;
    },
    enabled: !isEditMode, // Only fetch when creating new widget
  });

  const habits = useMemo(() => habitsData || [], [habitsData]);

  // Fetch the specific habit data when editing a habit_tracking widget
  const { data: editingHabitData } = useQuery({
    queryKey: ['habit', habitIdToEdit],
    queryFn: async () => {
      const response = await habitsApi.getOne(habitIdToEdit);
      return response.data;
    },
    enabled: !!habitIdToEdit, // Only fetch when editing a habit_tracking widget with a habit_id
  });

  // Form state
  const [formData, setFormData] = useState({
    type: widget?.type || 'weather',
    enabled: widget?.enabled !== false,
    position: {
      row: widget?.position?.row || 0,
      col: widget?.position?.col || 0,
      width: widget?.position?.width || 2,
      height: widget?.position?.height || 2,
    },
    refresh_interval: widget?.refresh_interval || 1800,
    config: widget?.config || {},
  });

  // Widget-specific config state
  const [widgetConfig, setWidgetConfig] = useState(() => {
    if (widget?.config) return widget.config;
    return getDefaultConfigForType(formData.type, habits);
  });

  // State for creating new habit when creating habit_tracking widget
  // Always default to 'new' - always create a new habit
  const [habitCreationMode, setHabitCreationMode] = useState('new');
  const [newHabitData, setNewHabitData] = useState({
    name: '',
    description: '',
  });

  // State for editing existing habit data
  const [editHabitData, setEditHabitData] = useState({
    name: '',
    description: '',
  });

  // Populate edit habit data when editing habit data is loaded
  useEffect(() => {
    if (editingHabitData) {
      setEditHabitData({
        name: editingHabitData.name || '',
        description: editingHabitData.description || '',
      });
    }
  }, [editingHabitData]);

  // Update config when type changes or habits are loaded
  useEffect(() => {
    if (!isEditMode) {
      setWidgetConfig(getDefaultConfigForType(formData.type, habits));
    }
  }, [formData.type, habits, isEditMode]);


  const [errors, setErrors] = useState({});

  // Create mutation
  const createMutation = useMutation({
    mutationFn: data => widgetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] });
      onSuccess?.();
    },
    onError: error => {
      const errorMessage = formatErrorMessage(error) || 'Failed to create widget';
      setErrors({ submit: errorMessage });
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => widgetsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] });
      // Also invalidate the specific widget's data query to refresh the display
      queryClient.invalidateQueries({ queryKey: ['widget', widget.id] });
      onSuccess?.();
    },
    onError: error => {
      const errorMessage = formatErrorMessage(error) || 'Failed to update widget';
      setErrors({ submit: errorMessage });
    },
  });

  // Habit update mutation
  const updateHabitMutation = useMutation({
    mutationFn: ({ id, data }) => habitsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['habits'] });
      queryClient.invalidateQueries({ queryKey: ['habit', habitIdToEdit] });
      // Also invalidate the widget data to refresh the display
      if (widget?.id) {
        queryClient.invalidateQueries({ queryKey: ['widget', widget.id] });
      }
    },
    onError: error => {
      const errorMessage = formatErrorMessage(error) || 'Failed to update habit';
      setErrors({ submit: errorMessage });
    },
  });

  const handleSubmit = async e => {
    e.preventDefault();
    setErrors({});

    // Validate form
    const newErrors = {};
    if (!formData.type) newErrors.type = 'Widget type is required';
    if (formData.refresh_interval < 60)
      newErrors.refresh_interval = 'Refresh interval must be at least 60 seconds';

    // Validate habit_tracking widget has new habit data
    if (formData.type === 'habit_tracking') {
      if (!isEditMode) {
        // Always creating a new habit
        if (!newHabitData.name.trim()) {
          newErrors.config = 'Habit name is required';
        } else if (!newHabitData.description.trim()) {
          newErrors.config = 'Habit description is required';
        }
      } else {
        // Validate edit habit data in edit mode
        if (!editHabitData.name.trim()) {
          newErrors.config = 'Habit name is required';
        }
      }
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const data = {
      ...formData,
      config: widgetConfig,
    };

    // If creating a habit_tracking widget, always include the new habit data
    if (!isEditMode && formData.type === 'habit_tracking') {
      data.create_habit = {
        name: newHabitData.name.trim(),
        description: newHabitData.description.trim(),
      };
    }

    if (isEditMode) {
      // If editing a habit_tracking widget, also update the habit
      if (isHabitTrackingWidget && habitIdToEdit) {
        try {
          await updateHabitMutation.mutateAsync({
            id: habitIdToEdit,
            data: {
              name: editHabitData.name.trim(),
              description: editHabitData.description.trim(),
            },
          });
        } catch (_error) {
          // Error is handled by the mutation's onError callback
          return;
        }
      }
      updateMutation.mutate({ id: widget.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePositionChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      position: { ...prev.position, [field]: parseInt(value) || 0 },
    }));
  };

  const handleConfigChange = (field, value) => {
    setWidgetConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-6">
      {errors.submit && (
        <div className="p-4 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
          {errors.submit}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Widget Type */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            Widget Type *
          </label>
          <select
            value={formData.type}
            onChange={e => handleInputChange('type', e.target.value)}
            disabled={isEditMode}
            className="w-full px-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-color)] focus:border-transparent disabled:opacity-50"
          >
            {widgetTypes.map(type => (
              <option key={type} value={type}>
                {formatTypeName(type)}
              </option>
            ))}
          </select>
        </div>

        {/* Enabled */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="enabled"
            checked={formData.enabled}
            onChange={e => handleInputChange('enabled', e.target.checked)}
            className="w-4 h-4 text-[var(--accent-color)] border-[var(--border-color)] rounded focus:ring-2 focus:ring-[var(--accent-color)]"
          />
          <label htmlFor="enabled" className="ml-2 text-sm font-medium text-[var(--text-primary)]">
            Enabled
          </label>
        </div>

        {/* Refresh Interval */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            Refresh Interval (seconds) *
          </label>
          <input
            type="number"
            value={formData.refresh_interval}
            onChange={e => handleInputChange('refresh_interval', parseInt(e.target.value))}
            min="60"
            max="86400"
            className="w-full px-4 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:ring-2 focus:ring-[var(--accent-color)] focus:border-transparent"
          />
          {errors.refresh_interval && (
            <p className="text-red-500 text-sm mt-1">{errors.refresh_interval}</p>
          )}
        </div>
      </div>

      {/* Position */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
          Position & Size
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Row</label>
            <input
              type="number"
              value={formData.position.row}
              onChange={e => handlePositionChange('row', e.target.value)}
              min="0"
              className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Column</label>
            <input
              type="number"
              value={formData.position.col}
              onChange={e => handlePositionChange('col', e.target.value)}
              min="0"
              className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Width</label>
            <input
              type="number"
              value={formData.position.width}
              onChange={e => handlePositionChange('width', e.target.value)}
              min="1"
              max="12"
              className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-xs text-[var(--text-secondary)] mb-1">Height</label>
            <input
              type="number"
              value={formData.position.height}
              onChange={e => handlePositionChange('height', e.target.value)}
              min="1"
              max="12"
              className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
        </div>
      </div>

      {/* Widget-specific configuration */}
      <div>
        <label className="block text-sm font-medium text-[var(--text-primary)] mb-3">
          Widget Configuration
        </label>
        <div className="space-y-4 p-4 bg-[var(--bg-primary)] rounded-lg border border-[var(--border-color)]">
          {formData.type === 'weather' && (
            <WeatherConfigFields config={widgetConfig} onChange={handleConfigChange} />
          )}
          {formData.type === 'exchange_rate' && (
            <ExchangeRateConfigFields config={widgetConfig} onChange={handleConfigChange} />
          )}
          {formData.type === 'news' && (
            <NewsConfigFields config={widgetConfig} onChange={handleConfigChange} />
          )}
          {formData.type === 'market' && (
            <MarketConfigFields config={widgetConfig} onChange={handleConfigChange} />
          )}
          {formData.type === 'habit_tracking' && (
            <HabitTrackingConfigFields
              config={widgetConfig}
              onChange={handleConfigChange}
              habits={habits}
              isEditMode={isEditMode}
              habitCreationMode={habitCreationMode}
              setHabitCreationMode={setHabitCreationMode}
              newHabitData={newHabitData}
              setNewHabitData={setNewHabitData}
              editHabitData={editHabitData}
              setEditHabitData={setEditHabitData}
            />
          )}
          {!['weather', 'exchange_rate', 'news', 'market', 'habit_tracking'].includes(formData.type) && (
            <p className="text-sm text-[var(--text-secondary)]">
              No additional configuration needed for this widget type.
            </p>
          )}
        </div>
        {errors.config && <p className="text-red-500 text-sm mt-2">{errors.config}</p>}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-color)]">
        <button
          type="button"
          onClick={onCancel}
          className="px-6 py-2 border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-primary)] transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={createMutation.isPending || updateMutation.isPending || updateHabitMutation.isPending}
          className="px-6 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {createMutation.isPending || updateMutation.isPending || updateHabitMutation.isPending
            ? 'Saving...'
            : isEditMode
              ? 'Update Widget'
              : 'Create Widget'}
        </button>
      </div>
    </form>
  );
};

// Helper functions
function formatTypeName(type) {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function getDefaultConfigForType(type, habits = []) {
  switch (type) {
    case 'weather':
      return {
        location: 'New York, US',
        units: 'metric',
        show_forecast: true,
      };
    case 'exchange_rate':
      return {
        base_currency: 'USD',
        target_currencies: ['EUR', 'GBP', 'JPY'],
        show_trend: false,
      };
    case 'news':
      return {
        rss_feeds: ['https://hnrss.org/frontpage'],
        max_articles: 10,
        description_length: 200,
      };
    case 'market':
      return {
        stocks: ['^GSPC', '^DJI'],
        crypto: ['BTC', 'ETH'],
      };
    case 'habit_tracking':
      // Set the first available habit as default, or empty string if no habits
      return {
        habit_id: habits.length > 0 ? habits[0].id : '',
      };
    default:
      return {};
  }
}

export default WidgetForm;
