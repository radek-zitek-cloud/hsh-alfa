const HabitTrackingConfigFields = ({
  config,
  onChange,
  habits,
  isEditMode,
  habitCreationMode,
  setHabitCreationMode,
  newHabitData,
  setNewHabitData,
  editHabitData,
  setEditHabitData,
}) => {
  return (
    <div className="space-y-4">
      {/* Show edit habit fields when in edit mode */}
      {isEditMode && (
        <div className="space-y-3">
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Edit the habit information tracked by this widget.
            </p>
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Habit Name *
            </label>
            <input
              type="text"
              value={editHabitData.name}
              onChange={e => setEditHabitData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Morning Exercise"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Habit Description
            </label>
            <textarea
              value={editHabitData.description}
              onChange={e =>
                setEditHabitData(prev => ({ ...prev, description: e.target.value }))
              }
              placeholder="e.g., 30 minutes of cardio or strength training"
              rows="2"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
            />
          </div>
        </div>
      )}

      {/* Only show mode selection when creating new widget */}
      {!isEditMode && (
        <div className="flex gap-4 mb-4">
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              name="habitMode"
              value="existing"
              checked={habitCreationMode === 'existing'}
              onChange={e => setHabitCreationMode(e.target.value)}
              className="w-4 h-4 text-[var(--accent-color)] border-[var(--border-color)] focus:ring-2 focus:ring-[var(--accent-color)]"
            />
            <span className="ml-2 text-sm text-[var(--text-primary)]">
              Select existing habit
            </span>
          </label>
          <label className="flex items-center cursor-pointer">
            <input
              type="radio"
              name="habitMode"
              value="new"
              checked={habitCreationMode === 'new'}
              onChange={e => setHabitCreationMode(e.target.value)}
              className="w-4 h-4 text-[var(--accent-color)] border-[var(--border-color)] focus:ring-2 focus:ring-[var(--accent-color)]"
            />
            <span className="ml-2 text-sm text-[var(--text-primary)]">Create new habit</span>
          </label>
        </div>
      )}

      {/* Existing habit selection - only when creating new widget */}
      {!isEditMode && habitCreationMode === 'existing' && (
        <div>
          <label className="block text-sm text-[var(--text-secondary)] mb-1">
            Select Habit to Track *
          </label>
          {habits.length === 0 ? (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <p className="text-sm text-blue-700 dark:text-blue-300">
                No existing habits found. Switch to &quot;Create new habit&quot; mode to create your first
                habit.
              </p>
            </div>
          ) : (
            <select
              value={config.habit_id || ''}
              onChange={e => onChange('habit_id', e.target.value)}
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
              required
            >
              <option value="">-- Select a habit --</option>
              {habits.map(habit => (
                <option key={habit.id} value={habit.id}>
                  {habit.name} {habit.description ? `- ${habit.description}` : ''}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* New habit creation */}
      {habitCreationMode === 'new' && !isEditMode && (
        <div className="space-y-3">
          <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-sm text-green-700 dark:text-green-300">
              A new habit will be created and tracked by this widget.
            </p>
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Habit Name *
            </label>
            <input
              type="text"
              value={newHabitData.name}
              onChange={e => setNewHabitData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Morning Exercise"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-[var(--text-secondary)] mb-1">
              Habit Description *
            </label>
            <textarea
              value={newHabitData.description}
              onChange={e =>
                setNewHabitData(prev => ({ ...prev, description: e.target.value }))
              }
              placeholder="e.g., 30 minutes of cardio or strength training"
              rows="2"
              className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
              required
            />
          </div>
        </div>
      )}

      <p className="text-xs text-[var(--text-secondary)] mt-2">
        Each widget tracks one habit. Create multiple widgets to track multiple habits.
      </p>
    </div>
  );
};

export default HabitTrackingConfigFields;
