import React from 'react'
import { Sun, Moon } from 'lucide-react'
import BookmarkGrid from './BookmarkGrid'
import WidgetGrid from './WidgetGrid'

const Dashboard = ({ theme, toggleTheme }) => {
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
        <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
          Bookmarks
        </h2>
        <BookmarkGrid />
      </section>

      {/* Widgets Section */}
      <section>
        <h2 className="text-xl font-semibold mb-4 text-[var(--text-primary)]">
          Widgets
        </h2>
        <WidgetGrid />
      </section>
    </div>
  )
}

export default Dashboard
