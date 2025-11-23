import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { Responsive, WidthProvider } from 'react-grid-layout'
import { widgetsApi } from '../services/api'
import { Loader } from 'lucide-react'
import WeatherWidget from './widgets/WeatherWidget'
import ExchangeRateWidget from './widgets/ExchangeRateWidget'
import 'react-grid-layout/css/styles.css'
import 'react-grid-layout/css/resizable.css'

const ResponsiveGridLayout = WidthProvider(Responsive)

// Map widget types to components
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
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

  // Convert widget configurations to grid layout
  const layouts = {
    lg: widgetsData.map((widget, index) => ({
      i: widget.id,
      x: widget.position?.col || index % 3,
      y: widget.position?.row || Math.floor(index / 3),
      w: widget.position?.width || 1,
      h: widget.position?.height || 2,
    })),
  }

  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={layouts}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: 4, md: 3, sm: 2, xs: 1, xxs: 1 }}
      rowHeight={150}
      isDraggable={false}
      isResizable={false}
    >
      {widgetsData.map((widget) => {
        const WidgetComponent = WIDGET_COMPONENTS[widget.type]

        if (!WidgetComponent) {
          return (
            <div key={widget.id} className="widget-card">
              <p className="text-[var(--text-secondary)]">
                Unknown widget type: {widget.type}
              </p>
            </div>
          )
        }

        return (
          <div key={widget.id}>
            <WidgetComponent widgetId={widget.id} config={widget.config} />
          </div>
        )
      })}
    </ResponsiveGridLayout>
  )
}

export default WidgetGrid
