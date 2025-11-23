import React from 'react'
import { useWidget } from '../../hooks/useWidget'
import { DollarSign, TrendingUp, TrendingDown, Loader, AlertCircle } from 'lucide-react'

const ExchangeRateWidget = ({ widgetId, config }) => {
  const { data, isLoading, error } = useWidget(widgetId, {
    refetchInterval: (config?.refresh_interval || 3600) * 1000,
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
            {error?.message || data?.error || 'Failed to load exchange rates'}
          </span>
        </div>
      </div>
    )
  }

  const rateData = data?.data
  if (!rateData || !rateData.rates) {
    return (
      <div className="widget-card">
        <p className="text-[var(--text-secondary)]">No exchange rate data available</p>
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
            Exchange Rates
          </h3>
        </div>

        {/* Base Currency */}
        <p className="text-sm text-[var(--text-secondary)] mb-3">
          Base: {rateData.base_currency}
        </p>

        {/* Rates */}
        <div className="space-y-3 flex-1">
          {rateData.rates.map((rate, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-2 bg-[var(--bg-primary)] rounded border border-[var(--border-color)]"
            >
              <div className="flex items-center gap-2">
                <span className="font-semibold text-[var(--text-primary)]">
                  {rate.currency}
                </span>
              </div>
              <div className="text-right">
                <div className="font-mono text-[var(--text-primary)]">
                  {rate.rate.toFixed(4)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Last Update */}
        {rateData.last_update && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
            <p className="text-xs text-[var(--text-secondary)]">
              Updated: {new Date(rateData.last_update).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ExchangeRateWidget
