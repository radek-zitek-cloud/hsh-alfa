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

      {/* New habit creation - always shown when creating new widget */}
      {!isEditMode && (
        <div className="space-y-3">
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
