import React, { useState, useEffect } from 'react';
import { Card } from 'react-bootstrap';
import { ALL_FACTS, FACTS_BY_CATEGORY, getRandomFact } from '../data/funFacts';

/**
 * FactsPane - A reusable rotating facts component that displays fun facts
 * about ska, AI, TDD, engineering, and more.
 *
 * @param {string} category - Optional: filter facts by category (ska, ai, tdd, engineering, performance, reliability, numbers, career)
 * @param {number} interval - Rotation interval in milliseconds (default: 15000 = 15 seconds)
 * @param {string} variant - Card background variant (default: 'light')
 * @param {boolean} showDots - Whether to show navigation dots (default: true)
 * @param {string} className - Additional CSS classes
 */
function FactsPane({
  category = null,
  interval = 15000,
  variant = 'light',
  showDots = true,
  className = ''
}) {
  const facts = category && FACTS_BY_CATEGORY[category]
    ? FACTS_BY_CATEGORY[category]
    : ALL_FACTS;

  const [currentIndex, setCurrentIndex] = useState(() => Math.floor(Math.random() * facts.length));

  // Rotate facts at the specified interval
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex(prev => (prev + 1) % facts.length);
    }, interval);
    return () => clearInterval(timer);
  }, [interval, facts.length]);

  // Get emoji based on category
  const getCategoryEmoji = () => {
    const currentFact = facts[currentIndex];
    // Try to determine category from the fact content
    if (ALL_FACTS.indexOf(currentFact) < 40) return '🎺'; // Ska
    if (ALL_FACTS.indexOf(currentFact) < 80) return '🤖'; // AI
    if (ALL_FACTS.indexOf(currentFact) < 120) return '🧪'; // TDD
    if (ALL_FACTS.indexOf(currentFact) < 160) return '⚙️'; // Engineering
    if (ALL_FACTS.indexOf(currentFact) < 200) return '⚡'; // Performance
    if (ALL_FACTS.indexOf(currentFact) < 240) return '🛡️'; // Reliability
    if (ALL_FACTS.indexOf(currentFact) < 270) return '📊'; // Numbers
    return '💼'; // Career
  };

  const currentFact = facts[currentIndex];

  return (
    <Card
      bg={variant}
      className={className}
      style={{ transition: 'all 0.3s ease' }}
    >
      <Card.Body>
        <h6 className="d-flex align-items-center gap-2 mb-2">
          <span>{getCategoryEmoji()}</span>
          <span>Fun Facts</span>
          <small className="text-muted" style={{ fontSize: '0.7rem', marginLeft: 'auto' }}>
            {currentIndex + 1} / {facts.length}
          </small>
        </h6>
        <p className="mb-0" style={{ fontSize: '0.875rem' }}>
          <strong>{currentFact.title}:</strong>{' '}
          {currentFact.fact}
        </p>
        {showDots && facts.length <= 20 && (
          <div className="mt-2 d-flex justify-content-center gap-1">
            {facts.slice(0, 12).map((_, idx) => (
              <span
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: idx === currentIndex % 12 ? '#333' : '#ccc',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s'
                }}
              />
            ))}
          </div>
        )}
      </Card.Body>
    </Card>
  );
}

export default FactsPane;
