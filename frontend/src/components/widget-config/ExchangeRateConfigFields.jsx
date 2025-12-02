const ExchangeRateConfigFields = ({ config, onChange }) => {
  return (
    <>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">Base Currency</label>
        <input
          type="text"
          value={config.base_currency || 'USD'}
          onChange={e => onChange('base_currency', e.target.value.toUpperCase())}
          placeholder="USD"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">
          Target Currencies (comma-separated)
        </label>
        <input
          type="text"
          value={
            Array.isArray(config.target_currencies) ? config.target_currencies.join(', ') : ''
          }
          onChange={e =>
            onChange(
              'target_currencies',
              e.target.value.split(',').map(c => c.trim().toUpperCase())
            )
          }
          placeholder="EUR, GBP, JPY"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
    </>
  );
};

export default ExchangeRateConfigFields;
