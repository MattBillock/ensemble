import React, { useState, useEffect, useRef } from 'react';
import ProblemInputForm from './components/ProblemInputForm';
import { generateSolution, connectWebSocket } from './services/api';

function App() {
  const [problemDescription, setProblemDescription] = useState(null);
  const [agentStatus, setAgentStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect WebSocket on mount
    wsRef.current = connectWebSocket(
      (data) => {
        setAgentStatus(data);
      },
      (error) => {
        setError('WebSocket connection failed');
      }
    );

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleProblemSubmit = async (description) => {
    setProblemDescription(description);
    setIsLoading(true);
    setError(null);

    try {
      const result = await generateSolution(description);
      console.log('Solution generation started:', result);

      // Request status for this agent
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ agent_id: result.agent_id }));
      }
    } catch (err) {
      setError('Failed to start solution generation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-8">Ensemble Agent System</h1>

        <ProblemInputForm onProblemSubmit={handleProblemSubmit} />

        {error && (
          <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {isLoading && (
          <div className="mt-8 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded-lg">
            <div className="flex items-center">
              <div className="animate-spin h-5 w-5 mr-3 border-2 border-blue-700 border-t-transparent rounded-full"></div>
              <span>Connecting to backend...</span>
            </div>
          </div>
        )}

        {problemDescription && (
          <div className="mt-8 p-4 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-4">Problem Description</h2>
            <p className="text-gray-700">{problemDescription}</p>
          </div>
        )}

        {agentStatus && (
          <div className="mt-8 p-4 bg-green-100 border border-green-400 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Agent Status</h2>
            <pre className="text-sm text-gray-800 whitespace-pre-wrap">
              {JSON.stringify(agentStatus, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;