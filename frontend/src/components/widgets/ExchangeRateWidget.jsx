import { useWidget } from '../../hooks/useWidget'
import { DollarSign, Loader, AlertCircle, ExternalLink } from 'lucide-react'

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
          {rateData.rates.map((rate) => {
            // Defensive checks to prevent crashes
            if (!rate || !rate.currency) return null
            const rateValue = rate.rate ?? 0
            const reverseRateValue = rate.reverse_rate ?? 0
            const yahooFinanceUrl = `https://finance.yahoo.com/quote/${rateData.base_currency}${rate.currency}=X/`

            return (
              <a
                key={rate.currency}
                href={yahooFinanceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2 bg-[var(--bg-primary)] rounded border border-[var(--border-color)] hover:border-[var(--accent-color)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer group"
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent-color)]">
                    {rate.currency}
                  </span>
                  <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 text-[var(--accent-color)] transition-opacity" />
                </div>
                <div className="text-right">
                  <div className="font-mono text-[var(--text-primary)]">
                    {rateValue.toFixed(4)} / {reverseRateValue.toFixed(4)}
                  </div>
                </div>
              </a>
            )
          })}
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
