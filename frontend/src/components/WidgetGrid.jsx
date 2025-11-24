import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { widgetsApi } from '../services/api'
import { Loader } from 'lucide-react'
import WeatherWidget from './widgets/WeatherWidget'
import ExchangeRateWidget from './widgets/ExchangeRateWidget'
import NewsWidget from './widgets/NewsWidget'

// Map widget types to components
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  news: NewsWidget,
}

const WidgetGrid = () => {
  const { data: widgetsData, isLoading, error } = useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll()
      return response.data.widgets
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin" size={32} />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        Error loading widgets: {error.message}
      </div>
    )
  }

  if (!widgetsData || widgetsData.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No widgets configured. Add widgets in the configuration file.
      </div>
    )
  }

  return (
    <div className="unified-grid">
      {widgetsData.map((widget) => {
        const WidgetComponent = WIDGET_COMPONENTS[widget.type]

        // Get width from widget configuration (default to 1 bookmark width)
        const widthMultiple = widget.position?.width || 1

        if (!WidgetComponent) {
          return (
            <div key={widget.id} className={`grid-span-${widthMultiple}`}>
              <div className="widget-card">
                <p className="text-[var(--text-secondary)]">
                  Unknown widget type: {widget.type}
                </p>
              </div>
            </div>
          )
        }

        return (
          <div key={widget.id} className={`grid-span-${widthMultiple}`}>
            <WidgetComponent widgetId={widget.id} config={widget.config} />
          </div>
        )
      })}
    </div>
  )
}

export default WidgetGrid
