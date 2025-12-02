import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminWidgetsTab = ({ widgets, widgetsLoading }) => {
  const queryClient = useQueryClient();
  const [editingWidget, setEditingWidget] = useState(null);
  const [widgetEditForm, setWidgetEditForm] = useState({});

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

  return (
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
  );
};

export default AdminWidgetsTab;
