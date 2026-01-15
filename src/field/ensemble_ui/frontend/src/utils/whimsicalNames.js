/**
 * Whimsical Names Utility Module
 * Provides word arrays, hashing, name generation, and emoji mapping for agent identification
 */

// Array of 40 adjectives for name generation
export const ADJECTIVES = [
  'Cosmic', 'Groovy', 'Jazzy', 'Mighty', 'Stellar',
  'Radical', 'Tubular', 'Gnarly', 'Bodacious', 'Wicked',
  'Fantastic', 'Amazing', 'Super', 'Ultra', 'Mega',
  'Epic', 'Legendary', 'Awesome', 'Marvelous', 'Incredible',
  'Sparkly', 'Nifty', 'Snazzy', 'Zippy', 'Zesty',
  'Funky', 'Peppy', 'Perky', 'Chipper', 'Spunky',
  'Rockin', 'Jammin', 'Kickin', 'Swingin', 'Cruisin',
  'Chillin', 'Vibin', 'Rollin', 'Bouncin', 'Groovin'
];

// Array of 40 nouns for name generation
export const NOUNS = [
  'Astronaut', 'Robot', 'Unicorn', 'Wizard', 'Ninja',
  'Pirate', 'Superhero', 'Viking', 'Cowboy', 'Samurai',
  'Panda', 'Penguin', 'Phoenix', 'Dragon', 'Tiger',
  'Eagle', 'Falcon', 'Wolf', 'Bear', 'Lion',
  'Rockstar', 'DJ', 'Dancer', 'Magician', 'Acrobat',
  'Champion', 'Hero', 'Legend', 'Maverick', 'Ace',
  'Comet', 'Meteor', 'Galaxy', 'Nebula', 'Supernova',
  'Stardust', 'Moonbeam', 'Sunray', 'Rainbow', 'Thunder'
];

/**
 * Hash a string using the djb2 algorithm
 * @param {string} str - String to hash
 * @returns {number} Positive integer hash value
 */
export function hashString(str) {
  let hash = 5381;
  
  for (let i = 0; i < str.length; i++) {
    const charCode = str.charCodeAt(i);
    hash = ((hash << 5) + hash) + charCode;
  }
  
  return Math.abs(hash);
}

/**
 * Generate a whimsical name from an agent ID
 * @param {string} agentId - Unique agent identifier
 * @returns {string} Whimsical name in format "[Adjective] [Noun]"
 */
export function generateWhimsicalName(agentId) {
  const hash = hashString(agentId);
  
  const adjectiveIndex = hash % ADJECTIVES.length;
  const nounIndex = Math.floor(hash / ADJECTIVES.length) % NOUNS.length;
  
  const adjective = ADJECTIVES[adjectiveIndex];
  const noun = NOUNS[nounIndex];
  
  return `${adjective} ${noun}`;
}

/**
 * Get emoji representation for an agent type
 * @param {string} agentType - Type of agent
 * @returns {string} Emoji character
 */
export function getAgentEmoji(agentType) {
  const emojiMap = {
    'executive': '👑',
    'developer': '🔧',
    'tester': '🧪',
    'support': '🛠️',
    'orchestrator': '🎯',
    'coordinator': '🎭'
  };
  
  return emojiMap[agentType] || '🤖';
}
