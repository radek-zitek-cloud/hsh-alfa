import { useState, useRef } from 'react';
import {
  Download,
  Upload,
  Trash2,
  FileJson,
  FileCode,
  FileText,
  FileX2,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { exportImportApi } from '../../services/api';

const AdminDataTab = () => {
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [isExporting, setIsExporting] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [isWiping, setIsWiping] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showWipeConfirm, setShowWipeConfirm] = useState(false);
  const [wipeBeforeImport, setWipeBeforeImport] = useState(false);
  const fileInputRef = useRef(null);

  const formats = [
    {
      value: 'json',
      label: 'JSON',
      icon: FileJson,
      description: 'JavaScript Object Notation - widely supported',
    },
    {
      value: 'yaml',
      label: 'YAML',
      icon: FileCode,
      description: 'Human-readable data serialization format',
    },
    { value: 'toml', label: 'TOML', icon: FileText, description: "Tom's Obvious Minimal Language" },
    { value: 'xml', label: 'XML', icon: FileX2, description: 'Extensible Markup Language' },
    {
      value: 'csv',
      label: 'CSV',
      icon: FileSpreadsheet,
      description: 'Comma-Separated Values - spreadsheet compatible',
    },
  ];

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await exportImportApi.exportData(selectedFormat);

      // Create blob from response
      const blob = new Blob([response.data], { type: response.headers['content-type'] });

      // Extract filename from Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition'];
      let filename = `home-sweet-home-export.${selectedFormat}`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Create download link and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      try {
        link.click();
      } finally {
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }

      setSuccess(`Data exported successfully as ${selectedFormat.toUpperCase()}!`);
    } catch (err) {
      console.error('Export failed:', err);
      setError(
        err.response?.data?.detail || err.message || 'Failed to export data. Please try again.'
      );
    } finally {
      setIsExporting(false);
    }
  };

  const handleImport = async event => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('wipe_before_import', wipeBeforeImport.toString());

      const response = await exportImportApi.importData(formData);

      setSuccess(
        `Import successful! Imported ${response.data.imported_bookmarks} bookmarks, ${response.data.imported_widgets} widgets, ${response.data.imported_sections} sections, ${response.data.imported_preferences} preferences, ${response.data.imported_habits} habits, ${response.data.imported_habit_completions} habit completions.`
      );
    } catch (err) {
      console.error('Import failed:', err);
      setError(
        err.response?.data?.detail || err.message || 'Failed to import data. Please try again.'
      );
    } finally {
      setIsImporting(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleWipe = async () => {
    setIsWiping(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await exportImportApi.wipeData();

      setSuccess(
        `Database wiped successfully! Deleted ${response.data.deleted_bookmarks} bookmarks, ${response.data.deleted_widgets} widgets, ${response.data.deleted_sections} sections, ${response.data.deleted_preferences} preferences, ${response.data.deleted_habits} habits, ${response.data.deleted_habit_completions} habit completions.`
      );
      setShowWipeConfirm(false);
    } catch (err) {
      console.error('Wipe failed:', err);
      setError(
        err.response?.data?.detail || err.message || 'Failed to wipe data. Please try again.'
      );
    } finally {
      setIsWiping(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
          <p className="text-red-500">{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg flex items-start gap-3">
          <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={20} />
          <p className="text-green-500">{success}</p>
        </div>
      )}

      {/* Export Section */}
      <div className="bg-[var(--bg-secondary)] rounded-lg p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Download size={20} />
          Export Database
        </h3>
        <p className="text-[var(--text-secondary)] text-sm mb-4">
          Download a complete backup of your bookmarks, widgets, sections, preferences, habits, and
          habit completions.
        </p>

        {/* Format Selection */}
        <div className="space-y-2 mb-4">
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            Select Export Format:
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
            {formats.map(format => {
              const Icon = format.icon;
              return (
                <label
                  key={format.value}
                  className={`
                    flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all
                    ${
                      selectedFormat === format.value
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-[var(--border-color)] hover:border-blue-500/50 hover:bg-[var(--bg-primary)]'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name="format"
                    value={format.value}
                    checked={selectedFormat === format.value}
                    onChange={e => setSelectedFormat(e.target.value)}
                    className="w-4 h-4 text-blue-500"
                  />
                  <Icon size={20} className="text-[var(--text-secondary)]" />
                  <div className="flex-1">
                    <div className="font-medium text-[var(--text-primary)]">{format.label}</div>
                    <div className="text-xs text-[var(--text-secondary)]">{format.description}</div>
                  </div>
                </label>
              );
            })}
          </div>
        </div>

        {/* Export Button */}
        <button
          onClick={handleExport}
          disabled={isExporting}
          className={`
            flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium
            transition-all
            ${
              isExporting
                ? 'bg-gray-500 cursor-not-allowed opacity-50'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }
          `}
        >
          <Download size={20} />
          {isExporting ? 'Exporting...' : `Export as ${selectedFormat.toUpperCase()}`}
        </button>
      </div>

      {/* Import Section */}
      <div className="bg-[var(--bg-secondary)] rounded-lg p-6">
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <Upload size={20} />
          Import Database
        </h3>
        <p className="text-[var(--text-secondary)] text-sm mb-4">
          Restore your data from a previously exported file. Supports JSON, YAML, and TOML formats.
        </p>

        {/* Wipe Before Import Option */}
        <div className="mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={wipeBeforeImport}
              onChange={e => setWipeBeforeImport(e.target.checked)}
              className="w-4 h-4 text-blue-500 rounded"
            />
            <span className="text-[var(--text-primary)]">Wipe existing data before import</span>
          </label>
          <p className="text-xs text-[var(--text-secondary)] mt-1 ml-6">
            Warning: This will delete all existing data before importing.
          </p>
        </div>

        {/* File Input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImport}
          accept=".json,.yaml,.yml,.toml"
          className="hidden"
          disabled={isImporting}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isImporting}
          className={`
            flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium
            transition-all
            ${
              isImporting
                ? 'bg-gray-500 cursor-not-allowed opacity-50'
                : 'bg-green-500 hover:bg-green-600 text-white'
            }
          `}
        >
          <Upload size={20} />
          {isImporting ? 'Importing...' : 'Select File to Import'}
        </button>
      </div>

      {/* Wipe Section */}
      <div className="bg-[var(--bg-secondary)] rounded-lg p-6 border border-red-500/30">
        <h3 className="text-lg font-semibold text-red-500 mb-4 flex items-center gap-2">
          <Trash2 size={20} />
          Wipe Database
        </h3>
        <p className="text-[var(--text-secondary)] text-sm mb-4">
          <strong className="text-red-500">Warning:</strong> This action will permanently delete all
          your data including bookmarks, widgets, sections, preferences, habits, and habit
          completions. This cannot be undone!
        </p>

        {!showWipeConfirm ? (
          <button
            onClick={() => setShowWipeConfirm(true)}
            className="flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium bg-red-500 hover:bg-red-600 text-white transition-all"
          >
            <Trash2 size={20} />
            Wipe All Data
          </button>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-start gap-3">
              <AlertTriangle className="text-red-500 flex-shrink-0 mt-0.5" size={24} />
              <div>
                <p className="font-semibold text-red-500">Are you absolutely sure?</p>
                <p className="text-sm text-[var(--text-secondary)]">
                  This will permanently delete ALL your data. Consider exporting a backup first.
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleWipe}
                disabled={isWiping}
                className={`
                  flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium
                  transition-all
                  ${
                    isWiping
                      ? 'bg-gray-500 cursor-not-allowed opacity-50'
                      : 'bg-red-600 hover:bg-red-700 text-white'
                  }
                `}
              >
                <Trash2 size={20} />
                {isWiping ? 'Wiping...' : 'Yes, Wipe Everything'}
              </button>
              <button
                onClick={() => setShowWipeConfirm(false)}
                disabled={isWiping}
                className="px-6 py-3 rounded-lg font-medium bg-[var(--bg-primary)] border border-[var(--border-color)] text-[var(--text-primary)] hover:bg-[var(--border-color)] transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminDataTab;
