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
    <div className="max-w-3xl mx-auto p-6 bg-white/10 backdrop-blur-md rounded-xl shadow-2xl border border-white/20">
      <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-2">
        <span>💬</span> New Task
      </h2>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-blue-200 mb-2">
            Task Description
          </label>
          <textarea
            value={problemDescription}
            onChange={(e) => setProblemDescription(e.target.value)}
            placeholder="Describe your problem or task here..."
            className="w-full p-4 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-white placeholder-gray-400"
            rows="4"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-blue-200 mb-2">
            Budget Tier
          </label>
          <select
            value={budgetTier}
            onChange={(e) => setBudgetTier(e.target.value)}
            className="w-full p-4 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-white"
          >
            <option value="economical" className="bg-slate-800">💰 Economical (0.7x cost) - Haiku for most tasks</option>
            <option value="balanced" className="bg-slate-800">⚖️ Balanced (1.0x cost) - Smart mix of models</option>
            <option value="full_firepower" className="bg-slate-800">🚀 Full Firepower (2.5x cost) - Best models</option>
          </select>
          <p className="mt-2 text-xs text-blue-300">
            {budgetTier === 'economical' && 'Cost-effective: Uses Haiku everywhere possible'}
            {budgetTier === 'balanced' && 'Recommended: Sonnet for complex tasks, Haiku for simple ones'}
            {budgetTier === 'full_firepower' && 'Maximum quality: Opus for strategic decisions'}
          </p>
        </div>

        <button
          type="submit"
          className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 text-white py-4 rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
        >
          🚀 Launch Agent
        </button>
      </form>
    </div>
  );
}

export default ProblemInputForm;