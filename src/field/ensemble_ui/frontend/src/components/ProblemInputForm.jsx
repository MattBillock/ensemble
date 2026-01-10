import React, { useState } from 'react';

function ProblemInputForm({ onProblemSubmit }) {
  const [problemDescription, setProblemDescription] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();
    if (problemDescription.trim()) {
      onProblemSubmit(problemDescription);
    }
  };

  return (
    <div className="max-w-md mx-auto p-4 bg-gray-100 rounded-lg shadow-md">
      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea 
          value={problemDescription}
          onChange={(e) => setProblemDescription(e.target.value)}
          placeholder="Describe your problem or task here..."
          className="w-full p-2 border rounded-md focus:outline-none focus:ring focus:border-blue-300"
          rows="4"
        />
        <button 
          type="submit" 
          className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 transition-colors"
        >
          Generate Solution
        </button>
      </form>
    </div>
  );
}

export default ProblemInputForm;