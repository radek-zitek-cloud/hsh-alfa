import { useState, useCallback } from 'react';
import { useWidget } from '../../hooks/useWidget';
import { Loader, AlertCircle } from 'lucide-react';
import { habitsApi } from '../../services/api';
import { useQueryClient } from '@tanstack/react-query';

const HabitTrackingWidget = ({ widgetId, config }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useWidget(widgetId, {
    refetchInterval: (config?.refresh_interval || 300) * 1000,
  });

  const handleToggleToday = useCallback(
    async (habitId, todayDate, currentlyCompleted) => {
      setIsSubmitting(true);

      // Optimistic update: immediately update the UI
      const newCompleted = !currentlyCompleted;
      queryClient.setQueryData(['widget', widgetId], oldData => {
        if (!oldData?.data?.habits?.[0]?.days) return oldData;
        return {
          ...oldData,
          data: {
            ...oldData.data,
            habits: oldData.data.habits.map(habit => ({
              ...habit,
              days: habit.days.map(day =>
                day.date === todayDate ? { ...day, completed: newCompleted } : day
              ),
            })),
          },
        };
      });

      try {
        await habitsApi.toggleCompletion({
          habit_id: habitId,
          completion_date: todayDate,
          completed: newCompleted,
        });
        // Refetch to ensure server state is in sync
        refetch();
      } catch (err) {
        // Revert optimistic update on error
        queryClient.setQueryData(['widget', widgetId], oldData => {
          if (!oldData?.data?.habits?.[0]?.days) return oldData;
          return {
            ...oldData,
            data: {
              ...oldData.data,
              habits: oldData.data.habits.map(habit => ({
                ...habit,
                days: habit.days.map(day =>
                  day.date === todayDate ? { ...day, completed: currentlyCompleted } : day
                ),
              })),
            },
          };
        });
        console.error('Error toggling habit completion:', err);
      } finally {
        setIsSubmitting(false);
      }
    },
    [widgetId, queryClient, refetch]
  );

  if (isLoading) {
    return (
      <div className="widget-card flex items-center justify-center">
        <Loader className="animate-spin" size={32} />
      </div>
    );
  }

  if (error || data?.error) {
    return (
      <div className="widget-card">
        <div className="flex items-center gap-2 text-red-500">
          <AlertCircle size={20} />
          <span className="text-sm">
            {error?.message || data?.error || 'Failed to load habit data'}
          </span>
        </div>
      </div>
    );
  }

  const habitData = data?.data;
  const habits = habitData?.habits || [];
  const habit = habits[0]; // Only one habit per widget

  if (!habit) {
    return (
      <div className="widget-card">
        <div className="flex flex-col h-full">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Habit Tracker</h3>
          <div className="text-center py-4 text-[var(--text-secondary)]">
            <p>No habit configured for this widget.</p>
          </div>
        </div>
      </div>
    );
  }

  // Find today's data
  const days = habit.days || [];
  const todayData = days.find(d => d.is_today);
  const isTodayCompleted = todayData?.completed || false;
  const todayDate = todayData?.date;

  return (
    <div className="widget-card">
      <div className="flex flex-col h-full">
        {/* Header with habit name */}
        <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">{habit.name}</h3>
        {habit.description && (
          <p className="text-xs text-[var(--text-secondary)] mb-4">{habit.description}</p>
        )}

        {/* Main action button */}
        <div className="mb-4">
          <button
            onClick={() => handleToggleToday(habit.id, todayDate, isTodayCompleted)}
            disabled={isSubmitting || !todayDate}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-all ${
              isTodayCompleted
                ? 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border-color)] hover:bg-[var(--bg-primary)]'
                : 'bg-[var(--accent-color)] text-white hover:opacity-90'
            } disabled:opacity-50`}
          >
            {isSubmitting ? 'Updating...' : isTodayCompleted ? 'Clear' : 'Completed'}
          </button>
        </div>

        {/* 7-day history circles */}
        <div className="flex justify-center gap-2">
          {days.map(day => (
            <div
              key={day.date}
              className={`w-6 h-6 rounded-full border-2 transition-all ${
                day.completed
                  ? 'bg-[var(--accent-color)] border-[var(--accent-color)]'
                  : 'bg-transparent border-[var(--border-color)]'
              }`}
              title={`${day.date} - ${day.completed ? 'Completed' : 'Not completed'}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default HabitTrackingWidget;
