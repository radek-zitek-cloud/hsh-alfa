import React from 'react'
import { useWidget } from '../../hooks/useWidget'
import { Cloud, CloudRain, Sun, Wind, Droplets, Loader, AlertCircle } from 'lucide-react'

const WeatherIcon = ({ icon }) => {
  const iconMap = {
    '01d': <Sun size={48} className="text-yellow-500" />,
    '01n': <Sun size={48} className="text-gray-400" />,
    '02d': <Cloud size={48} className="text-gray-400" />,
    '02n': <Cloud size={48} className="text-gray-500" />,
    '03d': <Cloud size={48} className="text-gray-400" />,
    '03n': <Cloud size={48} className="text-gray-500" />,
    '04d': <Cloud size={48} className="text-gray-500" />,
    '04n': <Cloud size={48} className="text-gray-600" />,
    '09d': <CloudRain size={48} className="text-blue-400" />,
    '09n': <CloudRain size={48} className="text-blue-500" />,
    '10d': <CloudRain size={48} className="text-blue-400" />,
    '10n': <CloudRain size={48} className="text-blue-500" />,
    '11d': <CloudRain size={48} className="text-purple-500" />,
    '11n': <CloudRain size={48} className="text-purple-600" />,
  }

  return iconMap[icon] || <Cloud size={48} />
}

const WeatherWidget = ({ widgetId, config }) => {
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
            {error?.message || data?.error || 'Failed to load weather data'}
          </span>
        </div>
      </div>
    )
  }

  const weatherData = data?.data
  if (!weatherData) {
    return (
      <div className="widget-card">
        <p className="text-[var(--text-secondary)]">No weather data available</p>
      </div>
    )
  }

  return (
    <div className="widget-card">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">
            {weatherData.location?.name}
          </h3>
          <p className="text-xs text-[var(--text-secondary)]">
            {weatherData.location?.country}
          </p>
        </div>

        {/* Current Weather */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-4xl font-bold text-[var(--text-primary)]">
              {weatherData.current?.temperature}
              {weatherData.current?.temp_unit}
            </div>
            <p className="text-sm text-[var(--text-secondary)] capitalize mt-1">
              {weatherData.current?.description}
            </p>
          </div>
          <WeatherIcon icon={weatherData.current?.icon} />
        </div>

        {/* Additional Info */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-1">
            <Wind size={16} className="text-[var(--text-secondary)]" />
            <span className="text-[var(--text-secondary)]">
              {weatherData.current?.wind_speed} m/s
            </span>
          </div>
          <div className="flex items-center gap-1">
            <Droplets size={16} className="text-[var(--text-secondary)]" />
            <span className="text-[var(--text-secondary)]">
              {weatherData.current?.humidity}%
            </span>
          </div>
        </div>

        {/* Forecast */}
        {weatherData.forecast && weatherData.forecast.length > 0 && (
          <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
            <div className="grid grid-cols-5 gap-1 text-xs">
              {weatherData.forecast.slice(0, 5).map((day) => (
                <div key={day.date} className="text-center">
                  <p className="text-[var(--text-secondary)] mb-1">
                    {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                  </p>
                  <p className="font-semibold text-[var(--text-primary)]">
                    {Math.round(day.temperature)}°
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default WeatherWidget
