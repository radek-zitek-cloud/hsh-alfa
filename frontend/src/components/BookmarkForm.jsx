import React, { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { bookmarksApi } from '../services/api'
import { Loader } from 'lucide-react'

const BookmarkForm = ({ bookmark, onSuccess, onCancel }) => {
  const queryClient = useQueryClient()
  const isEditing = !!bookmark

  const [formData, setFormData] = useState({
    title: '',
    url: '',
    description: '',
    category: '',
    tags: '',
    favicon: '',
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (bookmark) {
      setFormData({
        title: bookmark.title || '',
        url: bookmark.url || '',
        description: bookmark.description || '',
        category: bookmark.category || '',
        tags: Array.isArray(bookmark.tags) ? bookmark.tags.join(', ') : (bookmark.tags || ''),
        favicon: bookmark.favicon || '',
      })
    }
  }, [bookmark])

  const createMutation = useMutation({
    mutationFn: (data) => bookmarksApi.create(data),
    onMutate: async (newBookmark) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['bookmarks'] })

      // Snapshot previous value
      const previousBookmarks = queryClient.getQueryData(['bookmarks'])

      // Optimistically add the new bookmark (with temporary id)
      queryClient.setQueryData(['bookmarks'], (old) => [
        ...(old || []),
        { ...newBookmark, id: Date.now(), created: new Date().toISOString() }
      ])

      return { previousBookmarks }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['bookmarks'])
      onSuccess?.()
    },
    onError: (error, variables, context) => {
      console.error('Error creating bookmark:', error)
      setErrors({ submit: error.response?.data?.detail || 'Failed to create bookmark' })
      // Rollback to previous state
      if (context?.previousBookmarks) {
        queryClient.setQueryData(['bookmarks'], context.previousBookmarks)
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data) => bookmarksApi.update(bookmark.id, data),
    onMutate: async (updatedData) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['bookmarks'] })

      // Snapshot previous value
      const previousBookmarks = queryClient.getQueryData(['bookmarks'])

      // Optimistically update the bookmark
      queryClient.setQueryData(['bookmarks'], (old) =>
        old?.map((b) => (b.id === bookmark.id ? { ...b, ...updatedData } : b))
      )

      return { previousBookmarks }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['bookmarks'])
      onSuccess?.()
    },
    onError: (error, variables, context) => {
      console.error('Error updating bookmark:', error)
      setErrors({ submit: error.response?.data?.detail || 'Failed to update bookmark' })
      // Rollback to previous state
      if (context?.previousBookmarks) {
        queryClient.setQueryData(['bookmarks'], context.previousBookmarks)
      }
    },
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[name]
        return newErrors
      })
    }
  }

  const validate = () => {
    const newErrors = {}

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required'
    }

    if (!formData.url.trim()) {
      newErrors.url = 'URL is required'
    } else {
      try {
        const urlObj = new URL(formData.url)
        // Block dangerous URL schemes
        const dangerousSchemes = ['javascript', 'data', 'vbscript', 'file']
        if (dangerousSchemes.includes(urlObj.protocol.replace(':', '').toLowerCase())) {
          newErrors.url = 'URL scheme not allowed. Please use http or https'
        }
      } catch (e) {
        newErrors.url = 'Invalid URL format. Please enter a valid URL (e.g., https://example.com)'
      }
    }

    // Validate favicon URL if provided
    if (formData.favicon.trim()) {
      try {
        const faviconUrl = new URL(formData.favicon)
        const dangerousSchemes = ['javascript', 'data', 'vbscript', 'file']
        if (dangerousSchemes.includes(faviconUrl.protocol.replace(':', '').toLowerCase())) {
          newErrors.favicon = 'Favicon URL scheme not allowed. Please use http or https'
        }
      } catch (e) {
        newErrors.favicon = 'Invalid favicon URL format'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Process tags: split by comma and trim each tag
    const tagsArray = formData.tags.trim()
      ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0)
      : null

    const data = {
      title: formData.title.trim(),
      url: formData.url.trim(),
      description: formData.description.trim() || null,
      category: formData.category.trim() || null,
      tags: tagsArray,
      favicon: formData.favicon.trim() || null,
    }

    if (isEditing) {
      updateMutation.mutate(data)
    } else {
      createMutation.mutate(data)
    }
  }

  const isLoading = createMutation.isPending || updateMutation.isPending

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Title *
        </label>
        <input
          type="text"
          id="title"
          name="title"
          value={formData.title}
          onChange={handleChange}
          className={`w-full px-3 py-2 bg-[var(--bg-secondary)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)] ${
            errors.title ? 'border-red-500' : 'border-[var(--border-color)]'
          }`}
          placeholder="My Bookmark"
          disabled={isLoading}
        />
        {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
      </div>

      {/* URL */}
      <div>
        <label htmlFor="url" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          URL *
        </label>
        <input
          type="text"
          id="url"
          name="url"
          value={formData.url}
          onChange={handleChange}
          className={`w-full px-3 py-2 bg-[var(--bg-secondary)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)] ${
            errors.url ? 'border-red-500' : 'border-[var(--border-color)]'
          }`}
          placeholder="https://example.com"
          disabled={isLoading}
        />
        {errors.url && <p className="text-red-500 text-sm mt-1">{errors.url}</p>}
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Description
        </label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          rows={3}
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)]"
          placeholder="A brief description of this bookmark"
          disabled={isLoading}
        />
      </div>

      {/* Category */}
      <div>
        <label htmlFor="category" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Category
        </label>
        <input
          type="text"
          id="category"
          name="category"
          value={formData.category}
          onChange={handleChange}
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)]"
          placeholder="Work, Personal, etc."
          disabled={isLoading}
        />
      </div>

      {/* Tags */}
      <div>
        <label htmlFor="tags" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Tags
        </label>
        <input
          type="text"
          id="tags"
          name="tags"
          value={formData.tags}
          onChange={handleChange}
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)]"
          placeholder="tag1, tag2, tag3"
          disabled={isLoading}
        />
        <p className="text-xs text-[var(--text-secondary)] mt-1">Separate tags with commas</p>
      </div>

      {/* Favicon URL (optional) */}
      <div>
        <label htmlFor="favicon" className="block text-sm font-medium text-[var(--text-primary)] mb-1">
          Favicon URL
        </label>
        <input
          type="text"
          id="favicon"
          name="favicon"
          value={formData.favicon}
          onChange={handleChange}
          className={`w-full px-3 py-2 bg-[var(--bg-secondary)] border rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--accent-color)] ${
            errors.favicon ? 'border-red-500' : 'border-[var(--border-color)]'
          }`}
          placeholder="https://example.com/favicon.ico"
          disabled={isLoading}
        />
        {errors.favicon && <p className="text-red-500 text-sm mt-1">{errors.favicon}</p>}
      </div>

      {/* Submit Error */}
      {errors.submit && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-800 rounded-lg">
          <p className="text-red-600 dark:text-red-400 text-sm">{errors.submit}</p>
        </div>
      )}

      {/* Buttons */}
      <div className="flex gap-3 pt-2">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading && <Loader className="animate-spin" size={16} />}
          {isEditing ? 'Update' : 'Create'} Bookmark
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 bg-[var(--bg-secondary)] text-[var(--text-primary)] rounded-lg hover:bg-[var(--border-color)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default BookmarkForm
