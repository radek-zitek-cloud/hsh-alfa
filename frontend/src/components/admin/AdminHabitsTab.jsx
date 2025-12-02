import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminHabitsTab = ({ habits, habitsLoading, users }) => {
  const queryClient = useQueryClient();
  const [editingHabit, setEditingHabit] = useState(null);
  const [habitEditForm, setHabitEditForm] = useState({});

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

  const getUserName = userId => {
    const user = users.find(u => u.id === userId);
    return user ? user.name || user.email : `User ${userId}`;
  };

  return (
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
  );
};

export default AdminHabitsTab;
