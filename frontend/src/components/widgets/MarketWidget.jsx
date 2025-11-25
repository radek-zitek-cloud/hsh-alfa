import React from 'react'
import { useWidget } from '../../hooks/useWidget'
import { TrendingUp, TrendingDown, DollarSign, Loader, AlertCircle } from 'lucide-react'

const MarketWidget = ({ widgetId, config }) => {
  const { data, isLoading, error } = useWidget(widgetId, {
    refetchInterval: (config?.refresh_interval || 300) * 1000, // Default 5 minutes
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
            {error?.message || data?.error || 'Failed to load market data'}
          </span>
        </div>
      </div>
    )
  }

  const marketData = data?.data
  if (!marketData) {
    return (
      <div className="widget-card">
        <p className="text-[var(--text-secondary)]">No market data available</p>
      </div>
    )
  }

  const { stocks = [], crypto = [] } = marketData
  const hasData = stocks.length > 0 || crypto.length > 0

  if (!hasData) {
    return (
      <div className="widget-card">
        <p className="text-[var(--text-secondary)]">No market data configured</p>
      </div>
    )
  }

  const renderMarketItem = (item) => {
    // Defensive checks to prevent crashes
    if (!item || !item.symbol) {
      return null
    }

    const isPositive = item.change_percent && item.change_percent > 0
    const isNegative = item.change_percent && item.change_percent < 0
    const price = item.price ?? 0
    const currency = item.currency || 'USD'

    // Helper function to render period change indicator
    const renderPeriodChange = (label, changePercent) => {
      if (changePercent === null || changePercent === undefined) {
        return null
      }

      const isUp = changePercent > 0
      const isDown = changePercent < 0
      const colorClass = isUp ? 'text-green-500' : isDown ? 'text-red-500' : 'text-[var(--text-secondary)]'

      return (
        <div className={`flex items-center gap-1 ${colorClass}`}>
          {isUp && <TrendingUp size={10} />}
          {isDown && <TrendingDown size={10} />}
          <span className="font-mono text-xs">
            {label}: {isUp ? '+' : ''}{changePercent.toFixed(2)}%
          </span>
        </div>
      )
    }

    return (
      <div
        key={item.symbol}
        className="flex flex-col p-3 bg-[var(--bg-primary)] rounded border border-[var(--border-color)] hover:border-[var(--accent-color)] transition-colors"
      >
        {/* Top Row: Symbol and Price */}
        <div className="flex items-start justify-between mb-2">
          {/* Left: Symbol and Name */}
          <div className="flex flex-col">
            <span className="font-semibold text-[var(--text-primary)]">
              {item.symbol}
            </span>
            {item.name && item.name !== item.symbol && (
              <span className="text-xs text-[var(--text-secondary)]">
                {item.name}
              </span>
            )}
          </div>

          {/* Right: Price and 1-day Change */}
          <div className="flex flex-col items-end">
            <div className="font-mono text-[var(--text-primary)] font-semibold">
              {price.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: price < 1 ? 6 : 2
              })}
              <span className="text-xs text-[var(--text-secondary)] ml-1">
                {currency}
              </span>
            </div>

            {/* 1-day Change indicator */}
            {item.change_percent !== null && item.change_percent !== undefined && (
              <div className={`flex items-center gap-1 text-sm ${
                isPositive ? 'text-green-500' :
                isNegative ? 'text-red-500' :
                'text-[var(--text-secondary)]'
              }`}>
                {isPositive && <TrendingUp size={14} />}
                {isNegative && <TrendingDown size={14} />}
                <span className="font-mono">
                  {isPositive ? '+' : ''}{item.change_percent.toFixed(2)}%
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Row: Period Changes */}
        {(item.change_5d_percent !== null && item.change_5d_percent !== undefined ||
          item.change_30d_percent !== null && item.change_30d_percent !== undefined ||
          item.change_ytd_percent !== null && item.change_ytd_percent !== undefined) && (
          <div className="flex flex-wrap gap-3 pt-2 border-t border-[var(--border-color)]">
            {renderPeriodChange('5D', item.change_5d_percent)}
            {renderPeriodChange('30D', item.change_30d_percent)}
            {renderPeriodChange('YTD', item.change_ytd_percent)}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="widget-card">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <DollarSign size={24} className="text-[var(--accent-color)]" />
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            Markets
          </h3>
        </div>

        {/* Content */}
        <div className="space-y-3 flex-1 overflow-y-auto">
          {/* Stocks Section */}
          {stocks.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-2 uppercase tracking-wide">
                Stocks & Indices
              </h4>
              <div className="space-y-2">
                {stocks.map(renderMarketItem)}
              </div>
            </div>
          )}

          {/* Crypto Section */}
          {crypto.length > 0 && (
            <div className={stocks.length > 0 ? 'mt-4' : ''}>
              <h4 className="text-sm font-semibold text-[var(--text-secondary)] mb-2 uppercase tracking-wide">
                Cryptocurrency
              </h4>
              <div className="space-y-2">
                {crypto.map(renderMarketItem)}
              </div>
            </div>
          )}
        </div>

        {/* Last Update */}
        {data?.last_updated && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
            <p className="text-xs text-[var(--text-secondary)]">
              Updated: {new Date(data.last_updated).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default MarketWidget
