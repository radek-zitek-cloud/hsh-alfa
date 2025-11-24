import React, { useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { widgetsApi, sectionsApi } from '../services/api'
import { Loader } from 'lucide-react'
import WeatherWidget from './widgets/WeatherWidget'
import ExchangeRateWidget from './widgets/ExchangeRateWidget'
import NewsWidget from './widgets/NewsWidget'
import MarketWidget from './widgets/MarketWidget'
import SectionHeader from './SectionHeader'

// Map widget types to components
const WIDGET_COMPONENTS = {
  weather: WeatherWidget,
  exchange_rate: ExchangeRateWidget,
  news: NewsWidget,
  market: MarketWidget,
}

// Map widget types to section names
const WIDGET_TYPE_TO_SECTION = {
  weather: 'weather',
  exchange_rate: 'rates',
  market: 'markets',
  news: 'news',
}

const WidgetGrid = () => {
  const queryClient = useQueryClient()

  // Fetch widgets
  const { data: widgetsData, isLoading: widgetsLoading, error: widgetsError } = useQuery({
    queryKey: ['widgets'],
    queryFn: async () => {
      const response = await widgetsApi.getAll()
      return response.data.widgets
    },
  })

  // Fetch sections
  const { data: sectionsData, isLoading: sectionsLoading, error: sectionsError } = useQuery({
    queryKey: ['sections'],
    queryFn: async () => {
      const response = await sectionsApi.getAll()
      return response.data
    },
  })

  // Mutation for reordering sections
  const reorderMutation = useMutation({
    mutationFn: (sections) => sectionsApi.reorder(sections),
    onSuccess: () => {
      queryClient.invalidateQueries(['sections'])
    },
  })

  // Group widgets by section
  const widgetsBySection = useMemo(() => {
    if (!widgetsData || !sectionsData) return {}

    const grouped = {}

    // Initialize all sections with empty arrays
    sectionsData.forEach(section => {
      grouped[section.name] = []
    })

    // Group widgets by their section
    widgetsData.forEach(widget => {
      const sectionName = WIDGET_TYPE_TO_SECTION[widget.type]
      if (sectionName && grouped[sectionName]) {
        grouped[sectionName].push(widget)
      }
    })

    return grouped
  }, [widgetsData, sectionsData])

  // Handle moving section up
  const handleMoveUp = (sectionIndex) => {
    if (sectionIndex === 0) return

    const newSections = [...sectionsData]
    const temp = newSections[sectionIndex]
    newSections[sectionIndex] = newSections[sectionIndex - 1]
    newSections[sectionIndex - 1] = temp

    // Update positions
    const reorderData = newSections.map((section, index) => ({
      name: section.name,
      position: index,
    }))

    reorderMutation.mutate(reorderData)
  }

  // Handle moving section down
  const handleMoveDown = (sectionIndex) => {
    if (sectionIndex === sectionsData.length - 1) return

    const newSections = [...sectionsData]
    const temp = newSections[sectionIndex]
    newSections[sectionIndex] = newSections[sectionIndex + 1]
    newSections[sectionIndex + 1] = temp

    // Update positions
    const reorderData = newSections.map((section, index) => ({
      name: section.name,
      position: index,
    }))

    reorderMutation.mutate(reorderData)
  }

  if (widgetsLoading || sectionsLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader className="animate-spin" size={32} />
      </div>
    )
  }

  if (widgetsError || sectionsError) {
    return (
      <div className="text-red-500 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
        Error loading widgets: {(widgetsError || sectionsError).message}
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

  if (!sectionsData || sectionsData.length === 0) {
    return (
      <div className="text-[var(--text-secondary)] text-center p-8">
        No sections configured. Sections will be created automatically.
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {sectionsData.map((section, sectionIndex) => {
        const sectionWidgets = widgetsBySection[section.name] || []

        // Skip empty sections
        if (sectionWidgets.length === 0) return null

        return (
          <section key={section.id}>
            <SectionHeader
              section={section}
              onMoveUp={() => handleMoveUp(sectionIndex)}
              onMoveDown={() => handleMoveDown(sectionIndex)}
              isFirst={sectionIndex === 0}
              isLast={sectionIndex === sectionsData.length - 1}
            />
            <div className="unified-grid">
              {sectionWidgets.map((widget) => {
                const WidgetComponent = WIDGET_COMPONENTS[widget.type]
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
          </section>
        )
      })}
    </div>
  )
}

export default WidgetGrid
