import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { ChevronRight, ChevronDown, GripVertical, Plus } from 'lucide-react';

const NoteTreeItem = ({
  note,
  depth,
  isExpanded,
  hasChildren,
  isSelected,
  onToggle,
  onSelect,
  onCreateSubnote,
  isDragging,
  isOver,
}) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging: isSortableDragging } = useSortable({
    id: note.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging || isSortableDragging ? 0.5 : 1,
  };

  // Truncate content for preview
  const contentPreview = note.content
    ? note.content.substring(0, 50).replace(/\n/g, ' ')
    : '';

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-1 p-2 rounded cursor-pointer hover:bg-hover group ${
        isSelected ? 'bg-accent/20 border-l-2 border-accent' : ''
      } ${isOver ? 'ring-2 ring-accent bg-accent/10' : ''}`}
      onClick={onSelect}
    >
      {/* Indentation */}
      <div style={{ width: `${depth * 20}px` }} className="flex-shrink-0" />

      {/* Expand/Collapse button */}
      <button
        onClick={e => {
          e.stopPropagation();
          onToggle();
        }}
        className={`flex-shrink-0 p-1 hover:bg-hover rounded ${
          !hasChildren ? 'invisible' : ''
        }`}
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-muted" />
        )}
      </button>

      {/* Drag handle */}
      <div
        {...attributes}
        {...listeners}
        className="flex-shrink-0 cursor-grab active:cursor-grabbing p-1 hover:bg-hover rounded"
      >
        <GripVertical className="w-4 h-4 text-muted" />
      </div>

      {/* Note content */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-primary truncate">
          {note.title}
        </div>
        {contentPreview && (
          <div className="text-xs text-muted truncate">
            {contentPreview}
          </div>
        )}
        <div className="text-xs text-muted">
          {new Date(note.updated).toLocaleDateString()}
        </div>
      </div>

      {/* Add subnote button - shown on hover */}
      <button
        onClick={e => {
          e.stopPropagation();
          onCreateSubnote();
        }}
        className="flex-shrink-0 p-1 hover:bg-accent hover:text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
        title="Add subnote"
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
};

export default NoteTreeItem;
