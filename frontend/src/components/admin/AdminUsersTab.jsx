import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, X, Trash2, Edit2 } from 'lucide-react';
import { adminApi } from '../../services/api';

const AdminUsersTab = ({ users, usersLoading }) => {
  const queryClient = useQueryClient();
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({});

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

  const handleDeleteUser = userId => {
    if (window.confirm('Are you sure you want to delete this user? All their data will be permanently deleted.')) {
      deleteUserMutation.mutate(userId);
    }
  };

  return (
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
  );
};

export default AdminUsersTab;
