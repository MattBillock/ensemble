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
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <div className="flex-1">
        <textarea
          value={problemDescription}
          onChange={(e) => setProblemDescription(e.target.value)}
          placeholder="Describe your task... (e.g., 'Add user authentication to the app')"
          className="w-full px-4 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-white placeholder-gray-400 resize-none"
          rows="2"
        />
      </div>

      <div className="w-48">
        <select
          value={budgetTier}
          onChange={(e) => setBudgetTier(e.target.value)}
          className="w-full px-3 py-2 bg-white/5 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-white text-sm"
        >
          <option value="economical" className="bg-slate-800">💰 Economical</option>
          <option value="balanced" className="bg-slate-800">⚖️ Balanced</option>
          <option value="full_firepower" className="bg-slate-800">🚀 Full Power</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={!problemDescription.trim()}
        className="px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 transition-all font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
      >
        🚀 Launch
      </button>
    </form>
  );
}

export default ProblemInputForm;