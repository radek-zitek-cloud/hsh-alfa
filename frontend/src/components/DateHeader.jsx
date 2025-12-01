import { useState, useEffect, useCallback } from 'react';
import { getRandomOnThisDayEvent, getRandomFallbackFact } from '../services/wikipediaService';

// Helper function to get date key in MM-DD format
const getDateKey = date => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${month}-${day}`;
};

const DateHeader = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [currentDateKey, setCurrentDateKey] = useState(() => getDateKey(new Date()));
  const [historyFact, setHistoryFact] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  // Fetch a historical event from Wikipedia
  const fetchHistoricalEvent = useCallback(async date => {
    setIsLoading(true);
    try {
      const event = await getRandomOnThisDayEvent(date);
      setHistoryFact(event);
    } catch (error) {
      // Log the error for debugging and use a fallback fact
      console.warn('Failed to fetch historical event:', error.message);
      setHistoryFact(getRandomFallbackFact());
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch historical event on initial mount
  useEffect(() => {
    fetchHistoricalEvent(new Date());
  }, [fetchHistoricalEvent]);

  useEffect(() => {
    // Update the date every minute to keep it current
    const interval = setInterval(() => {
      const newDate = new Date();
      const newDateKey = getDateKey(newDate);

      setCurrentDate(newDate);

      // Only update the fact if the day has changed
      if (newDateKey !== currentDateKey) {
        setCurrentDateKey(newDateKey);
        fetchHistoricalEvent(newDate);
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [currentDateKey, fetchHistoricalEvent]);

  // Format the date in a nice readable format
  const formatDate = date => {
    const options = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    return date.toLocaleDateString('en-US', options);
  };

  return (
    <div className="flex flex-col">
      <h1 className="text-3xl font-bold text-[var(--text-primary)]">{formatDate(currentDate)}</h1>
      <p className="text-sm text-[var(--text-secondary)] mt-1">
        {isLoading ? 'Loading historical event...' : `On this day: ${historyFact}`}
      </p>
    </div>
  );
};

export default DateHeader;
