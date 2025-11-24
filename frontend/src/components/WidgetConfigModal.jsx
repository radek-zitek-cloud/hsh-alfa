import React, { useEffect, useState } from 'react'
import { X } from 'lucide-react'

const WidgetConfigModal = ({ isOpen, onClose, children, title }) => {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true)
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
      const timer = setTimeout(() => setIsVisible(false), 300)
      return () => clearTimeout(timer)
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isVisible && !isOpen) return null

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${
        isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative bg-[var(--bg-secondary)] rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden transition-all duration-300 ${
          isOpen ? 'scale-100' : 'scale-95'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border-color)]">
          <h2 className="text-2xl font-bold text-[var(--text-primary)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[var(--bg-primary)] transition-colors"
            aria-label="Close modal"
          >
            <X size={24} className="text-[var(--text-secondary)]" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-100px)]">
          {children}
        </div>
      </div>
    </div>
  )
}

export default WidgetConfigModal
