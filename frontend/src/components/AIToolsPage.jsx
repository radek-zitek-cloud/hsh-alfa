import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiToolsApi } from '../services/api';
import {
  ArrowLeft,
  Plus,
  Edit,
  Trash2,
  Save,
  X,
  Wand2,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast';

const AIToolsPage = ({ theme, toggleTheme }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [editingTool, setEditingTool] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt: '',
    api_key: '',
  });

  // Fetch all AI tools
  const { data: tools = [], isLoading } = useQuery({
    queryKey: ['ai-tools'],
    queryFn: async () => {
      const response = await aiToolsApi.getAll();
      return response.data;
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: aiToolsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['ai-tools']);
      resetForm();
      setIsCreating(false);
      showSuccess('AI tool created successfully');
    },
    onError: error => {
      showError(`Error creating tool: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => aiToolsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['ai-tools']);
      resetForm();
      setEditingTool(null);
      showSuccess('AI tool updated successfully');
    },
    onError: error => {
      showError(`Error updating tool: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: aiToolsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries(['ai-tools']);
      showSuccess('AI tool deleted successfully');
    },
    onError: error => {
      showError(`Error deleting tool: ${error.response?.data?.detail || error.message}`);
    },
  });

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      prompt: '',
      api_key: '',
    });
  };

  const handleEdit = tool => {
    setEditingTool(tool.id);
    setFormData({
      name: tool.name,
      description: tool.description || '',
      prompt: tool.prompt,
      api_key: tool.api_key,
    });
  };

  const handleCancel = () => {
    setEditingTool(null);
    setIsCreating(false);
    resetForm();
  };

  const handleSubmit = e => {
    e.preventDefault();

    if (!formData.name.trim() || !formData.prompt.trim() || !formData.api_key.trim()) {
      alert('Please fill in all required fields (Name, Prompt, API Key)');
      return;
    }

    if (editingTool) {
      updateMutation.mutate({ id: editingTool, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = tool => {
    if (confirm(`Are you sure you want to delete "${tool.name}"?`)) {
      deleteMutation.mutate(tool.id);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-[var(--bg-secondary)] border-b border-[var(--border-color)] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/')}
              className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
              title="Back to Dashboard"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-2xl font-bold flex items-center gap-2">
                <Wand2 size={24} />
                AI Tools
              </h1>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Manage your AI-powered note processing tools
              </p>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors"
            title="Toggle theme"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Create New Button */}
        {!isCreating && !editingTool && (
          <button
            onClick={() => setIsCreating(true)}
            className="mb-6 flex items-center gap-2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-[var(--accent-primary-hover)] transition-colors"
          >
            <Plus size={18} />
            Create New Tool
          </button>
        )}

        {/* Create/Edit Form */}
        {(isCreating || editingTool) && (
          <div className="mb-6 p-6 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg">
            <h2 className="text-xl font-bold mb-4">
              {editingTool ? 'Edit Tool' : 'Create New Tool'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
                  placeholder="e.g., Deep Scholar"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] min-h-[80px]"
                  placeholder="Help users understand what this tool does and when to use it"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Prompt <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.prompt}
                  onChange={e => setFormData({ ...formData, prompt: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] min-h-[200px] font-mono text-sm"
                  placeholder="Enter your prompt here. Use [PLACEHOLDER] where the note content should be inserted."
                />
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  Use <code className="px-1 py-0.5 bg-[var(--bg-tertiary)] rounded">[PLACEHOLDER]</code> to mark where the note content will be inserted.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  API Key <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  value={formData.api_key}
                  onChange={e => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full px-3 py-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)] font-mono text-sm"
                  placeholder="sk-..."
                />
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  Your OpenAI API key. This is stored securely and only used when applying this tool.
                </p>
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-[var(--accent-primary-hover)] transition-colors disabled:opacity-50"
                >
                  <Save size={18} />
                  {editingTool ? 'Update' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-tertiary)] rounded-lg hover:bg-[var(--bg-quaternary)] transition-colors"
                >
                  <X size={18} />
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Tools List */}
        <div className="space-y-4">
          {isLoading && (
            <div className="text-center py-8">
              <div className="spinner mx-auto"></div>
            </div>
          )}

          {!isLoading && tools.length === 0 && (
            <div className="text-center py-12 text-[var(--text-secondary)]">
              <Wand2 size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">No AI tools yet</p>
              <p className="text-sm">Create your first tool to get started!</p>
            </div>
          )}

          {tools.map(tool => (
            <div
              key={tool.id}
              className="p-6 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold">{tool.name}</h3>
                  {tool.description && (
                    <p className="text-sm text-[var(--text-secondary)] mt-1">
                      {tool.description}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(tool)}
                    disabled={isCreating || editingTool}
                    className="p-2 hover:bg-[var(--bg-tertiary)] rounded-lg transition-colors disabled:opacity-50"
                    title="Edit tool"
                  >
                    <Edit size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(tool)}
                    disabled={deleteMutation.isPending}
                    className="p-2 hover:bg-red-500/10 text-red-500 rounded-lg transition-colors disabled:opacity-50"
                    title="Delete tool"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
                <details className="cursor-pointer">
                  <summary className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                    View Prompt
                  </summary>
                  <pre className="mt-2 p-3 bg-[var(--bg-tertiary)] rounded text-xs overflow-x-auto whitespace-pre-wrap">
                    {tool.prompt}
                  </pre>
                </details>
              </div>

              <div className="mt-2 text-xs text-[var(--text-secondary)]">
                Created: {new Date(tool.created).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AIToolsPage;
