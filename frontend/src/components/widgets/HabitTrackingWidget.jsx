import React, { useState } from 'react';
import { useWidget } from '../../hooks/useWidget';
import { Plus, Loader, AlertCircle, Pencil, Trash2, Check } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const HabitTrackingWidget = ({ widgetId, config }) => {
  const [showAddHabit, setShowAddHabit] = useState(false);
  const [newHabitName, setNewHabitName] = useState('');
  const [newHabitDescription, setNewHabitDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isLoading, error, refetch } = useWidget(widgetId, {
    refetchInterval: (config?.refresh_interval || 300) * 1000,
  });

  const getAuthToken = () => {
    return localStorage.getItem('auth_token');
  };

  const handleCreateHabit = async e => {
    e.preventDefault();
    if (!newHabitName.trim()) return;

    setIsSubmitting(true);
    try {
      await axios.post(
        `${API_BASE_URL}/api/habits/`,
        {
          name: newHabitName.trim(),
          description: newHabitDescription.trim() || null,
          active: true,
        },
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );

      setNewHabitName('');
      setNewHabitDescription('');
      setShowAddHabit(false);
      refetch();
    } catch (error) {
      console.error('Error creating habit:', error);
      alert('Failed to create habit. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteHabit = async habitId => {
    if (!confirm('Are you sure you want to delete this habit? All history will be lost.')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/habits/${habitId}`, {
        headers: {
          Authorization: `Bearer ${getAuthToken()}`,
        },
      });
      refetch();
    } catch (error) {
      console.error('Error deleting habit:', error);
      alert('Failed to delete habit. Please try again.');
    }
  };

  const handleToggleCompletion = async (habitId, date, currentlyCompleted) => {
    try {
      await axios.post(
        `${API_BASE_URL}/api/habits/completions`,
        {
          habit_id: habitId,
          completion_date: date,
          completed: !currentlyCompleted,
        },
        {
          headers: {
            Authorization: `Bearer ${getAuthToken()}`,
          },
        }
      );
      refetch();
    } catch (error) {
      console.error('Error toggling habit completion:', error);
      alert('Failed to update habit. Please try again.');
    }
  };

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

  const getDayLabel = dayOfWeek => {
    const labels = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    return labels[dayOfWeek];
  };

  return (
    <div className="widget-card">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">Habit Tracker</h3>
          <button
            onClick={() => setShowAddHabit(!showAddHabit)}
            className="p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors"
            title="Add new habit"
          >
            <Plus size={20} className="text-[var(--text-secondary)]" />
          </button>
        </div>

        {/* Add Habit Form */}
        {showAddHabit && (
          <form onSubmit={handleCreateHabit} className="mb-4 p-3 bg-[var(--bg-secondary)] rounded">
            <input
              type="text"
              value={newHabitName}
              onChange={e => setNewHabitName(e.target.value)}
              placeholder="Habit name (e.g., Exercise, Read, Meditate)"
              className="w-full px-3 py-2 mb-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded text-[var(--text-primary)] text-sm"
              autoFocus
            />
            <input
              type="text"
              value={newHabitDescription}
              onChange={e => setNewHabitDescription(e.target.value)}
              placeholder="Description (optional)"
              className="w-full px-3 py-2 mb-2 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded text-[var(--text-primary)] text-sm"
            />
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={isSubmitting || !newHabitName.trim()}
                className="px-3 py-1 bg-[var(--accent-color)] text-white rounded text-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Adding...' : 'Add Habit'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAddHabit(false);
                  setNewHabitName('');
                  setNewHabitDescription('');
                }}
                className="px-3 py-1 bg-[var(--bg-primary)] border border-[var(--border-color)] rounded text-sm text-[var(--text-secondary)]"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Habits List */}
        {habits.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-secondary)]">
            <p>No habits yet. Click + to add your first habit!</p>
          </div>
        ) : (
          <div className="space-y-4 overflow-y-auto">
            {habits.map(habit => (
              <div key={habit.id} className="pb-4 border-b border-[var(--border-color)] last:border-b-0">
                {/* Habit Header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h4 className="font-medium text-[var(--text-primary)] text-sm">{habit.name}</h4>
                    {habit.description && (
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                        {habit.description}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteHabit(habit.id)}
                    className="p-1 hover:bg-[var(--bg-secondary)] rounded transition-colors ml-2"
                    title="Delete habit"
                  >
                    <Trash2 size={14} className="text-[var(--text-secondary)]" />
                  </button>
                </div>

                {/* Week Grid */}
                <div className="space-y-2">
                  {habit.weeks.map((week, weekIndex) => (
                    <div key={weekIndex} className="flex gap-1">
                      {week.map(day => (
                        <button
                          key={day.date}
                          onClick={() => handleToggleCompletion(habit.id, day.date, day.completed)}
                          className="relative w-8 h-8 rounded-full border-2 transition-all hover:scale-110"
                          style={{
                            backgroundColor: day.completed
                              ? 'var(--accent-color)'
                              : 'var(--bg-secondary)',
                            borderColor: day.completed
                              ? 'var(--accent-color)'
                              : 'var(--border-color)',
                          }}
                          title={`${day.date} - ${day.completed ? 'Completed' : 'Not completed'}`}
                        >
                          <span
                            className="absolute inset-0 flex items-center justify-center text-[9px] font-medium"
                            style={{
                              color: day.completed ? 'white' : 'var(--text-secondary)',
                            }}
                          >
                            {getDayLabel(day.day_of_week)}
                          </span>
                          {day.completed && (
                            <Check
                              size={12}
                              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-white"
                              strokeWidth={3}
                            />
                          )}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default HabitTrackingWidget;
