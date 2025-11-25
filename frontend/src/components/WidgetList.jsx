import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { widgetsApi } from '../services/api'
import { Edit, Trash2, Plus } from 'lucide-react'
import WidgetForm from './WidgetForm'

const WidgetList = () => {
  const queryClient = useQueryClient()
  const [editingWidget, setEditingWidget] = useState(null)
  const [isAddingWidget, setIsAddingWidget] = useState(false)

  // Fetch widgets
  const { data: widgets, isLoading, error } = useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll()
      return response.data
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id) => widgetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['widgets'] })
    },
  })

  const handleDelete = (widget) => {
    if (window.confirm(`Are you sure you want to delete widget "${widget.id}"?`)) {
      deleteMutation.mutate(widget.id)
    }
  }

  const handleEdit = (widget) => {
    setEditingWidget(widget)
    setIsAddingWidget(false)
  }

  const handleAdd = () => {
    setIsAddingWidget(true)
    setEditingWidget(null)
  }

  const handleFormSuccess = () => {
    setEditingWidget(null)
    setIsAddingWidget(false)
  }

  const handleFormCancel = () => {
    setEditingWidget(null)
    setIsAddingWidget(false)
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--accent-color)]"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-100 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg text-red-700 dark:text-red-300">
        Error loading widgets: {error.message}
      </div>
    )
  }

  // Show form if adding or editing
  if (isAddingWidget || editingWidget) {
    return (
      <div>
        <WidgetForm
          widget={editingWidget}
          onSuccess={handleFormSuccess}
          onCancel={handleFormCancel}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Add Widget Button */}
      <div className="flex justify-end">
        <button
          onClick={handleAdd}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          <Plus size={18} />
          Add Widget
        </button>
      </div>

      {/* Widgets List */}
      {widgets && widgets.length === 0 ? (
        <div className="text-center py-12 text-[var(--text-secondary)]">
          <p className="text-lg mb-2">No widgets configured yet</p>
          <p className="text-sm">Click "Add Widget" to create your first widget</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {widgets?.map((widget) => (
            <div
              key={widget.id}
              className="p-6 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                      {widget.id}
                    </h3>
                    <span className="px-2 py-1 text-xs font-medium bg-[var(--accent-color)]/10 text-[var(--accent-color)] rounded-full">
                      {formatTypeName(widget.type)}
                    </span>
                    {!widget.enabled && (
                      <span className="px-2 py-1 text-xs font-medium bg-gray-500/10 text-gray-500 rounded-full">
                        Disabled
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-[var(--text-secondary)]">
                    <div>
                      <span className="font-medium">Position:</span> Row {widget.position.row}, Col {widget.position.col}
                    </div>
                    <div>
                      <span className="font-medium">Size:</span> {widget.position.width}x{widget.position.height}
                    </div>
                    <div>
                      <span className="font-medium">Refresh:</span> {formatInterval(widget.refresh_interval)}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span>{' '}
                      <span className={widget.enabled ? 'text-green-600 dark:text-green-400' : 'text-gray-500'}>
                        {widget.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  </div>

                  {/* Widget Config Preview */}
                  <div className="mt-3 p-3 bg-[var(--bg-secondary)] rounded border border-[var(--border-color)]">
                    <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">Configuration:</p>
                    <pre className="text-xs text-[var(--text-primary)] overflow-x-auto">
                      {JSON.stringify(widget.config, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleEdit(widget)}
                    className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--border-color)] transition-colors"
                    title="Edit widget"
                  >
                    <Edit size={18} className="text-[var(--text-secondary)]" />
                  </button>
                  <button
                    onClick={() => handleDelete(widget)}
                    disabled={deleteMutation.isPending}
                    className="p-2 rounded-lg bg-[var(--bg-secondary)] hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                    title="Delete widget"
                  >
                    <Trash2 size={18} className="text-[var(--text-secondary)]" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// Helper functions
function formatTypeName(type) {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function formatInterval(seconds) {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return `${Math.floor(seconds / 86400)}d`
}

export default WidgetList
