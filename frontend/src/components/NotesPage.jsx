import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { notesApi, aiToolsApi } from '../services/api';
import { Plus, Edit2, Save, Trash2, X, FileText, Home, Sun, Moon, LogOut, Wand2, ChevronDown, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { useAuth } from '../contexts/AuthContext';
import NoteTree from './NoteTree';
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast';

// Markdown syntax helper component
function MarkdownHelper() {
  const examples = [
    { label: 'Headers', syntax: '# H1 ## H2 ### H3' },
    { label: 'Bold', syntax: '**bold text**' },
    { label: 'Italic', syntax: '*italic text*' },
    { label: 'Link', syntax: '[title](https://...)' },
    { label: 'Bullet List', syntax: '- Item 1\n- Item 2' },
    { label: 'Numbered List', syntax: '1. First\n2. Second' },
    { label: 'Task List', syntax: '- [ ] Todo\n- [x] Done' },
    { label: 'Code', syntax: '`inline code`' },
    { label: 'Code Block', syntax: '```\ncode block\n```' },
    { label: 'Quote', syntax: '> quote' },
    { label: 'Table', syntax: '| Col1 | Col2 |\n|------|------|\n| A | B |' },
  ];

  return (
    <div
      className="mt-4 p-3 rounded border text-xs"
      style={{
        backgroundColor: 'var(--bg-secondary)',
        borderColor: 'var(--border-color)',
        color: 'var(--text-secondary)',
      }}
    >
      <div className="font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
        Markdown Syntax Guide
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        {examples.map(({ label, syntax }) => (
          <div key={label} className="flex gap-2">
            <span className="font-medium min-w-[90px]">{label}:</span>
            <code className="font-mono">{syntax}</code>
          </div>
        ))}
      </div>
    </div>
  );
}

function NotesPage({ theme, toggleTheme }) {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const queryClient = useQueryClient();
  const [selectedNoteId, setSelectedNoteId] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editContent, setEditContent] = useState('');
  const [newNoteParentId, setNewNoteParentId] = useState(null);
  const [selectedToolId, setSelectedToolId] = useState(null);
  const [showToolDropdown, setShowToolDropdown] = useState(false);

  // Fetch all notes
  const { data: notes = [], isLoading } = useQuery({
    queryKey: ['notes'],
    queryFn: async () => {
      const response = await notesApi.getAll();
      return response.data;
    },
  });

  // Create note mutation
  const createNoteMutation = useMutation({
    mutationFn: notesApi.create,
    onSuccess: data => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setSelectedNoteId(data.data.id);
      setIsCreating(false);
      setEditTitle('');
      setEditContent('');
    },
  });

  // Update note mutation
  const updateNoteMutation = useMutation({
    mutationFn: ({ id, data }) => notesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setIsEditing(false);
    },
  });

  // Delete note mutation
  const deleteNoteMutation = useMutation({
    mutationFn: notesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setSelectedNoteId(null);
    },
  });

  // Fetch AI tools
  const { data: aiTools = [] } = useQuery({
    queryKey: ['ai-tools'],
    queryFn: async () => {
      const response = await aiToolsApi.getAll();
      return response.data;
    },
  });

  // Apply AI tool mutation
  const applyToolMutation = useMutation({
    mutationFn: aiToolsApi.apply,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setShowToolDropdown(false);
      setSelectedToolId(null);
      showInfo('AI tool is processing asynchronously. A new subnote has been created. Check it for the result.');
    },
    onError: error => {
      showError(`Error applying tool: ${error.response?.data?.detail || error.message}`);
    },
  });

  const selectedNote = notes.find(note => note.id === selectedNoteId);

  const handleCreateNew = () => {
    setIsCreating(true);
    setSelectedNoteId(null);
    setIsEditing(false);
    setEditTitle('New Note');
    setEditContent('');
    setNewNoteParentId(null);
  };

  const handleCreateSubnote = parentId => {
    setIsCreating(true);
    setSelectedNoteId(null);
    setIsEditing(false);
    setEditTitle('New Subnote');
    setEditContent('');
    setNewNoteParentId(parentId);
  };

  const handleSaveNew = () => {
    if (editTitle.trim()) {
      createNoteMutation.mutate({
        title: editTitle,
        content: editContent,
        parent_id: newNoteParentId,
      });
    }
  };

  const handleCancelNew = () => {
    setIsCreating(false);
    setEditTitle('');
    setEditContent('');
    setNewNoteParentId(null);
  };

  const handleEdit = () => {
    if (selectedNote) {
      setIsEditing(true);
      setEditTitle(selectedNote.title);
      setEditContent(selectedNote.content || '');
    }
  };

  const handleSaveEdit = () => {
    if (selectedNote && editTitle.trim()) {
      updateNoteMutation.mutate({
        id: selectedNote.id,
        data: {
          title: editTitle,
          content: editContent,
        },
      });
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditTitle('');
    setEditContent('');
  };

  const handleDelete = () => {
    if (selectedNote && confirm('Are you sure you want to delete this note?')) {
      deleteNoteMutation.mutate(selectedNote.id);
    }
  };

  const handleSelectNote = noteId => {
    setSelectedNoteId(noteId);
    setIsEditing(false);
    setIsCreating(false);
    setShowToolDropdown(false);
    setSelectedToolId(null);
  };

  const handleApplyTool = (toolId) => {
    if (!toolId || !selectedNoteId) {
      showWarning('Please select a tool');
      return;
    }

    applyToolMutation.mutate({
      note_id: selectedNoteId,
      tool_id: toolId,
    });
  };

  // Refresh note mutation - fetches the latest version from database
  const handleRefreshNote = async () => {
    if (!selectedNoteId) {
      showWarning('Please select a note to refresh');
      return;
    }

    try {
      await queryClient.invalidateQueries({ queryKey: ['notes'] });
      showSuccess('Note refreshed successfully');
    } catch (error) {
      showError('Failed to refresh note');
    }
  };

  // Auto-refresh when displayed note changes
  useEffect(() => {
    if (selectedNoteId) {
      // Invalidate queries to fetch fresh data from database
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    }
  }, [selectedNoteId, queryClient]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading notes...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col" style={{ backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <div
        className="px-6 py-4 border-b flex items-center justify-between"
        style={{ borderColor: 'var(--border-color)' }}
      >
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Notes
        </h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 rounded-lg transition-colors"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--border-color)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
            aria-label="Home"
            title="Home"
          >
            <Home size={24} />
          </button>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg transition-colors"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--border-color)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? <Moon size={24} /> : <Sun size={24} />}
          </button>
          <button
            onClick={logout}
            className="p-2 rounded-lg transition-colors"
            style={{ backgroundColor: 'var(--bg-secondary)' }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--border-color)')}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
            aria-label="Logout"
            title="Logout"
          >
            <LogOut size={24} />
          </button>
        </div>
      </div>

      {/* Main content area with two panels */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left panel - Notes tree */}
        <div
          className="w-[480px] border-r flex flex-col overflow-hidden"
          style={{ borderColor: 'var(--border-color)' }}
        >
          {/* New Note button */}
          <div className="p-4 border-b" style={{ borderColor: 'var(--border-color)' }}>
            <button
              onClick={handleCreateNew}
              className="w-full px-4 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
              style={{
                backgroundColor: 'var(--accent-color)',
                color: 'white',
              }}
              onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
              onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
            >
              <Plus size={20} />
              New Note
            </button>
          </div>

          {/* Notes list */}
          <div className="flex-1 overflow-y-auto">
            {notes.length === 0 && !isCreating ? (
              <div className="p-8 text-center" style={{ color: 'var(--text-secondary)' }}>
                <FileText size={48} className="mx-auto mb-4 opacity-30" />
                <p>No notes yet</p>
                <p className="text-sm mt-2">Click "New Note" to create one</p>
              </div>
            ) : (
              <div className="p-4">
                <NoteTree
                  notes={notes}
                  selectedNoteId={selectedNoteId}
                  onSelectNote={handleSelectNote}
                  onCreateSubnote={handleCreateSubnote}
                  isCreating={isCreating}
                />
              </div>
            )}
          </div>
        </div>

        {/* Right panel - Note content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {!selectedNote && !isCreating ? (
            <div
              className="flex-1 flex items-center justify-center"
              style={{ color: 'var(--text-secondary)' }}
            >
              <div className="text-center">
                <FileText size={64} className="mx-auto mb-4 opacity-20" />
                <p className="text-lg">Select a note to view</p>
              </div>
            </div>
          ) : isCreating ? (
            <>
              <div
                className="px-6 py-4 border-b flex items-center justify-between"
                style={{ borderColor: 'var(--border-color)' }}
              >
                <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {editTitle}
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveNew}
                    className="px-3 py-1.5 rounded flex items-center gap-2 transition-colors"
                    style={{
                      backgroundColor: 'var(--accent-color)',
                      color: 'white',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
                    onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                  >
                    <Save size={16} />
                    Save
                  </button>
                  <button
                    onClick={handleCancelNew}
                    className="px-3 py-1.5 rounded border transition-colors"
                    style={{
                      borderColor: 'var(--border-color)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
              <div className="flex-1 p-6 overflow-y-auto">
                <input
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 mb-4 rounded border text-lg font-semibold"
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    borderColor: 'var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                  placeholder="Note title"
                  autoFocus
                />
                <textarea
                  value={editContent}
                  onChange={e => setEditContent(e.target.value)}
                  className="w-full h-96 p-4 rounded border font-mono resize-none"
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    borderColor: 'var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                  placeholder="Write your note in markdown..."
                />
                <MarkdownHelper />
              </div>
            </>
          ) : isEditing ? (
            <>
              <div
                className="px-6 py-4 border-b flex items-center justify-between"
                style={{ borderColor: 'var(--border-color)' }}
              >
                <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {editTitle}
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveEdit}
                    className="px-3 py-1.5 rounded flex items-center gap-2 transition-colors"
                    style={{
                      backgroundColor: 'var(--accent-color)',
                      color: 'white',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
                    onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                  >
                    <Save size={16} />
                    Save
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="px-3 py-1.5 rounded border transition-colors"
                    style={{
                      borderColor: 'var(--border-color)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
              <div className="flex-1 p-6 overflow-y-auto">
                <input
                  type="text"
                  value={editTitle}
                  onChange={e => setEditTitle(e.target.value)}
                  className="w-full px-3 py-2 mb-4 rounded border text-lg font-semibold"
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    borderColor: 'var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                  placeholder="Note title"
                />
                <textarea
                  value={editContent}
                  onChange={e => setEditContent(e.target.value)}
                  className="w-full h-96 p-4 rounded border font-mono resize-none"
                  style={{
                    backgroundColor: 'var(--bg-primary)',
                    borderColor: 'var(--border-color)',
                    color: 'var(--text-primary)',
                  }}
                  placeholder="Write your note in markdown..."
                />
                <MarkdownHelper />
              </div>
            </>
          ) : (
            <>
              <div
                className="px-6 py-4 border-b flex items-center justify-between"
                style={{ borderColor: 'var(--border-color)' }}
              >
                <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                  {selectedNote.title}
                </h2>
                <div className="flex gap-2">
                  {/* AI Tools Dropdown */}
                  {aiTools.length > 0 && (
                    <div className="relative">
                      <button
                        onClick={() => setShowToolDropdown(!showToolDropdown)}
                        disabled={applyToolMutation.isPending}
                        className="px-3 py-1.5 rounded flex items-center gap-2 transition-colors"
                        style={{
                          backgroundColor: 'var(--bg-secondary)',
                          borderColor: 'var(--border-color)',
                          color: 'var(--text-primary)',
                          border: '1px solid var(--border-color)',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--border-color)')}
                        onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
                      >
                        <Wand2 size={16} />
                        {applyToolMutation.isPending ? 'Processing...' : 'AI Tools'}
                        <ChevronDown size={16} />
                      </button>
                      {showToolDropdown && (
                        <div
                          className="absolute right-0 mt-2 w-64 rounded-lg shadow-lg border z-10"
                          style={{
                            backgroundColor: 'var(--bg-secondary)',
                            borderColor: 'var(--border-color)',
                          }}
                        >
                          <div className="p-2">
                            <div className="text-xs font-semibold mb-2 px-2" style={{ color: 'var(--text-secondary)' }}>
                              Select an AI tool:
                            </div>
                            {aiTools.map(tool => (
                              <button
                                key={tool.id}
                                onClick={() => {
                                  setSelectedToolId(tool.id);
                                  setShowToolDropdown(false);
                                  handleApplyTool(tool.id);
                                }}
                                className="w-full text-left px-3 py-2 rounded hover:bg-[var(--bg-tertiary)] transition-colors"
                                style={{ color: 'var(--text-primary)' }}
                              >
                                <div className="font-medium">{tool.name}</div>
                                {tool.description && (
                                  <div className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
                                    {tool.description.substring(0, 80)}
                                    {tool.description.length > 80 ? '...' : ''}
                                  </div>
                                )}
                              </button>
                            ))}
                          </div>
                          <div
                            className="border-t p-2"
                            style={{ borderColor: 'var(--border-color)' }}
                          >
                            <button
                              onClick={() => navigate('/ai-tools')}
                              className="w-full text-xs px-2 py-1 rounded transition-colors"
                              style={{
                                color: 'var(--text-secondary)',
                              }}
                              onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)')}
                              onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'transparent')}
                            >
                              Manage AI Tools →
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                  {/* Refresh Note Button */}
                  <button
                    onClick={handleRefreshNote}
                    className="px-3 py-1.5 rounded flex items-center gap-2 transition-colors"
                    style={{
                      backgroundColor: 'var(--bg-secondary)',
                      borderColor: 'var(--border-color)',
                      color: 'var(--text-primary)',
                      border: '1px solid var(--border-color)',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.backgroundColor = 'var(--border-color)')}
                    onMouseLeave={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
                    title="Refresh note from database"
                  >
                    <RefreshCw size={16} />
                    Refresh
                  </button>
                  <button
                    onClick={handleEdit}
                    className="px-3 py-1.5 rounded flex items-center gap-2 transition-colors"
                    style={{
                      backgroundColor: 'var(--accent-color)',
                      color: 'white',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.opacity = '0.9')}
                    onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
                  >
                    <Edit2 size={16} />
                    Edit
                  </button>
                  <button
                    onClick={handleDelete}
                    className="px-3 py-1.5 rounded border transition-colors"
                    style={{
                      borderColor: 'var(--border-color)',
                      color: '#ef4444',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.backgroundColor = '#ef4444';
                      e.currentTarget.style.color = 'white';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = '#ef4444';
                    }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <div className="flex-1 p-6 overflow-y-auto">
                <div
                  className="prose max-w-none markdown-content"
                  style={{ color: 'var(--text-primary)' }}
                >
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeRaw]}>
                    {selectedNote.content || ''}
                  </ReactMarkdown>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default NotesPage;
