import React, { useState } from 'react'
import { X, Download, Upload, FileJson, FileCode, FileText, FileX2, FileSpreadsheet, AlertCircle } from 'lucide-react'
import { exportImportApi } from '../services/api'

const ExportImportModal = ({ isOpen, onClose }) => {
  const [selectedFormat, setSelectedFormat] = useState('json')
  const [isExporting, setIsExporting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const formats = [
    { value: 'json', label: 'JSON', icon: FileJson, description: 'JavaScript Object Notation - widely supported' },
    { value: 'yaml', label: 'YAML', icon: FileCode, description: 'Human-readable data serialization format' },
    { value: 'toml', label: 'TOML', icon: FileText, description: "Tom's Obvious Minimal Language" },
    { value: 'xml', label: 'XML', icon: FileX2, description: 'Extensible Markup Language' },
    { value: 'csv', label: 'CSV', icon: FileSpreadsheet, description: 'Comma-Separated Values - spreadsheet compatible' },
  ]

  if (!isOpen) return null

  const handleExport = async () => {
    setIsExporting(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await exportImportApi.exportData(selectedFormat)

      // Create blob from response
      const blob = new Blob([response.data], { type: response.headers['content-type'] })

      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition']
      let filename = `home-sweet-home-export.${selectedFormat}`

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }

      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setSuccess(`Data exported successfully as ${selectedFormat.toUpperCase()}!`)

      // Auto-close modal after successful export (optional)
      setTimeout(() => {
        onClose()
      }, 2000)
    } catch (err) {
      console.error('Export failed:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to export data. Please try again.')
    } finally {
      setIsExporting(false)
    }
  }

  const handleImport = () => {
    // Placeholder - not implemented yet
    setError('Import functionality is not yet implemented.')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[var(--bg-primary)] rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Export / Import Data
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[var(--bg-secondary)] transition-colors"
            aria-label="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Messages */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
              <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-red-500 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-2">
              <AlertCircle className="text-green-500 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-green-500 text-sm">{success}</p>
            </div>
          )}

          {/* Export Section */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Download size={20} />
              Export Database
            </h3>
            <p className="text-[var(--text-secondary)] text-sm mb-4">
              Download a complete backup of your bookmarks, widgets, sections, and preferences.
            </p>

            {/* Format Selection */}
            <div className="space-y-2 mb-4">
              <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
                Select Export Format:
              </label>
              <div className="grid grid-cols-1 gap-2">
                {formats.map((format) => {
                  const Icon = format.icon
                  return (
                    <label
                      key={format.value}
                      className={`
                        flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all
                        ${selectedFormat === format.value
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-[var(--border-color)] hover:border-blue-500/50 hover:bg-[var(--bg-secondary)]'
                        }
                      `}
                    >
                      <input
                        type="radio"
                        name="format"
                        value={format.value}
                        checked={selectedFormat === format.value}
                        onChange={(e) => setSelectedFormat(e.target.value)}
                        className="w-4 h-4 text-blue-500"
                      />
                      <Icon size={20} className="text-[var(--text-secondary)]" />
                      <div className="flex-1">
                        <div className="font-medium text-[var(--text-primary)]">{format.label}</div>
                        <div className="text-xs text-[var(--text-secondary)]">{format.description}</div>
                      </div>
                    </label>
                  )
                })}
              </div>
            </div>

            {/* Export Button */}
            <button
              onClick={handleExport}
              disabled={isExporting}
              className={`
                w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium
                transition-all
                ${isExporting
                  ? 'bg-gray-500 cursor-not-allowed opacity-50'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
                }
              `}
            >
              <Download size={20} />
              {isExporting ? 'Exporting...' : `Export as ${selectedFormat.toUpperCase()}`}
            </button>
          </div>

          {/* Divider */}
          <div className="border-t border-[var(--border-color)] my-6"></div>

          {/* Import Section */}
          <div>
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Upload size={20} />
              Import Database
            </h3>
            <p className="text-[var(--text-secondary)] text-sm mb-4">
              Restore your data from a previously exported file. (Coming soon)
            </p>

            {/* Import Button (Disabled) */}
            <button
              onClick={handleImport}
              disabled={true}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium bg-gray-500 cursor-not-allowed opacity-50 text-white"
              title="Import functionality is not yet implemented"
            >
              <Upload size={20} />
              Import Data (Coming Soon)
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExportImportModal
