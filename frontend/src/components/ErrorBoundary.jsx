import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console
    console.error('Error caught by boundary:', error, errorInfo)
    this.setState({
      error,
      errorInfo,
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[var(--bg-primary)] flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-[var(--bg-secondary)] rounded-lg p-6 border border-[var(--border-color)]">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle size={32} className="text-red-500" />
              <h1 className="text-xl font-bold text-[var(--text-primary)]">
                Something went wrong
              </h1>
            </div>

            <p className="text-[var(--text-secondary)] mb-4">
              The application encountered an unexpected error. Please try refreshing the page.
            </p>

            {this.state.error && (
              <details className="mb-4 text-sm">
                <summary className="cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                  Error details
                </summary>
                <div className="mt-2 p-3 bg-[var(--bg-primary)] rounded border border-[var(--border-color)] font-mono text-xs overflow-auto">
                  <div className="text-red-500 mb-2">
                    {this.state.error.toString()}
                  </div>
                  {this.state.errorInfo && (
                    <div className="text-[var(--text-secondary)]">
                      {this.state.errorInfo.componentStack}
                    </div>
                  )}
                </div>
              </details>
            )}

            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-[var(--accent-color)] text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              <RefreshCw size={18} />
              Refresh Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
