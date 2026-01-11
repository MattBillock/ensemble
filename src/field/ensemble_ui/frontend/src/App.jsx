import React, { useState, useEffect, useRef } from 'react';
import ProblemInputForm from './components/ProblemInputForm';
import { generateSolution, connectWebSocket, getApplicationStatus } from './services/api';

function App() {
  const [problemDescription, setProblemDescription] = useState(null);
  const [budgetTier, setBudgetTier] = useState(null);
  const [agentStatus, setAgentStatus] = useState(null);
  const [appStatus, setAppStatus] = useState({ status: 'connecting', active_agents: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect WebSocket with auto-reconnect
    const connectWS = () => {
      wsRef.current = connectWebSocket(
        (data) => {
          setAgentStatus(data);
          setError(null); // Clear error on successful message
        },
        (error) => {
          console.log('WebSocket disconnected, will retry on next status poll');
          // Don't show error immediately - status polling will reconnect
          if (wsRef.current) {
            wsRef.current = null;
          }
        }
      );
    };

    connectWS();

    // Poll application status and reconnect WebSocket if needed
    const statusInterval = setInterval(async () => {
      try {
        const status = await getApplicationStatus();
        setAppStatus(status);

        // Reconnect WebSocket if it's disconnected
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          console.log('🔄 Reconnecting WebSocket...');
          connectWS();
        }
      } catch (err) {
        console.error('Failed to fetch app status:', err);
        setAppStatus({ status: 'error', active_agents: 0 });
      }
    }, 2000);

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearInterval(statusInterval);
    };
  }, []);

  const handleProblemSubmit = async (description, tier) => {
    setProblemDescription(description);
    setBudgetTier(tier);
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await generateSolution(description, tier);
      console.log('Solution generation started:', response);
      setResult(response);

      // Request status for this agent
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ agent_id: response.agent_id }));
      }
    } catch (err) {
      setError('Failed to start solution generation');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header with Status */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-center mb-4 text-gray-900">Ensemble Agent System</h1>
          <div className="flex justify-center items-center gap-4 text-sm">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-sm">
              <div className={`w-3 h-3 rounded-full ${appStatus.status === 'running' ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="font-medium">{appStatus.status === 'running' ? 'System Online' : 'Connecting...'}</span>
            </div>
            <div className="px-4 py-2 bg-white rounded-full shadow-sm">
              <span className="font-medium">{appStatus.active_agents} Active Agent{appStatus.active_agents !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>

        <ProblemInputForm onProblemSubmit={handleProblemSubmit} />

        {error && (
          <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-800 rounded-lg shadow-sm">
            <div className="flex items-start">
              <span className="text-2xl mr-3">⚠️</span>
              <div>
                <p className="font-semibold">Error</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </div>
        )}

        {isLoading && (
          <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-500 text-blue-800 rounded-lg shadow-sm">
            <div className="flex items-center">
              <div className="animate-spin h-6 w-6 mr-3 border-3 border-blue-600 border-t-transparent rounded-full"></div>
              <span className="font-medium">Starting agent execution...</span>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-6 p-6 bg-white rounded-lg shadow-lg border border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Execution Started</h2>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                budgetTier === 'full_firepower' ? 'bg-purple-100 text-purple-800' :
                budgetTier === 'economical' ? 'bg-green-100 text-green-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {budgetTier === 'full_firepower' ? '🚀 Full Firepower' :
                 budgetTier === 'economical' ? '💰 Economical' :
                 '⚖️ Balanced'}
              </span>
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-sm font-semibold text-gray-600">Task</p>
                <p className="text-gray-900">{problemDescription}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600">Agent ID</p>
                <p className="text-sm font-mono text-gray-700">{result.agent_id}</p>
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600">Status</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                  <span className="text-sm capitalize">{result.status || 'running'}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {agentStatus && agentStatus.agents && Object.keys(agentStatus.agents).length > 0 && (
          <div className="mt-6 p-6 bg-white rounded-lg shadow-lg border border-gray-200">
            <h2 className="text-xl font-bold mb-4 text-gray-900">Agent Details</h2>
            {Object.entries(agentStatus.agents).map(([agentId, agentInfo]) => (
              <div key={agentId} className="mb-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{agentId}</h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    agentInfo.status === 'completed' ? 'bg-green-100 text-green-800' :
                    agentInfo.status === 'error' ? 'bg-red-100 text-red-800' :
                    agentInfo.status === 'running' ? 'bg-blue-100 text-blue-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {agentInfo.status}
                  </span>
                </div>
                <div className="space-y-2 text-sm">
                  <div><span className="font-semibold">Type:</span> {agentInfo.type}</div>
                  <div><span className="font-semibold">Budget:</span> {agentInfo.budget_tier}</div>
                  {agentInfo.problem && <div><span className="font-semibold">Task:</span> {agentInfo.problem}</div>}
                  {agentInfo.error && (
                    <div className="mt-3 p-3 bg-red-50 border-l-4 border-red-500 rounded">
                      <p className="font-semibold text-red-800">Error:</p>
                      <p className="text-red-700 mt-1">{agentInfo.error}</p>
                      {agentInfo.traceback && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-red-600 text-xs">Show traceback</summary>
                          <pre className="text-xs mt-2 overflow-auto max-h-48 bg-red-100 p-2 rounded">
                            {agentInfo.traceback}
                          </pre>
                        </details>
                      )}
                    </div>
                  )}
                  {agentInfo.result && (
                    <div className="mt-3 p-3 bg-green-50 border-l-4 border-green-500 rounded">
                      <p className="font-semibold text-green-800">Result:</p>
                      <pre className="text-xs mt-1 overflow-auto max-h-48">
                        {JSON.stringify(agentInfo.result, null, 2)}
                      </pre>
                    </div>
                  )}
                  {agentInfo.logs && agentInfo.logs.length > 0 && (
                    <div className="mt-3 p-3 bg-blue-50 border-l-4 border-blue-500 rounded">
                      <p className="font-semibold text-blue-800">Execution Log:</p>
                      <div className="mt-2 space-y-1 max-h-64 overflow-y-auto">
                        {agentInfo.logs.map((log, idx) => (
                          <div key={idx} className="text-xs text-blue-900 font-mono">
                            {log}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;