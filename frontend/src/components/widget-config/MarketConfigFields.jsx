const MarketConfigFields = ({ config, onChange }) => {
  return (
    <>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">
          Stock Symbols (comma-separated)
        </label>
        <input
          type="text"
          value={Array.isArray(config.stocks) ? config.stocks.join(', ') : ''}
          onChange={e =>
            onChange(
              'stocks',
              e.target.value
                .split(',')
                .map(s => s.trim().toUpperCase())
                .filter(s => s)
            )
          }
          placeholder="AAPL, GOOGL, MSFT"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">
          Crypto Symbols (comma-separated)
        </label>
        <input
          type="text"
          value={Array.isArray(config.crypto) ? config.crypto.join(', ') : ''}
          onChange={e =>
            onChange(
              'crypto',
              e.target.value
                .split(',')
                .map(c => c.trim().toUpperCase())
                .filter(c => c)
            )
          }
          placeholder="BTC, ETH, SOL"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
    </>
  );
};

export default MarketConfigFields;
