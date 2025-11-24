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
    const isPositive = item.change_percent && item.change_percent > 0
    const isNegative = item.change_percent && item.change_percent < 0

    return (
      <div
        key={item.symbol}
        className="flex items-center justify-between p-3 bg-[var(--bg-primary)] rounded border border-[var(--border-color)] hover:border-[var(--accent-color)] transition-colors"
      >
        {/* Left: Symbol and Name */}
        <div className="flex flex-col">
          <span className="font-semibold text-[var(--text-primary)]">
            {item.symbol}
          </span>
          {item.name !== item.symbol && (
            <span className="text-xs text-[var(--text-secondary)]">
              {item.name}
            </span>
          )}
        </div>

        {/* Right: Price and Change */}
        <div className="flex flex-col items-end">
          <div className="font-mono text-[var(--text-primary)] font-semibold">
            {item.price.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: item.price < 1 ? 6 : 2
            })}
            <span className="text-xs text-[var(--text-secondary)] ml-1">
              {item.currency}
            </span>
          </div>

          {/* Change indicator */}
          {item.change_percent !== null && (
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
