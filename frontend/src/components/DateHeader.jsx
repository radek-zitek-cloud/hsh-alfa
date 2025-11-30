import { useState, useEffect } from 'react'

// Collection of "on this day in history" facts organized by month and day
// Format: { "MM-DD": ["fact1", "fact2", ...] }
const HISTORY_FACTS = {
  "01-01": [
    "1863 - The Emancipation Proclamation takes effect in the United States",
    "1959 - Fidel Castro leads Cuban revolutionaries to victory",
    "1999 - The Euro is introduced in 11 European countries"
  ],
  "01-15": [
    "1929 - Martin Luther King Jr. is born in Atlanta, Georgia",
    "2001 - Wikipedia is launched",
    "1559 - Elizabeth I is crowned Queen of England"
  ],
  "02-14": [
    "1876 - Alexander Graham Bell patents the telephone",
    "1989 - The first GPS satellite is placed into orbit",
    "270 - Saint Valentine is executed in Rome"
  ],
  "03-14": [
    "1879 - Albert Einstein is born in Ulm, Germany",
    "2018 - Stephen Hawking passes away",
    "1794 - Eli Whitney patents the cotton gin"
  ],
  "04-15": [
    "1912 - The Titanic sinks after hitting an iceberg",
    "1452 - Leonardo da Vinci is born in Florence, Italy",
    "1865 - Abraham Lincoln dies from assassination wounds"
  ],
  "05-05": [
    "1821 - Napoleon Bonaparte dies in exile on Saint Helena",
    "1862 - Mexican forces defeat the French at the Battle of Puebla",
    "1961 - Alan Shepard becomes the first American in space"
  ],
  "06-06": [
    "1944 - D-Day: Allied forces land on Normandy beaches",
    "1984 - Tetris is first released in the Soviet Union",
    "1933 - The first drive-in movie theater opens in New Jersey"
  ],
  "07-04": [
    "1776 - The United States Declaration of Independence is adopted",
    "1826 - Thomas Jefferson and John Adams both die on the 50th anniversary of the Declaration",
    "2012 - The Higgs boson particle is discovered at CERN"
  ],
  "07-20": [
    "1969 - Apollo 11 lands on the Moon; Neil Armstrong and Buzz Aldrin walk on the lunar surface",
    "1976 - Viking 1 lands on Mars",
    "1944 - Adolf Hitler survives an assassination attempt"
  ],
  "08-06": [
    "1945 - The atomic bomb is dropped on Hiroshima, Japan",
    "1991 - The World Wide Web is publicly announced",
    "1926 - Gertrude Ederle becomes the first woman to swim the English Channel"
  ],
  "09-11": [
    "2001 - Terrorist attacks destroy the World Trade Center in New York City",
    "1789 - Alexander Hamilton is appointed the first U.S. Secretary of the Treasury",
    "1973 - A coup in Chile overthrows Salvador Allende"
  ],
  "10-31": [
    "1517 - Martin Luther posts his 95 Theses on the church door in Wittenberg",
    "1926 - Harry Houdini dies from peritonitis",
    "1941 - Mount Rushmore is completed after 14 years"
  ],
  "11-09": [
    "1989 - The Berlin Wall falls",
    "1938 - Kristallnacht, the Night of Broken Glass, begins in Nazi Germany",
    "1967 - The first issue of Rolling Stone magazine is published"
  ],
  "12-25": [
    "1991 - Mikhail Gorbachev resigns as President of the Soviet Union",
    "800 - Charlemagne is crowned Emperor of the Holy Roman Empire",
    "1914 - The Christmas Truce: British and German soldiers cease fire during WWI"
  ]
}

// Generic facts for days not in the specific list
const GENERIC_FACTS = [
  "Every day, history is being made by people around the world",
  "The calendar we use today (Gregorian) was introduced in 1582",
  "The concept of a seven-day week originated in ancient Babylon",
  "The first recorded New Year's celebration dates back 4,000 years to Babylon",
  "Ancient Egyptians invented the 365-day calendar",
  "The first mechanical clock was invented in 1656",
  "Time zones were established in 1884 at the International Meridian Conference",
  "The longest year in history was 46 BC, which had 445 days",
  "The Mayan calendar predicted the start of a new era in 2012",
  "Sundials were used as early as 1500 BC to tell time",
  "The first wristwatch was made for the Queen of Naples in 1810",
  "February was once the last month of the Roman calendar",
  "Julius Caesar added two extra months to the calendar in 46 BC",
  "The term 'fortnight' comes from 'fourteen nights'",
  "Ancient Romans counted years from the founding of Rome in 753 BC"
]

const DateHeader = () => {
  const [historyFact, setHistoryFact] = useState('')
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    // Update the date every minute to keep it current
    const interval = setInterval(() => {
      setCurrentDate(new Date())
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    // Get the current month and day in MM-DD format
    const month = String(currentDate.getMonth() + 1).padStart(2, '0')
    const day = String(currentDate.getDate()).padStart(2, '0')
    const dateKey = `${month}-${day}`

    // Try to get facts for this specific date, otherwise use generic facts
    const factsForDate = HISTORY_FACTS[dateKey] || GENERIC_FACTS
    
    // Select a random fact
    const randomIndex = Math.floor(Math.random() * factsForDate.length)
    setHistoryFact(factsForDate[randomIndex])
  }, [currentDate])

  // Format the date in a nice readable format
  const formatDate = (date) => {
    const options = { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    }
    return date.toLocaleDateString('en-US', options)
  }

  return (
    <div className="flex flex-col">
      <h1 className="text-3xl font-bold text-[var(--text-primary)]">
        {formatDate(currentDate)}
      </h1>
      <p className="text-sm text-[var(--text-secondary)] mt-1">
        On this day: {historyFact}
      </p>
    </div>
  )
}

export default DateHeader
