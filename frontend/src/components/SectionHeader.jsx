import { ChevronUp, ChevronDown, Eye, EyeOff, ArrowUp } from 'lucide-react'

const SectionHeader = ({ section, onMoveUp, onMoveDown, isFirst, isLast, onToggleCollapse, isCollapsed }) => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="flex items-center justify-between mb-4 pb-2 border-b border-[var(--border-color)]">
      <h2 className="text-xl font-semibold text-[var(--text-primary)]">
        {section.title}
      </h2>
      <div className="flex gap-2">
        <button
          onClick={scrollToTop}
          className="p-1 rounded transition-all text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
          aria-label="Scroll to top"
          title="Scroll to top"
        >
          <ArrowUp size={20} />
        </button>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded transition-all text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
          aria-label={isCollapsed ? "Expand section" : "Collapse section"}
          title={isCollapsed ? "Expand section" : "Collapse section"}
        >
          {isCollapsed ? (
            <EyeOff size={20} />
          ) : (
            <Eye size={20} />
          )}
        </button>
        <button
          onClick={onMoveUp}
          disabled={isFirst}
          className={`p-1 rounded transition-colors ${
            isFirst
              ? 'text-[var(--text-tertiary)] cursor-not-allowed'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
          }`}
          aria-label="Move section up"
          title="Move section up"
        >
          <ChevronUp size={20} />
        </button>
        <button
          onClick={onMoveDown}
          disabled={isLast}
          className={`p-1 rounded transition-colors ${
            isLast
              ? 'text-[var(--text-tertiary)] cursor-not-allowed'
              : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]'
          }`}
          aria-label="Move section down"
          title="Move section down"
        >
          <ChevronDown size={20} />
        </button>
      </div>
    </div>
  )
}

export default SectionHeader
