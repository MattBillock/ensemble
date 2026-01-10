import React, { useState } from 'react';
import ProblemInputForm from './components/ProblemInputForm';

function App() {
  const [problemDescription, setProblemDescription] = useState(null);

  const handleProblemSubmit = (description) => {
    setProblemDescription(description);
    // TODO: Implement solution generation logic
    console.log('Problem submitted:', description);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Ensemble Agent System</h1>
        <ProblemInputForm onProblemSubmit={handleProblemSubmit} />
        {problemDescription && (
          <div className="mt-8 p-4 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Problem Description</h2>
            <p>{problemDescription}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;