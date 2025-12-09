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

  const handleToggleCompletion = useCallback(
    async (habitId, date, currentlyCompleted) => {
      setIsSubmitting(true);

      // Optimistic update: immediately update the UI
      const newCompleted = !currentlyCompleted;
      queryClient.setQueryData(['widget', widgetId], oldData => {
        if (!oldData?.data?.habits?.length) return oldData;
        return {
          ...oldData,
          data: {
            ...oldData.data,
            habits: oldData.data.habits.map(habit =>
              habit.id === habitId
                ? {
                    ...habit,
                    days: habit.days.map(day =>
                      day.date === date ? { ...day, completed: newCompleted } : day
                    ),
                  }
                : habit
            ),
          },
        };
      });

      try {
        await habitsApi.toggleCompletion({
          habit_id: habitId,
          completion_date: date,
          completed: newCompleted,
        });
        // Refetch to ensure server state is in sync (including recalculated streak)
        await refetch();
      } catch (err) {
        // Revert optimistic update on error
        queryClient.setQueryData(['widget', widgetId], oldData => {
          if (!oldData?.data?.habits?.length) return oldData;
          return {
            ...oldData,
            data: {
              ...oldData.data,
              habits: oldData.data.habits.map(habit =>
                habit.id === habitId
                  ? {
                      ...habit,
                      days: habit.days.map(day =>
                        day.date === date ? { ...day, completed: currentlyCompleted } : day
                      ),
                    }
                  : habit
              ),
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

  // Use current streak from backend (which calculates based on all historical data)
  const currentStreak = habit.current_streak || 0;

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
            onClick={() => handleToggleCompletion(habit.id, todayDate, isTodayCompleted)}
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
        <div className="flex justify-center gap-2 mb-3">
          {days.map(day => (
            <button
              key={day.date}
              onClick={() => handleToggleCompletion(habit.id, day.date, day.completed)}
              disabled={isSubmitting}
              className={`w-6 h-6 rounded-full border-2 transition-all cursor-pointer ${
                day.completed
                  ? 'bg-[var(--accent-color)] border-[var(--accent-color)] hover:opacity-80'
                  : 'bg-transparent border-[var(--border-color)] hover:border-[var(--accent-color)]'
              } disabled:cursor-not-allowed disabled:opacity-50`}
              title={`${day.date} - ${day.completed ? 'Completed' : 'Not completed'} - Click to toggle`}
            />
          ))}
        </div>

        {/* Current streak display */}
        <div className="text-center">
          <p className="text-xs text-[var(--text-secondary)]">
            Current streak: <span className="font-semibold text-[var(--text-primary)]">{currentStreak} {currentStreak === 1 ? 'day' : 'days'}</span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default HabitTrackingWidget;
