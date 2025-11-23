import React from 'react'
import { useWidget } from '../../hooks/useWidget'
import { Newspaper, ExternalLink, Loader, AlertCircle, Calendar } from 'lucide-react'

const NewsArticle = ({ article }) => {
  const formatDate = (dateString) => {
    if (!dateString) return ''
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 60) {
        return `${diffMins}m ago`
      } else if (diffHours < 24) {
        return `${diffHours}h ago`
      } else if (diffDays < 7) {
        return `${diffDays}d ago`
      } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      }
    } catch (e) {
      return dateString
    }
  }

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block p-3 rounded-lg border border-[var(--border-color)] hover:bg-[var(--bg-primary)] transition-colors"
    >
      <div className="flex gap-3">
        {article.image_url && (
          <div className="flex-shrink-0 w-20 h-20 overflow-hidden rounded">
            <img
              src={article.image_url}
              alt={article.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none'
              }}
            />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-[var(--text-primary)] line-clamp-2 mb-1">
            {article.title}
          </h4>
          {article.description && (
            <p className="text-xs text-[var(--text-secondary)] line-clamp-2 mb-2">
              {article.description}
            </p>
          )}
          <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
            {article.source && (
              <span className="font-medium">{article.source}</span>
            )}
            {article.published_at && (
              <>
                <span>•</span>
                <div className="flex items-center gap-1">
                  <Calendar size={12} />
                  <span>{formatDate(article.published_at)}</span>
                </div>
              </>
            )}
            <ExternalLink size={12} className="ml-auto" />
          </div>
        </div>
      </div>
    </a>
  )
}

const NewsWidget = ({ widgetId, config }) => {
  const { data, isLoading, error } = useWidget(widgetId, {
    refetchInterval: (config?.refresh_interval || 1800) * 1000,
  })

  if (isLoading) {
    return (
      <div className="widget-card flex items-center justify-center">
        <Loader className="animate-spin" size={32} />
      </div>
    )
  }

  if (error || data?.error) {
    return (
      <div className="widget-card">
        <div className="flex items-center gap-2 text-red-500">
          <AlertCircle size={20} />
          <span className="text-sm">
            {error?.message || data?.error || 'Failed to load news data'}
          </span>
        </div>
      </div>
    )
  }

  const newsData = data?.data
  if (!newsData || !newsData.articles || newsData.articles.length === 0) {
    return (
      <div className="widget-card">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper size={20} className="text-[var(--text-primary)]" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">News</h3>
        </div>
        <p className="text-[var(--text-secondary)]">No news articles available</p>
      </div>
    )
  }

  return (
    <div className="widget-card">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <Newspaper size={20} className="text-[var(--text-primary)]" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            News
          </h3>
          <span className="ml-auto text-xs text-[var(--text-secondary)]">
            {newsData.total} {newsData.total === 1 ? 'article' : 'articles'}
          </span>
        </div>

        {/* Articles List */}
        <div className="flex-1 overflow-y-auto space-y-3">
          {newsData.articles.map((article, index) => (
            <NewsArticle key={`${article.url}-${index}`} article={article} />
          ))}
        </div>

        {/* Footer */}
        {data?.last_updated && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
            Last updated: {new Date(data.last_updated).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  )
}

export default NewsWidget
