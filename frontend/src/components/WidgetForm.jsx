import React, { useState, useEffect } from 'react';
import { widgetsApi, habitsApi } from '../services/api';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';

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

  const habits = habitsData || [];

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

  const handleSubmit = e => {
    e.preventDefault();
    setErrors({});

    // Validate form
    const newErrors = {};
    if (!formData.type) newErrors.type = 'Widget type is required';
    if (formData.refresh_interval < 60)
      newErrors.refresh_interval = 'Refresh interval must be at least 60 seconds';

    // Validate habit_tracking widget has a habit_id
    if (formData.type === 'habit_tracking' && !widgetConfig.habit_id) {
      newErrors.config = 'Please select a habit to track';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const data = {
      ...formData,
      config: widgetConfig,
    };

    if (isEditMode) {
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
          {renderConfigFields(formData.type, widgetConfig, handleConfigChange, habits)}
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
          disabled={createMutation.isPending || updateMutation.isPending}
          className="px-6 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
        >
          {createMutation.isPending || updateMutation.isPending
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

function renderConfigFields(type, config, onChange, habits = []) {
  switch (type) {
    case 'weather':
      return (
        <>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Location (City, Country Code)
            </label>
            <input
              type="text"
              value={config.location || ''}
              onChange={e => onChange('location', e.target.value)}
              placeholder="e.g., London, UK"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Units</label>
            <select
              value={config.units || 'metric'}
              onChange={e => onChange('units', e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            >
              <option value="metric">Metric (°C)</option>
              <option value="imperial">Imperial (°F)</option>
              <option value="standard">Standard (K)</option>
            </select>
          </div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="show_forecast"
              checked={config.show_forecast !== false}
              onChange={e => onChange('show_forecast', e.target.checked)}
              className="w-4 h-4"
            />
            <label htmlFor="show_forecast" className="ml-2 text-sm text-[var(--text-secondary)]">
              Show Forecast
            </label>
          </div>
        </>
      );

    case 'exchange_rate':
      return (
        <>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Base Currency</label>
            <input
              type="text"
              value={config.base_currency || 'USD'}
              onChange={e => onChange('base_currency', e.target.value.toUpperCase())}
              placeholder="USD"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Target Currencies (comma-separated)
            </label>
            <input
              type="text"
              value={
                Array.isArray(config.target_currencies) ? config.target_currencies.join(', ') : ''
              }
              onChange={e =>
                onChange(
                  'target_currencies',
                  e.target.value.split(',').map(c => c.trim().toUpperCase())
                )
              }
              placeholder="EUR, GBP, JPY"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
        </>
      );

    case 'news':
      return (
        <>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              RSS Feeds (one per line)
            </label>
            <textarea
              value={Array.isArray(config.rss_feeds) ? config.rss_feeds.join('\n') : ''}
              onChange={e => onChange('rss_feeds', e.target.value.split('\n').filter(Boolean))}
              rows="4"
              placeholder="https://hnrss.org/frontpage"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">Max Articles</label>
            <input
              type="number"
              value={config.max_articles || 10}
              onChange={e => onChange('max_articles', parseInt(e.target.value))}
              min="1"
              max="50"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
        </>
      );

    case 'market':
      return (
        <>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Stock Symbols (comma-separated)
            </label>
            <input
              type="text"
              value={Array.isArray(config.stocks) ? config.stocks.join(', ') : ''}
              onChange={e =>
                onChange(
                  'stocks',
                  e.target.value
                    .split(',')
                    .map(s => s.trim().toUpperCase())
                    .filter(s => s)
                )
              }
              placeholder="AAPL, GOOGL, MSFT"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Crypto Symbols (comma-separated)
            </label>
            <input
              type="text"
              value={Array.isArray(config.crypto) ? config.crypto.join(', ') : ''}
              onChange={e =>
                onChange(
                  'crypto',
                  e.target.value
                    .split(',')
                    .map(c => c.trim().toUpperCase())
                    .filter(c => c)
                )
              }
              placeholder="BTC, ETH, SOL"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
        </>
      );

    case 'habit_tracking':
      return (
        <>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Select Habit to Track *
            </label>
            {habits.length === 0 ? (
              <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  No habits available. Please create a habit first by adding it in an existing habit
                  tracking widget or contact support.
                </p>
              </div>
            ) : (
              <select
                value={config.habit_id || ''}
                onChange={e => onChange('habit_id', e.target.value)}
                className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
                required
              >
                <option value="">-- Select a habit --</option>
                {habits.map(habit => (
                  <option key={habit.id} value={habit.id}>
                    {habit.name} {habit.description ? `- ${habit.description}` : ''}
                  </option>
                ))}
              </select>
            )}
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              Each widget tracks one habit. Create multiple widgets to track multiple habits.
            </p>
          </div>
        </>
      );

    default:
      return (
        <p className="text-sm text-[var(--text-secondary)]">
          No additional configuration needed for this widget type.
        </p>
      );
  }
}

export default WidgetForm;
