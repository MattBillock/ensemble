import React, { useState } from 'react';

function ProblemInputForm({ onProblemSubmit }) {
  const [problemDescription, setProblemDescription] = useState('');
  const [budgetTier, setBudgetTier] = useState('balanced');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (problemDescription.trim()) {
      onProblemSubmit(problemDescription, budgetTier);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded-lg shadow-lg border border-gray-200">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Submit Task</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Task Description
          </label>
          <textarea
            value={problemDescription}
            onChange={(e) => setProblemDescription(e.target.value)}
            placeholder="Describe your problem or task here..."
            className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Budget Tier
          </label>
          <select
            value={budgetTier}
            onChange={(e) => setBudgetTier(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="economical">💰 Economical (0.7x cost) - Haiku for most tasks</option>
            <option value="balanced">⚖️ Balanced (1.0x cost) - Smart mix of models</option>
            <option value="full_firepower">🚀 Full Firepower (2.5x cost) - Best models</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            {budgetTier === 'economical' && 'Cost-effective: Uses Haiku everywhere possible'}
            {budgetTier === 'balanced' && 'Recommended: Sonnet for complex tasks, Haiku for simple ones'}
            {budgetTier === 'full_firepower' && 'Maximum quality: Opus for strategic decisions'}
          </p>
        </div>

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 transition-colors font-medium shadow-sm"
        >
          Generate Solution
        </button>
      </form>
    </div>
  );
}

export default ProblemInputForm;