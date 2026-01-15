/**
 * Unit tests for whimsicalNames.js
 * Tests for adjective/noun arrays, hash function, name generation, and emoji mapping
 */

import {
  ADJECTIVES,
  NOUNS,
  hashString,
  generateWhimsicalName,
  getAgentEmoji
} from '../whimsicalNames';

describe('whimsicalNames', () => {
  describe('ADJECTIVES array', () => {
    test('should exist and be an array', () => {
      expect(ADJECTIVES).toBeDefined();
      expect(Array.isArray(ADJECTIVES)).toBe(true);
    });

    test('should have exactly 40 elements', () => {
      expect(ADJECTIVES).toHaveLength(40);
    });

    test('should contain all required adjectives in order', () => {
      const expectedAdjectives = [
        'Cosmic', 'Groovy', 'Jazzy', 'Mighty', 'Stellar',
        'Radical', 'Tubular', 'Gnarly', 'Bodacious', 'Wicked',
        'Fantastic', 'Amazing', 'Super', 'Ultra', 'Mega',
        'Epic', 'Legendary', 'Awesome', 'Marvelous', 'Incredible',
        'Sparkly', 'Nifty', 'Snazzy', 'Zippy', 'Zesty',
        'Funky', 'Peppy', 'Perky', 'Chipper', 'Spunky',
        'Rockin', 'Jammin', 'Kickin', 'Swingin', 'Cruisin',
        'Chillin', 'Vibin', 'Rollin', 'Bouncin', 'Groovin'
      ];
      
      expect(ADJECTIVES).toEqual(expectedAdjectives);
    });

    test('should contain each specific adjective', () => {
      const requiredWords = [
        'Cosmic', 'Groovy', 'Jazzy', 'Mighty', 'Stellar',
        'Radical', 'Tubular', 'Gnarly', 'Bodacious', 'Wicked',
        'Fantastic', 'Amazing', 'Super', 'Ultra', 'Mega',
        'Epic', 'Legendary', 'Awesome', 'Marvelous', 'Incredible',
        'Sparkly', 'Nifty', 'Snazzy', 'Zippy', 'Zesty',
        'Funky', 'Peppy', 'Perky', 'Chipper', 'Spunky',
        'Rockin', 'Jammin', 'Kickin', 'Swingin', 'Cruisin',
        'Chillin', 'Vibin', 'Rollin', 'Bouncin', 'Groovin'
      ];

      requiredWords.forEach(word => {
        expect(ADJECTIVES).toContain(word);
      });
    });
  });

  describe('NOUNS array', () => {
    test('should exist and be an array', () => {
      expect(NOUNS).toBeDefined();
      expect(Array.isArray(NOUNS)).toBe(true);
    });

    test('should have exactly 40 elements', () => {
      expect(NOUNS).toHaveLength(40);
    });

    test('should contain all required nouns in order', () => {
      const expectedNouns = [
        'Astronaut', 'Robot', 'Unicorn', 'Wizard', 'Ninja',
        'Pirate', 'Superhero', 'Viking', 'Cowboy', 'Samurai',
        'Panda', 'Penguin', 'Phoenix', 'Dragon', 'Tiger',
        'Eagle', 'Falcon', 'Wolf', 'Bear', 'Lion',
        'Rockstar', 'DJ', 'Dancer', 'Magician', 'Acrobat',
        'Champion', 'Hero', 'Legend', 'Maverick', 'Ace',
        'Comet', 'Meteor', 'Galaxy', 'Nebula', 'Supernova',
        'Stardust', 'Moonbeam', 'Sunray', 'Rainbow', 'Thunder'
      ];
      
      expect(NOUNS).toEqual(expectedNouns);
    });

    test('should contain each specific noun', () => {
      const requiredWords = [
        'Astronaut', 'Robot', 'Unicorn', 'Wizard', 'Ninja',
        'Pirate', 'Superhero', 'Viking', 'Cowboy', 'Samurai',
        'Panda', 'Penguin', 'Phoenix', 'Dragon', 'Tiger',
        'Eagle', 'Falcon', 'Wolf', 'Bear', 'Lion',
        'Rockstar', 'DJ', 'Dancer', 'Magician', 'Acrobat',
        'Champion', 'Hero', 'Legend', 'Maverick', 'Ace',
        'Comet', 'Meteor', 'Galaxy', 'Nebula', 'Supernova',
        'Stardust', 'Moonbeam', 'Sunray', 'Rainbow', 'Thunder'
      ];

      requiredWords.forEach(word => {
        expect(NOUNS).toContain(word);
      });
    });
  });

  describe('hashString(str)', () => {
    test('should return a positive integer for valid input', () => {
      const result = hashString('test-string');
      expect(typeof result).toBe('number');
      expect(Number.isInteger(result)).toBe(true);
      expect(result).toBeGreaterThanOrEqual(0);
    });

    test('should be deterministic - same input produces same output', () => {
      const input = 'consistent-input';
      const result1 = hashString(input);
      const result2 = hashString(input);
      const result3 = hashString(input);
      
      expect(result1).toBe(result2);
      expect(result2).toBe(result3);
    });

    test('should produce different outputs for different inputs', () => {
      const result1 = hashString('input1');
      const result2 = hashString('input2');
      const result3 = hashString('input3');
      
      // While hash collisions are theoretically possible, 
      // these distinct strings should produce different hashes
      expect(result1).not.toBe(result2);
      expect(result2).not.toBe(result3);
    });

    test('should handle empty string', () => {
      const result = hashString('');
      expect(typeof result).toBe('number');
      expect(Number.isInteger(result)).toBe(true);
      expect(result).toBeGreaterThanOrEqual(0);
    });

    test('should handle special characters', () => {
      const specialStrings = [
        '!@#$%^&*()',
        'hello-world-123',
        'test_with_underscore',
        'unicode-测试-🎉',
        'spaces in string',
        'UPPERCASE',
        'MixedCase123'
      ];

      specialStrings.forEach(str => {
        const result = hashString(str);
        expect(typeof result).toBe('number');
        expect(Number.isInteger(result)).toBe(true);
        expect(result).toBeGreaterThanOrEqual(0);
      });
    });

    test('should handle very long strings', () => {
      const longString = 'a'.repeat(1000);
      const result = hashString(longString);
      expect(typeof result).toBe('number');
      expect(Number.isInteger(result)).toBe(true);
      expect(result).toBeGreaterThanOrEqual(0);
    });
  });

  describe('generateWhimsicalName(agentId)', () => {
    test('should return a string', () => {
      const result = generateWhimsicalName('test-agent-1');
      expect(typeof result).toBe('string');
    });

    test('should match pattern "[Adjective] [Noun]"', () => {
      const result = generateWhimsicalName('test-agent-2');
      const parts = result.split(' ');
      
      expect(parts).toHaveLength(2);
      expect(ADJECTIVES).toContain(parts[0]);
      expect(NOUNS).toContain(parts[1]);
    });

    test('should be deterministic - same agentId produces same name', () => {
      const agentId = 'deterministic-test';
      const name1 = generateWhimsicalName(agentId);
      const name2 = generateWhimsicalName(agentId);
      const name3 = generateWhimsicalName(agentId);
      
      expect(name1).toBe(name2);
      expect(name2).toBe(name3);
    });

    test('should produce different names for different agentIds', () => {
      const name1 = generateWhimsicalName('agent-1');
      const name2 = generateWhimsicalName('agent-2');
      const name3 = generateWhimsicalName('agent-3');
      
      // Different IDs should likely produce different names
      // (though collisions are theoretically possible)
      const uniqueNames = new Set([name1, name2, name3]);
      expect(uniqueNames.size).toBeGreaterThan(1);
    });

    test('should handle empty string agentId', () => {
      const result = generateWhimsicalName('');
      expect(typeof result).toBe('string');
      const parts = result.split(' ');
      expect(parts).toHaveLength(2);
      expect(ADJECTIVES).toContain(parts[0]);
      expect(NOUNS).toContain(parts[1]);
    });

    test('should handle special characters in agentId', () => {
      const specialIds = [
        '!@#$%',
        'agent-with-dashes',
        'agent_with_underscores',
        'UPPERCASE',
        '12345',
        'unicode-测试'
      ];

      specialIds.forEach(id => {
        const result = generateWhimsicalName(id);
        expect(typeof result).toBe('string');
        const parts = result.split(' ');
        expect(parts).toHaveLength(2);
        expect(ADJECTIVES).toContain(parts[0]);
        expect(NOUNS).toContain(parts[1]);
      });
    });

    test('should handle very long agentId', () => {
      const longId = 'a'.repeat(1000);
      const result = generateWhimsicalName(longId);
      expect(typeof result).toBe('string');
      const parts = result.split(' ');
      expect(parts).toHaveLength(2);
    });
  });

  describe('getAgentEmoji(agentType)', () => {
    test('should return correct emoji for executive agent', () => {
      expect(getAgentEmoji('executive')).toBe('👑');
    });

    test('should return correct emoji for developer agent', () => {
      expect(getAgentEmoji('developer')).toBe('🔧');
    });

    test('should return correct emoji for tester agent', () => {
      expect(getAgentEmoji('tester')).toBe('🧪');
    });

    test('should return correct emoji for support agent', () => {
      expect(getAgentEmoji('support')).toBe('🛠️');
    });

    test('should return correct emoji for orchestrator agent', () => {
      expect(getAgentEmoji('orchestrator')).toBe('🎯');
    });

    test('should return correct emoji for coordinator agent', () => {
      expect(getAgentEmoji('coordinator')).toBe('🎭');
    });

    test('should return robot emoji for unknown agent type', () => {
      expect(getAgentEmoji('unknown')).toBe('🤖');
      expect(getAgentEmoji('invalid')).toBe('🤖');
      expect(getAgentEmoji('random-type')).toBe('🤖');
    });

    test('should return robot emoji for empty string', () => {
      expect(getAgentEmoji('')).toBe('🤖');
    });

    test('should return robot emoji for null/undefined', () => {
      expect(getAgentEmoji(null)).toBe('🤖');
      expect(getAgentEmoji(undefined)).toBe('🤖');
    });

    test('should handle case sensitivity', () => {
      // Assuming the function is case-sensitive, these should return default
      expect(getAgentEmoji('EXECUTIVE')).toBe('🤖');
      expect(getAgentEmoji('Executive')).toBe('🤖');
      expect(getAgentEmoji('DEVELOPER')).toBe('🤖');
    });

    test('should return emoji for all known agent types', () => {
      const knownTypes = {
        'executive': '👑',
        'developer': '🔧',
        'tester': '🧪',
        'support': '🛠️',
        'orchestrator': '🎯',
        'coordinator': '🎭'
      };

      Object.entries(knownTypes).forEach(([type, expectedEmoji]) => {
        expect(getAgentEmoji(type)).toBe(expectedEmoji);
      });
    });
  });
});
