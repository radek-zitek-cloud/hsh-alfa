const NewsConfigFields = ({ config, onChange }) => {
  return (
    <>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">
          RSS Feeds (one per line)
        </label>
        <textarea
          value={Array.isArray(config.rss_feeds) ? config.rss_feeds.join('\n') : ''}
          onChange={e => onChange('rss_feeds', e.target.value.split('\n').filter(Boolean))}
          rows="4"
          placeholder="https://hnrss.org/frontpage"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
      <div>
        <label className="block text-sm text-[var(--text-secondary)] mb-1">Max Articles</label>
        <input
          type="number"
          value={config.max_articles || 10}
          onChange={e => onChange('max_articles', parseInt(e.target.value))}
          min="1"
          max="50"
          className="w-full px-3 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg"
        />
      </div>
    </>
  );
};

export default NewsConfigFields;
