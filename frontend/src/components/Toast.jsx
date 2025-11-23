import React, { useEffect } from 'react'
import { CheckCircle, XCircle, X } from 'lucide-react'

const Toast = ({ message, type = 'success', onClose, duration = 3000 }) => {
  useEffect(() => {
    if (duration) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)

      return () => clearTimeout(timer)
    }
  }, [duration, onClose])

  const icons = {
    success: <CheckCircle size={20} className="text-green-500" />,
    error: <XCircle size={20} className="text-red-500" />,
  }

  const bgColors = {
    success: 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-800',
    error: 'bg-red-50 dark:bg-red-900/20 border-red-300 dark:border-red-800',
  }

  const textColors = {
    success: 'text-green-800 dark:text-green-200',
    error: 'text-red-800 dark:text-red-200',
  }

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg ${bgColors[type]} animate-slide-up`}
      role="alert"
    >
      {icons[type]}
      <p className={`${textColors[type]} font-medium`}>{message}</p>
      <button
        onClick={onClose}
        className={`ml-2 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors`}
        aria-label="Close notification"
      >
        <X size={16} className={textColors[type]} />
      </button>
    </div>
  )
}

export default Toast
