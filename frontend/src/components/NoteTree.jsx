import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { notesApi } from '../services/api';
import NoteTreeItem from './NoteTreeItem';

const NoteTree = ({ notes, selectedNoteId, onSelectNote, isCreating, onCreateSubnote }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const queryClient = useQueryClient();

  // Build tree structure from flat list
  const noteTree = useMemo(() => {
    const noteMap = new Map();
    const roots = [];

    // First pass: create map of all notes
    notes.forEach(note => {
      noteMap.set(note.id, { ...note, children: [] });
    });

    // Second pass: build tree structure
    notes.forEach(note => {
      const treeNode = noteMap.get(note.id);
      if (note.parent_id === null || note.parent_id === undefined) {
        roots.push(treeNode);
      } else {
        const parent = noteMap.get(note.parent_id);
        if (parent) {
          parent.children.push(treeNode);
        } else {
          // Parent not found, treat as root
          roots.push(treeNode);
        }
      }
    });

    // Sort children by position
    const sortChildren = node => {
      if (node.children && node.children.length > 0) {
        node.children.sort((a, b) => a.position - b.position);
        node.children.forEach(sortChildren);
      }
    };

    roots.sort((a, b) => a.position - b.position);
    roots.forEach(sortChildren);

    return roots;
  }, [notes]);

  // Get flattened list for drag and drop (only visible items)
  const flattenedNotes = useMemo(() => {
    const flattened = [];

    const traverse = (node, depth = 0) => {
      flattened.push({ ...node, depth });

      if (expandedNodes.has(node.id) && node.children && node.children.length > 0) {
        node.children.forEach(child => traverse(child, depth + 1));
      }
    };

    noteTree.forEach(root => traverse(root));
    return flattened;
  }, [noteTree, expandedNodes]);

  const toggleNode = nodeId => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const reorderMutation = useMutation({
    mutationFn: ({ id, parent_id, position }) => notesApi.reorder(id, { parent_id, position }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => notesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      setDeleteConfirm(null);
    },
  });

  // Helper to get siblings of a note
  const getSiblings = (noteId) => {
    const note = notes.find(n => n.id === noteId);
    if (!note) return [];

    return notes
      .filter(n => n.parent_id === note.parent_id)
      .sort((a, b) => a.position - b.position);
  };

  // Helper to count descendants
  const countDescendants = (noteId) => {
    let count = 0;
    const children = notes.filter(n => n.parent_id === noteId);
    count += children.length;
    children.forEach(child => {
      count += countDescendants(child.id);
    });
    return count;
  };

  // Move note up in sibling list
  const handleMoveUp = (noteId) => {
    const siblings = getSiblings(noteId);
    const currentIndex = siblings.findIndex(n => n.id === noteId);

    if (currentIndex > 0) {
      const note = siblings[currentIndex];
      const prevNote = siblings[currentIndex - 1];

      // Swap positions
      reorderMutation.mutate({
        id: noteId,
        parent_id: note.parent_id,
        position: prevNote.position,
      });
    }
  };

  // Move note down in sibling list
  const handleMoveDown = (noteId) => {
    const siblings = getSiblings(noteId);
    const currentIndex = siblings.findIndex(n => n.id === noteId);

    if (currentIndex < siblings.length - 1) {
      const note = siblings[currentIndex];
      const nextNote = siblings[currentIndex + 1];

      // Swap positions
      reorderMutation.mutate({
        id: noteId,
        parent_id: note.parent_id,
        position: nextNote.position,
      });
    }
  };

  // Promote note to parent's level (move left)
  const handlePromote = (noteId) => {
    const note = notes.find(n => n.id === noteId);
    if (!note || !note.parent_id) return;

    const parent = notes.find(n => n.id === note.parent_id);
    if (!parent) return;

    // Get grandparent's children to determine new position
    const newSiblings = notes
      .filter(n => n.parent_id === parent.parent_id)
      .sort((a, b) => a.position - b.position);

    // Place after current parent
    const parentIndex = newSiblings.findIndex(n => n.id === parent.id);
    const newPosition = parentIndex >= 0 ? newSiblings[parentIndex].position + 1 : 0;

    reorderMutation.mutate({
      id: noteId,
      parent_id: parent.parent_id,
      position: newPosition,
    });
  };

  // Demote note to be child of sibling above (move right)
  const handleDemote = (noteId) => {
    const siblings = getSiblings(noteId);
    const currentIndex = siblings.findIndex(n => n.id === noteId);

    if (currentIndex > 0) {
      const prevSibling = siblings[currentIndex - 1];

      // Make this note a child of the previous sibling
      reorderMutation.mutate({
        id: noteId,
        parent_id: prevSibling.id,
        position: 0, // Add as last child
      });

      // Expand the new parent so user can see the change
      setExpandedNodes(prev => {
        const newSet = new Set(prev);
        newSet.add(prevSibling.id);
        return newSet;
      });
    }
  };

  // Delete note with confirmation
  const handleDelete = (noteId) => {
    const note = notes.find(n => n.id === noteId);
    const childCount = countDescendants(noteId);

    setDeleteConfirm({
      noteId,
      title: note?.title || 'this note',
      childCount,
    });
  };

  const confirmDelete = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm.noteId);
    }
  };

  // Check what operations are allowed for a note
  const getOperationFlags = (noteId) => {
    const note = notes.find(n => n.id === noteId);
    if (!note) return {};

    const siblings = getSiblings(noteId);
    const currentIndex = siblings.findIndex(n => n.id === noteId);

    return {
      canMoveUp: currentIndex > 0,
      canMoveDown: currentIndex < siblings.length - 1,
      canPromote: note.parent_id !== null && note.parent_id !== undefined,
      canDemote: currentIndex > 0,
    };
  };

  return (
    <>
      <div className="space-y-1">
        {flattenedNotes.map(note => {
          const flags = getOperationFlags(note.id);
          return (
            <NoteTreeItem
              key={note.id}
              note={note}
              depth={note.depth}
              isExpanded={expandedNodes.has(note.id)}
              hasChildren={note.children && note.children.length > 0}
              isSelected={note.id === selectedNoteId}
              onToggle={() => toggleNode(note.id)}
              onSelect={() => onSelectNote(note.id)}
              onCreateSubnote={() => onCreateSubnote(note.id)}
              onMoveUp={() => handleMoveUp(note.id)}
              onMoveDown={() => handleMoveDown(note.id)}
              onPromote={() => handlePromote(note.id)}
              onDemote={() => handleDemote(note.id)}
              onDelete={() => handleDelete(note.id)}
              canMoveUp={flags.canMoveUp}
              canMoveDown={flags.canMoveDown}
              canPromote={flags.canPromote}
              canDemote={flags.canDemote}
            />
          );
        })}
      </div>

      {/* Delete Confirmation Dialog */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-primary p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-primary mb-2">
              Delete Note
            </h3>
            <p className="text-muted mb-4">
              Are you sure you want to delete "{deleteConfirm.title}"?
            </p>
            {deleteConfirm.childCount > 0 && (
              <p className="text-destructive font-semibold mb-4">
                Warning: This note has {deleteConfirm.childCount} subnote{deleteConfirm.childCount > 1 ? 's' : ''} that will also be deleted.
              </p>
            )}
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 rounded bg-hover text-primary hover:bg-accent/20"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="px-4 py-2 rounded bg-destructive text-white hover:bg-destructive/90"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default NoteTree;
