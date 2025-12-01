import axios from 'axios';

// Wikimedia "On This Day" API endpoint
const WIKIMEDIA_API_BASE = 'https://api.wikimedia.org/feed/v1/wikipedia';

// Fallback facts for when the API is unavailable
const FALLBACK_FACTS = [
  'Every day, history is being made by people around the world',
  'The calendar we use today (Gregorian) was introduced in 1582',
  'The concept of a seven-day week originated in ancient Babylon',
  'The first recorded New Year celebration dates back 4,000 years to Babylon',
  'Ancient Egyptians invented the 365-day calendar',
  'The first mechanical clock was invented in 1656',
  'Time zones were established in 1884 at the International Meridian Conference',
  'The longest year in history was 46 BC, which had 445 days',
  'The Mayan calendar predicted the start of a new era in 2012',
  'Sundials were used as early as 1500 BC to tell time',
  'The first wristwatch was made for the Queen of Naples in 1810',
  'February was once the last month of the Roman calendar',
  'Julius Caesar added two extra months to the calendar in 46 BC',
  'The term fortnight comes from fourteen nights',
  'Ancient Romans counted years from the founding of Rome in 753 BC',
];

/**
 * Fetch "On This Day" historical events from the Wikimedia API
 * @param {Date} date - The date to fetch events for
 * @returns {Promise<string[]>} - Array of historical events
 */
export const fetchOnThisDayEvents = async (date = new Date()) => {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  try {
    const response = await axios.get(`${WIKIMEDIA_API_BASE}/en/onthisday/events/${month}/${day}`, {
      timeout: 10000,
      headers: {
        Accept: 'application/json',
      },
    });

    if (response.data && response.data.events && response.data.events.length > 0) {
      // Extract and format events
      return response.data.events.map(event => {
        return `${event.year} - ${event.text}`;
      });
    }

    return FALLBACK_FACTS;
  } catch (error) {
    console.error('Failed to fetch "On This Day" events from Wikipedia:', error.message);
    return FALLBACK_FACTS;
  }
};

/**
 * Get a random historical event for the given date
 * @param {Date} date - The date to get an event for
 * @returns {Promise<string>} - A random historical event
 */
export const getRandomOnThisDayEvent = async (date = new Date()) => {
  const events = await fetchOnThisDayEvents(date);
  const randomIndex = Math.floor(Math.random() * events.length);
  return events[randomIndex];
};

/**
 * Get a random fallback fact (for when API fails)
 * @returns {string} - A random fallback fact
 */
export const getRandomFallbackFact = () => {
  const randomIndex = Math.floor(Math.random() * FALLBACK_FACTS.length);
  return FALLBACK_FACTS[randomIndex];
};

export default {
  fetchOnThisDayEvents,
  getRandomOnThisDayEvent,
  getRandomFallbackFact,
  FALLBACK_FACTS,
};
