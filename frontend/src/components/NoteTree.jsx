import { useState, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { notesApi } from '../services/api';
import NoteTreeItem from './NoteTreeItem';

const NoteTree = ({ notes, selectedNoteId, onSelectNote, isCreating }) => {
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [activeId, setActiveId] = useState(null);
  const queryClient = useQueryClient();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

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

  const handleDragStart = event => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = event => {
    const { active, over } = event;
    setActiveId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const activeIndex = flattenedNotes.findIndex(n => n.id === active.id);
    const overIndex = flattenedNotes.findIndex(n => n.id === over.id);

    if (activeIndex === -1 || overIndex === -1) {
      return;
    }

    const activeNote = flattenedNotes[activeIndex];
    const overNote = flattenedNotes[overIndex];

    // Determine new parent and position
    let newParentId = overNote.parent_id;
    let newPosition = overNote.position;

    // If dropping on a note with children that is expanded, make it a child
    const overHasChildren = overNote.children && overNote.children.length > 0;
    const overIsExpanded = expandedNodes.has(overNote.id);

    if (overHasChildren && overIsExpanded && overIndex < activeIndex) {
      // Make it first child of the over note
      newParentId = overNote.id;
      newPosition = 0;
    } else if (activeIndex < overIndex) {
      // Moving down - insert after
      newPosition = overNote.position + 1;
    } else {
      // Moving up - insert before
      newPosition = overNote.position;
    }

    // Only update if parent or position changed
    if (activeNote.parent_id !== newParentId || activeNote.position !== newPosition) {
      reorderMutation.mutate({
        id: activeNote.id,
        parent_id: newParentId,
        position: newPosition,
      });
    }
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  // Find the active note for drag overlay
  const activeNote = activeId ? flattenedNotes.find(n => n.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <SortableContext items={flattenedNotes.map(n => n.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-1">
          {flattenedNotes.map(note => (
            <NoteTreeItem
              key={note.id}
              note={note}
              depth={note.depth}
              isExpanded={expandedNodes.has(note.id)}
              hasChildren={note.children && note.children.length > 0}
              isSelected={note.id === selectedNoteId}
              onToggle={() => toggleNode(note.id)}
              onSelect={() => onSelectNote(note.id)}
              isDragging={note.id === activeId}
            />
          ))}
        </div>
      </SortableContext>

      <DragOverlay>
        {activeNote ? (
          <div className="bg-primary p-2 rounded shadow-lg border border-accent opacity-80">
            <div className="text-sm font-medium text-primary">{activeNote.title}</div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
};

export default NoteTree;
