import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminSettingsTab = ({ preferences, preferencesLoading, users }) => {
  const queryClient = useQueryClient();
  const [editingPreference, setEditingPreference] = useState(null);
  const [preferenceEditForm, setPreferenceEditForm] = useState({});

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

  return (
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
  );
};

export default AdminSettingsTab;
