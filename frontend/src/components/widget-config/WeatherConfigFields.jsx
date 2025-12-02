const WeatherConfigFields = ({ config, onChange }) => {
  return (
    <>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">
          Location (City, Country Code)
        </label>
        <input
          type="text"
          value={config.location || ''}
          onChange={e => onChange('location', e.target.value)}
          placeholder="e.g., London, UK"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">Units</label>
        <select
          value={config.units || 'metric'}
          onChange={e => onChange('units', e.target.value)}
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        >
          <option value="metric">Metric (°C)</option>
          <option value="imperial">Imperial (°F)</option>
          <option value="standard">Standard (K)</option>
        </select>
      </div>
      <div className="flex items-center">
        <input
          type="checkbox"
          id="show_forecast"
          checked={config.show_forecast !== false}
          onChange={e => onChange('show_forecast', e.target.checked)}
          className="w-4 h-4"
        />
        <label htmlFor="show_forecast" className="ml-2 text-sm text-[var(--text-secondary)]">
          Show Forecast
        </label>
      </div>
    </>
  );
};

export default WeatherConfigFields;
