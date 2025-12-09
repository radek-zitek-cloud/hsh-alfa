import { ChevronRight, ChevronDown, Plus, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Trash2 } from 'lucide-react';

const NoteTreeItem = ({
  note,
  depth,
  isExpanded,
  hasChildren,
  isSelected,
  onToggle,
  onSelect,
  onCreateSubnote,
  onMoveUp,
  onMoveDown,
  onPromote,
  onDemote,
  onDelete,
  canMoveUp,
  canMoveDown,
  canPromote,
  canDemote,
}) => {

  // Truncate content for preview
  const contentPreview = note.content
    ? note.content.substring(0, 50).replace(/\n/g, ' ')
    : '';

  return (
    <div
      className={`flex items-center gap-1 p-2 rounded cursor-pointer hover:bg-hover group ${
        isSelected ? 'bg-accent/20 border-l-2 border-accent' : ''
      }`}
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

      {/* Note content with overlay controls */}
      <div className="flex-1 min-w-0 relative">
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

        {/* Overlay Controls - positioned at bottom right */}
        <div className="absolute bottom-0 right-0 flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity bg-background/90 backdrop-blur-sm rounded p-0.5">
          {/* Move Up */}
          <button
            onClick={e => {
              e.stopPropagation();
              onMoveUp();
            }}
            disabled={!canMoveUp}
            className={`p-1 hover:bg-accent hover:text-white rounded ${
              !canMoveUp ? 'opacity-30 cursor-not-allowed' : ''
            }`}
            title="Move up"
          >
            <ArrowUp className="w-3.5 h-3.5" />
          </button>

          {/* Move Down */}
          <button
            onClick={e => {
              e.stopPropagation();
              onMoveDown();
            }}
            disabled={!canMoveDown}
            className={`p-1 hover:bg-accent hover:text-white rounded ${
              !canMoveDown ? 'opacity-30 cursor-not-allowed' : ''
            }`}
            title="Move down"
          >
            <ArrowDown className="w-3.5 h-3.5" />
          </button>

          {/* Promote (move left) */}
          <button
            onClick={e => {
              e.stopPropagation();
              onPromote();
            }}
            disabled={!canPromote}
            className={`p-1 hover:bg-accent hover:text-white rounded ${
              !canPromote ? 'opacity-30 cursor-not-allowed' : ''
            }`}
            title="Promote to parent level"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
          </button>

          {/* Demote (move right - make child of sibling above) */}
          <button
            onClick={e => {
              e.stopPropagation();
              onDemote();
            }}
            disabled={!canDemote}
            className={`p-1 hover:bg-accent hover:text-white rounded ${
              !canDemote ? 'opacity-30 cursor-not-allowed' : ''
            }`}
            title="Make child of sibling above"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          {/* Add subnote */}
          <button
            onClick={e => {
              e.stopPropagation();
              onCreateSubnote();
            }}
            className="p-1 hover:bg-accent hover:text-white rounded"
            title="Add subnote"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>

          {/* Delete */}
          <button
            onClick={e => {
              e.stopPropagation();
              onDelete();
            }}
            className="p-1 hover:bg-destructive hover:text-white rounded"
            title={hasChildren ? "Delete note and all subnotes" : "Delete note"}
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default NoteTreeItem;
