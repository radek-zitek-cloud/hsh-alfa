import React, { useState } from 'react'
import { Sun, Moon, Plus } from 'lucide-react'
import BookmarkGrid from './BookmarkGrid'
import WidgetGrid from './WidgetGrid'
import BookmarkModal from './BookmarkModal'
import BookmarkForm from './BookmarkForm'
import WidgetForm from './WidgetForm'

const Dashboard = ({ theme, toggleTheme }) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [isAddWidgetModalOpen, setIsAddWidgetModalOpen] = useState(false)

  return (
    <div className="min-h-screen p-4 md:p-6 lg:p-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-[var(--text-primary)]">
          Home Sweet Home
        </h1>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'light' ? <Moon size={24} /> : <Sun size={24} />}
        </button>
      </header>

      {/* Bookmarks Section */}
      <section className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Bookmarks
          </h2>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus size={18} />
            Add Bookmark
          </button>
        </div>
        <BookmarkGrid />
      </section>

      {/* Widgets Section */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Widgets
          </h2>
          <button
            onClick={() => setIsAddWidgetModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
          >
            <Plus size={18} />
            Add Widget
          </button>
        </div>
        <WidgetGrid />
      </section>

      {/* Add Bookmark Modal */}
      <BookmarkModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Bookmark"
      >
        <BookmarkForm
          onSuccess={() => setIsAddModalOpen(false)}
          onCancel={() => setIsAddModalOpen(false)}
        />
      </BookmarkModal>

      {/* Add Widget Modal */}
      <BookmarkModal
        isOpen={isAddWidgetModalOpen}
        onClose={() => setIsAddWidgetModalOpen(false)}
        title="Add New Widget"
      >
        <WidgetForm
          onSuccess={() => setIsAddWidgetModalOpen(false)}
          onCancel={() => setIsAddWidgetModalOpen(false)}
        />
      </BookmarkModal>
    </div>
  )
}

export default Dashboard
