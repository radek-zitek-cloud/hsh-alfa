import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminSectionsTab = ({ sections, sectionsLoading, users }) => {
  const queryClient = useQueryClient();
  const [editingSection, setEditingSection] = useState(null);
  const [sectionEditForm, setSectionEditForm] = useState({});

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

  const getUserName = userId => {
    const user = users.find(u => u.id === userId);
    return user ? user.name || user.email : `User ${userId}`;
  };

  return (
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
  );
};

export default AdminSectionsTab;
